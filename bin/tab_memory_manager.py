# MIT License
#
# Copyright (c) 2021-2026 Souvik Nandi
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

"""
Tab Memory & Lifecycle Manager
==============================
Smart memory optimizer and tab lifecycle coordinator for Neutrino Browser and Qelaro Browser.

Features:
- Inactive tab auto-hibernation / sleeping (reduces multi-tab RAM/VRAM footprint)
- Closed tabs recovery stack (Ctrl+Shift+T undo tab close)
- Tab pinning protection (prevents accidental closures)
- Memory usage metrics and telemetry
"""

import time
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QUrl


class TabMemoryManager(QObject):
    """
    Manages tab activity, hibernates idle background tabs,
    and maintains the closed tab recovery history.
    """
    tabSleepingChanged = pyqtSignal(object, bool)  # (tab_widget, is_sleeping)
    tabPinnedChanged = pyqtSignal(object, bool)    # (tab_widget, is_pinned)
    closedTabsUpdated = pyqtSignal(int)            # count of restorable tabs

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.closed_tabs_stack: List[Dict] = []  # LIFO stack of closed tabs
        self.max_closed_history = 30

        # Memory optimization settings
        self.auto_discard_enabled = True
        self.discard_timeout_seconds = 20 * 60  # 20 minutes idle threshold
        self.min_tabs_before_discard = 3        # Only sleep tabs if >3 tabs open

        # Activity tracker
        self.tab_last_active: Dict[int, float] = {}  # id(tab) -> timestamp
        self.tab_pinned: Dict[int, bool] = {}        # id(tab) -> bool
        self.tab_saved_state: Dict[int, Dict] = {}   # id(tab) -> {url, title}

        # Periodic memory optimization timer
        self.check_timer = QTimer(self)
        self.check_timer.setInterval(60 * 1000)  # Check every 60 seconds
        self.check_timer.timeout.connect(self.check_idle_tabs)
        self.check_timer.start()

    def record_tab_active(self, tab):
        """Updates the active timestamp of a tab and wakes it if sleeping."""
        if not tab:
            return
        tab_id = id(tab)
        self.tab_last_active[tab_id] = time.time()
        if getattr(tab, "is_sleeping", False):
            self.wake_tab(tab)

    def record_tab_closed(self, tab, index: int):
        """Pushes closed tab details to the restoration stack."""
        if not tab:
            return
        
        tab_id = id(tab)
        # Clean up internal tracking
        self.tab_last_active.pop(tab_id, None)
        self.tab_pinned.pop(tab_id, None)
        self.tab_saved_state.pop(tab_id, None)

        # Do not save internal empty or setup pages
        url = tab.url().toString() if hasattr(tab, "url") else ""
        if not url or url.startswith(("about:blank", "disunic://newtab", "neutrino://newtab")):
            return

        title = tab.title() if hasattr(tab, "title") else "Untitled"
        self.closed_tabs_stack.append({
            "url": url,
            "title": title,
            "index": index,
            "closed_at": time.time()
        })

        if len(self.closed_tabs_stack) > self.max_closed_history:
            self.closed_tabs_stack.pop(0)

        self.closedTabsUpdated.emit(len(self.closed_tabs_stack))

    def restore_last_closed_tab(self):
        """Restores the most recently closed tab (Ctrl+Shift+T)."""
        if not self.closed_tabs_stack:
            if hasattr(self.main_window, "update_status_message"):
                self.main_window.update_status_message("No recently closed tabs to restore")
            return None

        tab_data = self.closed_tabs_stack.pop()
        self.closedTabsUpdated.emit(len(self.closed_tabs_stack))

        url_str = tab_data.get("url")
        if url_str and hasattr(self.main_window, "add_new_tab"):
            new_tab = self.main_window.add_new_tab(url=url_str, activate=True)
            if hasattr(self.main_window, "update_status_message"):
                self.main_window.update_status_message(f"Restored: {tab_data.get('title', url_str)}")
            return new_tab
        return None

    def toggle_pin_tab(self, tab):
        """Toggles pinned status for a tab."""
        tab_id = id(tab)
        current = self.tab_pinned.get(tab_id, False)
        new_state = not current
        self.tab_pinned[tab_id] = new_state
        setattr(tab, "is_pinned", new_state)
        self.tabPinnedChanged.emit(tab, new_state)
        return new_state

    def is_tab_pinned(self, tab) -> bool:
        """Returns True if tab is pinned."""
        return self.tab_pinned.get(id(tab), False) or getattr(tab, "is_pinned", False)

    def check_idle_tabs(self):
        """Evaluates background tabs and hibernates those exceeding idle threshold."""
        if not self.auto_discard_enabled:
            return
        if not hasattr(self.main_window, "tab_widget"):
            return

        tab_widget = self.main_window.tab_widget
        count = tab_widget.count()
        if count <= self.min_tabs_before_discard:
            return

        current_tab = self.main_window.current_browser()
        now = time.time()

        for i in range(count):
            tab = tab_widget.widget(i)
            # Never sleep the currently visible tab or pinned tabs
            if tab == current_tab or self.is_tab_pinned(tab):
                continue

            # Don't sleep tabs playing audio
            if hasattr(tab, "page") and tab.page().recentlyAudible():
                continue

            # Don't sleep internal special pages
            if hasattr(tab, "url"):
                url_str = tab.url().toString()
                if url_str.startswith(("disunic:", "neutrino:", "about:")):
                    continue

            tab_id = id(tab)
            last_active = self.tab_last_active.get(tab_id, now)
            if (now - last_active) > self.discard_timeout_seconds:
                if not getattr(tab, "is_sleeping", False):
                    self.sleep_tab(tab)

    def sleep_tab(self, tab):
        """Puts a background tab into memory-saving hibernation."""
        if not hasattr(tab, "url") or not hasattr(tab, "setHtml"):
            return

        url_str = tab.url().toString()
        title_str = tab.title() if hasattr(tab, "title") else "Sleeping Tab"

        tab_id = id(tab)
        self.tab_saved_state[tab_id] = {
            "url": url_str,
            "title": title_str
        }

        tab.is_sleeping = True
        sleeping_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>[Sleeping] {title_str}</title>
    <style>
        body {{
            background: #141416;
            color: #71717a;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            text-align: center;
        }}
        .card {{
            padding: 30px;
            border-radius: 12px;
            background: #1e1e24;
            border: 1px solid #2e2e38;
            max-width: 400px;
        }}
        h2 {{ color: #e4e4e7; font-size: 1.1rem; margin-bottom: 8px; }}
        p {{ font-size: 0.9rem; margin-bottom: 16px; }}
        button {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Tab Sleeping to Save Memory</h2>
        <p>{title_str}</p>
        <button onclick="window.location.href='{url_str}'">Wake Up Tab</button>
    </div>
</body>
</html>
"""
        tab.setHtml(sleeping_html, QUrl(url_str))
        self.tabSleepingChanged.emit(tab, True)

    def wake_tab(self, tab):
        """Restores a hibernated tab back to its original URL."""
        tab_id = id(tab)
        saved = self.tab_saved_state.pop(tab_id, None)
        tab.is_sleeping = False
        self.tabSleepingChanged.emit(tab, False)

        if saved and "url" in saved:
            tab.setUrl(QUrl(saved["url"]))
        elif hasattr(tab, "reload"):
            tab.reload()

    def get_memory_stats(self) -> Dict:
        """Returns statistics regarding sleeping and active tabs."""
        tab_widget = getattr(self.main_window, "tab_widget", None)
        total = tab_widget.count() if tab_widget else 0
        sleeping = 0
        pinned = 0
        if tab_widget:
            for i in range(total):
                w = tab_widget.widget(i)
                if getattr(w, "is_sleeping", False):
                    sleeping += 1
                if self.is_tab_pinned(w):
                    pinned += 1

        return {
            "total_tabs": total,
            "active_tabs": total - sleeping,
            "sleeping_tabs": sleeping,
            "pinned_tabs": pinned,
            "restorable_closed_tabs": len(self.closed_tabs_stack),
            "est_ram_saved_mb": round(sleeping * 85.0, 1)
        }
