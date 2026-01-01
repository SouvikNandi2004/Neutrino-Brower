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
import base64
import html
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtCore import QUrl, Qt, QSettings, QPoint, QSize, QEvent, QObject, pyqtSlot, pyqtSignal, QTimer, QRectF ,QPropertyAnimation,QEasingCurve
from PyQt6.QtWidgets import (
    QMainWindow, QLineEdit, QToolBar, QPushButton, QMenu, QApplication, QFrame,
    QMessageBox, QVBoxLayout, QLabel, QListWidget, QDialogButtonBox, QDialog, QStyle, QListWidgetItem, QWidget, QHBoxLayout, QScrollArea,
    QCheckBox, QTabBar, QStackedWidget, QFileDialog 
)
from PyQt6.QtGui import QAction, QIcon, QMouseEvent, QCloseEvent, QKeySequence, QShortcut, QPixmap, QPainter, QPainterPath, QColor
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtNetwork import QNetworkProxy
from bin.browser_tab import BrowserTab
from bin.download_manager import DownloadManagerPage
from bin.settings_page import SettingsPage
from bin.history_manager import HistoryManager
from bin.bookmarks_manager import BookmarksManager
from bin.updater import Updater
from bin.adblocker import AdblockInterceptor
from bin.utils import get_profile_path, SVG_ICONS, create_icon_from_svg, qicon_to_base64, qpixmap_to_base64, DraggableFramelessDialog, CustomMessageBox
from bin.url_bar import UrlBar
from bin.tab_widget import TabWidget
from bin.find_bar import FindBar
from bin.tab_overview import TabOverview
from bin.bookmarks_bar import BookmarksBar

# Global reference to main window
main_window = None

class RoundedIconLabel(QLabel):
    """A QLabel that displays a pixmap with a circular mask."""
    def __init__(self, pixmap, size, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.pixmap)

class WelcomeDialog(DraggableFramelessDialog):
    """A custom, styled dialog for the first-time welcome and terms agreement."""
    def __init__(self, parent=None):
        # We pass `None` to the super constructor to ensure this dialog is a true
        # top-level window, which is necessary for it to appear before the main
        # window is visible. The `parent` argument is still used to get a
        # reference to the main window for theming and other properties.
        super().__init__(None)
        self.main_window = parent
        self.setMinimumWidth(500)
        self.setMaximumWidth(500)
        
        # The parent DraggableFramelessDialog provides self.content_layout
        self.content_layout.setSpacing(0)

        # --- Header with Icon ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 35, 30, 25)
        header_layout.setSpacing(15)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_pixmap = QPixmap()
        try:
            # Go up two levels from the current script's directory to find the project root
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            favicon_path_png = os.path.join(app_root, 'favicon.png')
            favicon_path_ico = os.path.join(app_root, 'favicon.ico')
            
            logo_path = None
            if os.path.exists(favicon_path_png):
                logo_path = favicon_path_png
            elif os.path.exists(favicon_path_ico):
                logo_path = favicon_path_ico

            if logo_path:
                logo_pixmap.load(logo_path)
        except Exception as e:
            print(f"Could not load logo for welcome dialog: {e}")

        if not logo_pixmap.isNull():
            icon_label = RoundedIconLabel(logo_pixmap, 64, self)
        else:
            # Fallback to SVG if logo not found
            icon_label = QLabel()
            theme = self.main_window.theme
            accent_color = self.main_window.ACCENT_COLOR
            icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['security_level'], accent_color, QSize(64, 64)).pixmap(QSize(64, 64)))

        header_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Welcome to Neutrino")
        title_label.setObjectName("DialogTitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        intro_label = QLabel(
            "A production-ready, open-source browser from India, built for privacy and security and powered by the Tor network."
        )
        intro_label.setWordWrap(True)
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_label.setObjectName("IntroLabel")
        header_layout.addWidget(intro_label)

        self.content_layout.addWidget(header_widget)

        # --- Scrollable Terms Area ---
        terms_scroll_area = QScrollArea()
        terms_scroll_area.setObjectName("TermsScrollArea")
        terms_scroll_area.setWidgetResizable(True)
        terms_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(25, 15, 25, 20)

        terms_label = QLabel(
            "<h3>Disclaimer & Terms of Use</h3>"
            "<p>Neutrino Browser is an open-source project. By using this software, you acknowledge and agree to the following:</p>"
            "<ul>"
            "<li><b>At Your Own Risk:</b> This software is provided 'as is', without warranty of any kind. You assume all risks associated with its use, including but not limited to data loss, system failure, or security breaches.</li>"
            "<li><b>No Liability:</b> The developers and contributors of Neutrino are not liable for any direct, indirect, incidental, or consequential damages arising from the use of this software.</li>"
            "<li><b>Legal Responsibility:</b> You are solely responsible for your actions while using this browser. Any illegal, harmful, or unethical activities are strictly your own responsibility.</li>"
            "</ul>"
            "<p>By clicking 'Accept & Continue', you confirm that you have read, understood, and agree to be bound by these terms.</p>"
        )
        terms_label.setWordWrap(True)
        terms_label.setObjectName("TermsLabel")
        scroll_layout.addWidget(terms_label)
        terms_scroll_area.setWidget(scroll_content)
        
        self.content_layout.addWidget(terms_scroll_area, 1) # Make it stretch

        # --- Checkbox ---
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(30, 15, 30, 15)
        self.terms_checkbox = QCheckBox("I have read and agree to the terms and conditions")
        checkbox_layout.addWidget(self.terms_checkbox)
        self.content_layout.addWidget(checkbox_widget)

        # --- Button Footer ---
        button_widget = QWidget()
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.addStretch()

        self.decline_btn = QPushButton("Decline")
        self.decline_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.decline_btn)

        self.accept_btn = QPushButton("Accept & Continue")
        self.accept_btn.setObjectName("AccentButton")
        self.accept_btn.setEnabled(False)
        self.accept_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.accept_btn)

        self.terms_checkbox.stateChanged.connect(lambda state: self.accept_btn.setEnabled(state == Qt.CheckState.Checked.value))
        self.content_layout.addWidget(button_widget)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        theme = self.main_window.theme
        # A helper to get an "R, G, B" string from a color definition
        def get_rgb_string(color_str):
            if color_str.startswith('#'):
                h = color_str.lstrip('#')
                return ', '.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
            return "0, 0, 0" # Fallback
        bg_rgb = get_rgb_string(theme['BG_COLOR'])
        accent_color = self.main_window.ACCENT_COLOR
        check_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" viewBox="0 0 16 16"><path d="M10.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/></svg>'

        # Apply styles to the container that has the shadow
        self.shadow_container.setStyleSheet(f"""
            #ShadowContainer {{
                background-color: rgba({bg_rgb}, 0.75);
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 12px;
            }}
            #DialogTitleLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
            }}
            #IntroLabel {{
                font-size: 14px;
                color: {theme['TAB_TEXT_COLOR']};
                max-width: 380px;
                font-weight: 700;
            }}
            #TermsScrollArea {{
                background-color: transparent;
                border: none;
                margin: 0 10px; /* Give the scroll area some breathing room */
                border-radius: 0px; /* No radius for the scroll area itself */
            }}
            #TermsScrollArea QWidget {{ /* The widget inside the scroll area */
                background-color: transparent;
            }}
            #TermsLabel {{
                font-size: 13px;
                color: {theme['TAB_TEXT_COLOR']};
                background-color: transparent;
                font-weight: 700;
            }}
            #TermsLabel h3 {{
                font-size: 16px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
            }}
            #TermsLabel ul {{ padding-left: 20px; }}
            #TermsLabel li {{ margin-bottom: 10px; }}

            QCheckBox {{
                color: {theme['TEXT_COLOR']};
                font-size: 13px;
                font-weight: 700;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 4px;
                border: 1px solid {theme['BORDER_COLOR']};
                background-color: {theme['URL_BAR_BG']};
            }}
            QCheckBox::indicator:hover {{ border-color: {accent_color}; }}
            QCheckBox::indicator:checked {{
                background-color: {accent_color};
                border-color: {accent_color};
                image: url('data:image/svg+xml,{urllib.parse.quote(check_icon_svg)}');
            }}
            #ButtonWidget {{ 
                background-color: {theme['TOOLBAR_COLOR']}; 
                border-top: 1px solid {theme['BORDER_COLOR']}; 
                border-bottom-left-radius: 12px; 
                border-bottom-right-radius: 12px; 
            }}
            QPushButton {{ 
                background-color: {theme['MSGBOX_BUTTON_BG']}; 
                border: 1px solid {theme['BORDER_COLOR']}; 
                padding: 8px 16px; 
                border-radius: 6px; 
                color: {theme['TEXT_COLOR']}; 
                min-width: 90px; 
                font-weight: 700; 
            }}
            QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {accent_color}; }}
            QPushButton:disabled {{
                background-color: {theme['MSGBOX_BUTTON_BG']};
                color: {theme['DISABLED_TEXT_COLOR']};
                border-color: {theme['BORDER_COLOR']};
            }}
            #AccentButton {{ background-color: {accent_color}; border-color: {accent_color}; color: white; }}
            #AccentButton:hover {{ background-color: #5aa1f2; }}
            #AccentButton:disabled {{
                background-color: {theme['DISABLED_TEXT_COLOR']};
                border-color: {theme['DISABLED_TEXT_COLOR']};
                color: {theme['TEXT_COLOR']};
            }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {theme['BORDER_COLOR']}; min-height: 20px; border-radius: 4px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

class HistoryPageBackend(QObject):
    """Backend object to expose Python history functions to JavaScript."""
    historyCleared = pyqtSignal()
    clearHistoryRequested = pyqtSignal()

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self._history_manager = history_manager

    @pyqtSlot(int)
    def removeHistoryItem(self, history_id):
        """Removes a single history item by its ID."""
        self._history_manager.remove_visit(history_id)

    @pyqtSlot()
    def clearHistory(self):
        """
        Emits a signal to request the 'Clear Browsing Data' confirmation dialog.
        """
        self.clearHistoryRequested.emit()

class TorBrowser(QMainWindow):
    __version__ = "1.5.5"
    # New default theme for the liquid glass design
    DEFAULT_THEMES = {
        "liquid_glass": { "BG_COLOR": "#1e1e1e", "TEXT_COLOR": "#e0e0e0", "TOOLBAR_COLOR": "rgba(30, 30, 30, 0.65)", "URL_BAR_COLOR": "#18181B", "BORDER_COLOR": "rgba(255, 255, 255, 0.1)", "TAB_ACTIVE_COLOR": "#1e1e1e", "TAB_HOVER_COLOR": "rgba(255, 255, 255, 0.1)", "TAB_TEXT_COLOR": "#a0a0a0", "TAB_TEXT_SELECTED_COLOR": "#ffffff", "ICON_COLOR": "#e0e0e0", "STATUS_BAR_TEXT_COLOR": "#a0a0a0", "URL_BAR_BG": "#2c2c2c", "URL_BAR_BORDER": "rgba(255, 255, 255, 0.15)", "BUTTON_HOVER_COLOR": "rgba(255, 255, 255, 0.1)", "BUTTON_PRESSED_COLOR": "rgba(255, 255, 255, 0.05)", "MENU_BG_COLOR": "rgba(30, 30, 30, 0.8)", "MENU_SEPARATOR_COLOR": "rgba(255, 255, 255, 0.1)", "DISABLED_TEXT_COLOR": "#666666", "MSGBOX_BUTTON_BG": "rgba(255, 255, 255, 0.1)", "DANGER_COLOR": "#e53935", "SECURE_COLOR": "#43a047", "CONTENT_BG_COLOR": "#121212" },
        "dark": { "BG_COLOR": "#09090B", "TEXT_COLOR": "#FAFAFA", "TOOLBAR_COLOR": "rgba(24, 24, 27, 0.75)", "URL_BAR_COLOR": "#18181B", "BORDER_COLOR": "rgba(255, 255, 255, 0.12)", "TAB_ACTIVE_COLOR": "#09090B", "TAB_HOVER_COLOR": "rgba(250, 250, 250, 0.08)", "TAB_TEXT_COLOR": "#A1A1AA", "TAB_TEXT_SELECTED_COLOR": "#FAFAFA", "ICON_COLOR": "#FAFAFA", "STATUS_BAR_TEXT_COLOR": "#A1A1AA", "URL_BAR_BG": "#27272a", "URL_BAR_BORDER": "rgba(255, 255, 255, 0.15)", "BUTTON_HOVER_COLOR": "rgba(255, 255, 255, 0.1)", "BUTTON_PRESSED_COLOR": "rgba(255, 255, 255, 0.05)", "MENU_BG_COLOR": "rgba(24, 24, 27, 0.85)", "MENU_SEPARATOR_COLOR": "rgba(255, 255, 255, 0.1)", "DISABLED_TEXT_COLOR": "#62626B", "MSGBOX_BUTTON_BG": "rgba(255, 255, 255, 0.1)", "DANGER_COLOR": "#991B1B", "SECURE_COLOR": "#2ecc71", "CONTENT_BG_COLOR": "#000000" },
        "light": { "BG_COLOR": "#f5f5f5", "TEXT_COLOR": "#09090B", "TOOLBAR_COLOR": "rgba(255, 255, 255, 0.65)", "URL_BAR_COLOR": "#E5E5E5", "BORDER_COLOR": "rgba(0, 0, 0, 0.08)", "TAB_ACTIVE_COLOR": "#f5f5f5", "TAB_HOVER_COLOR": "rgba(0, 0, 0, 0.08)", "TAB_TEXT_COLOR": "#71717A", "TAB_TEXT_SELECTED_COLOR": "#09090B", "ICON_COLOR": "#71717A", "STATUS_BAR_TEXT_COLOR": "#71717A", "URL_BAR_BG": "#e5e5e5", "URL_BAR_BORDER": "rgba(0, 0, 0, 0.1)", "BUTTON_HOVER_COLOR": "rgba(0, 0, 0, 0.08)", "BUTTON_PRESSED_COLOR": "rgba(0, 0, 0, 0.12)", "MENU_BG_COLOR": "rgba(255, 255, 255, 0.8)", "MENU_SEPARATOR_COLOR": "rgba(0, 0, 0, 0.1)", "DISABLED_TEXT_COLOR": "#CCCCCC", "MSGBOX_BUTTON_BG": "rgba(0, 0, 0, 0.05)", "DANGER_COLOR": "#F43F5E", "SECURE_COLOR": "#27ae60", "CONTENT_BG_COLOR": "#FFFFFF" },
        "hacker": { "BG_COLOR": "#000000", "TEXT_COLOR": "#00FF41", "TOOLBAR_COLOR": "rgba(13, 13, 13, 0.75)", "URL_BAR_COLOR": "#0A0A0A", "BORDER_COLOR": "#00FF41", "TAB_ACTIVE_COLOR": "#000000", "TAB_HOVER_COLOR": "rgba(0, 255, 65, 0.15)", "TAB_TEXT_COLOR": "#00CC33", "TAB_TEXT_SELECTED_COLOR": "#00FF41", "ICON_COLOR": "#00FF41", "STATUS_BAR_TEXT_COLOR": "#00CC33", "URL_BAR_BG": "#1a1a1a", "URL_BAR_BORDER": "#00FF41", "BUTTON_HOVER_COLOR": "rgba(0, 255, 65, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(0, 255, 65, 0.1)", "MENU_BG_COLOR": "rgba(0, 0, 0, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(0, 255, 65, 0.2)", "DISABLED_TEXT_COLOR": "#004400", "MSGBOX_BUTTON_BG": "rgba(0, 255, 65, 0.1)", "DANGER_COLOR": "#FF0033", "SECURE_COLOR": "#00FF41", "CONTENT_BG_COLOR": "#0A0A0A" },
        "bluish": { "BG_COLOR": "#0D1B2A", "TEXT_COLOR": "#E0E6ED", "TOOLBAR_COLOR": "rgba(27, 38, 59, 0.75)", "URL_BAR_COLOR": "#1E3A5F", "BORDER_COLOR": "#3A506B", "TAB_ACTIVE_COLOR": "#1B263B", "TAB_HOVER_COLOR": "rgba(59, 130, 246, 0.15)", "TAB_TEXT_COLOR": "#94A3B8", "TAB_TEXT_SELECTED_COLOR": "#3B82F6", "ICON_COLOR": "#60A5FA", "STATUS_BAR_TEXT_COLOR": "#94A3B8", "URL_BAR_BG": "#1b263b", "URL_BAR_BORDER": "#3A506B", "BUTTON_HOVER_COLOR": "rgba(59, 130, 246, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(59, 130, 246, 0.1)", "MENU_BG_COLOR": "rgba(15, 23, 42, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(59, 130, 246, 0.2)", "DISABLED_TEXT_COLOR": "#334155", "MSGBOX_BUTTON_BG": "rgba(59, 130, 246, 0.1)", "DANGER_COLOR": "#EF4444", "SECURE_COLOR": "#3B82F6", "CONTENT_BG_COLOR": "#0F172A" },
        "solarized_dark": { "BG_COLOR": "#002b36", "TEXT_COLOR": "#93a1a1", "TOOLBAR_COLOR": "rgba(7, 54, 66, 0.75)", "URL_BAR_COLOR": "#073642", "BORDER_COLOR": "#586e75", "TAB_ACTIVE_COLOR": "#002b36", "TAB_HOVER_COLOR": "rgba(131, 148, 150, 0.2)", "TAB_TEXT_COLOR": "#93a1a1", "TAB_TEXT_SELECTED_COLOR": "#b58900", "ICON_COLOR": "#268bd2", "STATUS_BAR_TEXT_COLOR": "#586e75", "URL_BAR_BG": "#073642", "URL_BAR_BORDER": "#586e75", "BUTTON_HOVER_COLOR": "rgba(38, 139, 210, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(38, 139, 210, 0.1)", "MENU_BG_COLOR": "rgba(0, 43, 54, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(88, 110, 117, 0.2)", "DISABLED_TEXT_COLOR": "#586e75", "MSGBOX_BUTTON_BG": "rgba(38, 139, 210, 0.1)", "DANGER_COLOR": "#dc322f", "SECURE_COLOR": "#859900", "CONTENT_BG_COLOR": "#001f27" },
        "solarized_light": { "BG_COLOR": "#fdf6e3", "TEXT_COLOR": "#586e75", "TOOLBAR_COLOR": "rgba(238, 232, 213, 0.75)", "URL_BAR_COLOR": "#eee8d5", "BORDER_COLOR": "#93a1a1", "TAB_ACTIVE_COLOR": "#fdf6e3", "TAB_HOVER_COLOR": "rgba(38, 139, 210, 0.15)", "TAB_TEXT_COLOR": "#657b83", "TAB_TEXT_SELECTED_COLOR": "#268bd2", "ICON_COLOR": "#268bd2", "STATUS_BAR_TEXT_COLOR": "#93a1a1", "URL_BAR_BG": "#eee8d5", "URL_BAR_BORDER": "#93a1a1", "BUTTON_HOVER_COLOR": "rgba(38, 139, 210, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(38, 139, 210, 0.1)", "MENU_BG_COLOR": "rgba(253, 246, 227, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(88, 110, 117, 0.2)", "DISABLED_TEXT_COLOR": "#b2b8b5", "MSGBOX_BUTTON_BG": "rgba(38, 139, 210, 0.1)", "DANGER_COLOR": "#dc322f", "SECURE_COLOR": "#859900", "CONTENT_BG_COLOR": "#f0eada" },
        "gruvbox_dark": { "BG_COLOR": "#282828", "TEXT_COLOR": "#ebdbb2", "TOOLBAR_COLOR": "rgba(60, 56, 54, 0.75)", "URL_BAR_COLOR": "#3c3836", "BORDER_COLOR": "#504945", "TAB_ACTIVE_COLOR": "#282828", "TAB_HOVER_COLOR": "rgba(235, 219, 178, 0.1)", "TAB_TEXT_COLOR": "#a89984", "TAB_TEXT_SELECTED_COLOR": "#fabd2f", "ICON_COLOR": "#d79921", "STATUS_BAR_TEXT_COLOR": "#bdae93", "URL_BAR_BG": "#3c3836", "URL_BAR_BORDER": "#504945", "BUTTON_HOVER_COLOR": "rgba(250, 189, 47, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(250, 189, 47, 0.1)", "MENU_BG_COLOR": "rgba(40, 40, 40, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(250, 189, 47, 0.2)", "DISABLED_TEXT_COLOR": "#665c54", "MSGBOX_BUTTON_BG": "rgba(250, 189, 47, 0.1)", "DANGER_COLOR": "#fb4934", "SECURE_COLOR": "#b8bb26", "CONTENT_BG_COLOR": "#1d1d1d" },
        "gruvbox_light": { "BG_COLOR": "#fbf1c7", "TEXT_COLOR": "#3c3836", "TOOLBAR_COLOR": "rgba(235, 219, 178, 0.75)", "URL_BAR_COLOR": "#ebdbb2", "BORDER_COLOR": "#a89984", "TAB_ACTIVE_COLOR": "#fbf1c7", "TAB_HOVER_COLOR": "rgba(250, 189, 47, 0.15)", "TAB_TEXT_COLOR": "#7c6f64", "TAB_TEXT_SELECTED_COLOR": "#d79921", "ICON_COLOR": "#d79921", "STATUS_BAR_TEXT_COLOR": "#928374", "URL_BAR_BG": "#ebdbb2", "URL_BAR_BORDER": "#a89984", "BUTTON_HOVER_COLOR": "rgba(215, 153, 33, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(215, 153, 33, 0.1)", "MENU_BG_COLOR": "rgba(251, 241, 199, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(215, 153, 33, 0.2)", "DISABLED_TEXT_COLOR": "#bdae93", "MSGBOX_BUTTON_BG": "rgba(215, 153, 33, 0.1)", "DANGER_COLOR": "#cc241d", "SECURE_COLOR": "#98971a", "CONTENT_BG_COLOR": "#f2e5bc" },
        "midnight": { "BG_COLOR": "#0f172a", "TEXT_COLOR": "#e2e8f0", "TOOLBAR_COLOR": "rgba(30, 41, 59, 0.75)", "URL_BAR_COLOR": "#1e293b", "BORDER_COLOR": "#334155", "TAB_ACTIVE_COLOR": "#0f172a", "TAB_HOVER_COLOR": "rgba(96, 165, 250, 0.15)", "TAB_TEXT_COLOR": "#94a3b8", "TAB_TEXT_SELECTED_COLOR": "#60a5fa", "ICON_COLOR": "#3b82f6", "STATUS_BAR_TEXT_COLOR": "#64748b", "URL_BAR_BG": "#1e293b", "URL_BAR_BORDER": "#334155", "BUTTON_HOVER_COLOR": "rgba(59, 130, 246, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(59, 130, 246, 0.1)", "MENU_BG_COLOR": "rgba(15, 23, 42, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(96, 165, 250, 0.2)", "DISABLED_TEXT_COLOR": "#475569", "MSGBOX_BUTTON_BG": "rgba(59, 130, 246, 0.1)", "DANGER_COLOR": "#ef4444", "SECURE_COLOR": "#22d3ee", "CONTENT_BG_COLOR": "#0b111e" },
        "sunset": { "BG_COLOR": "#2d1b2d", "TEXT_COLOR": "#fbcfe8", "TOOLBAR_COLOR": "rgba(69, 26, 62, 0.75)", "URL_BAR_COLOR": "#5b2139", "BORDER_COLOR": "#9333ea", "TAB_ACTIVE_COLOR": "#2d1b2d", "TAB_HOVER_COLOR": "rgba(236, 72, 153, 0.15)", "TAB_TEXT_COLOR": "#f472b6", "TAB_TEXT_SELECTED_COLOR": "#ec4899", "ICON_COLOR": "#f472b6", "STATUS_BAR_TEXT_COLOR": "#f9a8d4", "URL_BAR_BG": "#5b2139", "URL_BAR_BORDER": "#9333ea", "BUTTON_HOVER_COLOR": "rgba(236, 72, 153, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(236, 72, 153, 0.1)", "MENU_BG_COLOR": "rgba(45, 27, 45, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(236, 72, 153, 0.2)", "DISABLED_TEXT_COLOR": "#7e2553", "MSGBOX_BUTTON_BG": "rgba(236, 72, 153, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#9333ea", "CONTENT_BG_COLOR": "#1e121e" },
        "forest": { "BG_COLOR": "#0b2414", "TEXT_COLOR": "#d1fae5", "TOOLBAR_COLOR": "rgba(20, 83, 45, 0.75)", "URL_BAR_COLOR": "#166534", "BORDER_COLOR": "#22c55e", "TAB_ACTIVE_COLOR": "#0b2414", "TAB_HOVER_COLOR": "rgba(34, 197, 94, 0.15)", "TAB_TEXT_COLOR": "#86efac", "TAB_TEXT_SELECTED_COLOR": "#22c55e", "ICON_COLOR": "#4ade80", "STATUS_BAR_TEXT_COLOR": "#86efac", "URL_BAR_BG": "#166534", "URL_BAR_BORDER": "#22c55e", "BUTTON_HOVER_COLOR": "rgba(34, 197, 94, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(34, 197, 94, 0.1)", "MENU_BG_COLOR": "rgba(11, 36, 20, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(34, 197, 94, 0.2)", "DISABLED_TEXT_COLOR": "#14532d", "MSGBOX_BUTTON_BG": "rgba(34, 197, 94, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#22c55e", "CONTENT_BG_COLOR": "#061a0e" },
        "pastel": { "BG_COLOR": "#fdf2f8", "TEXT_COLOR": "#4a044e", "TOOLBAR_COLOR": "rgba(252, 231, 243, 0.75)", "URL_BAR_COLOR": "#fbcfe8", "BORDER_COLOR": "#f472b6", "TAB_ACTIVE_COLOR": "#fdf2f8", "TAB_HOVER_COLOR": "rgba(236, 72, 153, 0.15)", "TAB_TEXT_COLOR": "#db2777", "TAB_TEXT_SELECTED_COLOR": "#be185d", "ICON_COLOR": "#ec4899", "STATUS_BAR_TEXT_COLOR": "#be185d", "URL_BAR_BG": "#fbcfe8", "URL_BAR_BORDER": "#f472b6", "BUTTON_HOVER_COLOR": "rgba(236, 72, 153, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(236, 72, 153, 0.1)", "MENU_BG_COLOR": "rgba(253, 242, 248, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(236, 72, 153, 0.2)", "DISABLED_TEXT_COLOR": "#fda4af", "MSGBOX_BUTTON_BG": "rgba(236, 72, 153, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#22c55e", "CONTENT_BG_COLOR": "#fceef3" },
        "retro": { "BG_COLOR": "#1d1f21", "TEXT_COLOR": "#c5c8c6", "TOOLBAR_COLOR": "rgba(40, 42, 46, 0.75)", "URL_BAR_COLOR": "#373b41", "BORDER_COLOR": "#969896", "TAB_ACTIVE_COLOR": "#1d1f21", "TAB_HOVER_COLOR": "rgba(181, 137, 0, 0.2)", "TAB_TEXT_COLOR": "#b294bb", "TAB_TEXT_SELECTED_COLOR": "#f0c674", "ICON_COLOR": "#81a2be", "STATUS_BAR_TEXT_COLOR": "#969896", "URL_BAR_BG": "#373b41", "URL_BAR_BORDER": "#373b41", "BUTTON_HOVER_COLOR": "rgba(240, 198, 116, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(240, 198, 116, 0.1)", "MENU_BG_COLOR": "rgba(29, 31, 33, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(240, 198, 116, 0.2)", "DISABLED_TEXT_COLOR": "#5f6368", "MSGBOX_BUTTON_BG": "rgba(240, 198, 116, 0.1)", "DANGER_COLOR": "#cc342b", "SECURE_COLOR": "#198844", "CONTENT_BG_COLOR": "#161719" },
        "neon": { "BG_COLOR": "#0f0f0f", "TEXT_COLOR": "#f5f5f5", "TOOLBAR_COLOR": "rgba(26, 26, 26, 0.75)", "URL_BAR_COLOR": "#111111", "BORDER_COLOR": "#00ffff", "TAB_ACTIVE_COLOR": "#0f0f0f", "TAB_HOVER_COLOR": "rgba(255, 0, 255, 0.2)", "TAB_TEXT_COLOR": "#00ffff", "TAB_TEXT_SELECTED_COLOR": "#ff00ff", "ICON_COLOR": "#39ff14", "STATUS_BAR_TEXT_COLOR": "#ff00ff", "URL_BAR_BG": "#222222", "URL_BAR_BORDER": "#00ffff", "BUTTON_HOVER_COLOR": "rgba(0, 255, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(0, 255, 255, 0.1)", "MENU_BG_COLOR": "rgba(15, 15, 15, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(255, 0, 255, 0.2)", "DISABLED_TEXT_COLOR": "#333333", "MSGBOX_BUTTON_BG": "rgba(255, 0, 255, 0.1)", "DANGER_COLOR": "#ff073a", "SECURE_COLOR": "#00ff9f", "CONTENT_BG_COLOR": "#0a0a0a" },
        "ocean": { "BG_COLOR": "#011627", "TEXT_COLOR": "#d6deeb", "TOOLBAR_COLOR": "rgba(29, 59, 83, 0.75)", "URL_BAR_COLOR": "#133a5e", "BORDER_COLOR": "#82aaff", "TAB_ACTIVE_COLOR": "#011627", "TAB_HOVER_COLOR": "rgba(130, 170, 255, 0.2)", "TAB_TEXT_COLOR": "#82aaff", "TAB_TEXT_SELECTED_COLOR": "#22d3ee", "ICON_COLOR": "#82aaff", "STATUS_BAR_TEXT_COLOR": "#7b8794", "URL_BAR_BG": "#133a5e", "URL_BAR_BORDER": "#82aaff", "BUTTON_HOVER_COLOR": "rgba(130, 170, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(130, 170, 255, 0.1)", "MENU_BG_COLOR": "rgba(1, 22, 39, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(130, 170, 255, 0.2)", "DISABLED_TEXT_COLOR": "#475569", "MSGBOX_BUTTON_BG": "rgba(130, 170, 255, 0.1)", "DANGER_COLOR": "#ef4444", "SECURE_COLOR": "#22d3ee", "CONTENT_BG_COLOR": "#01101c" },
        "lavender": { "BG_COLOR": "#2e1a47", "TEXT_COLOR": "#f3e8ff", "TOOLBAR_COLOR": "rgba(76, 29, 149, 0.75)", "URL_BAR_COLOR": "#5b21b6", "BORDER_COLOR": "#8b5cf6", "TAB_ACTIVE_COLOR": "#2e1a47", "TAB_HOVER_COLOR": "rgba(139, 92, 246, 0.2)", "TAB_TEXT_COLOR": "#c4b5fd", "TAB_TEXT_SELECTED_COLOR": "#a78bfa", "ICON_COLOR": "#c084fc", "STATUS_BAR_TEXT_COLOR": "#c4b5fd", "URL_BAR_BG": "#5b21b6", "URL_BAR_BORDER": "#8b5cf6", "BUTTON_HOVER_COLOR": "rgba(139, 92, 246, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(139, 92, 246, 0.1)", "MENU_BG_COLOR": "rgba(46, 26, 71, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(139, 92, 246, 0.2)", "DISABLED_TEXT_COLOR": "#5b21b6", "MSGBOX_BUTTON_BG": "rgba(139, 92, 246, 0.1)", "DANGER_COLOR": "#f43f5e", "SECURE_COLOR": "#8b5cf6", "CONTENT_BG_COLOR": "#231436" },
        "coffee": { "BG_COLOR": "#2c1810", "TEXT_COLOR": "#f5f5dc", "TOOLBAR_COLOR": "rgba(74, 50, 34, 0.75)", "URL_BAR_COLOR": "#5c3d2e", "BORDER_COLOR": "#d6b370", "TAB_ACTIVE_COLOR": "#2c1810", "TAB_HOVER_COLOR": "rgba(214, 179, 112, 0.2)", "TAB_TEXT_COLOR": "#d6b370", "TAB_TEXT_SELECTED_COLOR": "#f5deb3", "ICON_COLOR": "#e6be8a", "STATUS_BAR_TEXT_COLOR": "#cbb67c", "URL_BAR_BG": "#5c3d2e", "URL_BAR_BORDER": "#d6b370", "BUTTON_HOVER_COLOR": "rgba(214, 179, 112, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(214, 179, 112, 0.1)", "MENU_BG_COLOR": "rgba(44, 24, 16, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(214, 179, 112, 0.2)", "DISABLED_TEXT_COLOR": "#5c3d2e", "MSGBOX_BUTTON_BG": "rgba(214, 179, 112, 0.1)", "DANGER_COLOR": "#cc241d", "SECURE_COLOR": "#b8bb26", "CONTENT_BG_COLOR": "#21120c" },
        "ice": { "BG_COLOR": "#e0f7fa", "TEXT_COLOR": "#006064", "TOOLBAR_COLOR": "rgba(178, 235, 219, 0.75)", "URL_BAR_COLOR": "#80deea", "BORDER_COLOR": "#26c6da", "TAB_ACTIVE_COLOR": "#e0f7fa", "TAB_HOVER_COLOR": "rgba(0, 188, 212, 0.2)", "TAB_TEXT_COLOR": "#00acc1", "TAB_TEXT_SELECTED_COLOR": "#00838f", "ICON_COLOR": "#00acc1", "STATUS_BAR_TEXT_COLOR": "#0097a7", "URL_BAR_BG": "#b2ebf2", "URL_BAR_BORDER": "#26c6da", "BUTTON_HOVER_COLOR": "rgba(0, 188, 212, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(0, 188, 212, 0.1)", "MENU_BG_COLOR": "rgba(224, 247, 250, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(0, 188, 212, 0.2)", "DISABLED_TEXT_COLOR": "#80deea", "MSGBOX_BUTTON_BG": "rgba(0, 188, 212, 0.1)", "DANGER_COLOR": "#f44336", "SECURE_COLOR": "#00838f", "CONTENT_BG_COLOR": "#d1f2f6" },
        "desert": { "BG_COLOR": "#edc9af", "TEXT_COLOR": "#3e2723", "TOOLBAR_COLOR": "rgba(215, 184, 153, 0.75)", "URL_BAR_COLOR": "#cba57f", "BORDER_COLOR": "#a1887f", "TAB_ACTIVE_COLOR": "#edc9af", "TAB_HOVER_COLOR": "rgba(161, 136, 127, 0.2)", "TAB_TEXT_COLOR": "#795548", "TAB_TEXT_SELECTED_COLOR": "#5d4037", "ICON_COLOR": "#8d6e63", "STATUS_BAR_TEXT_COLOR": "#6d4c41", "URL_BAR_BG": "#d7b899", "URL_BAR_BORDER": "#a1887f", "BUTTON_HOVER_COLOR": "rgba(161, 136, 127, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(161, 136, 127, 0.1)", "MENU_BG_COLOR": "rgba(237, 201, 175, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(161, 136, 127, 0.2)", "DISABLED_TEXT_COLOR": "#cba57f", "MSGBOX_BUTTON_BG": "rgba(161, 136, 127, 0.1)", "DANGER_COLOR": "#d84315", "SECURE_COLOR": "#6d4c41", "CONTENT_BG_COLOR": "#e3bfa2" },
        "rose": { "BG_COLOR": "#ffe4e6", "TEXT_COLOR": "#9d174d", "TOOLBAR_COLOR": "rgba(254, 205, 211, 0.75)", "URL_BAR_COLOR": "#fda4af", "BORDER_COLOR": "#f43f5e", "TAB_ACTIVE_COLOR": "#ffe4e6", "TAB_HOVER_COLOR": "rgba(244, 63, 94, 0.15)", "TAB_TEXT_COLOR": "#e11d48", "TAB_TEXT_SELECTED_COLOR": "#be123c", "ICON_COLOR": "#f43f5e", "STATUS_BAR_TEXT_COLOR": "#be123c", "URL_BAR_BG": "#fecdd3", "URL_BAR_BORDER": "#f43f5e", "BUTTON_HOVER_COLOR": "rgba(244, 63, 94, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(244, 63, 94, 0.1)", "MENU_BG_COLOR": "rgba(255, 228, 230, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(244, 63, 94, 0.2)", "DISABLED_TEXT_COLOR": "#fda4af", "MSGBOX_BUTTON_BG": "rgba(244, 63, 94, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#22c55e", "CONTENT_BG_COLOR": "#ffd9dc" },
        "mint": { "BG_COLOR": "#ecfdf5", "TEXT_COLOR": "#064e3b", "TOOLBAR_COLOR": "rgba(209, 250, 229, 0.75)", "URL_BAR_COLOR": "#a7f3d0", "BORDER_COLOR": "#10b981", "TAB_ACTIVE_COLOR": "#ecfdf5", "TAB_HOVER_COLOR": "rgba(16, 185, 129, 0.2)", "TAB_TEXT_COLOR": "#059669", "TAB_TEXT_SELECTED_COLOR": "#047857", "ICON_COLOR": "#34d399", "STATUS_BAR_TEXT_COLOR": "#047857", "URL_BAR_BG": "#d1fae5", "URL_BAR_BORDER": "#10b981", "BUTTON_HOVER_COLOR": "rgba(16, 185, 129, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(16, 185, 129, 0.1)", "MENU_BG_COLOR": "rgba(236, 253, 245, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(16, 185, 129, 0.2)", "DISABLED_TEXT_COLOR": "#a7f3d0", "MSGBOX_BUTTON_BG": "rgba(16, 185, 129, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#047857", "CONTENT_BG_COLOR": "#e0f8ef" },
        "gold": { "BG_COLOR": "#fff8e1", "TEXT_COLOR": "#78350f", "TOOLBAR_COLOR": "rgba(255, 236, 179, 0.75)", "URL_BAR_COLOR": "#ffe082", "BORDER_COLOR": "#fbbf24", "TAB_ACTIVE_COLOR": "#fff8e1", "TAB_HOVER_COLOR": "rgba(251, 191, 36, 0.2)", "TAB_TEXT_COLOR": "#d97706", "TAB_TEXT_SELECTED_COLOR": "#b45309", "ICON_COLOR": "#f59e0b", "STATUS_BAR_TEXT_COLOR": "#b45309", "URL_BAR_BG": "#ffecb3", "URL_BAR_BORDER": "#fbbf24", "BUTTON_HOVER_COLOR": "rgba(251, 191, 36, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(251, 191, 36, 0.1)", "MENU_BG_COLOR": "rgba(255, 248, 225, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(251, 191, 36, 0.2)", "DISABLED_TEXT_COLOR": "#ffe082", "MSGBOX_BUTTON_BG": "rgba(251, 191, 36, 0.1)", "DANGER_COLOR": "#d97706", "SECURE_COLOR": "#22c55e", "CONTENT_BG_COLOR": "#fff4d4" },
        "high_contrast": { "BG_COLOR": "#000000", "TEXT_COLOR": "#ffffff", "TOOLBAR_COLOR": "rgba(0, 0, 0, 0.75)", "URL_BAR_COLOR": "#000000", "BORDER_COLOR": "#ffffff", "TAB_ACTIVE_COLOR": "#000000", "TAB_HOVER_COLOR": "rgba(255, 255, 255, 0.2)", "TAB_TEXT_COLOR": "#ffffff", "TAB_TEXT_SELECTED_COLOR": "#ffff00", "ICON_COLOR": "#ffffff", "STATUS_BAR_TEXT_COLOR": "#ffffff", "URL_BAR_BG": "#222222", "URL_BAR_BORDER": "#ffffff", "BUTTON_HOVER_COLOR": "rgba(255, 255, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(255, 255, 255, 0.1)", "MENU_BG_COLOR": "rgba(0, 0, 0, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(255, 255, 255, 0.2)", "DISABLED_TEXT_COLOR": "#666666", "MSGBOX_BUTTON_BG": "rgba(255, 255, 255, 0.1)", "DANGER_COLOR": "#ff0000", "SECURE_COLOR": "#00ff00", "CONTENT_BG_COLOR": "#111111" },
        "aqua": { "BG_COLOR": "#e0f2f1", "TEXT_COLOR": "#004d40", "TOOLBAR_COLOR": "rgba(178, 223, 219, 0.75)", "URL_BAR_COLOR": "#80cbc4", "BORDER_COLOR": "#26a69a", "TAB_ACTIVE_COLOR": "#e0f2f1", "TAB_HOVER_COLOR": "rgba(38, 166, 154, 0.2)", "TAB_TEXT_COLOR": "#00897b", "TAB_TEXT_SELECTED_COLOR": "#00695c", "ICON_COLOR": "#26a69a", "STATUS_BAR_TEXT_COLOR": "#00695c", "URL_BAR_BG": "#b2dfdb", "URL_BAR_BORDER": "#26a69a", "BUTTON_HOVER_COLOR": "rgba(38, 166, 154, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(38, 166, 154, 0.1)", "MENU_BG_COLOR": "rgba(224, 242, 241, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(38, 166, 154, 0.2)", "DISABLED_TEXT_COLOR": "#80cbc4", "MSGBOX_BUTTON_BG": "rgba(38, 166, 154, 0.1)", "DANGER_COLOR": "#d32f2f", "SECURE_COLOR": "#388e3c", "CONTENT_BG_COLOR": "#d1e9e7" },
        "plasma": { "BG_COLOR": "#1a002b", "TEXT_COLOR": "#f3f4f6", "TOOLBAR_COLOR": "rgba(44, 0, 62, 0.75)", "URL_BAR_COLOR": "#40005a", "BORDER_COLOR": "#e11d48", "TAB_ACTIVE_COLOR": "#1a002b", "TAB_HOVER_COLOR": "rgba(225, 29, 72, 0.2)", "TAB_TEXT_COLOR": "#f472b6", "TAB_TEXT_SELECTED_COLOR": "#db2777", "ICON_COLOR": "#ec4899", "STATUS_BAR_TEXT_COLOR": "#f472b6", "URL_BAR_BG": "#40005a", "URL_BAR_BORDER": "#e11d48", "BUTTON_HOVER_COLOR": "rgba(225, 29, 72, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(225, 29, 72, 0.1)", "MENU_BG_COLOR": "rgba(26, 0, 43, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(225, 29, 72, 0.2)", "DISABLED_TEXT_COLOR": "#5b21b6", "MSGBOX_BUTTON_BG": "rgba(225, 29, 72, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#22c55e", "CONTENT_BG_COLOR": "#140021" }
    }

    def __init__(self):
        super().__init__()
        global main_window
        main_window = self
        self.setObjectName("MainWindow")
        self.is_shutting_down = False
        try:
            # Set application icon
            # Go up one level from the 'bin' directory to find the root
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.setWindowIcon(QIcon(os.path.join(app_root, 'favicon.ico')))
        except Exception:
            # Icon not found, continue without it
            pass

        # --- Frameless Window Setup ---
        # On Windows, we use a custom frameless window. On Linux and macOS, we use the native frame.
        if sys.platform == "win32":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            self.drag_pos = QPoint()
            self._resizing = False
            self._resize_edge = None
            self._resize_margin = 8
        elif sys.platform == "darwin": # macOS
            self.setUnifiedTitleAndToolBarOnMac(True)

        self.setMinimumSize(600, 400) # Set a reasonable minimum size
        # --- Theme Colors ---
        self.load_themes()
        settings = QSettings("DisunicX", "Browser")
        self.tab_style = "modern" if settings.value("tab_style", 0, type=int) == 0 else "classic"
        self.theme_name = settings.value("theme", "dark", type=str)
        # Ensure theme_name is valid, otherwise default to "dark"
        if self.theme_name not in self.THEMES:
            self.theme_name = "dark" if "dark" in self.THEMES else list(self.THEMES.keys())[0]
        self.theme = self.THEMES[self.theme_name]
        
        # Keep direct references for colors used frequently in Python logic
        self.BG_COLOR = self.theme["BG_COLOR"]
        self.TEXT_COLOR = self.theme["TEXT_COLOR"]
        self.CONTENT_BG_COLOR = self.theme.get("CONTENT_BG_COLOR", self.theme["BG_COLOR"]) # New content background
        self.TOOLBAR_COLOR = self.theme["TOOLBAR_COLOR"]
        self.ACCENT_COLOR = "#3F51B5" # Primary color from theme
        self.BORDER_COLOR = self.theme["BORDER_COLOR"]
        self.DANGER_COLOR = self.theme["DANGER_COLOR"]
        self.SECURE_COLOR = self.theme["SECURE_COLOR"]

        self.profile = QWebEngineProfile("DisunicXProfile", self)
        self.profile.setPersistentStoragePath(get_profile_path())
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setCachePath(os.path.join(get_profile_path(), "Cache"))
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.set_tor_proxy()

        # --- Ad Blocker Setup ---
        self.adblocker = AdblockInterceptor()
        self.adblocker.load_rules()
        if settings.value("adblocker_enabled", True, type=bool):
            self.profile.setUrlRequestInterceptor(self.adblocker)


        # Connect the download request signal here, only once.
        self.profile.downloadRequested.connect(self.handle_new_download)

        # Show welcome dialog before any UI setup
        self.history_manager = HistoryManager()
        self.bookmarks_manager = BookmarksManager()
        self.download_manager = DownloadManagerPage(self, self)
        self.download_manager_is_in_tab = False
        self.settings_page = SettingsPage(self.profile, self)
        self.settings_page_is_in_tab = False

        # This needs to be called before the UI is built so the window can be shown
        # if the dialog is accepted.
        if sys.platform == "win32":
            self.setWindowTitle(f"DisunicX v{self.__version__}")
        else:
            self.setWindowTitle("DisunicX")
        self.setGeometry(100, 100, 1200, 800)

        self.toolbar = QToolBar("mainToolbar")

        # If the user declines the welcome dialog, it will quit the application.
        if not self.show_welcome_if_first_time():
            self.is_shutting_down = True
            return  # Prevent further initialization
        
        self.apply_stylesheet()

        # --- Main Layout Structure ---
        main_container = QWidget()
        main_container.setMouseTracking(True)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Custom Title Bar Area
        self.title_bar_widget = QWidget()
        self.title_bar_widget.setObjectName("TitleBarWidget") # This now contains tabs and toolbar
        self.title_bar_widget.setMouseTracking(True)
        title_bar_layout = QHBoxLayout(self.title_bar_widget)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(0)
        
        self.tab_widget = TabWidget(self.theme, style=self.tab_style, parent=self) # type: ignore
        self.tab_widget.newTabRequested.connect(lambda: self.add_new_tab())
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.tabContextMenuRequested.connect(self.show_tab_context_menu)

        self.setup_toolbar()
        self.setup_status_bar()


        if self.tab_style == "classic":
            # Classic layout: Tab bar in title bar, toolbar below
            title_bar_layout.addWidget(self.tab_widget)
            title_bar_layout.addStretch(1) # Add stretchable space for dragging
            # The main_layout will contain: title_bar_widget -> toolbar -> content
        else: # Modern layout
            # Modern layout: Toolbar integrated into title bar
            title_bar_layout.addWidget(self.toolbar, 1)

        if sys.platform == "win32":
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

            window_controls_layout.addWidget(self.minimize_btn) # type: ignore
            window_controls_layout.addWidget(self.maximize_btn)
            window_controls_layout.addWidget(self.close_btn)
            title_bar_layout.addWidget(self.window_controls_widget)

        # 3. Bookmarks Bar
        self.bookmarks_bar = BookmarksBar(self.theme, self)
        self.bookmarks_bar.bookmarkClicked.connect(lambda url: self.add_new_tab(QUrl(url)))
        self.bookmarks_bar.removeBookmarkRequested.connect(self.remove_bookmark)
        self.bookmarks_bar.bookmarksReordered.connect(self.reorder_bookmarks)

        # 4. Find Bar
        self.find_bar = FindBar(self.theme, self)
        self.find_bar.findNext.connect(self.on_find_next)
        self.find_bar.findPrevious.connect(self.on_find_previous)
        self.find_bar.closed.connect(self.on_find_closed)
        
        # 5. Tab Overview
        self.tab_overview = TabOverview(self.theme, self)
        self.tab_overview.tab_selected.connect(self.select_tab_from_overview)
        self.tab_overview.tab_closed.connect(self.close_tab_from_overview)
        self.tab_overview.overview_closed.connect(self.hide_tab_overview)
        self.tab_overview.new_tab_requested.connect(self.add_new_tab_from_overview)
        self.tab_overview.title_changed.connect(self.on_tab_title_changed_from_overview)
        self.tab_overview.close_all_tabs_requested.connect(self.close_all_tabs)
        self.tab_overview.tabs_reordered.connect(self.reorder_tabs)

        # Create a container for the main content (stacked widget) and the sidebar
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_stack = QStackedWidget()
        # In classic mode, tab_widget's layout contains the stacked_widget.
        # In modern mode, it IS the stacked_widget.
        if self.tab_style == "classic":
            self.main_stack.addWidget(self.tab_widget.stacked_widget)
        else:
            self.main_stack.addWidget(self.tab_widget)
        self.main_stack.addWidget(self.tab_overview)
        self.content_layout.addWidget(self.main_stack)

        # Add widgets to main layout in the correct order
        main_layout.addWidget(self.title_bar_widget) # Contains tabs (classic) or toolbar (modern)
        if self.tab_style == "classic":
            main_layout.addWidget(self.toolbar) # Toolbar is separate in classic mode

        main_layout.addWidget(self.bookmarks_bar)
        main_layout.addWidget(self.find_bar)
        main_layout.addWidget(self.content_container, 1) # Add content area

        main_layout.addWidget(self.status) # type: ignore

        self.setCentralWidget(main_container)
        
        # Add initial tab
        # Defer adding the initial tab until after the constructor is fully finished
        # to ensure session restore logic works correctly.
        QTimer.singleShot(0, self.add_initial_tabs)

        # Enable mouse tracking for custom resizing on Windows
        if sys.platform == "win32" or sys.platform == "darwin":
            self.setMouseTracking(True)

        self.populate_bookmarks_bar()
        self.load_bookmarks_bar_visibility()

        # Add shortcut for Find
        find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        find_shortcut.activated.connect(self.show_find_bar)

        if sys.platform == "darwin":
            self.setup_menu_bar()
        else:
            self.setup_main_menu_button()
            # On Linux, create a sidebar menu instead of just a popup
            if sys.platform.startswith('linux'):
                self.setup_sidebar_menu()

        # Check for updates on startup
        self.check_for_updates()

    def apply_stylesheet(self):
        # Helper to get an "R, G, B" string from a color definition for rgba()
        def get_rgb_string(color_str):
            if color_str.startswith('#'):
                h = color_str.lstrip('#')
                return ', '.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
            return "0, 0, 0" # Fallback
        border_style = "1px solid transparent" # No border on Linux/macOS with native frame by default
        if sys.platform == "win32":
            border_style = f"1px solid {self.theme['BORDER_COLOR']}"
            
        # Use a radial gradient for a subtle depth effect on the main background
        bg_gradient = f"""qradialgradient(
            cx: 0.5, cy: 0.5, radius: 1.5,
            fx: 0.5, fy: 0.5,
            stop: 0 {self.theme['TOOLBAR_COLOR']}, stop: 1 {self.BG_COLOR}
        )"""

        self.setStyleSheet(f"""/* Base Styles */
            #MainWindow, #TitleBarWidget {{
                background-color: {self.BG_COLOR};
                color: {self.TEXT_COLOR};
                background-image: {bg_gradient};
                border: {border_style};
            }}
            #TitleBarWidget {{ /* On macOS, this should be transparent to show the native blur */
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({get_rgb_string(self.theme['TOOLBAR_COLOR'])}, 0.9),
                    stop:1 rgba({get_rgb_string(self.theme['TOOLBAR_COLOR'])}, 0.7));
                border-bottom: none;
            }}
            #ContentStack {{
                background-color: {self.CONTENT_BG_COLOR};
                border-bottom: none;
            }}
            QToolBar {{
                background-color: transparent;
                border: none;
                padding: 5px;
                spacing: 5px;
            }}
            #mainToolbar {{
                background-color: transparent;
                border: none;
                padding: 5px;
                spacing: 5px;
            }}
            #mainToolbar QPushButton {{
                background-color: transparent;
                color: {self.theme["TEXT_COLOR"]};
                border: none;
                border-radius: 6px; /* Rounded square buttons */
                padding: 8px; /* Increased padding for a larger click area */
                font-size: 14px;
            }}
            #mainToolbar QPushButton:hover {{
                background-color: {self.theme["BUTTON_HOVER_COLOR"]};
            }}
            #mainToolbar QPushButton:pressed {{
                background-color: {self.theme["BUTTON_PRESSED_COLOR"]};
            }}
            #UrlEdit {{
                background-color: transparent;
                color: {self.theme["TEXT_COLOR"]};
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
                background-color: {self.theme["BUTTON_HOVER_COLOR"]};
            }}
            /* The background and border for #UrlBar are now handled by its custom paintEvent.
               We only need to ensure the inner QLineEdit is transparent. */
            #UrlBar, #UrlBar > #UrlEdit {{ background-color: transparent; border: none; }}

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
                background-color: {self.theme["BUTTON_HOVER_COLOR"]};
            }}
            #CloseBtn:hover {{
                background-color: {self.theme["DANGER_COLOR"]};
            }}
            QTabBar::close-button:pressed {{
                background-color: #c0392b; /* Darker red on press */
            }}

            /* Status Bar */
            QStatusBar#StatusBar {{
                background-color: {self.theme['TOOLBAR_COLOR']};
                border-top: 1px solid {self.theme['BORDER_COLOR']};
                font-size: 12px;
                padding: 2px 4px;
            }}
            QStatusBar#StatusBar::item {{
                border: none; /* Remove default item borders */
                margin: 0;
                padding: 0;
            }}
            QLabel#StatusLabel {{
                color: {self.theme["STATUS_BAR_TEXT_COLOR"]};
                padding: 4px 10px;
                font-weight: 700;
                background-color: transparent;
                border-radius: 8px;
            }}
            /* TorStatusWidget is styled dynamically */
        """)

    def setup_status_bar(self):
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
        
        # Zoom level indicator
        self.zoom_label = QLabel()
        self.zoom_label.setObjectName("StatusLabel")
        self.status.addPermanentWidget(self.zoom_label)

        self.update_tor_status(QUrl()) # Initial setup
    def load_themes(self):
        """Loads default themes and merges custom themes from themes.json."""
        # Start with a copy of the hardcoded default themes
        self.THEMES = self.DEFAULT_THEMES.copy()
        
        try: # type: ignore
            # Load custom themes from themes.json
            script_dir = os.path.dirname(os.path.abspath(__file__))
            themes_path = os.path.join(script_dir, 'themes.json')
            if os.path.exists(themes_path):
                with open(themes_path, 'r', encoding='utf-8') as f:
                    custom_themes = json.load(f)
                    # Merge custom themes, overwriting defaults if names match
                    self.THEMES.update(custom_themes)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load custom themes from themes.json: {e}")
            # Continue with just the default themes

    def get_new_tab_html(self):
        """Generates the HTML for the modern new tab page with a background image and customization sidebar."""
        settings = QSettings("DisunicX", "Browser")
        search_engine = settings.value("search_engine", "DuckDuckGo")
        theme = self.THEMES.get(self.theme_name, self.THEMES["dark"])

        # --- Logo Logic ---
        # Fallback to the app name from the window title
        app_name = self.windowTitle().split(" v")[0]
        logo_html = f'<h1>{app_name}</h1>'
        try:
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path_png = os.path.join(app_root, 'favicon.png')
            logo_path_ico = os.path.join(app_root, 'favicon.ico')
            
            logo_path = None
            if os.path.exists(logo_path_png): logo_path = logo_path_png
            elif os.path.exists(logo_path_ico): logo_path = logo_path_ico

            if logo_path:
                pixmap = QPixmap(logo_path).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_data_uri = qpixmap_to_base64(pixmap)
                if logo_data_uri:
                    logo_html = f'<img src="{logo_data_uri}" alt="Logo" class="logo-img">'
        except Exception as e:
            print(f"Could not load logo for new tab page: {e}")

        # --- Background Image Logic ---
        background_image_css = ""
        try:
            # Go up one level from 'bin' to the project root
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Assume an image named 'background.jpg' exists in the project root
            bg_path = os.path.join(app_root, 'background.jpg')
            if os.path.exists(bg_path):
                with open(bg_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                    data_uri = f"data:image/jpeg;base64,{encoded_string}"
                    background_image_css = f"background-image: url('{data_uri}');"
            else:
                # Fallback to a gradient if local file not found
                background_image_css = f"background-image: linear-gradient(to bottom, {theme['TOOLBAR_COLOR']}, {theme['BG_COLOR']});"
        except Exception as e:
            print(f"Could not load background image: {e}")
            # Fallback to a gradient if all else fails
            background_image_css = f"background-image: linear-gradient(to bottom, {theme['TOOLBAR_COLOR']}, {theme['BG_COLOR']});"

        # A helper to get an "R, G, B" string from a color definition
        def get_rgb_string(color_str):
            """Handles both #RRGGBB and rgba(r,g,b,a) formats."""
            if color_str.startswith('rgba'):
                # Extract the 'r, g, b' part from 'rgba(r, g, b, a)'
                try:
                    return color_str.split('(')[1].split(')')[0].rsplit(',', 1)[0]
                except (IndexError, ValueError):
                    return "0, 0, 0" # Fallback
            elif color_str.startswith('#'):
                h = color_str.lstrip('#')
                return ', '.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
            return "0, 0, 0" # Fallback for unknown formats

        search_bg_rgb = get_rgb_string(theme['TOOLBAR_COLOR'])
        sidebar_bg_rgb = get_rgb_string(theme['TOOLBAR_COLOR'])
        search_bg_alpha = '0.6' if self.theme_name == 'dark' else '0.85'
        # --- Top Sites Logic ---
        top_sites = self.history_manager.get_top_sites(limit=8)
        top_sites_html = ""
        if top_sites:
            for site in top_sites:
                site_title = site['title']
                try:
                    domain = urllib.parse.urlparse(site['url']).netloc.replace('www.', '')
                    if not site_title or len(site_title) > 20:
                        site_title = domain
                except Exception:
                    site_title = site['title'] if site['title'] else "Link"

                favicon_html = f'<img src="{site["favicon"]}" class="site-favicon" alt="" onerror="this.style.display=\'none\'; this.nextSibling.style.display=\'flex\';">' if site["favicon"] else ''
                placeholder_display = 'none' if site["favicon"] else 'flex'
                
                top_sites_html += f"""
                    <a href="{site['url']}" class="site-tile" title="{html.escape(site['title'])}">
                        <div class="favicon-container">
                            {favicon_html}
                            <div class="site-favicon-placeholder" style="display: {placeholder_display};">
                                {html.escape(site_title[0].upper())}
                            </div>
                        </div>
                        <span class="site-title">{html.escape(site_title)}</span>
                    </a>
                """
        else:
            star_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
            top_sites_html = f"""
                <div class="no-sites-message">
                    {star_icon_svg}
                    <h3>Quick Links</h3>
                    <p>Your frequently visited sites will appear here.</p>
                </div>
            """
        
        # Icons
        search_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'.replace("currentColor", theme['TAB_TEXT_COLOR'])
        settings_icon_svg = SVG_ICONS['settings_general'].replace("currentColor", theme['TEXT_COLOR'])
        close_icon_svg = SVG_ICONS['close'].replace("currentColor", theme['TEXT_COLOR'])

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Tab</title>
    <style>
        html {{
            overflow: hidden; /* Prevent root-level scrollbars */
        }}
        .clock {{
            position: fixed;
            top: 24px;
            left: 24px;
            font-size: 1.5rem;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            text-shadow: 0 1px 5px rgba(0,0,0,0.3);
            z-index: 10;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        body {{
            background-color: {theme['BG_COLOR']};
            color: {theme['TEXT_COLOR']};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            overflow: hidden; /* Prevent scrollbars from the main body */
        }}
        .background-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            {background_image_css}
            background-size: cover;
            background-position: center;
            z-index: -1;
            filter: brightness(0.6) blur(4px); /* Darken and blur the image */
        }}
        body.background-hidden .background-overlay {{
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease-in-out;
        }}
        .main-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
        }}
        .container {{
            max-width: 600px;
            width: 100%;
            padding: 20px;
            animation: fadeIn 0.5s ease-out forwards;
        }}
        .logo {{
            margin-bottom: 2rem;
            /* Container for the image or text */
        }}
        .logo-img {{
            width: 128px;
            height: 128px;
            border-radius: 26px;
            object-fit: contain;
            filter: drop-shadow(0 3px 15px rgba(0,0,0,0.2));
        }}
        .logo h1 {{
            font-size: 4rem;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            text-shadow: 0 3px 15px rgba(0,0,0,0.2);
            margin: 0;
        }}
        .search-form {{
            position: relative;
            margin-bottom: 3rem;
        }}
        .search-input {{
            width: 100%;
            padding: 16px 24px 16px 56px;
            border-radius: 9999px;
            background-color: rgba({search_bg_rgb}, {search_bg_alpha});
            border: 1px solid rgba(255,255,255,0.1);
            color: {theme['TEXT_COLOR']};
            font-size: 1.1rem;
            outline: none;
            transition: all 0.2s ease;
            box-sizing: border-box;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 10px 20px rgba(0,0,0,0.1);
        }}
        body.background-hidden .search-input {{
            background-color: {theme['TOOLBAR_COLOR']};
            backdrop-filter: none;
        }}
        .search-input:hover {{
            border-color: rgba(255,255,255,0.3);
        }}
        .search-input:focus {{
            border-color: {self.ACCENT_COLOR};
            box-shadow: 0 0 0 3px rgba(63, 81, 181, 0.3);
        }}
        .search-input::placeholder {{
            color: {theme['TAB_TEXT_COLOR']};
        }}
        .search-icon {{
            position: absolute;
            left: 22px;
            top: 50%;
            transform: translateY(-50%);
            width: 22px;
            height: 22px;
            color: {theme['TAB_TEXT_COLOR']};
            pointer-events: none;
        }}
        .top-sites-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px; /* Increased gap */
            transition: opacity 0.3s, transform 0.3s;
        }}
        body.top-sites-hidden .top-sites-grid {{
            opacity: 0;
            transform: scale(0.95);
            pointer-events: none;
        }}
        .no-sites-message {{
            grid-column: 1 / -1; /* Span all columns */
            text-align: center;
            padding: 2rem;
            color: {theme['TAB_TEXT_COLOR']};
            background-color: rgba(0,0,0,0.2);
            border-radius: 12px;
            backdrop-filter: blur(5px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}
        .no-sites-message svg {{
            stroke: {theme['TAB_TEXT_COLOR']};
            margin-bottom: 0.5rem;
        }}
        .no-sites-message h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            margin: 0;
        }}
        .no-sites-message p {{
            font-size: 0.875rem;
            margin: 0;
        }}
        .site-tile {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 12px;
            border-radius: 12px; /* Increased radius */
            text-decoration: none;
            color: {theme['TEXT_COLOR']};
            background-color: rgba(0,0,0,0.2);
            transition: all 0.2s ease-in-out;
            backdrop-filter: blur(5px);
        }}
        body.background-hidden .site-tile {{
            background-color: {theme['TOOLBAR_COLOR']};
            backdrop-filter: none;
        }}
        .site-tile:hover {{
            background-color: rgba(0,0,0,0.4);
            transform: translateY(-4px); /* Increased transform */
            box-shadow: 0 8px 16px rgba(0,0,0,0.25);
        }}
        .site-tile:hover .favicon-container {{
            background-color: rgba(255,255,255,0.1);
        }}
        .favicon-container {{
            width: 48px;
            height: 48px;
            border-radius: 50%; /* Circular */
            background-color: rgba(255,255,255,0.05);
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 12px; /* Increased margin */
            transition: background-color 0.2s ease-in-out;
        }}
        .site-favicon {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
        }}
        .site-favicon-placeholder {{
            width: 100%;
            height: 100%;
            border-radius: 50%; /* Circular */
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 20px;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            background-color: {theme['BORDER_COLOR']};
        }}
        .site-title {{
            font-size: 13px; /* Increased size */
            font-weight: 600; /* Semi-bold */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }}

        /* --- Settings Button --- */
        .settings-btn {{
            position: fixed;
            top: 24px;
            right: 24px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            z-index: 99;
        }}
        .settings-btn:hover {{
            background: rgba(0,0,0,0.5);
            transform: scale(1.05);
        }}
        .settings-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* --- Sidebar --- */
        .sidebar {{
            position: fixed;
            top: 0;
            right: -350px; /* Start off-screen, increased to fully hide */
            width: 300px;
            height: 100%;
            background-color: rgba({sidebar_bg_rgb}, 0.7);
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: -5px 0 25px rgba(0,0,0,0.3);
            z-index: 100;
            transition: right 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), background-color 0.3s;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        .sidebar.is-open {{
            right: 0; /* Slide in */
        }}
        .sidebar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }}
        .sidebar-header h2 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0;
        }}
        .sidebar-close-btn {{
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 5px;
            border-radius: 50%;
        }}
        .sidebar-close-btn:hover {{
            background-color: {theme['BUTTON_HOVER_COLOR']};
        }}
        .sidebar-close-btn svg {{
            width: 18px;
            height: 18px;
        }}
        .setting-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid {theme['BORDER_COLOR']};
        }}
        .setting-row label {{
            font-size: 14px;
        }}

        /* Simple CSS Toggle Switch */
        .toggle-switch {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
        }}
        .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: {theme['BORDER_COLOR']};
            transition: .4s;
            border-radius: 24px;
        }}
        .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }}
        input:checked + .slider {{
            background-color: {self.ACCENT_COLOR};
        }}
        input:checked + .slider:before {{
            transform: translateX(20px);
        }}
    </style>
</head>
<body>
    <div class="background-overlay"></div>

    <div id="clock" class="clock"></div>

    <div class="main-container">
        <div class="container">
            <div class="logo">
                {logo_html}
            </div>
            <form id="search-form" class="search-form">
                <div class="search-icon">{search_icon_svg}</div>
                <input type="text" id="search-input" class="search-input"
                    placeholder="Search with {search_engine} or enter address" 
                    autocomplete="off" autofocus>
            </form>
            <div class="top-sites-grid">
                {top_sites_html}
            </div>
        </div>
    </div>

    <!-- Settings Button -->
    <button class="settings-btn" id="settings-btn" title="Customize New Tab">
        {settings_icon_svg}
    </button>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h2>Customize</h2>
            <button class="sidebar-close-btn" id="sidebar-close-btn">
                {close_icon_svg}
            </button>
        </div>
        <div class="sidebar-content">
            <div class="setting-row">
                <label for="show-top-sites-toggle">Show Top Sites</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="show-top-sites-toggle">
                    <span class="slider"></span>
                </label>
            </div>
            <div class="setting-row">
                <label for="show-background-toggle">Show Background Image</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="show-background-toggle">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const clockElement = document.getElementById('clock');
            function updateClock() {{
                const now = new Date();
                let hours = now.getHours();
                const minutes = now.getMinutes().toString().padStart(2, '0');
                const ampm = hours >= 12 ? 'PM' : 'AM';
                hours = hours % 12;
                hours = hours ? hours : 12; // Hour '0' should be '12'
                
                clockElement.textContent = `${{hours}}:${{minutes}} ${{ampm}}`;
            }}
            
            updateClock();
            setInterval(updateClock, 1000);

            const searchForm = document.getElementById('search-form');
            const searchInput = document.getElementById('search-input');
            const searchEngine = "{search_engine}";
            
            searchForm.addEventListener('submit', (e) => {{
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {{
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

            // --- New Sidebar and Settings Logic ---
            const settingsBtn = document.getElementById('settings-btn');
            const sidebar = document.getElementById('sidebar');
            const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
            const topSitesToggle = document.getElementById('show-top-sites-toggle');
            const backgroundToggle = document.getElementById('show-background-toggle');

            // Open sidebar
            settingsBtn.addEventListener('click', () => {{
                sidebar.classList.add('is-open');
            }});

            // Close sidebar
            sidebarCloseBtn.addEventListener('click', () => {{
                sidebar.classList.remove('is-open');
            }});

            // Handle toggle for showing/hiding top sites
            topSitesToggle.addEventListener('change', (e) => {{
                const show = e.target.checked;
                if (show) {{
                    document.body.classList.remove('top-sites-hidden');
                    localStorage.setItem('showTopSites', 'true');
                }} else {{
                    document.body.classList.add('top-sites-hidden');
                    localStorage.setItem('showTopSites', 'false');
                }}
            }});

            // Load saved preference on start
            const showTopSites = localStorage.getItem('showTopSites') !== 'false'; // Default to true
            topSitesToggle.checked = showTopSites;
            if (!showTopSites) {{
                document.body.classList.add('top-sites-hidden');
            }}

            // Handle toggle for showing/hiding background image
            backgroundToggle.addEventListener('change', (e) => {{
                const show = e.target.checked;
                if (show) {{
                    document.body.classList.remove('background-hidden');
                    localStorage.setItem('showBackgroundImage', 'true');
                }} else {{
                    document.body.classList.add('background-hidden');
                    localStorage.setItem('showBackgroundImage', 'false');
                }}
            }});

            // Load saved preference for background on start
            const showBackgroundImage = localStorage.getItem('showBackgroundImage') !== 'false'; // Default to true
            backgroundToggle.checked = showBackgroundImage;
            if (!showBackgroundImage) {{
                document.body.classList.add('background-hidden');
            }}
        }});
    </script>
</body>
</html>
"""

    def get_history_page_html(self):
        """Generates the HTML for the premium, modern history page."""
        # --- Python Data Processing ---
        history_items = self.history_manager.get_history(limit=500)
        
        grouped_history = defaultdict(list)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        for history_tuple in history_items:
            # item is a tuple: (id, url, title, visit_time_iso, favicon)
            visit_dt = datetime.fromisoformat(history_tuple[3])
            visit_date = visit_dt.date()

            if visit_date == today:
                group_key = "Today"
            elif visit_date == yesterday:
                group_key = "Yesterday"
            else:
                group_key = visit_date.strftime("%A, %B %d, %Y")
            
            grouped_history[group_key].append({
                "id": history_tuple[0],
                "url": history_tuple[1],
                "title": history_tuple[2] if history_tuple[2] else history_tuple[1],
                "visit_time": visit_dt.strftime("%I:%M %p"), # e.g., "03:45 PM"
                "favicon": history_tuple[4]
            })

        history_groups_list = [{"date": key, "items": value} for key, value in grouped_history.items()]
        history_json = json.dumps(history_groups_list)
        
        theme = self.THEMES.get(self.theme_name, self.THEMES["dark"])

        # --- HTML, CSS, and JavaScript ---
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
                /* Custom scrollbar for a premium feel */
                ::-webkit-scrollbar {{ width: 12px; }}
                ::-webkit-scrollbar-track {{ background: transparent; }}
                ::-webkit-scrollbar-thumb {{ background-color: {theme['BORDER_COLOR']}; border-radius: 20px; border: 3px solid {theme['BG_COLOR']}; }}
                ::-webkit-scrollbar-thumb:hover {{ background-color: {theme['TAB_TEXT_COLOR']}; }}
                body {{
                    background-color: {theme['BG_COLOR']};
                    color: {theme['TEXT_COLOR']};
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }}
                /* Define dynamic colors as CSS variables for Tailwind to use */
                :root {{
                    --danger-color: {theme['DANGER_COLOR']};
                    --toolbar-color: {theme['TOOLBAR_COLOR']};
                    --bg-color: {theme['BG_COLOR']};
                    --accent-color: {self.ACCENT_COLOR};
                    --text-color: {theme['TEXT_COLOR']};
                    --border-color: {theme['BORDER_COLOR']};
                    --tab-text-color: {theme['TAB_TEXT_COLOR']};
                }}
            </style>
        </head>
        <body class="antialiased">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                
                <div class="flex justify-between items-center mb-8">
                    <h1 class="text-4xl font-bold tracking-tight">History</h1>
                    <button id="clear-history-btn" class="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-bold rounded-md shadow-sm text-white bg-[var(--danger-color)] hover:bg-opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                        Clear Browsing Data
                    </button>
                </div>
                
                <div class="relative mb-8">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" /></svg>
                    </div>
                    <input type="text" id="search-input" placeholder="Search history..."
                           class="block w-full pl-12 pr-3 py-3 border-transparent rounded-lg leading-5 bg-[var(--toolbar-color)] text-[var(--text-color)] placeholder-gray-400 focus:outline-none focus:bg-[var(--bg-color)] focus:border-[var(--accent-color)] focus:ring-1 focus:ring-[var(--accent-color)] sm:text-sm">
                </div>
                
                <div id="history-list" class="space-y-8">
                    <!-- History items will be rendered here -->
                </ul>
                <div id="no-results" class="text-center py-16 hidden">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" /></svg>
                    <h3 class="mt-2 text-sm font-bold text-gray-200">No history items</h3>
                    <p class="mt-1 text-sm text-gray-400">Your browsing history is empty or doesn't match your search.</p>
                </div>
            </div>

            <script>
                const historyData = {history_json};

                const list = document.getElementById('history-list');
                const searchInput = document.getElementById('search-input');
                const noResults = document.getElementById('no-results');
                const defaultFavicon = `<div class="h-5 w-5 flex items-center justify-center bg-[var(--border-color)] rounded-sm"><svg class="h-3.5 w-3.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2h1a2 2 0 002-2v-1a2 2 0 012-2h1.945M7.758 16.242a3.5 3.5 0 01-4.95-4.95L7.758 6.343" /></svg></div>`;

                function renderHistory(groups) {{
                    if (groups.length === 0) {{
                        list.innerHTML = '';
                        noResults.classList.remove('hidden');
                        return;
                    }}
                    noResults.classList.add('hidden');

                    let html = '';
                    for (const group of groups) {{
                        html += `<div class="date-group">
                                    <h2 class="text-lg font-bold mb-3 px-3">${{group.date}}</h2>
                                    <ul class="space-y-1">`;
                        // Use template literals for the entire loop for cleaner code
                        for (const item of group.items) {{
                            const faviconHtml = item.favicon ? `<img src="${{item.favicon}}" class="h-5 w-5" alt="">` : defaultFavicon;
                            html += `
                            <li class="group">
                                <a href="${{item.url}}" class="flex items-center p-3 rounded-lg hover:bg-[var(--toolbar-color)] transition-colors">
                                    <div class="flex-shrink-0 w-24 text-sm text-right pr-4 text-[var(--tab-text-color)]">${{item.visit_time}}</div>
                                    <div class="flex-shrink-0">${{faviconHtml}}</div>
                                    <div class="ml-4 flex-auto overflow-hidden">
                                        <p class="text-sm font-bold text-ellipsis truncate" title="${{item.title}}">${{item.title}}</p>
                                        <p class="text-xs text-gray-400 text-ellipsis truncate">${{item.url}}</p>
                                    </div>
                                    <button data-history-id="${{item.id}}" class="remove-item-btn flex-shrink-0 ml-4 p-1.5 rounded-full text-gray-400 hover:bg-[var(--border-color)] hover:text-white opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity" title="Remove from history">
                                        <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                    </button>
                                </a>
                            </li>`;
                        }}
                        html += `</ul></div>`;
                    }}
                    list.innerHTML = html;
                }}

                searchInput.addEventListener('input', (e) => {{
                    const searchTerm = e.target.value.toLowerCase();
                    if (!searchTerm) {{
                        renderHistory(historyData);
                        return;
                    }}
                    const filteredGroups = [];
                    for (const group of historyData) {{
                        const filteredItems = group.items.filter(item => 
                            item.title.toLowerCase().includes(searchTerm) || 
                            item.url.toLowerCase().includes(searchTerm)
                        );
                        if (filteredItems.length > 0) {{
                            filteredGroups.push({{ date: group.date, items: filteredItems }});
                        }}
                    }}
                    renderHistory(filteredGroups);
                }});

                // Event delegation for remove buttons
                list.addEventListener('click', function(e) {{
                    const removeButton = e.target.closest('.remove-item-btn');
                    if (removeButton) {{
                        e.preventDefault(); // Prevent navigation
                        const historyId = parseInt(removeButton.dataset.historyId, 10);
                        if (historyId && window.backend) {{
                            window.backend.removeHistoryItem(historyId);
                            
                            // Optimistically remove from UI
                            const li = removeButton.closest('li.group');
                            const ul = li.parentElement;
                            li.remove();
                            if (ul.children.length === 0) {{
                                ul.closest('.date-group').remove();
                            }}

                            // Also remove from local data to keep search consistent
                            for (const group of historyData) {{
                                const index = group.items.findIndex(item => item.id == historyId);
                                if (index > -1) {{
                                    group.items.splice(index, 1);
                                    break;
                                }}
                            }}
                            
                            if (list.children.length === 0) {{
                                noResults.classList.remove('hidden');
                            }}
                        }}
                    }}
                }});

                document.getElementById('clear-history-btn').addEventListener('click', () => {{
                    if (window.backend) {{
                        window.backend.clearHistory();
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
        theme = self.theme
        current_year = datetime.now().year
        
        logo_html = ""
        try:
            # Look for favicon.png or favicon.ico in the same directory as this script
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            favicon_path_png = os.path.join(app_root, 'favicon.png')
            favicon_path_ico = os.path.join(app_root, 'favicon.ico')
            
            favicon_path = None
            if os.path.exists(favicon_path_png):
                favicon_path = favicon_path_png
                mime_type = "image/png"
            elif os.path.exists(favicon_path_ico):
                favicon_path = favicon_path_ico
                mime_type = "image/x-icon"

            if favicon_path:
                with open(favicon_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                    logo_html = f'<img src="data:{mime_type};base64,{encoded_string}" alt="DisunicX Logo">'
            else:
                # Fallback to SVG if no favicon is found
                logo_html = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)
        except Exception as e:
            print(f"Could not load logo for about page: {e}")
            # Fallback to SVG on any error
            logo_html = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)

        # --- Feature Icons ---
        tor_icon = SVG_ICONS['tor_active'].replace('currentColor', self.ACCENT_COLOR)
        privacy_icon = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)
        settings_icon = SVG_ICONS['settings_general'].replace('currentColor', self.ACCENT_COLOR)
        updates_icon = SVG_ICONS['downloads'].replace('currentColor', self.ACCENT_COLOR)

        return f"""<!DOCTYPE html>
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>About DisunicX</title>
            <style>
                :root {{
                    --bg-color: {theme['BG_COLOR']};
                    --text-color: {theme['TEXT_COLOR']};
                    --toolbar-color: {theme['TOOLBAR_COLOR']};
                    --border-color: {theme['BORDER_COLOR']};
                    --accent-color: {self.ACCENT_COLOR};
                    --subtle-text-color: {theme['TAB_TEXT_COLOR']};
                }}
                body {{
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    margin: 0;
                    padding: 40px;
                    display: grid;
                    place-items: center;
                    min-height: 100vh;
                    box-sizing: border-box;
                    background-image: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 1.5,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {theme['TOOLBAR_COLOR']}, stop: 1 {theme['BG_COLOR']}
                    );
                }}
                .container {{
                    max-width: 700px;
                    width: 100%;
                }}
                .header {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center; 
                    padding-bottom: 40px;
                    border-bottom: 1px solid var(--border-color);
                    margin-bottom: 40px;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    margin-bottom: 20px;
                }}
                .logo img, .logo svg {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                    border-radius: 16px;
                }}
                h1 {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin: 0;
                }}
                .version {{
                    font-size: 1rem;
                    color: var(--subtle-text-color);
                    margin-top: 8px;
                    background-color: var(--toolbar-color);
                    padding: 4px 12px;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                }}
                .description {{
                    font-size: 1.1rem; 
                    line-height: 1.6;
                    color: var(--subtle-text-color);
                    max-width: 550px;
                    margin-top: 16px;
                }}
                .features-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .feature-card {{
                    background-color: var(--toolbar-color);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 20px;
                    display: flex;
                    align-items: flex-start; 
                    gap: 15px;
                }}
                .feature-icon {{
                    width: 24px;
                    height: 24px;
                    flex-shrink: 0;
                }}
                .feature-text h3 {{
                    font-size: 1rem; 
                    font-weight: 600;
                    margin: 0 0 5px 0;
                }}
                .feature-text p {{
                    font-size: 0.9rem;
                    color: var(--subtle-text-color);
                    margin: 0;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    padding-top: 30px;
                    border-top: 1px solid var(--border-color);
                }}
                .update-button {{
                    display: inline-block;
                    background-color: var(--accent-color);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    text-decoration: none;
                    transition: transform 0.2s, background-color 0.2s;
                    margin-bottom: 30px;
                }} 
                .update-button:hover {{
                    transform: scale(1.05);
                }}
                .footer-links a {{
                    color: var(--subtle-text-color);
                    text-decoration: none;
                    margin: 0 12px;
                    font-size: 0.9rem;
                }} 
                .footer-links a:hover {{
                    text-decoration: underline;
                }}
                .copyright {{
                    margin-top: 16px;
                    font-size: 0.8rem;
                    color: var(--subtle-text-color);
                }} 
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{logo_html}</div>
                    <h1>DisunicX</h1>
                    <p class="version">Version {self.__version__}</p>
                    <p class="description">
                        A modern, open-source web browser proudly developed in India, built for privacy and security with the Tor network.
                    </p>
                </div>

                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">{tor_icon}</div>
                        <div class="feature-text">
                            <h3>Tor Integration</h3>
                            <p>Automatically routes traffic through the Tor network for enhanced anonymity.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{privacy_icon}</div>
                        <div class="feature-text">
                            <h3>Privacy Focused</h3>
                            <p>Control cookies, tracking, and security levels to protect your data.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{settings_icon}</div>
                        <div class="feature-text">
                            <h3>Customizable</h3>
                            <p>Personalize your experience with themes, settings, and a bookmarks bar.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{updates_icon}</div>
                        <div class="feature-text">
                            <h3>Automatic Updates</h3>
                            <p>Stay up-to-date with the latest features and security patches seamlessly.</p>
                        </div>
                    </div>
                </div>

                <div class="footer">
                    <a href="disunic://check-for-updates" class="update-button">Check for Updates</a>
                    <div class="footer-links">
                        <a href="https://github.com/SouvikNandi1/disunicx2021" target="_blank">GitHub</a>
                        <a href="https://github.com/SouvikNandi1/disunicx2021/blob/main/LICENSE" target="_blank">License</a>
                    </div>
                    <p class="copyright">Copyright © {current_year} The DisunicX Project. Developed by Souvik Nandi.</p>
                </div>
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

    def mousePressEvent(self, event: QMouseEvent):
        if sys.platform != "win32":
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for resizing first
            if not self.isMaximized():
                self._resize_edge = self.get_resize_edge(event.position().toPoint())
                if self._resize_edge is not None:
                    self._resizing = True
                    event.accept()
                    return

            # Check for title bar drag
            title_bar_pos = self.title_bar_widget.mapFrom(self, event.position().toPoint())
            is_on_title_bar = self.title_bar_widget.rect().contains(title_bar_pos)

            # Check if the click is on the title bar area
            if is_on_title_bar: 
                # Determine if the click was on an interactive element that should NOT start a drag.
                on_window_controls = self.window_controls_widget.geometry().contains(title_bar_pos)
                
                # Check if the click was on an actual tab, not the empty space in the tab bar.
                tab_bar_widget = self.tab_widget.tab_bar
                on_a_tab = tab_bar_widget.tabAt(tab_bar_widget.mapFromGlobal(event.globalPosition().toPoint())) != -1

                if not on_window_controls and not on_a_tab:
                    self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if sys.platform != "win32":
            super().mouseMoveEvent(event)
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._resizing:
                self.resize_window(event.globalPosition().toPoint())
                event.accept()
                return
            elif not self.drag_pos.isNull():
                if self.isMaximized():
                    # Un-maximize and adjust drag position
                    self.toggle_maximize()
                    self.drag_pos = QPoint(int(self.width() * (event.position().x() / self.width())), 15)
                self.move(event.globalPosition().toPoint() - self.drag_pos)
                event.accept()
                return
        elif not self.isMaximized():
            self.update_resize_cursor(event.position().toPoint())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if sys.platform != "win32":
            super().mouseReleaseEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = QPoint()
            self._resizing = False
            self._resize_edge = None
            self.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if sys.platform != "win32":
            super().mouseDoubleClickEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for title bar double-click to maximize/restore
            title_bar_pos = self.title_bar_widget.mapFrom(self, event.position().toPoint())
            is_on_title_bar = self.title_bar_widget.rect().contains(title_bar_pos)
            
            if is_on_title_bar:
                on_window_controls = self.window_controls_widget.geometry().contains(title_bar_pos)
                tab_bar_widget = self.tab_widget.tab_bar
                on_a_tab = tab_bar_widget.tabAt(tab_bar_widget.mapFromGlobal(event.globalPosition().toPoint())) != -1

            if is_on_title_bar and not on_window_controls and not on_a_tab:
                self.toggle_maximize()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def get_resize_edge(self, pos: QPoint):
        if sys.platform != "win32":
            return None
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
        if sys.platform != "win32":
            return

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
        if sys.platform != "win32":
            return

        edge = self.get_resize_edge(pos)
        if edge in ("top", "bottom"):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edge in ("left", "right"):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in ("topleft", "bottomright"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("topright", "bottomleft"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def toggle_maximize(self):
        if sys.platform != "win32":
            return

        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def changeEvent(self, event):
        # This event is triggered when the window state changes (e.g., maximized, minimized)
        if event.type() == QEvent.Type.WindowStateChange:
            if sys.platform != "win32":
                super().changeEvent(event)
                return

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
            reply = CustomMessageBox.question(
                self,
                "Downloads in Progress",
                "You have active downloads. Closing the browser will cancel them. Are you sure you want to exit?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # User wants to close, proceed.
                self.download_manager.cancel_active_downloads()
                event.accept()
            else:
                # User wants to keep the browser open.
                event.ignore()
        else:
            # --- Session Saving Logic ---
            settings = QSettings("DisunicX", "Browser")
            startup_behavior = settings.value("startup_behavior", 0, type=int)
            if startup_behavior == 1: # "Continue where you left off"
                urls_to_save = []
                for i in range(self.tab_widget.count()):
                    widget = self.tab_widget.widget(i)
                    if isinstance(widget, BrowserTab):
                        url = widget.url().toString()
                        # Don't save internal or blank pages
                        if not url.startswith(("disunic:", "about:")):
                            urls_to_save.append(url)
                settings.setValue("last_session_urls", urls_to_save)
            else:
                # Clear last session if the user doesn't want to restore it
                settings.remove("last_session_urls")

            # Force writing settings to disk to ensure session is saved.
            settings.sync()

            # No active downloads, close normally.
            event.accept()

    def add_initial_tabs(self):
        """Adds the initial tabs on startup based on user settings."""
        settings = QSettings("DisunicX", "Browser")
        startup_behavior = settings.value("startup_behavior", 0, type=int)

        if startup_behavior == 1: # Continue where you left off
            last_urls = settings.value("last_session_urls", [])
            # Ensure last_urls is a list, as QSettings can sometimes return a single string
            if isinstance(last_urls, str):
                last_urls = [last_urls]

            if last_urls:
                for url in last_urls:
                    self.add_new_tab(QUrl(url))
                # If we successfully restored tabs, we are done.
                return

        # If we are not restoring a session, or if the session was empty,
        # create a single new tab based on the startup setting.
        if startup_behavior == 2: # "Show a blank page"
            self.add_new_tab(QUrl("about:blank"))
        else: # Default to "Show the New Tab page"
            self.add_new_tab()

    def set_tor_proxy(self):
        settings = QSettings("DisunicX", "Browser")
        
        # Tor is not supported on macOS in this version.
        if sys.platform == "darwin":
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            return

        if settings.value("use_proxy", True, type=bool) and sys.platform != "darwin":
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
        self.toolbar.setIconSize(QSize(22, 22))

        icon_color = self.theme["ICON_COLOR"]

        self.back_btn = QPushButton()
        self.back_btn.setIcon(create_icon_from_svg(SVG_ICONS["back"], icon_color))
        self.back_btn.setToolTip("Back")
        self.back_btn.clicked.connect(lambda: self.current_browser().back())
        self.toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(create_icon_from_svg(SVG_ICONS["forward"], icon_color))
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.clicked.connect(lambda: self.current_browser().forward())
        self.toolbar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(create_icon_from_svg(SVG_ICONS["reload"], icon_color))
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.clicked.connect(lambda: self.current_browser().reload())
        self.toolbar.addWidget(self.reload_btn)

        self.url_bar = UrlBar(self.theme, self)
        self.url_bar.setObjectName("UrlBar") # For styling the container
        self.url_bar.url_edit.setStyleSheet(f"color: {self.TEXT_COLOR};") # Ensure text color
        self.url_bar.url_edit.returnPressed.connect(self.navigate_to_url)
        self.url_bar.bookmarkButtonClicked.connect(self.toggle_bookmark)
        self.toolbar.addWidget(self.url_bar)

        # In modern style, the new tab and overview buttons are in the toolbar
        if self.tab_style == "modern":
            self.new_tab_btn = QPushButton()
            self.new_tab_btn.setIcon(create_icon_from_svg(SVG_ICONS["new_tab"], icon_color))
            self.new_tab_btn.setToolTip("New Tab")
            self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
            self.toolbar.addWidget(self.new_tab_btn)

            self.show_tabs_btn = QPushButton()
            self.show_tabs_btn.setIcon(create_icon_from_svg(SVG_ICONS["tab_grid"], icon_color))
            self.show_tabs_btn.setToolTip("Show All Tabs")
            self.show_tabs_btn.clicked.connect(self.show_tab_overview)
            self.toolbar.addWidget(self.show_tabs_btn)

        # The menu button is now only for non-macOS platforms
        if sys.platform != "darwin":
            # Separator before action buttons
            self.toolbar.addSeparator()
            downloads_btn = QPushButton()
            downloads_btn.setIcon(create_icon_from_svg(SVG_ICONS["downloads"], icon_color))
            downloads_btn.setToolTip("Downloads")
            downloads_btn.clicked.connect(self.open_downloads)
            self.toolbar.addWidget(downloads_btn)

            self.menu_btn = QPushButton()
            self.menu_btn.setIcon(create_icon_from_svg(SVG_ICONS["menu"], icon_color))
            self.menu_btn.setToolTip("Menu")
            self.menu_btn.clicked.connect(self.show_menu)
            self.toolbar.addWidget(self.menu_btn)
    
    def populate_bookmarks_bar(self):
        bookmarks = self.bookmarks_manager.get_bookmarks()
        self.bookmarks_bar.populate_bookmarks(bookmarks)

    def toggle_bookmark(self):
        current_widget = self.current_browser()
        if not isinstance(current_widget, BrowserTab):
            return

        url = current_widget.url().toString()
        title = current_widget.title()
        
        if self.bookmarks_manager.is_bookmarked(url):
            self.bookmarks_manager.remove_bookmark(url)
            self.update_status_message("Bookmark removed")
        else:
            icon_data = qicon_to_base64(current_widget.page().icon())
            self.bookmarks_manager.add_bookmark(title, url, icon_data)
            self.update_status_message("Bookmark added")
        
        self.update_bookmark_button_state(current_widget.url())
        self.populate_bookmarks_bar()

    def remove_bookmark(self, url):
        self.bookmarks_manager.remove_bookmark(url)
        self.update_status_message("Bookmark removed")
        self.populate_bookmarks_bar()
        # Update the button state if the removed bookmark was for the current page
        if self.current_browser().url().toString() == url:
            self.update_bookmark_button_state(self.current_browser().url())

    def reorder_bookmarks(self, url_list):
        """Saves the new order of bookmarks from the bookmarks bar."""
        self.bookmarks_manager.update_order(url_list)

    def toggle_bookmarks_bar(self):
        # The state to transition to
        show = not self.bookmarks_bar.isVisible() or self.bookmarks_bar.height() == 0

        if show:
            self.bookmarks_bar.show_animated()
        else:
            self.bookmarks_bar.hide_animated()
        
        settings = QSettings("DisunicX", "Browser")
        settings.setValue("show_bookmarks_bar", show)

    def load_bookmarks_bar_visibility(self):
        settings = QSettings("DisunicX", "Browser")
        is_visible = settings.value("show_bookmarks_bar", False, type=bool)
        if is_visible:
            # If it should be visible, ensure its height is not 0.
            self.bookmarks_bar.setMaximumHeight(self.bookmarks_bar.sizeHint().height())
            self.bookmarks_bar.setVisible(True)
        else:
            self.bookmarks_bar.setMaximumHeight(0)
            self.bookmarks_bar.setVisible(False)

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

    def open_new_window(self, url=None):
        """Creates and shows a new browser window instance. Can optionally load a URL."""
        new_window = TorBrowser()
        if url:
            new_window.add_new_tab(url)
        new_window.show()

    def update_navigation_state(self, *args):
        """Updates the state of navigation buttons based on the current tab."""
        widget = self.tab_widget.current_widget()
        is_web_tab = isinstance(widget, BrowserTab)

        can_go_back = is_web_tab and widget.history().canGoBack()
        can_go_forward = is_web_tab and widget.history().canGoForward()

        self.back_btn.setEnabled(can_go_back)
        self.forward_btn.setEnabled(can_go_forward)
        self.reload_btn.setEnabled(is_web_tab)
        self.url_bar.setEnabled(is_web_tab) # type: ignore

    def setup_main_menu_button(self):
        """Creates the main menu and its actions once."""
        theme = self.theme
        self.main_menu = QMenu(self)
        self.main_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.main_menu.setWindowFlags(self.main_menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.main_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['MENU_BG_COLOR']};
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']}; /* Fallback border */
                border-radius: 8px;
                padding: 8px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 13px; 
                font-weight: 700; 
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
                min-width: 180px;
            }}
            QMenu::item:selected {{
                background-color: {self.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: {theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
            QMenu::icon {{ padding-left: 5px; }}
            QMenu::right-arrow {{
                image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["forward"].replace("currentColor", theme['ICON_COLOR']))}');
                width: 16px; height: 16px; right: 8px;
            }}
        """)

        actions = [
            {"text": "New Tab", "handler": self.add_new_tab, "icon": "new_tab"},
            {"text": "New Window", "handler": self.open_new_window, "icon": "new_window"},
            {"text": "Home", "handler": self.navigate_home, "icon": "home"},
            None,
            {"text": "Downloads", "handler": self.open_downloads, "icon": "downloads"},
            {"text": "History", "handler": self.open_history, "icon": "history"},
            None,
            {"text": "Bookmarks", "handler": None, "icon": "bookmark_filled", "submenu": [
                {"text": "Show Bookmarks Bar", "handler": self.toggle_bookmarks_bar, "checkable": True},
                {"text": "Bookmark This Tab", "handler": self.toggle_bookmark}
            ]},
            {"text": "Find in Page...", "handler": self.show_find_bar, "icon": "find_in_page"},
            None,
            {"text": "Save Page as PDF...", "handler": self.handle_print_action, "icon": "save_pdf"},
            None,
            {"text": "Settings", "handler": self.open_settings, "icon": "settings_general"},
            {"text": "About DisunicX", "handler": self.show_about, "icon": "info"},
            {"text": "Clear Browsing Data", "handler": self.clear_browsing_data, "icon": "clear_data", "color": self.DANGER_COLOR},
            None,
            {"text": "Exit", "handler": self.close, "icon": "close"}
        ]

        icon_color = theme["ICON_COLOR"]
        for action_data in actions:
            if action_data is None:
                self.main_menu.addSeparator()
                continue

            if "submenu" in action_data:
                submenu = self.main_menu.addMenu(action_data["text"])
                submenu.setWindowFlags(submenu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
                submenu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                submenu.setIcon(create_icon_from_svg(SVG_ICONS[action_data["icon"]], icon_color, QSize(16, 16)))
                for sub_action_data in action_data["submenu"]:
                    sub_act = QAction(sub_action_data["text"], self)
                    if sub_action_data.get("checkable"):
                        sub_act.setCheckable(True)
                        if sub_action_data["text"] == "Show Bookmarks Bar":
                            self.show_bookmarks_bar_action = sub_act
                    sub_act.triggered.connect(lambda checked=False, h=sub_action_data["handler"]: h())
                    submenu.addAction(sub_act)
                continue

            text, handler = action_data["text"], action_data["handler"]
            icon_name, custom_color = action_data.get("icon"), action_data.get("color", icon_color)
            icon = create_icon_from_svg(SVG_ICONS[icon_name], custom_color, QSize(16, 16)) if icon_name else QIcon()
            act = QAction(icon, text, self)
            act.triggered.connect(lambda checked=False, h=handler: h())
            self.main_menu.addAction(act)

            if text == "Save Page as PDF...": self.save_pdf_action = act
            if text == "Find in Page...": self.find_in_page_action = act
            if text == "Home": self.home_action = act

    def setup_menu_bar(self):
        """Creates a native QMenuBar for macOS."""
        self.menu_bar = self.menuBar()
        theme = self.theme
        icon_color = theme["ICON_COLOR"]

        # --- File Menu ---
        file_menu = self.menu_bar.addMenu("&File")
        file_menu.addAction(QAction("New Tab", self, triggered=self.add_new_tab, shortcut=QKeySequence.StandardKey.AddTab))
        file_menu.addAction(QAction("New Window", self, triggered=self.open_new_window, shortcut=QKeySequence.StandardKey.New))
        file_menu.addSeparator()
        self.save_pdf_action = file_menu.addAction(QAction("Save Page as PDF...", self, triggered=self.handle_print_action))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Close Tab", self, triggered=lambda: self.close_tab(self.tab_widget.tab_bar.currentIndex()), shortcut=QKeySequence.StandardKey.Close))
        file_menu.addAction(QAction("Close Window", self, triggered=self.close))

        # --- Edit Menu ---
        edit_menu = self.menu_bar.addMenu("&Edit")
        self.find_in_page_action = edit_menu.addAction(QAction("Find in Page...", self, triggered=self.show_find_bar, shortcut=QKeySequence.StandardKey.Find))
        edit_menu.addSeparator()
        # Standard edit actions are often handled by the system on macOS, but we add them for completeness
        edit_menu.addAction(QAction("Cut", self, triggered=lambda: self.current_browser().triggerPageAction(QWebEnginePage.WebAction.Cut), shortcut=QKeySequence.StandardKey.Cut))
        edit_menu.addAction(QAction("Copy", self, triggered=lambda: self.current_browser().triggerPageAction(QWebEnginePage.WebAction.Copy), shortcut=QKeySequence.StandardKey.Copy))
        edit_menu.addAction(QAction("Paste", self, triggered=lambda: self.current_browser().triggerPageAction(QWebEnginePage.WebAction.Paste), shortcut=QKeySequence.StandardKey.Paste))
        edit_menu.addSeparator()
        # On macOS, the "Preferences" action belongs in the app menu. Setting the role handles this.
    

        # --- View Menu ---
        view_menu = self.menu_bar.addMenu("&View")
        view_menu.addAction(QAction("Reload Page", self, triggered=lambda: self.current_browser().reload(), shortcut=QKeySequence.StandardKey.Refresh))
        view_menu.addSeparator()
        self.show_bookmarks_bar_action = QAction("Show Bookmarks Bar", self, checkable=True, triggered=self.toggle_bookmarks_bar)
        view_menu.addAction(self.show_bookmarks_bar_action)

        # --- Settings Menu (for macOS) ---
        settings_menu = self.menu_bar.addMenu("&Settings")
        open_settings_action = QAction("Open Settings...", self, triggered=self.open_settings, shortcut=QKeySequence.StandardKey.Preferences)
        settings_menu.addAction(open_settings_action)

        # --- History Menu ---
        history_menu = self.menu_bar.addMenu("&History")
        self.home_action = history_menu.addAction(QAction("Home", self, triggered=self.navigate_home, shortcut=QKeySequence("Alt+Home")))
        history_menu.addAction(QAction("Back", self, triggered=lambda: self.current_browser().back(), shortcut=QKeySequence.StandardKey.Back))
        history_menu.addAction(QAction("Forward", self, triggered=lambda: self.current_browser().forward(), shortcut=QKeySequence.StandardKey.Forward))
        history_menu.addSeparator()
        history_menu.addAction(QAction("Show All History", self, triggered=self.open_history))
        history_menu.addAction(QAction("Clear Browsing Data...", self, triggered=self.clear_browsing_data))

        # --- Bookmarks Menu ---
        bookmarks_menu = self.menu_bar.addMenu("&Bookmarks")
        bookmarks_menu.addAction(QAction("Bookmark This Tab", self, triggered=self.toggle_bookmark, shortcut=QKeySequence("Ctrl+D")))
        bookmarks_menu.addAction(self.show_bookmarks_bar_action) # Also add it here for convenience

        # --- Window Menu ---
        window_menu = self.menu_bar.addMenu("&Window")
        window_menu.addAction(QAction("Downloads", self, triggered=self.open_downloads))
        window_menu.addAction(QAction("Minimize", self, triggered=self.showMinimized, shortcut=QKeySequence("Cmd+M")))
        window_menu.addAction(QAction("Zoom", self, triggered=self.toggle_maximize, shortcut=QKeySequence("Ctrl+Shift+F")))

        # --- Help Menu ---
        help_menu = self.menu_bar.addMenu("&Help")
        # On macOS, the "About" action belongs in the app menu. Setting the role handles this.
        about_action = QAction("About DisunicX", self, triggered=self.show_about)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        help_menu.addAction(about_action)
        help_menu.addAction(QAction("Check for Updates...", self, triggered=lambda: self.check_for_updates(force_check=True)))

    def show_menu(self):
        """Updates and shows the main menu."""
        is_web_tab = isinstance(self.current_browser(), BrowserTab)
        self.save_pdf_action.setEnabled(is_web_tab)
        self.find_in_page_action.setEnabled(is_web_tab)
        self.show_bookmarks_bar_action.setChecked(self.bookmarks_bar.isVisible())
        self.home_action.setEnabled(is_web_tab)

        if sys.platform.startswith('linux') and hasattr(self, 'sidebar_menu'):
            self.toggle_sidebar_menu()
        else:
            btn_pos = self.menu_btn.pos()
            menu_pos = self.mapToGlobal(btn_pos) + QPoint(0, self.menu_btn.height() + 4)
            self.main_menu.popup(menu_pos)

    def setup_sidebar_menu(self):
        """Creates the sidebar menu for Linux."""
        self.sidebar_menu = QFrame(self)
        self.sidebar_menu.setObjectName("SidebarMenu")
        self.sidebar_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.sidebar_menu.setFixedWidth(0) # Start hidden
        self.sidebar_menu.setVisible(False)

        sidebar_layout = QVBoxLayout(self.sidebar_menu)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(5)

        # Add actions from the main menu to the sidebar
        for action in self.main_menu.actions():
            if action.isSeparator():
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet(f"border-top: 1px solid {self.theme['MENU_SEPARATOR_COLOR']}; margin: 5px 0;")
                sidebar_layout.addWidget(separator)
            elif action.menu(): # It's a submenu
                # For now, we just add the main action. Submenu items could be a future enhancement.
                btn = QPushButton(action.icon(), action.text())
                btn.setObjectName("SidebarMenuButton")
                # We can't directly trigger the submenu, so we'll have it open settings as a placeholder
                if "Bookmarks" in action.text():
                    btn.clicked.connect(self.toggle_bookmarks_bar)
                sidebar_layout.addWidget(btn)
            else:
                btn = QPushButton(action.icon(), action.text())
                btn.setObjectName("SidebarMenuButton")
                btn.clicked.connect(action.trigger)
                sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        self.content_layout.addWidget(self.sidebar_menu)

        self.sidebar_animation = QPropertyAnimation(self.sidebar_menu, b"maximumWidth")
        self.sidebar_animation.setDuration(200)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setStyleSheet(self.styleSheet() + f"""
            #SidebarMenu {{ 
                background-color: {self.theme['MENU_BG_COLOR']}; 
                border-left: 1px solid {self.theme['BORDER_COLOR']}; 
            }}
            #SidebarMenu QPushButton {{ text-align: left; padding: 10px; border: none; border-radius: 6px; font-weight: 700; color: {self.theme['TEXT_COLOR']}; }}
            #SidebarMenu QPushButton:hover {{ background-color: {self.theme['BUTTON_HOVER_COLOR']}; }}
        """)

    def show_tab_context_menu(self, index, global_pos):
        browser = self.tab_widget.widget(index) # type: ignore
        # Only show for BrowserTab, not for Settings, Downloads etc.
        if not isinstance(browser, BrowserTab):
            return

        theme = self.theme
        menu = QMenu(self) # type: ignore
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        menu.setStyleSheet(f"""
            QMenu {{ # type: ignore
                background-color: {theme['MENU_BG_COLOR']};
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 700; 
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
                min-width: 180px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: {theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
            QMenu::icon {{
                padding-left: 5px;
            }}
        """)

        icon_color = theme["ICON_COLOR"]

        # Mute/Unmute action
        if browser.page().recentlyAudible():
            is_muted = browser.page().isAudioMuted()
            mute_action_text = "Unmute Tab" if is_muted else "Mute Tab"
            icon_name = "audio_muted" if is_muted else "audio_playing" # type: ignore
            mute_action = QAction(create_icon_from_svg(SVG_ICONS[icon_name], icon_color, QSize(16, 16)), mute_action_text, self)
            mute_action.triggered.connect(browser.toggle_mute)
            menu.addAction(mute_action)
            menu.addSeparator()

        # Reload
        reload_action = QAction(create_icon_from_svg(SVG_ICONS["reload"], icon_color, QSize(16, 16)), "Reload", self)
        reload_action.triggered.connect(browser.reload)
        menu.addAction(reload_action)

        # Duplicate
        duplicate_action = QAction(create_icon_from_svg(SVG_ICONS["new_tab"], icon_color, QSize(16, 16)), "Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.add_new_tab(browser.url()))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Close
        close_action = QAction(create_icon_from_svg(SVG_ICONS["close"], icon_color, QSize(16, 16)), "Close Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)

        menu.exec(global_pos)

    def toggle_sidebar_menu(self):
        """Animates the sidebar menu open or closed on Linux."""
        if not hasattr(self, 'sidebar_menu'):
            return

        # Disconnect any previous connections to avoid unwanted behavior
        try:
            self.sidebar_animation.finished.disconnect()
        except (TypeError, RuntimeError):
            # No connections to disconnect, which is fine
            pass

        if self.sidebar_menu.isVisible():
            self.sidebar_animation.setStartValue(250)
            self.sidebar_animation.setEndValue(0)
            # When the closing animation finishes, hide the widget
            self.sidebar_animation.finished.connect(lambda: self.sidebar_menu.setVisible(False))
        else:
            self.sidebar_menu.setVisible(True)
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(250)
        self.sidebar_animation.start()
    def open_history(self):
        # Check if a history tab is already open and switch to it
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                self.tab_widget.set_current_index(i)
                return

        # If not, create a new tab for history
        html = self.get_history_page_html()
        browser = self.add_new_tab(activate=True)
        
        # Setup QWebChannel to allow JS to call Python
        channel = QWebChannel(browser.page())
        history_backend = HistoryPageBackend(self.history_manager)
        history_backend.clearHistoryRequested.connect(self.clear_browsing_data)
        channel.registerObject("backend", history_backend)
        browser.page().setWebChannel(channel)

        # Keep backend and channel alive with the browser tab to prevent garbage collection
        browser.history_backend = history_backend
        browser.channel = channel

        browser.setHtml(html, QUrl("disunic://history"))

    def open_downloads(self):
        """Opens the download manager in a new tab, or switches to it if already open."""
        if self.download_manager_is_in_tab:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.download_manager:
                    self.tab_widget.set_current_index(i)
                    return
        
        # If not in a tab, add it
        icon_color = self.theme["ICON_COLOR"]
        icon = create_icon_from_svg(SVG_ICONS["downloads"], icon_color)
        self.tab_widget.add_tab(self.download_manager, "Downloads", icon)
        self.download_manager_is_in_tab = True


    def open_settings(self, tab_index=0):
        """Opens the settings page in a new tab, or switches to it if already open."""
        if self.settings_page_is_in_tab:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.settings_page:
                    self.tab_widget.set_current_index(i)
                    self.settings_page.nav_list.setCurrentRow(tab_index) # Also switch to the correct inner tab
                    return

        # If not in a tab, add it
        icon_color = self.theme["ICON_COLOR"]
        icon = create_icon_from_svg(SVG_ICONS["settings_general"], icon_color)
        self.tab_widget.add_tab(self.settings_page, "Settings", icon)
        self.settings_page.nav_list.setCurrentRow(tab_index)
        self.settings_page_is_in_tab = True
    
    def clear_browsing_data(self):
        reply = CustomMessageBox.question(
            self,
            "Clear Browsing Data",
            "Are you sure you want to clear all browsing data (history, cookies, cache)? This action cannot be undone.",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            self.history_manager.clear_history()
            self.download_manager.clear_all()

            # Find and update any open history tabs
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                    if hasattr(widget, 'history_backend'):
                        # Emit the signal to tell the JS to clear its view
                        widget.history_backend.historyCleared.emit()

            # Use a non-modal dialog to avoid blocking the event loop,
            # which would prevent the historyCleared signal from being processed by the web page.
            info_box = QMessageBox(QMessageBox.Icon.Information, "Information", "All browsing data has been cleared.", QMessageBox.StandardButton.Ok, self)
            info_box.setWindowModality(Qt.WindowModality.NonModal)
            info_box.show()
    
    def show_about(self):
        # Check if an about tab is already open
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://about":
                self.tab_widget.set_current_index(i)
                return

        # If not, create a new tab for it
        html = self.get_about_page_html()
        browser = self.add_new_tab()
        browser.setHtml(html, QUrl("disunic://about")) # type: ignore
    
    def add_new_tab(self, url=None):
        # Ensure url is a QUrl object if it's passed as a string
        if isinstance(url, str):
            url = QUrl(url)

        browser = BrowserTab(self.profile, self) # Pass main_window reference
        browser.page_loaded_for_history.connect(self.add_to_history)
        browser.urlChanged.connect(self.update_url_bar)
        browser.urlChanged.connect(self.update_navigation_state)
        browser.urlChanged.connect(self.update_bookmark_button_state)
        browser.page().zoomFactorChanged.connect(self.update_zoom_label)

        browser.audioStateChanged.connect(self.update_tab_audio_indicator)
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

        def on_find_finished(result):
            if self.find_bar.isVisible():
                self.find_bar.update_results(result.activeMatch(), result.numberOfMatches())
        browser.page().findTextFinished.connect(on_find_finished)

        browser.page().linkHovered.connect(lambda url: self.update_status_message(url if url else ("Loading..." if browser.is_loading else "Ready")))

        browser.titleChanged.connect(self.update_tab_title)
        browser.page().iconChanged.connect(lambda icon, b=browser: self.update_tab_icon(b, icon))

        load_new_tab_page = False
        if url is None:
            load_new_tab_page = True

        # Add to stacked widget and tab bar
        self.tab_widget.add_tab(browser, "Loading...")

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
        self.find_bar.hide_and_clear()
        if index > -1:
            widget = self.tab_widget.widget(index)

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
                self.update_bookmark_button_state(widget.url())
            elif isinstance(widget, DownloadManagerPage):
                self.update_url_bar(QUrl("disunic://downloads"))
                self.update_status_message("Downloads")
            elif isinstance(widget, SettingsPage):
                self.update_url_bar(QUrl("disunic://settings"))
                self.update_status_message("Settings")
            
            self.update_navigation_state()
            self.update_zoom_label()
        else:
            self.update_url_bar(QUrl(""))
            self.update_status_message("Ready")
            self.update_bookmark_button_state(QUrl(""))
            self.update_navigation_state()
    
    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            widget_to_remove = self.tab_widget.remove_tab(index)

            # Special handling for the download manager tab
            if widget_to_remove == self.download_manager:
                self.download_manager_is_in_tab = False
                # IMPORTANT: Do not delete the widget, just hide it.
                # It's parented to the main window, so it won't be garbage collected.
            elif widget_to_remove == self.settings_page:
                self.settings_page_is_in_tab = False
            else:
                widget_to_remove.deleteLater() # Important to free memory
        else:
            self.close()
    
    def update_tab_audio_indicator(self, is_audible, is_muted):
        sender_browser = self.sender()
        if not isinstance(sender_browser, BrowserTab):
            return

        index = self.tab_widget.index_of(sender_browser)
        if index == -1:
            return

        # The tab button is on the tab bar, which is inside the tab_widget
        tab_bar = self.tab_widget.tab_bar
        existing_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide)

        if not is_audible:
            if existing_button:
                tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
                existing_button.deleteLater()
            return

        button = existing_button
        if not button:
            button = QPushButton()
            button.setObjectName("AudioIndicatorBtn")
            button.setFlat(True)
            button.clicked.connect(sender_browser.toggle_mute)
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, button)

        icon_color = self.theme["ICON_COLOR"]
        if is_muted:
            button.setIcon(create_icon_from_svg(SVG_ICONS["audio_muted"], icon_color, QSize(16, 16)))
            button.setToolTip("Unmute Tab")
        else:
            button.setIcon(create_icon_from_svg(SVG_ICONS["audio_playing"], icon_color, QSize(16, 16)))
            button.setToolTip("Mute Tab")

    def show_find_bar(self):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            self.find_bar.show_bar()

    def on_find_next(self, text):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText(text)

    def on_find_previous(self, text):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText(text, QWebEnginePage.FindFlags(QWebEnginePage.FindFlag.FindBackward))

    def on_find_closed(self):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText("") # Clear find highlights

    def show_tab_overview(self):
        """Captures tab snapshots and shows the tab overview grid."""
        tabs_data = []
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, (BrowserTab, SettingsPage, DownloadManagerPage)):
                pixmap = QPixmap(widget.size())
                widget.render(pixmap)
                tabs_data.append({
                    'index': i,
                    'title': self.tab_widget.tab_bar.tabText(i),
                    'pixmap': pixmap
                })
        
        self.tab_overview.populate(tabs_data)
        self.main_stack.setCurrentWidget(self.tab_overview)

    def hide_tab_overview(self):
        """Hides the tab overview and returns to the tab view."""
        if self.tab_style == "classic":
            self.main_stack.setCurrentWidget(self.tab_widget.stacked_widget)
        else: # modern
            self.main_stack.setCurrentWidget(self.tab_widget)

    def select_tab_from_overview(self, index):
        self.tab_widget.set_current_index(index)
        self.hide_tab_overview()

    def add_new_tab_from_overview(self):
        """Adds a new tab and immediately switches to it from the overview."""
        self.add_new_tab()
        self.hide_tab_overview()

    def close_tab_from_overview(self, index):
        self.close_tab(index)
        self.show_tab_overview() # Refresh the overview

    def reorder_tabs(self, from_index, to_index):
        """Moves a tab in the underlying QTabBar when reordered in the overview."""
        # Move the tab in the non-visible tab bar first. This updates the logical order.
        self.tab_widget.tab_bar.moveTab(from_index, to_index)
        # Defer the visual refresh to the next event loop cycle. This prevents the crash.
        QTimer.singleShot(0, self.show_tab_overview)

    def on_tab_title_changed_from_overview(self, index, new_title):
        """Updates the tab's title when edited in the overview."""
        self.tab_widget.set_tab_text(index, new_title)

    def close_all_tabs(self):
        """Closes all tabs and creates a single new one."""
        # Block signals to prevent unwanted side effects during removal
        self.tab_widget.blockSignals(True)

        # Remove all widgets from the tab widget
        while self.tab_widget.count() > 0:
            widget_to_remove = self.tab_widget.remove_tab(0)
            if widget_to_remove not in [self.download_manager, self.settings_page]:
                widget_to_remove.deleteLater()

        # Unblock signals and create a fresh tab
        self.tab_widget.blockSignals(False)
        self.add_new_tab()
        self.hide_tab_overview()

    def current_browser(self):
        return self.tab_widget.current_widget()

    def update_status_bar(self, message):
        self.status.showMessage(message)
    
    def update_status_message(self, message="Ready"):
        # Truncate long hover URLs
        if message.startswith("http") and len(message) > 80:
            message = message[:77] + "..."
        self.status_label.setText(message) 
        # If the message is not the default "Ready", start a timer to clear it.
        if message != "Ready":
            self.status_clear_timer.start()
        else:
            # If we are setting it to ready, stop any pending clear timers.
            self.status_clear_timer.stop()

    def update_tor_status(self, url: QUrl):
        def _hex_to_rgba(hex_color, alpha):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"rgba({r}, {g}, {b}, {alpha})"

        if sys.platform == "darwin":
            self.tor_status_widget.hide()
            return

        settings = QSettings("DisunicX", "Browser")
        if settings.value("use_proxy", True, type=bool) and sys.platform != "darwin":
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
            
            secure_color = self.SECURE_COLOR
            secure_bg = _hex_to_rgba(secure_color, 0.15)
            secure_border = _hex_to_rgba(secure_color, 0.3)

            self.tor_status_widget.setStyleSheet(f"""
                QWidget#TorStatusWidget {{
                    background-color: transparent;
                    border-radius: 8px;
                    border: none;
                    padding: 4px 10px;
                }}
                QLabel#TorStatusLabel {{
                    color: {secure_color};
                    background-color: transparent;
                    font-weight: 700;
                    padding: 0; margin: 0;
                }}
            """)
            self.tor_status_icon.setPixmap(create_icon_from_svg(SVG_ICONS["tor_active"], secure_color, size=QSize(14, 14)).pixmap(QSize(14, 14)))
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
        self.url_bar.setUrl(url, self.SECURE_COLOR, self.DANGER_COLOR)
        # Update Tor status based on the new URL
        self.update_tor_status(url)
        self.update_bookmark_button_state(url)
        self.update_zoom_label()

    def update_bookmark_button_state(self, url):
        if not isinstance(self.current_browser(), BrowserTab):
            self.url_bar.bookmark_button.setVisible(False)
            return

        url_str = url.toString()
        is_special_page = url_str.startswith(("disunic:", "about:", "view-source:")) or not url_str
        
        self.url_bar.bookmark_button.setVisible(not is_special_page)
        if not is_special_page:
            is_bookmarked = self.bookmarks_manager.is_bookmarked(url_str)
            color = self.ACCENT_COLOR if is_bookmarked else self.theme["ICON_COLOR"]
            self.url_bar.set_bookmark_icon(is_bookmarked, color)

    def update_tab_title(self, title):
        # Find the tab that emitted the signal
        sender_browser = self.sender()
        if sender_browser and self.tab_widget:
            index = self.tab_widget.index_of(sender_browser)
            if index != -1:
                self.tab_widget.set_tab_text(index, title)
                self.tab_widget.set_tab_tooltip(index, title)

        # Find the tab that emitted the signal
        sender_browser = self.sender()
        if sender_browser and self.tab_widget:
            index = self.tab_widget.index_of(sender_browser)
            if index != -1:
                self.tab_widget.set_tab_text(index, title)
                self.tab_widget.set_tab_tooltip(index, title)

    def update_tab_icon(self, browser, icon):
        if self.tab_widget:
            index = self.tab_widget.index_of(browser)
            if index != -1:
                self.tab_widget.set_tab_icon(index, icon)

    def check_for_updates(self, force_check=False):
        """Initializes and runs the application updater."""
        if not hasattr(self, 'updater'):
            self.updater = Updater(current_version=self.__version__, parent=self)
        self.updater.check_for_updates(force_check=force_check)
    
    def show_welcome_if_first_time(self):
        settings = QSettings("DisunicX", "Browser")
        if not settings.value("terms_accepted", False, type=bool):
            dialog = WelcomeDialog(self)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                settings.setValue("terms_accepted", True)
                
                CustomMessageBox.information(
                    self,
                    "Thank You",
                    "Thank you for accepting the terms. Enjoy browsing securely!"
                )
                return True
            else: # User clicked Decline or closed the dialog
                # The application cannot run without accepting the terms.
                QApplication.instance().quit()
                return False # Signal to the constructor to stop initialization.
        return True

    def update_toolbar_icons(self, color):
        """Helper to update the color of all toolbar icons."""
        self.back_btn.setIcon(create_icon_from_svg(SVG_ICONS["back"], color))
        self.forward_btn.setIcon(create_icon_from_svg(SVG_ICONS["forward"], color))
        self.reload_btn.setIcon(create_icon_from_svg(SVG_ICONS["reload"], color))
        if self.tab_style == "modern":
            self.new_tab_btn.setIcon(create_icon_from_svg(SVG_ICONS["new_tab"], color))
            self.show_tabs_btn.setIcon(create_icon_from_svg(SVG_ICONS["tab_grid"], color))
        if sys.platform != "darwin":
            self.menu_btn.setIcon(create_icon_from_svg(SVG_ICONS["menu"], color))

    def show_tab_context_menu(self, index, global_pos):
        browser = self.tab_widget.widget(index)
        # Only show for BrowserTab, not for Settings, Downloads etc.
        if not isinstance(browser, BrowserTab):
            return

        theme = self.theme
        menu = QMenu(self) # type: ignore
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        menu.setStyleSheet(f"""
            QMenu {{ # type: ignore
                background-color: {theme['MENU_BG_COLOR']};
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 700; 
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
                min-width: 180px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: {theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
            QMenu::icon {{
                padding-left: 5px;
            }}
        """)

        icon_color = theme["ICON_COLOR"]

        # Mute/Unmute action
        if browser.page().recentlyAudible():
            is_muted = browser.page().isAudioMuted()
            mute_action_text = "Unmute Tab" if is_muted else "Mute Tab"
            icon_name = "audio_muted" if is_muted else "audio_playing" # type: ignore
            mute_action = QAction(create_icon_from_svg(SVG_ICONS[icon_name], icon_color, QSize(16, 16)), mute_action_text, self)
            mute_action.triggered.connect(browser.toggle_mute)
            menu.addAction(mute_action)
            menu.addSeparator()

        # Reload
        reload_action = QAction(create_icon_from_svg(SVG_ICONS["reload"], icon_color, QSize(16, 16)), "Reload", self)
        reload_action.triggered.connect(browser.reload)
        menu.addAction(reload_action)

        # Duplicate
        duplicate_action = QAction(create_icon_from_svg(SVG_ICONS["new_tab"], icon_color, QSize(16, 16)), "Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.add_new_tab(browser.url()))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Close
        close_action = QAction(create_icon_from_svg(SVG_ICONS["close"], icon_color, QSize(16, 16)), "Close Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)

        menu.exec(global_pos)

    def show_tab_context_menu(self, index, global_pos):
        browser = self.tab_widget.widget(index)
        # Only show for BrowserTab, not for Settings, Downloads etc.
        if not isinstance(browser, BrowserTab):
            return

        theme = self.theme
        menu = QMenu(self) # type: ignore
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        menu.setStyleSheet(f"""
            QMenu {{ # type: ignore
                background-color: {theme['MENU_BG_COLOR']};
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 700; 
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
                min-width: 180px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: {theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
            QMenu::icon {{
                padding-left: 5px;
            }}
        """)

        icon_color = theme["ICON_COLOR"]

        # Mute/Unmute action
        if browser.page().recentlyAudible():
            is_muted = browser.page().isAudioMuted()
            mute_action_text = "Unmute Tab" if is_muted else "Mute Tab"
            icon_name = "audio_muted" if is_muted else "audio_playing" # type: ignore
            mute_action = QAction(create_icon_from_svg(SVG_ICONS[icon_name], icon_color, QSize(16, 16)), mute_action_text, self)
            mute_action.triggered.connect(browser.toggle_mute)
            menu.addAction(mute_action)
            menu.addSeparator()

        # Reload
        reload_action = QAction(create_icon_from_svg(SVG_ICONS["reload"], icon_color, QSize(16, 16)), "Reload", self)
        reload_action.triggered.connect(browser.reload)
        menu.addAction(reload_action)

        # Duplicate
        duplicate_action = QAction(create_icon_from_svg(SVG_ICONS["new_tab"], icon_color, QSize(16, 16)), "Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.add_new_tab(browser.url()))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Close
        close_action = QAction(create_icon_from_svg(SVG_ICONS["close"], icon_color, QSize(16, 16)), "Close Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)

        menu.exec(global_pos)

    def open_history(self):
        # Check if a history tab is already open and switch to it
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                self.tab_widget.set_current_index(i)
                return

        # If not, create a new tab for history
        html = self.get_history_page_html()
        browser = self.add_new_tab()

        # Setup QWebChannel to allow JS to call Python
        channel = QWebChannel(browser.page())
        history_backend = HistoryPageBackend(self.history_manager)
        history_backend.clearHistoryRequested.connect(self.clear_browsing_data)
        channel.registerObject("backend", history_backend)
        browser.page().setWebChannel(channel)

        # Keep backend and channel alive with the browser tab to prevent garbage collection
        browser.history_backend = history_backend
        browser.channel = channel

        browser.setHtml(html, QUrl("disunic://history"))

    def open_downloads(self):
        """Opens the download manager in a new tab, or switches to it if already open."""
        if self.download_manager_is_in_tab:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.download_manager:
                    self.tab_widget.set_current_index(i)
                    return
        
        # If not in a tab, add it
        icon_color = self.theme["ICON_COLOR"]
        icon = create_icon_from_svg(SVG_ICONS["downloads"], icon_color)
        self.tab_widget.add_tab(self.download_manager, "Downloads", icon)
        self.download_manager_is_in_tab = True


    def open_settings(self, tab_index=0):
        """Opens the settings page in a new tab, or switches to it if already open."""
        if self.settings_page_is_in_tab:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.settings_page:
                    self.tab_widget.set_current_index(i)
                    self.settings_page.nav_list.setCurrentRow(tab_index) # Also switch to the correct inner tab
                    return

        # If not in a tab, add it
        icon_color = self.theme["ICON_COLOR"]
        icon = create_icon_from_svg(SVG_ICONS["settings_general"], icon_color) # type: ignore
        self.tab_widget.add_tab(self.settings_page, "Settings", icon)
        self.settings_page.nav_list.setCurrentRow(tab_index)
        self.settings_page_is_in_tab = True
    
    def clear_browsing_data(self):
        reply = CustomMessageBox.question(
            self,
            "Clear Browsing Data",
            "Are you sure you want to clear all browsing data (history, cookies, cache)? This action cannot be undone.",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            self.history_manager.clear_history()
            self.download_manager.clear_all()

            # Find and update any open history tabs
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://history":
                    if hasattr(widget, 'history_backend'):
                        # Emit the signal to tell the JS to clear its view
                        widget.history_backend.historyCleared.emit()

            # Use a non-modal dialog to avoid blocking the event loop,
            # which would prevent the historyCleared signal from being processed by the web page.
            info_box = QMessageBox(QMessageBox.Icon.Information, "Information", "All browsing data has been cleared.", QMessageBox.StandardButton.Ok, self)
            info_box.setWindowModality(Qt.WindowModality.NonModal)
            info_box.show()
    
    def show_about(self):
        # Check if an about tab is already open
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, BrowserTab) and widget.url().toString() == "disunic://about":
                self.tab_widget.set_current_index(i)
                return

        # If not, create a new tab for it
        html = self.get_about_page_html()
        browser = self.add_new_tab()
        browser.setHtml(html, QUrl("disunic://about"))
    
    def add_new_tab(self, url=None, activate=True):
        # This is a safeguard. Some signals (like from a button click) might pass a
        # boolean `checked` state as the first argument. We must ensure `url` is not a bool.
        if isinstance(url, bool):
            url = None

        # Ensure url is a QUrl object if it's passed as a string
        if isinstance(url, str):
            url = QUrl(url)

        browser = BrowserTab(self.profile, self) # Pass main_window reference
        browser.page_loaded_for_history.connect(self.add_to_history)
        browser.urlChanged.connect(self.update_url_bar)
        browser.urlChanged.connect(self.update_navigation_state)
        browser.urlChanged.connect(self.update_bookmark_button_state)

        browser.audioStateChanged.connect(self.update_tab_audio_indicator)
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

        def on_find_finished(result):
            if self.find_bar.isVisible():
                self.find_bar.update_results(result.activeMatch(), result.numberOfMatches())
        browser.page().findTextFinished.connect(on_find_finished)

        browser.page().linkHovered.connect(lambda url: self.update_status_message(url if url else ("Loading..." if browser.is_loading else "Ready")))

        browser.titleChanged.connect(self.update_tab_title)
        browser.page().iconChanged.connect(lambda icon, b=browser: self.update_tab_icon(b, icon))

        load_new_tab_page = False
        if url is None or url.toString() == "disunic://newtab":
            load_new_tab_page = True

        # Add to stacked widget and tab bar
        index = self.tab_widget.add_tab(browser, "Loading...")

        if not activate:
            self.tab_widget.set_current_index(index) # This seems counterintuitive, but it adds the tab without switching to it if another tab is active

        # Load the content
        if load_new_tab_page:
            html = self.get_new_tab_html()
            browser.setHtml(html, QUrl("disunic://newtab"))
        elif url.toString() == "about:blank":
            browser.setUrl(url)
        else:
            browser.setUrl(url)
        
        return browser

    def add_to_history(self, url, title, icon):
        icon_b64 = qicon_to_base64(icon)
        self.history_manager.add_visit(url, title, icon_b64)

    def on_tab_changed(self, index):
        self.find_bar.hide_and_clear()
        if index > -1:
            widget = self.tab_widget.widget(index)

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
                self.update_bookmark_button_state(widget.url())
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
            self.update_bookmark_button_state(QUrl(""))
            self.update_navigation_state()
    
    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            widget_to_remove = self.tab_widget.remove_tab(index)

            # Special handling for the download manager tab
            if widget_to_remove == self.download_manager:
                self.download_manager_is_in_tab = False
                # IMPORTANT: Do not delete the widget, just hide it.
                # It's parented to the main window, so it won't be garbage collected.
            elif widget_to_remove == self.settings_page:
                self.settings_page_is_in_tab = False
            else:
                widget_to_remove.deleteLater() # Important to free memory
        else:
            self.close()
    
    def update_tab_audio_indicator(self, is_audible, is_muted):
        sender_browser = self.sender()
        if not isinstance(sender_browser, BrowserTab):
            return

        index = self.tab_widget.index_of(sender_browser)
        if index == -1:
            return

        # The tab button is on the tab bar, which is inside the tab_widget
        tab_bar = self.tab_widget.tab_bar
        existing_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide)

        if not is_audible:
            if existing_button:
                tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
                existing_button.deleteLater()
            return

        button = existing_button
        if not button:
            button = QPushButton()
            button.setObjectName("AudioIndicatorBtn")
            button.setFlat(True)
            button.clicked.connect(sender_browser.toggle_mute)
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, button)

        icon_color = self.theme["ICON_COLOR"]
        if is_muted:
            button.setIcon(create_icon_from_svg(SVG_ICONS["audio_muted"], icon_color, QSize(16, 16)))
            button.setToolTip("Unmute Tab")
        else:
            button.setIcon(create_icon_from_svg(SVG_ICONS["audio_playing"], icon_color, QSize(16, 16)))
            button.setToolTip("Mute Tab")

    def show_find_bar(self):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            self.find_bar.show_bar()

    def on_find_next(self, text):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText(text)

    def on_find_previous(self, text):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText(text, QWebEnginePage.FindFlags(QWebEnginePage.FindFlag.FindBackward))

    def on_find_closed(self):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            browser.page().findText("") # Clear find highlights

    def current_browser(self):
        return self.tab_widget.current_widget()

    def update_zoom_label(self):
        browser = self.current_browser()
        if isinstance(browser, BrowserTab):
            zoom_percentage = int(browser.zoomFactor() * 100)
            self.zoom_label.setText(f"{zoom_percentage}%")

    def update_status_bar(self, message):
        self.status.showMessage(message)
    
    def update_status_message(self, message="Ready"):
        # Truncate long hover URLs
        if message.startswith("http") and len(message) > 80:
            message = message[:77] + "..."
        self.status_label.setText(message) 
        # # If the message is not the default "Ready", start a timer to clear it.
        # if message != "Ready":
        #     self.status_clear_timer.start()
        # else:
        #     # If we are setting it to ready, stop any pending clear timers.
        #     self.status_clear_timer.stop()

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
        self.url_bar.setUrl(url, self.SECURE_COLOR, self.DANGER_COLOR)
        # Update Tor status based on the new URL
        self.update_tor_status(url)
        self.update_bookmark_button_state(url)

    def update_bookmark_button_state(self, url):
        if not isinstance(self.current_browser(), BrowserTab):
            self.url_bar.bookmark_button.setVisible(False)
            return

        url_str = url.toString()
        is_special_page = url_str.startswith(("disunic:", "about:", "view-source:")) or not url_str
        
        self.url_bar.bookmark_button.setVisible(not is_special_page)
        if not is_special_page:
            is_bookmarked = self.bookmarks_manager.is_bookmarked(url_str)
            color = self.ACCENT_COLOR if is_bookmarked else self.theme["ICON_COLOR"]
            self.url_bar.set_bookmark_icon(is_bookmarked, color)

    def update_tab_title(self, title):
        # Find the tab that emitted the signal
        sender_browser = self.sender()
        if sender_browser and self.tab_widget:
            index = self.tab_widget.index_of(sender_browser)
            if index != -1:
                self.tab_widget.set_tab_text(index, title)
                self.tab_widget.set_tab_tooltip(index, title)

    def update_tab_icon(self, browser, icon):
        if self.tab_widget: # type: ignore
            index = self.tab_widget.index_of(browser) # type: ignore
            if index != -1:
                self.tab_widget.set_tab_icon(index, icon) # type: ignore