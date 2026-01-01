# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import json
from packaging import version  # A robust way to compare versions
from PyQt6.QtCore import QObject, QUrl, pyqtSignal, Qt, QSettings, QDateTime, QPoint
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import os
import re
from bin.utils import create_icon_from_svg, SVG_ICONS, DraggableFramelessDialog

# IMPORTANT: Replace with your actual GitHub repository details
GITHUB_REPO = "SouvikNandi1/disunicx2021"
# This should be the name of the installer asset you upload to GitHub releases
INSTALLER_ASSET_NAME = "DisunicX-setup.exe"

class UpdateDialog(DraggableFramelessDialog):
    """A custom, styled dialog for prompting the user to update."""
    def __init__(self, version_str, notes_html, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setMinimumWidth(500)

        # Container for all content, to handle border-radius and background
        container = QWidget()
        container.setObjectName("Container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Title Bar ---
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(50)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 0, 10, 0)

        title_label = QLabel("Update Available")
        title_label.setObjectName("DialogTitleLabel")

        self.close_btn = QPushButton()
        self.close_btn.setObjectName("DialogCloseBtn")
        self.close_btn.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_btn)
        container_layout.addWidget(title_bar)

        # --- Content Area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(15)

        content_title_label = QLabel(f"A new version ({version_str}) is available!")
        content_title_label.setObjectName("ContentTitleLabel")
        content_layout.addWidget(content_title_label)

        info_label = QLabel("Your personal data (history, bookmarks, etc.) will not be affected by this update.")
        info_label.setObjectName("InfoLabel")
        info_label.setWordWrap(True)
        info_label.setContentsMargins(0, 5, 0, 5)
        content_layout.addWidget(info_label)

        notes_header = QLabel("<b>What's new:</b>")
        content_layout.addWidget(notes_header)

        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setObjectName("NotesScrollArea")
        notes_scroll.setFixedHeight(200)

        notes_content = QLabel(notes_html)
        notes_content.setWordWrap(True)
        notes_content.setAlignment(Qt.AlignTop)
        notes_content.setContentsMargins(10, 10, 10, 10)
        notes_scroll.setWidget(notes_content)
        content_layout.addWidget(notes_scroll)
        container_layout.addWidget(content_widget)

        # --- Buttons Footer ---
        button_widget = QWidget()
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.addStretch()

        self.later_btn = QPushButton("Later")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)

        self.download_btn = QPushButton("Download & Install")
        self.download_btn.setObjectName("AccentButton")
        self.download_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.download_btn)
        container_layout.addWidget(button_widget)
        
        self.content_layout.addWidget(container)
        self.apply_stylesheet()

    def apply_stylesheet(self):
        theme = self.main_window.theme
        self.close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))

        self.setStyleSheet(f"""
            QDialog {{ border: 1px solid {theme['BORDER_COLOR']}; border-radius: 12px; }}
            #Container {{ background-color: {theme['BG_COLOR']}; border-radius: 11px; }}
            
            #TitleBar {{ border-bottom: 1px solid {theme['BORDER_COLOR']}; }}
            #DialogTitleLabel {{ font-size: 16px; font-weight: 700; }}
            #DialogCloseBtn {{
                background-color: transparent; border: none; border-radius: 4px;
                padding: 4px; min-width: 28px; max-width: 28px;
                min-height: 28px; max-height: 28px;
            }}
            #DialogCloseBtn:hover {{
                background-color: {theme['DANGER_COLOR']};
            }}

            QLabel {{ color: {theme['TEXT_COLOR']}; }}
            #ContentTitleLabel {{ font-size: 18px; font-weight: 700; }}
            
            #InfoLabel {{
                color: {theme['TAB_TEXT_COLOR']};
                font-size: 13px;
                padding: 10px;
                background-color: {theme['URL_BAR_BG']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 6px;
                font-weight: 700;
            }}

            #ButtonWidget {{ 
                background-color: {theme['TOOLBAR_COLOR']}; 
                border-top: 1px solid {theme['BORDER_COLOR']}; 
                border-bottom-left-radius: 11px; 
                border-bottom-right-radius: 11px; 
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
            QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {self.main_window.ACCENT_COLOR}; }}
            #AccentButton {{ background-color: {self.main_window.ACCENT_COLOR}; border-color: {self.main_window.ACCENT_COLOR}; color: white; }}
            #AccentButton:hover {{ background-color: #5aa1f2; }}
            
            #NotesScrollArea {{ 
                background-color: {theme['URL_BAR_BG']}; 
                border: 1px solid {theme['BORDER_COLOR']}; 
                border-radius: 6px; 
            }}
            #NotesScrollArea QLabel {{ color: {theme['TEXT_COLOR']}; background-color: transparent; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 10px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {theme['BORDER_COLOR']}; min-height: 20px; border-radius: 5px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)


class Updater(QObject):
    def __init__(self, current_version, parent=None, repo_or_url=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_version = current_version
        self.network_manager = QNetworkAccessManager(self)
        self.repo_or_url = repo_or_url or GITHUB_REPO
        self.network_manager.finished.connect(self.on_check_finished)
        self.settings = QSettings()

    def _format_release_notes(self, text):
        """Converts basic GitHub markdown to simple HTML for the dialog."""
        processed_lines = []
        for line in text.splitlines():
            # Headings (e.g., #, ##, ###) -> bold
            line = re.sub(r'^\s*#+\s*(.*)', r'<b>\1</b>', line)
            
            # Bold (e.g., **text**) -> <b>text</b>
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            
            # List items (e.g., * item or - item) -> • item
            line = re.sub(r'^\s*[\*\-]\s*(.*)', r'• \1', line)
            
            processed_lines.append(line)
        return '<br>'.join(processed_lines)

    def check_for_updates(self, force_check=False):
        """
        Fetches the latest release information from GitHub.
        """
        print("Checking for updates...")
        
        # Determine if it's a GitHub repo slug or a full URL
        if '/' in self.repo_or_url and not self.repo_or_url.startswith('http'):
            # Assumes GitHub repo slug like "user/repo"
            api_url = f"https://api.github.com/repos/{self.repo_or_url}/releases/latest"
        else:
            # Assumes a direct URL to a JSON file
            api_url = self.repo_or_url

        request = QNetworkRequest(QUrl(api_url))
        # GitHub API prefers a User-Agent header
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "DisunicX-Updater")
        self.network_manager.get(request)

    def on_check_finished(self, reply: QNetworkReply):
        """Handles the response from the GitHub API."""
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)

        if reply.error() != QNetworkReply.NetworkError.NoError:
            print(f"Update check failed: {reply.errorString()}")
            if status_code:
                print(f"HTTP Status Code: {status_code}")
            error_body = bytes(reply.readAll()).decode('utf-8', 'ignore')
            if error_body:
                print(f"Server response: {error_body}")
            reply.deleteLater()
            return

        try:
            data = json.loads(bytes(reply.readAll()))
            latest_version_str = data.get("tag_name", "0.0.0").lstrip('v')

            if version.parse(latest_version_str) > version.parse(self.current_version):
                release_notes = data.get("body", "No release notes available.")
                download_url = self._find_asset_url(data.get("assets", []))
                if download_url:
                    formatted_notes = self._format_release_notes(release_notes)
                    self._prompt_user_to_update(latest_version_str, formatted_notes, download_url)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing update data: {e}")

        reply.deleteLater()

    def _find_asset_url(self, assets):
        """Finds the download URL for the specific installer asset."""
        for asset in assets:
            if asset.get("name") == INSTALLER_ASSET_NAME:
                return asset.get("browser_download_url")
        print(f"Could not find asset '{INSTALLER_ASSET_NAME}' in release.")
        return None

    def _prompt_user_to_update(self, version_str, notes_html, url):
        """Shows a custom, styled dialog asking the user if they want to update."""
        dialog = UpdateDialog(version_str, notes_html, self.parent_window)
        # exec() returns 1 if accepted (Download Now), 0 if rejected (Later)
        if dialog.exec():
            self._download_update(url)

    def _download_update(self, url):
        """Starts the download within the browser's own download manager."""
        if self.parent_window and hasattr(self.parent_window, 'add_new_tab'):
            # By opening the URL in a new tab, the browser's download-handling
            # mechanism will be triggered automatically, showing the download
            # in the browser's "Downloads" tab.
            self.parent_window.add_new_tab(url=QUrl(url))
        else:
            # Fallback to opening in the default external browser if something is wrong
            QDesktopServices.openUrl(QUrl(url))