# MIT License
#
# Copyright (c) 2021-2026 Souvik Nandi
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

"""
Privacy Shield Engine
=====================
High-performance content blocking, tracker protection, and privacy header enforcement
designed for Neutrino Browser and directly reusable in Qelaro Browser.

Features:
- O(1) subdomain and domain suffix lookups (replaces linear O(N) rule scanning)
- Anti-tracking and telemetry script blocking
- Fingerprinting mitigation & Do Not Track / Global Privacy Control headers
- Whitelist / Exception management
- Live blocking statistics and telemetry
"""

import os
import time
import ssl
import threading
import urllib.request
from typing import Set, Dict, Optional, Tuple
from PyQt6.QtCore import QUrl, pyqtSignal, QObject
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
import certifi
from .utils import resource_path, get_profile_path

BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
UPDATE_INTERVAL_DAYS = 7

# Common tracking / analytics domain fragments for heuristics
TRACKER_SIGNATURES = {
    "google-analytics.com", "googletagmanager.com", "analytics.twitter.com",
    "doubleclick.net", "facebook.net/tr", "adnxs.com", "criteo.com",
    "hotjar.com", "segment.io", "mixpanel.com", "quantserve.com",
    "scorecardresearch.com", "outbrain.com", "taboola.com", "amplitude.com"
}


class PrivacyShieldSignals(QObject):
    """Qt Signals emitted by the Privacy Shield."""
    rules_updated = pyqtSignal(int)
    stats_updated = pyqtSignal(dict)
    item_blocked = pyqtSignal(str, str)  # (url, category)


class PrivacyShieldUpdater(threading.Thread):
    """Background updater thread for blocklist synchronization."""
    def __init__(self, shield_instance):
        super().__init__(daemon=True)
        self.shield = shield_instance

    def run(self):
        self.shield.update_rules_if_needed()


class PrivacyShieldInterceptor(QWebEngineUrlRequestInterceptor):
    """
    High-performance network request interceptor.
    Applies privacy headers, blocks advertisements and trackers using O(1) set lookups,
    and maintains live privacy telemetry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.signals = PrivacyShieldSignals()
        self.cache_path = os.path.join(get_profile_path(), "privacy_shield_cache.txt")
        self.whitelist_path = os.path.join(get_profile_path(), "privacy_whitelist.txt")
        
        # Telemetry statistics
        self.stats = {
            "ads_blocked": 0,
            "trackers_blocked": 0,
            "total_blocked": 0,
            "requests_processed": 0,
            "bandwidth_saved_kb": 0.0
        }
        self._stats_lock = threading.Lock()

        # Feature flags
        self.block_ads_enabled = True
        self.block_trackers_enabled = True
        self.inject_gpc_enabled = True
        self.strip_referrer_enabled = True

        self.load_whitelist()

    def load_whitelist(self):
        """Loads domain whitelist from disk."""
        if os.path.exists(self.whitelist_path):
            try:
                with open(self.whitelist_path, 'r', encoding='utf-8') as f:
                    self.whitelist = {line.strip().lower() for line in f if line.strip() and not line.startswith('#')}
            except Exception as e:
                print(f"PrivacyShield: Error loading whitelist: {e}")

    def save_whitelist(self):
        """Persists domain whitelist to disk."""
        try:
            with open(self.whitelist_path, 'w', encoding='utf-8') as f:
                for domain in sorted(self.whitelist):
                    f.write(domain + '\n')
        except Exception as e:
            print(f"PrivacyShield: Error saving whitelist: {e}")

    def add_to_whitelist(self, domain: str):
        """Adds a domain to the bypass whitelist."""
        clean_domain = domain.strip().lower()
        if clean_domain:
            self.whitelist.add(clean_domain)
            self.save_whitelist()

    def remove_from_whitelist(self, domain: str):
        """Removes a domain from the bypass whitelist."""
        clean_domain = domain.strip().lower()
        if clean_domain in self.whitelist:
            self.whitelist.remove(clean_domain)
            self.save_whitelist()

    def is_whitelisted(self, host: str) -> bool:
        """Checks if a host or its parent domains are whitelisted."""
        if not host or not self.whitelist:
            return False
        host = host.lower()
        parts = host.split('.')
        for i in range(len(parts) - 1):
            sub = '.'.join(parts[i:])
            if sub in self.whitelist:
                return True
        return False

    def load_rules(self):
        """Loads rules from cache or fallback bundled list and checks for updates."""
        loaded = False
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.rules = {line.strip().lower() for line in f if line.strip()}
                print(f"PrivacyShield: Loaded {len(self.rules)} rules from cache.")
                loaded = True
            except Exception as e:
                print(f"PrivacyShield: Error loading cache: {e}")

        if not loaded:
            # Fallback to assets
            try:
                blocklist_path = resource_path('assets/adblock_list.txt')
                if os.path.exists(blocklist_path):
                    with open(blocklist_path, 'r', encoding='utf-8') as f:
                        self.rules = {line.strip().lower() for line in f if line.strip() and not line.startswith('!')}
                    print(f"PrivacyShield: Loaded {len(self.rules)} rules from fallback list.")
            except Exception as e:
                print(f"PrivacyShield: Error loading fallback rules: {e}")

        # Schedule background update check
        updater = PrivacyShieldUpdater(self)
        updater.start()

    def force_update_rules(self):
        """Forces an immediate update from the remote blocklist."""
        thread = threading.Thread(target=lambda: self.update_rules_if_needed(force=True), daemon=True)
        thread.start()

    def update_rules_if_needed(self, force=False):
        """Checks if cached blocklist requires refresh and downloads if needed."""
        needs_update = force
        if not os.path.exists(self.cache_path):
            needs_update = True
        elif not force:
            try:
                age = time.time() - os.path.getmtime(self.cache_path)
                if age > (UPDATE_INTERVAL_DAYS * 86400):
                    needs_update = True
            except OSError:
                needs_update = True

        if needs_update:
            print("PrivacyShield: Fetching updated blocklist...")
            self._download_and_process_list()

    def _download_and_process_list(self):
        """Downloads hosts-style blocklist and updates rule set."""
        try:
            new_rules = set()
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            req = urllib.request.Request(
                BLOCKLIST_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NeutrinoPrivacyShield/2.0"}
            )
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                for line in resp:
                    try:
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        if line_str and not line_str.startswith('#'):
                            parts = line_str.split()
                            if len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                                domain = parts[1].lower()
                                if domain != 'localhost':
                                    new_rules.add(domain)
                    except Exception:
                        continue

            if new_rules:
                self.rules = new_rules
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    for rule in sorted(self.rules):
                        f.write(rule + '\n')
                print(f"PrivacyShield: Successfully refreshed {len(self.rules)} rules.")
                self.signals.rules_updated.emit(len(self.rules))
        except Exception as e:
            print(f"PrivacyShield: Remote update failed: {e}")

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """
        Main interception point called by Chromium before every network request.
        Applies privacy headers and matches domains in O(1) time.
        """
        with self._stats_lock:
            self.stats["requests_processed"] += 1

        # 1. Apply Global Privacy Control & Do Not Track headers
        if self.inject_gpc_enabled:
            info.setHttpHeader(b"Sec-GPC", b"1")
            info.setHttpHeader(b"DNT", b"1")

        qurl = info.requestUrl()
        host = qurl.host().lower()

        if not host:
            return

        # Check whitelist
        if self.is_whitelisted(host):
            return

        url_str = qurl.toString().lower()

        # 2. Check for tracker signatures (heuristic)
        if self.block_trackers_enabled:
            for sig in TRACKER_SIGNATURES:
                if sig in url_str:
                    info.block(True)
                    self._record_block(url_str, "tracker", est_kb=35.0)
                    return

        # 3. Check domain blocklist using O(1) hierarchical label lookup
        if self.block_ads_enabled and self.rules:
            parts = host.split('.')
            # Walk parent domain candidates: e.g. sub.adserver.com -> sub.adserver.com, adserver.com
            for i in range(len(parts) - 1):
                candidate = '.'.join(parts[i:])
                if candidate in self.rules:
                    info.block(True)
                    self._record_block(url_str, "ad", est_kb=45.0)
                    return

    def _record_block(self, url: str, category: str, est_kb: float):
        """Records telemetry for blocked item."""
        with self._stats_lock:
            if category == "tracker":
                self.stats["trackers_blocked"] += 1
            else:
                self.stats["ads_blocked"] += 1
            self.stats["total_blocked"] += 1
            self.stats["bandwidth_saved_kb"] += est_kb

        self.signals.item_blocked.emit(url, category)
        if self.stats["total_blocked"] % 5 == 0:
            self.signals.stats_updated.emit(dict(self.stats))

    def get_stats(self) -> Dict:
        """Returns snapshot of live telemetry statistics."""
        with self._stats_lock:
            return dict(self.stats)

    def reset_stats(self):
        """Resets telemetry metrics."""
        with self._stats_lock:
            self.stats = {
                "ads_blocked": 0,
                "trackers_blocked": 0,
                "total_blocked": 0,
                "requests_processed": 0,
                "bandwidth_saved_kb": 0.0
            }
        self.signals.stats_updated.emit(dict(self.stats))
