# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os, time, threading, urllib.request,ssl
from PyQt6.QtCore import QUrl, pyqtSignal, QObject
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
import certifi
from .utils import resource_path, get_profile_path


BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
UPDATE_INTERVAL_DAYS = 7 # Check for a new list once a week.

class AdblockSignals(QObject):
    """Defines signals for the adblocker."""
    rules_updated = pyqtSignal(int) # Emits the new rule count

class AdblockUpdater(threading.Thread):
    """Runs the adblock update process in a background thread to not block the UI."""
    def __init__(self, adblocker_instance):
        super().__init__(daemon=True)
        self.adblocker = adblocker_instance

    def run(self):
        self.adblocker.update_rules_if_needed()

class AdblockInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Intercepts network requests and blocks them if they match the adblock list.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = set()
        self.signals = AdblockSignals()
        self.cache_path = os.path.join(get_profile_path(), "adblock_cache.txt")

    def load_rules(self):
        """
        Loads rules from the local cache or the bundled fallback list,
        and kicks off a background check for updates.
        """
        loaded_from_cache = False
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.rules = {line.strip() for line in f if line.strip()}
                print(f"Adblocker: Loaded {len(self.rules)} rules from cache.")
                loaded_from_cache = True
            except Exception as e:
                print(f"Adblocker: Error loading from cache: {e}")

        if not loaded_from_cache:
            # Fallback to the small bundled list if cache is unavailable
            try:
                blocklist_path = resource_path('assets/adblock_list.txt')
                if os.path.exists(blocklist_path):
                    with open(blocklist_path, 'r', encoding='utf-8') as f:
                        self.rules = {line.strip() for line in f if line.strip() and not line.startswith('!')}
                    print(f"Adblocker: Loaded {len(self.rules)} rules from bundled list.")
            except Exception as e:
                print(f"Adblocker: Error loading bundled rules: {e}")

        # Check for updates in a background thread
        updater_thread = AdblockUpdater(self)
        updater_thread.start()

    def force_update_rules(self):
        """Public method to allow forcing an update, e.g., from a UI button."""
        print("Adblocker: Force update requested.")
        # Run the forced update in a background thread
        force_updater_thread = threading.Thread(target=lambda: self.update_rules_if_needed(force=True), daemon=True)
        force_updater_thread.start()

    def update_rules_if_needed(self, force=False):
        """Checks if the cached list is stale and downloads a new one if needed."""
        needs_update = force
        if not os.path.exists(self.cache_path):
            needs_update = True
        elif not force:
            try:
                file_age_seconds = time.time() - os.path.getmtime(self.cache_path)
                if file_age_seconds > (UPDATE_INTERVAL_DAYS * 24 * 60 * 60):
                    needs_update = True
            except OSError:
                needs_update = True

        if needs_update:
            print("Adblocker: Updating blocklist from the network...")
            self._download_and_process_list()

    def _download_and_process_list(self):
        """Downloads the list from the URL, processes it, and saves to cache."""
        try:
            new_rules = set()
            # Create an SSL context that uses the certifi bundle for verification
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(BLOCKLIST_URL, timeout=30, context=ssl_context) as response:
                for line in response:
                    try:
                        line = line.decode('utf-8').strip()
                        # Hosts file format: "0.0.0.0 domain.com # comment"
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                                domain = parts[1]
                                if domain != 'localhost':
                                    new_rules.add(domain)
                    except (UnicodeDecodeError, IndexError):
                        continue # Ignore malformed lines
            
            if new_rules:
                self.rules = new_rules
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    for rule in sorted(list(self.rules)):
                        f.write(rule + '\n')
                print(f"Adblocker: Successfully updated. Loaded {len(self.rules)} new rules.")
                self.signals.rules_updated.emit(len(self.rules))
        except Exception as e:
            print(f"Adblocker: Failed to download or process new blocklist: {e}")

    def interceptRequest(self, info):
        """
        This method is called for every network request.
        """
        url = info.requestUrl().toString()

        # Check if the URL or its domain matches any of our rules
        if self.should_block(url):
            # print(f"Adblocker: Blocking {url}")
            info.block(True)

    def should_block(self, url: str) -> bool:
        """
        Checks if a given URL should be blocked based on the loaded rules.
        This is a simplified matching logic. Real adblockers have complex rule engines.
        """
        if not self.rules:
            return False

        try:
            parsed_url = QUrl(url)
            host = parsed_url.host()
            if not host:
                return False

            for rule in self.rules:
                # More precise matching:
                # 1. Exact match (e.g., host 'a.com' matches rule 'a.com')
                # 2. Subdomain match (e.g., host 'b.a.com' matches rule 'a.com')
                if host == rule or host.endswith('.' + rule):
                    return True
        except Exception:
            return False # Ignore invalid URLs
        return False