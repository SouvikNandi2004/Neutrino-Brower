# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
import re
import json
import sys
import urllib.parse
from PyQt6.QtCore import QUrl, Qt, QSettings, QPoint, QSize, QEvent, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import ( #
    QMainWindow, QLineEdit, QToolBar, QPushButton, QMenu, QApplication,
    QMessageBox, QVBoxLayout, QLabel, QListWidget, QDialogButtonBox, QDialog, QStyle, QListWidgetItem, QWidget, QHBoxLayout,
    QCheckBox, QTabBar, QStackedWidget, QFileDialog
)
from PyQt6.QtGui import QAction, QIcon, QMouseEvent, QCloseEvent
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtNetwork import QNetworkProxy
from browser_tab import BrowserTab
from download_manager import DownloadManagerPage
from settings_page import SettingsPage
from history_manager import HistoryManager
from .updater import Updater
from .utils import get_profile_path, SVG_ICONS, create_icon_from_svg, qicon_to_base64
from .url_bar import UrlBar

# Global reference to main window
main_window = None

class HistoryPageBackend(QObject):
    """Backend object to expose Python history functions to JavaScript."""
    historyCleared = pyqtSignal()

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self._history_manager = history_manager

    @pyqtSlot(int)
    def removeHistoryItem(self, history_id):
        """Removes a single history item by its ID."""
        self._history_manager.remove_visit(history_id)

class TorBrowser(QMainWindow):
    __version__ = "1.0.1"

    def __init__(self):
        super().__init__()
        global main_window
        main_window = self
        self.setObjectName("MainWindow")
        # Make the window frameless. Qt.Window is necessary for it to show in the taskbar.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.drag_pos = QPoint()

        # --- Additions for resizing ---
        self._resizing = False
        self._resize_edge = None
        self._resize_margin = 8  # Pixels
        # self.setMouseTracking(True) # No longer needed, will be handled by event filter
        self.setMinimumSize(600, 400) # Set a reasonable minimum size

        # --- Theme Colors ---
        self.BG_COLOR = "#0d0d0d"  # Near-black for a sleeker look
        self.TEXT_COLOR = "#f0f0f0" # Brighter white for better contrast
        self.TOOLBAR_COLOR = "#1a1a1a" # Slightly lighter than background
        self.URL_BAR_COLOR = "#2c313c" # Kept for consistency
        self.ACCENT_COLOR = "#007aff" # Apple's vibrant blue for a modern feel
        self.BORDER_COLOR = "#2a2a2a" # Softer border color
        self.DANGER_COLOR = "#ff3b30" # Apple's red for destructive actions
        self.TAB_INACTIVE_COLOR = "rgba(255, 255, 255, 0.08)" # More visible inactive tabs
        self.TAB_ACTIVE_COLOR = "#2c2c2c" # A distinct active tab color

        # Create persistent profile
        self.profile = QWebEngineProfile("DisunicXProfile", self)
        self.profile.setPersistentStoragePath(get_profile_path())
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setCachePath(os.path.join(get_profile_path(), "Cache"))
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.set_tor_proxy()

        # Show welcome dialog before any UI setup
        self.history_manager = HistoryManager()
        self.download_manager = DownloadManagerPage(self)
        self.download_manager_is_in_tab = False
        self.settings_page = SettingsPage(self.profile, self, self)
        self.settings_page_is_in_tab = False

        # This needs to be called before the UI is built so the window can be shown
        # if the dialog is accepted.
        self.setWindowTitle(f"DisunicX v{self.__version__}")
        self.setGeometry(100, 100, 1200, 800)

        self.toolbar = QToolBar("mainToolbar")

        if not self.show_welcome_if_first_time():
            QApplication.instance().quit()
            return  # Prevent further initialization

        self.setStyleSheet(f"""
            #MainWindow, #TitleBarWidget {{
                background-color: {self.BG_COLOR};
                color: {self.TEXT_COLOR};
                /* A 1px border helps distinguish the window when not maximized */
                border: 1px solid #101216;
            }}
            #TitleBarWidget {{
                background-color: {self.BG_COLOR};
            }}
            QToolBar {{
                background-color: {self.TOOLBAR_COLOR};
                border: none;
                padding: 5px;
                spacing: 5px;
            }}
            #mainToolbar QPushButton {{
                background-color: transparent;
                color: {self.TEXT_COLOR};
                border: none;
                border-radius: 6px;
                padding: 7px;
                font-size: 14px;
            }}
            #mainToolbar QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            #mainToolbar QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
            #UrlEdit {{
                background-color: transparent;
                color: {self.TEXT_COLOR};
                border: none; /* Border is on the container */
                padding: 8px 10px;
                font-size: 14px;
            }}
            #UrlBar QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
                border-radius: 6px;
            }}
            #UrlBarButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            /* Container for the URL bar to get a focus ring */
            #UrlBar {{
                background-color: rgba(255, 255, 255, 0.07);
                /* Use a slightly lighter, more visible border */
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
            }}
            #UrlBar[hasFocus="true"] {{
                border: 1px solid {self.ACCENT_COLOR};
            }}

            /* Main content area background */
            #ContentStack {{
                background: {self.BG_COLOR};
            }}

            /* --- Custom Title/Tab Bar --- */
            QTabBar {{
                background: transparent;
                border: none;
                margin-left: 8px;
            }}
            /* Style for the '+' new tab button */
            QTabBar QToolButton, #NewTabBtn {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 8px;
                margin: 8px 4px 0 4px;
                font-size: 18px;
            }}
            QTabBar QToolButton:hover, #NewTabBtn:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}

            /* --- Tab Scroller Arrows --- */
            QTabBar::scroller QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
                margin: 4px;
            }}
            QTabBar::scroller QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QTabBar::left-arrow {{
                image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["back"].replace("currentColor", "white"))}');
            }}
            QTabBar::right-arrow {{
                image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["forward"].replace("currentColor", "white"))}');
            }}
            QTabBar::left-arrow:disabled, QTabBar::right-arrow:disabled {{
                image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["back"].replace("currentColor", "#666"))}');
            }}

            QTabBar::tab {{
                background: {self.TAB_INACTIVE_COLOR};
                color: #a0a0a0;
                padding: 8px 20px;
                border: none;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px; /* Add space between tabs */
                margin-top: 8px;
            }}
            QTabBar::tab:!selected:hover {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }}
            QTabBar::tab:selected {{
                background: {self.TAB_ACTIVE_COLOR}; /* Match the toolbar below */
                color: {self.TEXT_COLOR};
                /* Make selected tab taller to overlap the top of the toolbar area */
                padding-bottom: 9px; /* Make selected tab slightly taller to hide the line */
                margin-top: 6px;
            }}
            /* --- Custom Window Controls --- */
            .WindowControlBtn {{
                background-color: transparent;
                color: {self.TEXT_COLOR};
                border: none;
                font-size: 14px;
                font-family: "Segoe UI Symbol", "sans-serif";
                width: 46px;
                height: 32px;
            }}
            .WindowControlBtn:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            #CloseBtn:hover {{
                background-color: #e81123;
            }}
            QTabBar::close-button {{
                image: url('data:image/svg+xml,%3csvg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="white" viewBox="0 0 16 16"%3e%3cpath d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/%3e%3c/svg%3e');
                subcontrol-position: right;
                subcontrol-origin: padding;
                margin: 2px;
                background-color: transparent; /* Ensure button is always rendered */
                padding: 2px;
                border-radius: 4px;
            }}
            QTabBar::close-button:hover {{
                background-color: {self.DANGER_COLOR}; /* Red background on hover */
            }}
            QTabBar::close-button:pressed {{
                background-color: #c0392b; /* Darker red on press */
            }}

            /* Status Bar */
            QStatusBar#StatusBar {{
                background-color: transparent;
                border-top: 1px solid {self.BORDER_COLOR};
            }}
            QLabel#StatusLabel {{
                color: #aaa;
                padding-left: 10px;
                background-color: transparent;
            }}
            QWidget#TorStatusWidget {{
                background-color: rgba(0, 230, 118, 0.15); /* Greenish background */
                border-radius: 8px;
                border: 1px solid rgba(0, 230, 118, 0.3);
                margin: 2px 4px;
            }}
            QLabel#TorStatusLabel {{
                color: #00e676; /* Green color */
                font-weight: 500;
                background-color: transparent;
            }}
        """)

        # --- Main Layout Structure ---
        main_container = QWidget()
        main_container.setMouseTracking(True)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Custom Title Bar Area
        self.title_bar_widget = QWidget()
        self.title_bar_widget.setObjectName("TitleBarWidget")
        self.title_bar_widget.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(self.title_bar_widget)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(0)

        # setup_tabs will now create self.tab_bar and self.stacked_widget
        self.setup_tabs()
        title_bar_layout.addWidget(self.tab_bar)
        title_bar_layout.addWidget(self.new_tab_btn)
        title_bar_layout.addStretch(1)

        # Custom window control buttons
        self.window_controls_widget = QWidget()
        window_controls_layout = QHBoxLayout(self.window_controls_widget)
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        window_controls_layout.setSpacing(0)

        self.minimize_btn = QPushButton("—")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("✕")
        self.minimize_btn.setProperty("class", "WindowControlBtn")
        self.maximize_btn.setProperty("class", "WindowControlBtn")
        self.close_btn.setProperty("class", "WindowControlBtn")
        self.close_btn.setObjectName("CloseBtn")

        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.close)

        window_controls_layout.addWidget(self.minimize_btn)
        window_controls_layout.addWidget(self.maximize_btn)
        window_controls_layout.addWidget(self.close_btn)
        title_bar_layout.addWidget(self.window_controls_widget, 0, Qt.AlignmentFlag.AlignTop)

        # 2. Toolbar
        self.setup_toolbar()
        
        self.status = self.statusBar()
        self.status.setObjectName("StatusBar")

        # Left side: status message
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status.addWidget(self.status_label, 1) # stretch = 1

        # Right side: Tor status widget
        self.tor_status_widget = QWidget()
        self.tor_status_widget.setObjectName("TorStatusWidget")
        tor_status_layout = QHBoxLayout(self.tor_status_widget)
        tor_status_layout.setContentsMargins(8, 0, 8, 0)
        tor_status_layout.setSpacing(5)

        self.tor_status_icon = QLabel()
        tor_status_layout.addWidget(self.tor_status_icon)

        self.tor_status_label = QLabel()
        self.tor_status_label.setObjectName("TorStatusLabel")
        tor_status_layout.addWidget(self.tor_status_label)

        self.status.addPermanentWidget(self.tor_status_widget)

        self.update_status_message("Ready")
        self.update_tor_status(QUrl()) # Initial setup
        self.update_security_button_tooltip()

        # Add all widgets to the main layout
        main_layout.addWidget(self.title_bar_widget)
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.status)

        self.setCentralWidget(main_container)

        # Add initial tab
        self.add_new_tab()
        
        # Install the global event filter to handle window movement and resizing
        QApplication.instance().installEventFilter(self)

        # Check for updates on startup
        self.check_for_updates()

    def get_new_tab_html(self):
        """Generates the HTML for the custom new tab page."""
        settings = QSettings("DisunicX", "Browser")
        search_engine = settings.value("search_engine", "DuckDuckGo")

        # Convert hex to RGB for transparent colors
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        bg_rgb = hex_to_rgb(self.BG_COLOR)
        text_color = self.TEXT_COLOR
        border_color = self.BORDER_COLOR
        accent_color = self.ACCENT_COLOR
        icon_color = self.TEXT_COLOR
        tab_text_color = "#a0a0a0" # From stylesheet
        button_hover_color = "rgba(255, 255, 255, 0.1)" # From stylesheet

        # Icons for buttons
        settings_icon = SVG_ICONS['settings_general'].replace("currentColor", icon_color)
        history_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M12 8v4l2 2"/></svg>'.replace("currentColor", icon_color)
        downloads_icon = SVG_ICONS['downloads'].replace("currentColor", icon_color)
        search_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'.replace("currentColor", tab_text_color)

        # The JS needs the search engine name, which we inject directly.
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Tab</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: {text_color};
            overflow: hidden;
        }}
        .background-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url('https://picsum.photos/1920/1080?grayscale&blur=2');
            background-size: cover;
            background-position: center;
            z-index: -1;
        }}
        .main-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .frosted-glass {{
            background-color: rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.8);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            padding: 3rem 4rem;
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            flex-direction: column;
            gap: 2rem; /* gap-8 */
            max-width: 700px;
            width: 90%;
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }}
        h1 {{
            font-size: 3rem; /* text-5xl */
            font-weight: bold;
            margin: 0;
            background: linear-gradient(to right, #4a90e2, #8e44ad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .search-form {{
            position: relative;
            width: 100%;
        }}
        .search-input {{
            width: 100%;
            padding: 1rem 1rem 1rem 3rem; /* pl-12 */
            border-radius: 9999px; /* rounded-full */
            background-color: rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.5); /* bg-background/50 */
            border: 1px solid {border_color};
            color: {text_color};
            font-size: 1.1rem;
            outline: none;
            transition: border-color 0.3s, box-shadow 0.3s;
            box-sizing: border-box;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); /* shadow-lg */
        }}
        .search-input:focus {{
            border-color: {accent_color};
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.3);
        }}
        .search-input::placeholder {{
            color: {tab_text_color};
        }}
        .search-icon {{
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            color: {tab_text_color};
            pointer-events: none;
        }}
        .action-buttons {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        .action-btn {{
            display: inline-flex;
            align-items: center;
            background-color: transparent;
            border: 1px solid {border_color};
            color: {text_color};
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s, border-color 0.2s;
        }}
        .action-btn:hover {{
            background-color: {button_hover_color};
            border-color: {accent_color};
        }}
        .action-btn svg {{
            width: 16px;
            height: 16px;
            margin-right: 0.5rem; /* mr-2 */
        }}
    </style>
</head>
<body>
    <div class="background-container"></div>
    <main class="main-content">
        <div class="frosted-glass">
            <h1>DisunicX</h1>

            <form id="search-form" class="search-form">
                <div class="search-icon">{search_icon_svg}</div>
                <input type="text" id="search-input" class="search-input"
                    placeholder="Search with {search_engine} or enter address" 
                    autocomplete="off" autofocus>
            </form>

            <div class="action-buttons">
                <button id="settings-btn" class="action-btn">{settings_icon} Settings</button>
                <button id="history-btn" class="action-btn">{history_icon_svg} History</button>
                <button id="downloads-btn" class="action-btn">{downloads_icon} Downloads</button>
            </div>
        </div>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const searchForm = document.getElementById('search-form');
            const searchInput = document.getElementById('search-input');
            const searchEngine = "{search_engine}";
            
            searchForm.addEventListener('submit', (e) => {{
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {{
                    // Basic check for URL
                    if ((query.includes('.') && !query.includes(' ')) || query.startsWith('http')) {{
                        let url = query;
                        if (!url.startsWith('http://') && !url.startsWith('https://')) {{
                            url = 'https://' + url;
                        }}
                        window.location.href = url;
                        return;
                    }}

                    const encodedQuery = encodeURIComponent(query);
                    const urls = {{
                        'Google': `https://www.google.com/search?q=${{encodedQuery}}`,
                        'Bing': `https://www.bing.com/search?q=${{encodedQuery}}`,
                        'Yahoo': `https://search.yahoo.com/search?p=${{encodedQuery}}`,
                        'StartPage': `https://www.startpage.com/do/search?query=${{encodedQuery}}`,
                        'Ecosia': `https://www.ecosia.org/search?q=${{encodedQuery}}`,
                        'Disunic': `https://souviknandi1.github.io/search.html#gsc.tab=0&gsc.sort=&gsc.q=${{encodedQuery}}`,
                        'DuckDuckGo': `https://duckduckgo.com/?q=${{encodedQuery}}`
                    }};
                    window.location.href = urls[searchEngine] || urls['DuckDuckGo'];
                }}
            }});

            document.getElementById('settings-btn').addEventListener('click', () => {{
                window.location.href = 'disunic://settings';
            }});
            document.getElementById('history-btn').addEventListener('click', () => {{
                window.location.href = 'disunic://history';
            }});
            document.getElementById('downloads-btn').addEventListener('click', () => {{
                window.location.href = 'disunic://downloads';
            }});
        }});
    </script>
</body>
</html>
"""

    def get_history_page_html(self):
        """Generates the HTML for the custom history page."""
        history_items = self.history_manager.get_history(limit=500)
        history_json = json.dumps([ # Renamed 'item' to 'h_item' to avoid conflict
            {
                "id": h_item[0],
                "url": h_item[1],
                "title": h_item[2] if h_item[2] else h_item[1],
                "visit_time": h_item[3],
                "favicon": h_item[4]
            }
            for h_item in history_items
        ])

        # Using f-strings for colors, and {{}} for JS objects
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <script>
                // This is the official qwebchannel.js file from Qt, required for JS-Python communication.
                var QWebChannel=function(a,b){{"object"!=typeof a&&console.error("Cannot construct QWebChannel, no transport object given!"),this.transport=a,this.transport.onmessage=function(c){{var d=c.data;"string"==typeof d&&(d=JSON.parse(d)),e.handleMessage(d)}},this.execCallbacks={{}},this.execId=0,this.objects={{}},this.objectSignals={{}},this.send=function(c){{"string"!=typeof c&&(c=JSON.stringify(c)),e.transport.send(c)}};var e=this;this.handleMessage=function(c){{var d=c.type;d===QWebChannelMessageTypes.signal?e.handleSignal(c):d===QWebChannelMessageTypes.response?e.handleResponse(c):d===QWebChannelMessageTypes.propertyUpdate?e.handlePropertyUpdate(c):console.error("invalid message received:",c)}},this.handleSignal=function(c){{var d=e.objects[c.object];if(d){{var f=c.signal;if(f){{var g=e.objectSignals[c.object][f];g&&g.apply(g,c.args)}}}}}},this.handleResponse=function(c){{var d=e.execCallbacks[c.id];d&&(d(c.data),delete e.execCallbacks[c.id])}},this.handlePropertyUpdate=function(c){{for(var d in c.data){{var f=c.data[d],g=e.objects[f.object];if(g){{var h=f.signal;if(h){{var i=g[h];i&&i.apply(i,f.args)}}}}}}}},this.exec=function(c,d){{if(!d)return c.type=QWebChannelMessageTypes.invokeMethod,void e.send(c);var f=++e.execId;c.id=f,c.type=QWebChannelMessageTypes.invokeMethod,e.execCallbacks[f]=d,e.send(c)}},this.registerObject=function(c,d){{e.objects[c]=d;for(var f in d.signals){{var g=d.signals[f];void 0===e.objectSignals[c]&&(e.objectSignals[c]={{}}),e.objectSignals[c][g]=d[g]}}if(d.signalEmitted)d.signalEmitted.connect(function(){{for(var d=[],f=1;f<arguments.length;++f)d.push(arguments[f]);e.exec({{type:QWebChannelMessageTypes.signal,object:c,signal:arguments[0],args:d}})}})}},this.debug=function(c){{e.send({{type:"debug",data:c}})}},e.exec({{type:QWebChannelMessageTypes.init}},function(c){{for(var d in c){{var f=new QObject(d,c[d],e);e.registerObject(d,f)}}for(var d in e.objects)e.objects[d].unwrapSignals();b&&b(e)}})}},QWebChannelMessageTypes={{signal:1,propertyUpdate:2,init:3,invokeMethod:4,connectToSignal:5,disconnectFromSignal:6,setProperty:7,response:8}},QObject=function(a,b,c){{this.__id__=a,this.webChannel=c,this.isSignalConnected={{}};var d=this;this.signals=[],this.properties=[],this.methods=[];var e=function(a,b){{this.name=a,this.args=b,this.callbacks=[],this.connect=function(b){{"function"!=typeof b?console.error("Signal.connect: callback is not a function!"):(this.callbacks.push(b),d.isSignalConnected[a]||(d.webChannel.exec({{type:QWebChannelMessageTypes.connectToSignal,object:d.__id__,signal:a}}),d.isSignalConnected[a]=!0))}},this.disconnect=function(b){{"function"!=typeof b?console.error("Signal.disconnect: callback is not a function!"):this.callbacks.indexOf(b)===-1?console.error("Signal.disconnect: callback not found!"):(this.callbacks.splice(idx,1),0===this.callbacks.length&&d.isSignalConnected[a]&&(d.webChannel.exec({{type:QWebChannelMessageTypes.disconnectFromSignal,object:d.__id__,signal:a}}),delete d.isSignalConnected[a]))}},this.apply=function(a,b){{for(var c=0;c<this.callbacks.length;++c)this.callbacks[c].apply(a,b)}}}};this.addSignal=function(a,b){{var c=new e(a,b);d[a]=c,d.signals.push(a)}},this.unwrapSignals=function(){{for(var a in d.properties){{var b=d.properties[a],c=d[b];if(c.notifier){{var e=d[c.notifier];e&&(c.notifier=function(a,b){{return function(){{b.value=arguments[0],a.apply(a,arguments)}}}}(e,c))}}}}}};for(var f in b.properties){{var g=b.properties[f];this.addProperty(g.type,g.name,g.notifier)}}for(var f in b.signals){{var h=b.signals[f];this.addSignal(h.name,h.args)}}for(var f in b.methods){{var i=b.methods[f];!function(a,b){{d[a]=function(){{for(var e=[],f=void 0,g=0;g<arguments.length;++g)"function"==typeof arguments[g]?f=arguments[g]:e.push(arguments[g]);d.webChannel.exec({{type:QWebChannelMessageTypes.invokeMethod,object:d.__id__,method:a,args:e}},f)}}}}(i.name,i.args)}}}};
            </script>
            <meta charset="UTF-8">
            <title>History - DisunicX</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{
                    background-color: {self.BG_COLOR};
                    color: {self.TEXT_COLOR};
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }}
                .search-bar {{
                    background-color: {self.TOOLBAR_COLOR};
                    border: 1px solid {self.BORDER_COLOR};
                    color: {self.TEXT_COLOR};
                }}
                .history-item {{
                    border-bottom: 1px solid {self.TOOLBAR_COLOR};
                    transition: background-color 0.2s;
                }}
                .history-item:hover {{
                    background-color: {self.TOOLBAR_COLOR};
                }}
                .url-text {{
                    color: #b0bec5; /* Brighter color for better visibility */
                }}
                .favicon {{
                    width: 16px;
                    height: 16px;
                    margin-right: 12px;
                    flex-shrink: 0;
                }}
                .clear-btn {{
                    background-color: {self.DANGER_COLOR};
                    transition: background-color 0.2s;
                }}
                .clear-btn:hover {{
                    background-color: #c0392b;
                }}
            </style>
        </head>
        <body class="p-4 md:p-8">
            <div class="max-w-5xl mx-auto">
                
                <h1 class="text-3xl font-bold mb-6">History</h1>
                
                <input type="text" id="search-input" placeholder="Search history..." 
                       class="w-full p-3 rounded-md search-bar focus:outline-none focus:ring-2 focus:ring-blue-500">
                
                <ul id="history-list" class="mt-6">
                    <!-- History items will be rendered here -->
                </ul>
                <p id="no-results" class="text-center text-gray-400 mt-8 hidden">No history items found.</p>
            </div>

            <script>
                const historyData = {history_json};

                const list = document.getElementById('history-list');
                const searchInput = document.getElementById('search-input');
                const noResults = document.getElementById('no-results');
                const defaultFavicon = `<svg class="favicon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#aaa" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/></svg>`;

                function formatTime(isoString) {{
                    const date = new Date(isoString);
                    return date.toLocaleString(undefined, {{
                        year: 'numeric', month: 'long', day: 'numeric', 
                        hour: 'numeric', minute: '2-digit'
                    }});
                }}

                function renderHistory(items) {{
                    if (items.length === 0) {{
                        list.innerHTML = '';
                        noResults.classList.remove('hidden');
                        return;
                    }}
                    noResults.classList.add('hidden');

                    let html = '';
                    for (const item of items) {{
                        const faviconHtml = item.favicon ? `<img src="${{item.favicon}}" class="favicon" alt="">` : defaultFavicon;
                        html += `<li class="history-item flex justify-between items-center p-3">
                            <a href="${{item.url}}" class="flex items-center flex-grow overflow-hidden mr-4">
                                ${{faviconHtml}}
                                <div class="flex-grow overflow-hidden">
                                    <p class="text-base truncate" title="${{item.title}}">${{item.title}}</p>
                                    <p class="text-sm url-text truncate">${{item.url}}</p>
                                </div>
                            </a>
                            <div class="flex items-center flex-shrink-0">
                                <p class="text-sm text-gray-400 mr-4 whitespace-nowrap">${{formatTime(item.visit_time)}}</p>
                                <button data-history-id="${{item.id}}" class="remove-item-btn p-1 rounded-full hover:bg-gray-600 transition-colors" title="Remove from history">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="text-gray-400" viewBox="0 0 16 16"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/></svg>
                                </button>
                            </div>
                        </li>`;
                    }}
                    list.innerHTML = html;
                }}

                searchInput.addEventListener('input', (e) => {{
                    const searchTerm = e.target.value.toLowerCase();
                    if (!searchTerm) {{
                        renderHistory(historyData);
                        return;
                    }}
                    const filteredItems = historyData.filter(item => 
                        item.title.toLowerCase().includes(searchTerm) || 
                        item.url.toLowerCase().includes(searchTerm)
                    );
                    renderHistory(filteredItems);
                }});

                // Event delegation for remove buttons
                list.addEventListener('click', function(e) {{
                    const removeButton = e.target.closest('.remove-item-btn');
                    if (removeButton) {{
                        const historyId = removeButton.dataset.historyId;
                        if (historyId && window.backend) {{
                            window.backend.removeHistoryItem(parseInt(historyId, 10));
                            
                            // Optimistically remove from UI
                            removeButton.closest('li').remove();

                            // Also remove from local data to keep search consistent
                            const index = historyData.findIndex(item => item.id == historyId);
                            if (index > -1) {{
                                historyData.splice(index, 1);
                            }}
                            if (historyData.length === 0 && list.children.length === 0) {{
                                noResults.classList.remove('hidden');
                            }}
                        }}
                    }}
                }});

                // Setup communication channel with Python backend
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.backend = channel.objects.backend;

                    window.backend.historyCleared.connect(() => {{
                        document.getElementById('history-list').innerHTML = '';
                        document.getElementById('no-results').classList.remove('hidden');
                        historyData.length = 0; // Clear the local data array
                    }});
                }});

                // Initial render
                renderHistory(historyData);
            </script>
        </body>
        </html>
        """

    def get_about_page_html(self):
        """Generates the HTML for the custom about page."""
        about_content = (
            f"<h2 style='color:{self.ACCENT_COLOR}; font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem;'>DisunicX Browser</h2>"
            f"<p style='font-size:1.1rem; color: #a0b3d6;'>Version <b>1.0</b></p>"
            f"<p style='font-size:1rem; margin-top: 1.5rem;'>An <b>open source</b> privacy-focused browser using the Tor network.<br>"
            f"Built for security, anonymity, and freedom.</p>"
            f"<p style='font-size:1rem; margin-top: 1rem; color:{self.ACCENT_COLOR};'>Developed by Souvik Nandi</p>"
            f"<p style='font-size:1rem; margin-top:1rem;'><b>Built with:</b><br>PySide6, Qt WebEngine, and Python</p>"
            f"<hr style='border: none; border-top: 1px solid {self.BORDER_COLOR}; margin: 2rem 0;'>"
            f"<p style='font-size:0.8rem; color:#8f96a8;'>DisunicX is not responsible for any misuse or illegal activity.<br>"
            "You use this software at your own risk.</p>"
        )

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>About DisunicX</title>
            <style>
                body {{
                    background-color: {self.BG_COLOR};
                    color: {self.TEXT_COLOR};
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    text-align: center;
                }}
                .container {{
                    max-width: 600px;
                    padding: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {about_content}
            </div>
        </body>
        </html>
        """

    def handle_new_download(self, download_item):
        """Handles a download request from any tab."""
        # Ensure the downloads page/tab exists and is visible
        self.open_downloads()
        # Add the download to the page
        self.download_manager.add_download(download_item)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # We only care about events for our window or its children, and only when it's active
        if not self.isActiveWindow():
            return super().eventFilter(watched, event)
        if not isinstance(watched, QWidget) or watched.window() is not self:
            return super().eventFilter(watched, event)

        # Get event position in global and window-local coordinates
        if event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick]:
            global_pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(global_pos)

        # --- Handle Mouse Move for resizing cursor and dragging ---
        if event.type() == QEvent.Type.MouseMove:
            if event.buttons() == Qt.MouseButton.LeftButton:
                if self._resizing:
                    self.resize_window(global_pos)
                    return True  # Consume event
                elif not self.drag_pos.isNull():
                    if self.isMaximized():
                        self.toggle_maximize()
                        self.drag_pos = QPoint(int(self.width() * (local_pos.x() / self.width())), 15)
                    self.move(global_pos - self.drag_pos)
                    return True  # Consume event
            elif not self.isMaximized():
                self.update_resize_cursor(local_pos)

        # --- Handle Mouse Press to initiate resizing or dragging ---
        elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if not self.isMaximized():
                self._resize_edge = self.get_resize_edge(local_pos)
                if self._resize_edge is not None:
                    self._resizing = True
                    return True  # Consume event
            # Check for title bar drag, but ignore if it's on interactive elements.
            # We need to map the point to the title bar's coordinate system for accurate hit-testing.
            title_bar_pos = self.title_bar_widget.mapFrom(self, local_pos)
            on_controls = self.window_controls_widget.geometry().contains(title_bar_pos)
            on_new_tab_btn = self.new_tab_btn.geometry().contains(title_bar_pos)
            on_tab_bar = self.tab_bar.geometry().contains(title_bar_pos)
            if local_pos.y() < self.title_bar_widget.height() and not on_controls and not on_new_tab_btn and not on_tab_bar:
                    self.drag_pos = global_pos - self.frameGeometry().topLeft()
                    return True  # Consume event

        # --- Handle Mouse Release to stop resizing/dragging ---
        elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if self._resizing or not self.drag_pos.isNull():
                self.drag_pos = QPoint()
                self._resizing = False
                self._resize_edge = None
                self.unsetCursor()
                return True  # Consume event

        # --- Handle Double-click on title bar ---
        elif event.type() == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
            # Only maximize if double-clicking the empty space on the title bar.
            # We need to map the point to the title bar's coordinate system for accurate hit-testing.
            title_bar_pos = self.title_bar_widget.mapFrom(self, local_pos)
            on_controls = self.window_controls_widget.geometry().contains(title_bar_pos)
            on_new_tab_btn = self.new_tab_btn.geometry().contains(title_bar_pos)
            on_tab_bar = self.tab_bar.geometry().contains(title_bar_pos)
            if local_pos.y() < self.title_bar_widget.height() and not on_controls and not on_new_tab_btn and not on_tab_bar:
                    self.toggle_maximize()
                    return True  # Consume event

        return super().eventFilter(watched, event)

    def get_resize_edge(self, pos: QPoint):
        """Check if the mouse position is on a resizable edge."""
        margin = self._resize_margin
        rect = self.rect()
        
        on_left = abs(pos.x() - rect.left()) < margin
        on_right = abs(pos.x() - rect.right()) < margin
        on_top = abs(pos.y() - rect.top()) < margin
        on_bottom = abs(pos.y() - rect.bottom()) < margin

        if on_top and on_left: return "topleft"
        if on_top and on_right: return "topright"
        if on_bottom and on_left: return "bottomleft"
        if on_bottom and on_right: return "bottomright"
        if on_left: return "left"
        if on_right: return "right"
        if on_top: return "top"
        if on_bottom: return "bottom"
        
        return None

    def resize_window(self, global_pos: QPoint):
        """Resize the window based on the edge being dragged."""
        rect = self.geometry()
        min_size = self.minimumSize()

        if self._resize_edge == "top":
            if rect.height() - (global_pos.y() - rect.y()) > min_size.height():
                rect.setTop(global_pos.y())
        elif self._resize_edge == "bottom":
            rect.setBottom(global_pos.y())
        elif self._resize_edge == "left":
            if rect.width() - (global_pos.x() - rect.x()) > min_size.width():
                rect.setLeft(global_pos.x())
        elif self._resize_edge == "right":
            rect.setRight(global_pos.x())
        elif self._resize_edge == "topleft":
            if rect.height() - (global_pos.y() - rect.y()) > min_size.height():
                rect.setTop(global_pos.y())
            if rect.width() - (global_pos.x() - rect.x()) > min_size.width():
                rect.setLeft(global_pos.x())
        elif self._resize_edge == "topright":
            if rect.height() - (global_pos.y() - rect.y()) > min_size.height():
                rect.setTop(global_pos.y())
            rect.setRight(global_pos.x())
        elif self._resize_edge == "bottomleft":
            rect.setBottom(global_pos.y())
            if rect.width() - (global_pos.x() - rect.x()) > min_size.width():
                rect.setLeft(global_pos.x())
        elif self._resize_edge == "bottomright":
            rect.setBottom(global_pos.y())
            rect.setRight(global_pos.x())
        
        self.setGeometry(rect)

    def update_resize_cursor(self, pos: QPoint):
        """Sets the appropriate resize cursor when hovering over window edges."""
        edge = self.get_resize_edge(pos)
        if edge in ("top", "bottom"):
            self.setCursor(Qt.SizeVerCursor)
        elif edge in ("left", "right"):
            self.setCursor(Qt.SizeHorCursor)
        elif edge in ("topleft", "bottomright"):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge in ("topright", "bottomleft"):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def changeEvent(self, event):
        # This event is triggered when the window state changes (e.g., maximized, minimized)
        if event.type() == QEvent.Type.WindowStateChange:
            # Update the maximize button icon and window margins
            if self.isMaximized():
                self.maximize_btn.setText("❐")
                self.maximize_btn.setToolTip("Restore")
                # Remove margins when maximized for a seamless full-screen look
                self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
            else:
                self.maximize_btn.setText("□")
                self.maximize_btn.setToolTip("Maximize")
                # Restore the 1px border when not maximized
                self.centralWidget().layout().setContentsMargins(1, 1, 1, 1)
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent):
        """Overrides the default close event to check for active downloads."""
        if self.download_manager and self.download_manager.has_active_downloads():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Downloads in Progress")
            msg_box.setText("You have active downloads. Closing the browser will cancel them. Are you sure you want to exit?")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            yes_button.setObjectName("AccentButton")

            msg_box.setStyleSheet(f"""
                QMessageBox {{ background-color: {self.TOOLBAR_COLOR}; border: 1px solid {self.BORDER_COLOR}; }}
                QMessageBox QLabel {{ color: {self.TEXT_COLOR}; font-size: 14px; }}
                QMessageBox QPushButton {{ background-color: rgba(255, 255, 255, 0.1); border: 1px solid {self.BORDER_COLOR}; padding: 8px 16px; border-radius: 4px; color: {self.TEXT_COLOR}; min-width: 80px; }}
                QMessageBox QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.15); border: 1px solid {self.ACCENT_COLOR}; }}
                QMessageBox QPushButton#AccentButton {{ background-color: {self.ACCENT_COLOR}; border-color: {self.ACCENT_COLOR}; color: white; }}
                QMessageBox QPushButton#AccentButton:hover {{ background-color: #5aa1f2; }}
            """)
            
            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Yes:
                # User wants to close, proceed.
                self.download_manager.clear_all()
                event.accept()
            else:
                # User wants to keep the browser open.
                event.ignore()
        else:
            # No active downloads, close normally.
            event.accept()

    def setup_tabs(self):
        self.tab_bar = QTabBar()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentStack")

        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setUsesScrollButtons(True)
        self.tab_bar.setElideMode(Qt.ElideRight) # Ensure text is truncated with '...' when needed
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

        # Create the "New Tab" button to be added to the layout later
        self.new_tab_btn = QPushButton("+", objectName="NewTabBtn")
        self.new_tab_btn.clicked.connect(self.add_new_tab)

    def set_tor_proxy(self):
        settings = QSettings("DisunicX", "Browser")
        if settings.value("use_proxy", True, type=bool):
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.ProxyType.Socks5Proxy)
            proxy.setHostName(str(settings.value("proxy_host", "127.0.0.1")))
            proxy.setPort(int(settings.value("proxy_port", 9050)))
            QNetworkProxy.setApplicationProxy(proxy)
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
    
    def setup_toolbar(self):
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(20, 20))

        self.back_btn = QPushButton()
        self.back_btn.setIcon(create_icon_from_svg(SVG_ICONS["back"], self.TEXT_COLOR))
        self.back_btn.setToolTip("Back")
        self.back_btn.clicked.connect(lambda: self.current_browser().back())
        self.toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(create_icon_from_svg(SVG_ICONS["forward"], self.TEXT_COLOR))
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.clicked.connect(lambda: self.current_browser().forward())
        self.toolbar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(create_icon_from_svg(SVG_ICONS["reload"], self.TEXT_COLOR))
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.clicked.connect(lambda: self.current_browser().reload())
        self.toolbar.addWidget(self.reload_btn)

        self.home_btn = QPushButton()
        self.home_btn.setIcon(create_icon_from_svg(SVG_ICONS["home"], self.TEXT_COLOR))
        self.home_btn.setToolTip("Home")
        self.home_btn.clicked.connect(self.navigate_home)
        self.toolbar.addWidget(self.home_btn)

        self.url_bar = UrlBar()
        self.url_bar.setObjectName("UrlBar") # For styling the container
        self.url_bar.url_edit.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        downloads_btn = QPushButton()
        downloads_btn.setIcon(create_icon_from_svg(SVG_ICONS["downloads"], self.TEXT_COLOR))
        downloads_btn.setToolTip("Downloads")
        downloads_btn.clicked.connect(self.open_downloads)
        self.toolbar.addWidget(downloads_btn)

        self.security_level_btn = QPushButton()
        self.security_level_btn.setIcon(create_icon_from_svg(SVG_ICONS["security_level"], self.TEXT_COLOR))
        self.security_level_btn.clicked.connect(lambda: self.open_settings(tab_index=1))
        self.toolbar.addWidget(self.security_level_btn)

        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(create_icon_from_svg(SVG_ICONS["menu"], self.TEXT_COLOR))
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self.show_menu)
        self.toolbar.addWidget(self.menu_btn)
    
    def open_dev_tools(self):
        # Ensure we only open dev tools for a web tab
        if isinstance(self.current_browser(), BrowserTab):
            self.current_browser().open_dev_tools()
    
    def handle_print_action(self):
        """Handles the print action from the menu by saving to PDF."""
        widget = self.current_browser()
        if isinstance(widget, BrowserTab):
            # Suggest a filename based on the page title
            default_filename = widget.title().replace(" ", "_") + ".pdf"
            
            path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Page as PDF", 
                default_filename, 
                "PDF files (*.pdf)"
            )
            if path:
                widget.page().printToPdf(path, self._pdf_print_finished)

    def _pdf_print_finished(self, success):
        """Callback for when the PDF print operation is finished."""
        if success:
            self.update_status_message("Page saved as PDF.")
        else:
            QMessageBox.warning(self, "Save to PDF Failed", "Could not save the page as a PDF.")
            self.update_status_message("Failed to save PDF.")

    def open_new_window(self):
        """Creates and shows a new browser window instance."""
        new_window = TorBrowser()
        new_window.show()

    def update_navigation_state(self, *args):
        """Updates the state of navigation buttons based on the current tab."""
        widget = self.stacked_widget.currentWidget()
        is_web_tab = isinstance(widget, BrowserTab)

        self.back_btn.setEnabled(is_web_tab and widget.history().canGoBack())
        self.forward_btn.setEnabled(is_web_tab and widget.history().canGoForward())
        self.reload_btn.setEnabled(is_web_tab)
        self.home_btn.setEnabled(is_web_tab)
        self.url_bar.setEnabled(is_web_tab)

    def show_menu(self):
        menu = QMenu(self)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: rgba(30, 30, 30, 0.70); /* Increased transparency */
                color: {self.TEXT_COLOR};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                margin: 0;
                border-radius: 4px;
                min-width: 140px;
            }}
            QMenu::item:selected {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {self.TEXT_COLOR};
            }}
            QMenu::separator {{
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                margin: 8px 0;
            }}
        """)
        
        is_web_tab = isinstance(self.current_browser(), BrowserTab)
        
        # Create actions without icons
        actions = [
            ("New Tab", self.add_new_tab),
            ("New Window", self.open_new_window),
            None,  # Separator
            ("Downloads", self.open_downloads),
            ("History", self.open_history),
            None,  # Separator
            ("Save Page as PDF...", self.handle_print_action),
            None,  # Separator
            ("Settings", self.open_settings),
            ("About DisunicX", self.show_about),
            ("Clear Browsing Data", self.clear_browsing_data),
            None,  # Separator
            ("Exit", self.close)
        ]
        
        for action in actions:
            if action is None:
                menu.addSeparator()
            else:
                text, handler = action
                act = QAction(text, self)
                if text in ["Save Page as PDF..."] and not is_web_tab:
                    act.setEnabled(False)
                act.triggered.connect(handler)
                menu.addAction(act)
        
        # Calculate position with offset
        btn_pos = self.menu_btn.pos()
        menu_pos = self.mapToGlobal(btn_pos) + QPoint(0, self.menu_btn.height() + 4)
        
        menu.exec(menu_pos)

    def open_history(self):
        # Check if a history tab is already open and switch to it
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                self.tab_bar.setCurrentIndex(i)
                return

        # If not, create a new tab for history
        html = self.get_history_page_html()
        browser = self.add_new_tab()

        # Setup QWebChannel to allow JS to call Python
        channel = QWebChannel(browser.page())
        history_backend = HistoryPageBackend(self.history_manager)
        channel.registerObject("backend", history_backend)
        browser.page().setWebChannel(channel)

        # Keep backend and channel alive with the browser tab to prevent garbage collection
        browser.history_backend = history_backend
        browser.channel = channel

        browser.setHtml(html, QUrl("disunic://history"))

    def open_downloads(self):
        """Opens the download manager in a new tab, or switches to it if already open."""
        if self.download_manager_is_in_tab:
            # Find the tab and switch to it
            for i in range(self.stacked_widget.count()):
                if self.stacked_widget.widget(i) == self.download_manager:
                    self.tab_bar.setCurrentIndex(i)
                    return
        
        # If not in a tab, add it
        index = self.stacked_widget.addWidget(self.download_manager)
        self.tab_bar.addTab("Downloads")
        self.tab_bar.setTabIcon(index, create_icon_from_svg(SVG_ICONS["downloads"], self.TEXT_COLOR))
        self.tab_bar.setCurrentIndex(index)
        self.download_manager_is_in_tab = True


    def open_settings(self, tab_index=0):
        """Opens the settings page in a new tab, or switches to it if already open."""
        if self.settings_page_is_in_tab:
            # Find the tab and switch to it
            for i in range(self.stacked_widget.count()):
                if self.stacked_widget.widget(i) == self.settings_page:
                    self.tab_bar.setCurrentIndex(i)
                    self.settings_page.nav_list.setCurrentRow(tab_index) # Also switch to the correct inner tab
                    return

        # If not in a tab, add it
        index = self.stacked_widget.addWidget(self.settings_page)
        self.tab_bar.addTab("Settings")
        self.tab_bar.setTabIcon(index, create_icon_from_svg(SVG_ICONS["settings_general"], self.TEXT_COLOR))
        self.tab_bar.setCurrentIndex(index)
        self.settings_page.nav_list.setCurrentRow(tab_index)
        self.settings_page_is_in_tab = True

    def update_security_button_tooltip(self):
        settings = QSettings("DisunicX", "Browser")
        level = settings.value("security_level", 0, type=int)
        levels = ["Standard", "Safer", "Safest"]
        self.security_level_btn.setToolTip(f"Security Level: {levels[level]}")
    
    def clear_browsing_data(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Clear Browsing Data")
        msg_box.setText("Are you sure you want to clear all browsing data (history, cookies, cache)?")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setObjectName("AccentButton")

        msg_box.setStyleSheet(f"""
            QMessageBox {{ background-color: {self.TOOLBAR_COLOR}; border: 1px solid {self.BORDER_COLOR}; }}
            QMessageBox QLabel {{ color: {self.TEXT_COLOR}; font-size: 14px; }}
            QMessageBox QPushButton {{ background-color: rgba(255, 255, 255, 0.1); border: 1px solid {self.BORDER_COLOR}; padding: 8px 16px; border-radius: 4px; color: {self.TEXT_COLOR}; min-width: 80px; }}
            QMessageBox QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.15); border: 1px solid {self.ACCENT_COLOR}; }}
            QMessageBox QPushButton#AccentButton {{ background-color: {self.ACCENT_COLOR}; border-color: {self.ACCENT_COLOR}; color: white; }}
            QMessageBox QPushButton#AccentButton:hover {{ background-color: #5aa1f2; }}
        """)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            self.history_manager.clear_history()
            self.download_manager.clear_all()

            # Find and update any open history tabs
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                    if hasattr(widget, 'history_backend'):
                        # Emit the signal to tell the JS to clear its view
                        widget.history_backend.historyCleared.emit()
            
            info_box = QMessageBox(self)
            info_box.information(self, "Information", "All browsing data has been cleared.")
    
    def show_about(self):
        # Check if an about tab is already open
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://about":
                self.tab_bar.setCurrentIndex(i)
                return

        # If not, create a new tab for it
        html = self.get_about_page_html()
        browser = self.add_new_tab()
        browser.setHtml(html, QUrl("disunic://about"))
    
    def add_new_tab(self, url=None):
        # Ensure url is a QUrl object if it's passed as a string
        if isinstance(url, str):
            url = QUrl(url)

        browser = BrowserTab(self.profile)
        browser.page_loaded_for_history.connect(self.add_to_history)
        browser.urlChanged.connect(self.update_url_bar)
        browser.urlChanged.connect(self.update_navigation_state)

        # Track loading state
        browser.is_loading = False

        def on_load_started():
            browser.is_loading = True
            self.update_status_message("Loading...")

        def on_load_progress(p):
            browser.is_loading = True
            self.update_status_message(f"Loading... {p}%")

        def on_load_finished(ok):
            browser.is_loading = False
            self.update_status_message("Ready" if ok else "Failed to load")
            self.update_navigation_state()

        browser.page().loadStarted.connect(on_load_started)
        browser.page().loadProgress.connect(on_load_progress)
        browser.page().loadFinished.connect(on_load_finished)
        browser.page().linkHovered.connect(lambda url: self.update_status_message(url if url else ("Loading..." if browser.is_loading else "Ready")))

        browser.titleChanged.connect(self.update_tab_title)
        browser.page().iconChanged.connect(lambda icon, b=browser: self.update_tab_icon(b, icon))

        load_new_tab_page = False
        if url is None or isinstance(url, bool):
            settings = QSettings("DisunicX", "Browser")
            startup_behavior = settings.value("startup_behavior", 0, type=int)
            if startup_behavior in [0, 1]:  # Open new tab page or continue session (which defaults to new tab)
                load_new_tab_page = True
            else:  # Open blank page
                url = QUrl("about:blank")

        # Add to stacked widget and tab bar
        index = self.stacked_widget.addWidget(browser)
        self.tab_bar.addTab("Loading...")
        self.tab_bar.setTabIcon(index, QIcon()) # Placeholder for icon
        self.tab_bar.setCurrentIndex(index)

        # Load the content
        if load_new_tab_page:
            html = self.get_new_tab_html()
            browser.setHtml(html, QUrl("disunic://newtab"))
        else:
            browser.setUrl(url)
        
        return browser

    def add_to_history(self, url, title, icon):
        icon_b64 = qicon_to_base64(icon)
        self.history_manager.add_visit(url, title, icon_b64)

    def on_tab_changed(self, index):
        if index > -1:
            self.stacked_widget.setCurrentIndex(index)
            widget = self.stacked_widget.widget(index)

            if isinstance(widget, BrowserTab):
                url_str = widget.url().toString()
                if hasattr(widget, "is_loading") and widget.is_loading:
                    self.update_status_message("Loading...")
                elif url_str == "disunic://history":
                    self.update_status_message("History")
                elif url_str == "disunic://about":
                    self.update_status_message("About DisunicX")
                else:
                    self.update_status_message("Ready")
                self.update_url_bar(widget.url())
            elif isinstance(widget, DownloadManagerPage):
                self.update_url_bar(QUrl("disunic://downloads"))
                self.update_status_message("Downloads")
            elif isinstance(widget, SettingsPage):
                self.update_url_bar(QUrl("disunic://settings"))
                self.update_status_message("Settings")
            
            self.update_navigation_state()
        else:
            self.update_url_bar(QUrl(""))
            self.update_status_message("Ready")
            self.update_navigation_state()
    
    def close_tab(self, index):
        if self.tab_bar.count() > 1:
            widget_to_remove = self.stacked_widget.widget(index)

            # Special handling for the download manager tab
            if widget_to_remove == self.download_manager:
                self.stacked_widget.removeWidget(widget_to_remove)
                self.tab_bar.removeTab(index)
                self.download_manager_is_in_tab = False
                # IMPORTANT: Do not delete the widget, just hide it.
                # It's parented to the main window, so it won't be garbage collected.
            elif widget_to_remove == self.settings_page:
                self.stacked_widget.removeWidget(widget_to_remove)
                self.tab_bar.removeTab(index)
                self.settings_page_is_in_tab = False
            else:
                self.stacked_widget.removeWidget(widget_to_remove)
                self.tab_bar.removeTab(index)
                widget_to_remove.deleteLater() # Important to free memory
        else:
            self.close()
    
    def current_browser(self):
        return self.stacked_widget.currentWidget()

    def update_status_bar(self, message):
        self.status.showMessage(message)
    
    def update_status_message(self, message="Ready"):
        # Truncate long hover URLs
        if message.startswith("http") and len(message) > 80:
            message = message[:77] + "..."
        self.status_label.setText(message) 

    def update_tor_status(self, url: QUrl):
        settings = QSettings("DisunicX", "Browser")
        if settings.value("use_proxy", True, type=bool):
            is_onion = url.host().endswith(".onion")
            if is_onion:
                self.tor_status_widget.setToolTip(
                    "This is an onion service. Traffic is end-to-end encrypted and relayed through the DisunicX network."
                )
                self.tor_status_label.setText("Secured by DisunicX Servers")
            else:
                self.tor_status_widget.setToolTip(
                    "Your connection is secured using the Tor network."
                )
                self.tor_status_label.setText("Dark Web Active")
            
            self.tor_status_icon.setPixmap(create_icon_from_svg(SVG_ICONS["tor_active"], "#00e676", size=QSize(14, 14)).pixmap(QSize(14, 14)))
            self.tor_status_widget.show()
        else:
            self.tor_status_widget.hide()
    
    def navigate_home(self):
        html = self.get_new_tab_html()
        self.current_browser().setHtml(html, QUrl("disunic://newtab"))

    def navigate_to_url(self):
        url = self.url_bar.url_edit.text().strip()
        settings = QSettings("DisunicX", "Browser")
        search_engine = settings.value("search_engine", "DuckDuckGo")
        
        if url.lower() == "disunic://settings":
            self.open_settings()
            return
        
        current_browser = self.current_browser()
        
        # Check if it's already a valid URL
        if re.match(r"^(https?://|about:|file:)", url):
            self.current_browser().setUrl(QUrl(url))
            return
        
        # Check if it's a domain name (contains dot but no spaces)
        if '.' in url and not ' ' in url and not url.startswith('www.'):
            # Try with https:// prefix
            self.current_browser().setUrl(QUrl(f"https://{url}"))
            return
        
        SEARCH_URL_TEMPLATES = {
            "Disunic": "https://souviknandi1.github.io/search.html#gsc.tab=0&gsc.sort=&gsc.q={{query}}",
            "DuckDuckGo": "https://duckduckgo.com/?q={query}",
            "Google": "https://www.google.com/search?q={query}",
            "Bing": "https://www.bing.com/search?q={query}",
            "Yahoo": "https://search.yahoo.com/search?p={query}",
            "StartPage": "https://www.startpage.com/do/search?query={query}",
            "Ecosia": "https://www.ecosia.org/search?q={query}",
        }
        
        # Otherwise treat as search query
        if settings.value("default_search", True, type=bool):
            template = SEARCH_URL_TEMPLATES.get(search_engine, SEARCH_URL_TEMPLATES["DuckDuckGo"])
            search_url = template.format(query=urllib.parse.quote(url))
        else:
            # Fallback to DuckDuckGo
            template = SEARCH_URL_TEMPLATES["DuckDuckGo"]
            search_url = template.format(query=urllib.parse.quote(url))
        
        self.current_browser().setUrl(QUrl(search_url))
    
    def update_url_bar(self, url):
        self.url_bar.setUrl(url)
        # Update Tor status based on the new URL
        self.update_tor_status(url)

    def update_tab_title(self, title):
        index = self.tab_bar.currentIndex()
        if index != -1:
            self.tab_bar.setTabText(index, title)

    def update_tab_icon(self, browser, icon):
        index = self.stacked_widget.indexOf(browser)
        if index != -1:
            self.tab_bar.setTabIcon(index, icon)

    def check_for_updates(self):
        """Initializes and runs the application updater."""
        self.updater = Updater(current_version=self.__version__, parent=self)
        self.updater.check_for_updates()
    
    def show_welcome_if_first_time(self):
        settings = QSettings("DisunicX", "Browser")
        if not settings.value("terms_accepted", False, type=bool):
            dialog = QDialog(self)
            dialog.setWindowTitle("Welcome to DisunicX Browser")
            dialog.setMinimumWidth(550) # type: ignore
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)  # Disable close button

            layout = QVBoxLayout(dialog)
            welcome_label = QLabel(
                f"<h2 style='color:{self.ACCENT_COLOR};'>Welcome to DisunicX Browser!</h2>"
                f"<p>This browser is an <b>open source project</b> built for privacy and security. "
                f"It uses the Tor network to help protect your anonymity online.</p>"
                f"<p><b>Disclaimer:</b> DisunicX and its contributors are not responsible for any illegal, harmful, or unethical activities performed using this browser. "
                f"You use this software at your own risk.</p>"
                f"<p>By clicking <b>Accept</b>, you agree to these terms and conditions.</p>"
            )
            welcome_label.setWordWrap(True)
            layout.addWidget(welcome_label)

            terms_checkbox = QCheckBox("I accept the terms and conditions")
            layout.addWidget(terms_checkbox)

            button_layout = QHBoxLayout()
            accept_btn = QPushButton("Accept")
            accept_btn.setEnabled(False)
            decline_btn = QPushButton("Decline")
            button_layout.addWidget(accept_btn)
            button_layout.addWidget(decline_btn)
            layout.addLayout(button_layout)

            def on_checkbox_changed(state):
                accept_btn.setEnabled(terms_checkbox.isChecked())
            terms_checkbox.stateChanged.connect(on_checkbox_changed)

            def on_accept():
                settings.setValue("terms_accepted", True)
                dialog.accept()
                
                info_box = QMessageBox(self)
                info_box.setWindowTitle("Thank You")
                info_box.setText("Thank you for accepting the terms. Enjoy browsing securely!")
                info_box.setIcon(QMessageBox.Icon.Information)
                ok_button = info_box.addButton(QMessageBox.StandardButton.Ok)
                ok_button.setObjectName("AccentButton")
                info_box.setStyleSheet(f"""
                    QMessageBox {{ background-color: {self.TOOLBAR_COLOR}; border: 1px solid {self.BORDER_COLOR}; }}
                    QMessageBox QLabel {{ color: {self.TEXT_COLOR}; font-size: 14px; }}
                    QMessageBox QPushButton {{ background-color: {self.ACCENT_COLOR}; border: 1px solid {self.ACCENT_COLOR}; padding: 8px 16px; border-radius: 4px; color: white; min-width: 80px; }}
                    QMessageBox QPushButton:hover {{ background-color: #5aa1f2; }}
                """)
                info_box.exec()

            accept_btn.clicked.connect(on_accept)

            def on_decline():
                dialog.reject()
            decline_btn.clicked.connect(on_decline)

            result = dialog.exec()
            return result == QDialog.DialogCode.Accepted
        return True