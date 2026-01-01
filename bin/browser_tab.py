# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
import urllib.parse
import html
from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QPoint, QStandardPaths, QSettings
from PyQt6.QtWidgets import (
    QMenu, QDialog, QVBoxLayout, QTextEdit, QFileDialog, QLabel, QPushButton ,QWidget ,QHBoxLayout, QMessageBox, QLineEdit
)
from PyQt6.QtGui import QGuiApplication, QFont, QIcon, QPixmap
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QStandardPaths, QSettings
# Import TorBrowser class for type hinting and creating new windows.
# Use a forward declaration style to avoid circular imports at runtime.
from typing import TYPE_CHECKING
from bin.utils import create_icon_from_svg, SVG_ICONS, DraggableFramelessDialog, CustomMessageBox

class JavaScriptPromptDialog(DraggableFramelessDialog):
    """A custom, modern, frameless dialog for JavaScript's prompt()."""
    def __init__(self, parent, title, message, default_value=""):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.setMinimumWidth(450)

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
        title_label = QLabel(title)
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
        
        text_label = QLabel(message)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(text_label)

        self.input_edit = QLineEdit(default_value)
        content_layout.addWidget(self.input_edit)
        container_layout.addWidget(content_widget)

        # --- Button Footer ---
        button_widget = QWidget()
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(10)
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("AccentButton")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        container_layout.addWidget(button_widget)

        self.content_layout.addWidget(container)
        self.apply_stylesheet()
        
        self.input_edit.setFocus()
        self.input_edit.selectAll()

    def get_text(self):
        return self.input_edit.text()

    def apply_stylesheet(self):
        theme = self.main_window.theme
        accent_color = self.main_window.ACCENT_COLOR
        self.close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))

        self.shadow_container.setStyleSheet(f"""
            #ShadowContainer {{
                background-color: {theme['BG_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
            }}
            #TitleBar {{ border-bottom: 1px solid {theme['BORDER_COLOR']}; }}
            #DialogTitleLabel {{ font-size: 14px; font-weight: 700; color: {theme['TAB_TEXT_COLOR']}; }}
            #DialogCloseBtn {{ background-color: transparent; border: none; border-radius: 4px; padding: 4px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }}
            #DialogCloseBtn:hover {{ background-color: {theme['DANGER_COLOR']}; }}
            QLabel {{ font-size: 14px; color: {theme['TEXT_COLOR']}; }}
            QLineEdit {{ background-color: {theme['URL_BAR_BG']}; color: {theme['TEXT_COLOR']}; border: 1px solid {theme['BORDER_COLOR']}; border-radius: 6px; padding: 8px; }}
            QLineEdit:focus {{ border-color: {accent_color}; }}
            #ButtonWidget {{ background-color: {theme['TOOLBAR_COLOR']}; border-top: 1px solid {theme['BORDER_COLOR']}; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }}
            #ButtonWidget QPushButton {{ background-color: {theme['MSGBOX_BUTTON_BG']}; border: 1px solid {theme['BORDER_COLOR']}; padding: 8px 16px; border-radius: 6px; color: {theme['TEXT_COLOR']}; min-width: 90px; font-weight: 700; }}
            #ButtonWidget QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {accent_color}; }}
            #AccentButton {{ background-color: {accent_color}; border-color: {accent_color}; color: white; }}
            #AccentButton:hover {{ background-color: #5aa1f2; }}
        """)

class CustomWebEnginePage(QWebEnginePage):
    """A custom QWebEnginePage to intercept navigation requests for internal URLs."""
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if is_main_frame and url.scheme() == 'disunic':
            # The parent of this page is the BrowserTab (QWebEngineView) instance.
            view = self.parent()
            if view and hasattr(view, 'main_window'):
                if url.host() == 'settings':
                    view.main_window.open_settings()
                elif url.host() == 'history':
                    view.main_window.open_history()
                elif url.host() == 'downloads':
                    view.main_window.open_downloads()
                elif url.host() == 'check-for-updates':
                    # The force_check parameter is for future use if timed checks are added
                    view.main_window.check_for_updates(force_check=True)
                return False  # Block the navigation

        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def featurePermissionRequested(self, securityOrigin: QUrl, feature: QWebEnginePage.Feature):
        """
        Handles permission requests from web pages for features like camera, microphone, etc.
        It checks the application's settings to decide whether to grant, deny, or prompt the user.
        """
        settings = QSettings("DisunicX", "Browser")
        
        # Map features to their setting keys and user-facing names
        feature_map = {
            QWebEnginePage.Feature.Geolocation: ("ask_location", "Location"),
            QWebEnginePage.Feature.MediaAudioCapture: ("ask_microphone", "Microphone"),
            QWebEnginePage.Feature.MediaVideoCapture: ("ask_camera", "Camera"),
            QWebEnginePage.Feature.MediaAudioVideoCapture: ("ask_camera", "Camera & Microphone"),
            QWebEnginePage.Feature.Notifications: ("ask_notifications", "Notifications"),
            QWebEnginePage.Feature.MouseLock: ("allow_mouse_lock", "Mouse Lock"),
            QWebEnginePage.Feature.DesktopVideoCapture: ("allow_screen_capture", "Screen Capture"),
            QWebEnginePage.Feature.DesktopAudioVideoCapture: ("allow_screen_capture", "Screen & Audio Capture"),
        }

        if feature not in feature_map:
            # For unknown or unhandled features, deny by default for security.
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
            return

        setting_key, feature_name = feature_map[feature]
        
        # Check if the user has a preference set in the settings.
        # The default is True, meaning we should ask the user.
        should_ask = settings.value(setting_key, True, type=bool)

        if not should_ask:
            # If the setting is disabled, deny the permission outright.
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
            return

        # If the setting is enabled, prompt the user.
        title = "Permission Request"
        question = f"The page at <b>{securityOrigin.host()}</b> wants to use your <b>{feature_name}</b>. Do you want to allow this?"
        
        reply = CustomMessageBox.question(self.view(), title, question, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, defaultButton=QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

    def javaScriptAlert(self, securityOrigin: QUrl, msg: str):
        """Overrides the default JavaScript alert() to show a custom, modern dialog."""
        parent_view = self.parent()
        if not parent_view: return
        
        title = f"The page at {securityOrigin.host()} says:"
        CustomMessageBox.information(parent_view, title, msg)

    def javaScriptConfirm(self, securityOrigin: QUrl, msg: str) -> bool:
        """Overrides the default JavaScript confirm() to show a custom, modern dialog."""
        parent_view = self.parent()
        if not parent_view: return False

        title = f"The page at {securityOrigin.host()} asks:"
        reply = CustomMessageBox.question(
            parent_view,
            title,
            msg,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            defaultButton=QMessageBox.StandardButton.Cancel
        )
        return reply == QMessageBox.StandardButton.Ok

    def javaScriptPrompt(self, securityOrigin: QUrl, msg: str, defaultValue: str) -> tuple[bool, str]:
        """Overrides the default JavaScript prompt() to show a custom, modern dialog."""
        parent_view = self.parent()
        if not parent_view: return False, ""

        title = f"The page at {securityOrigin.host()} prompts:"
        dialog = JavaScriptPromptDialog(parent_view, title, msg, defaultValue)
        
        result = dialog.exec()
        
        return result == QDialog.DialogCode.Accepted, dialog.get_text()

if TYPE_CHECKING:
    # This avoids a circular import, but allows type checkers to see the class
    from bin.tor_browser import TorBrowser


class BrowserTab(QWebEngineView):
    page_loaded_for_history = pyqtSignal(str, str, QIcon)
    audioStateChanged = pyqtSignal(bool, bool) # is_audible, is_muted

    def __init__(self, profile, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.main_window = main_window
        self.context_menu_pos = None

        # Enable smooth scrolling
        self.enable_smooth_scrolling()
        
        # Create and set page with the profile
        self.custom_page = CustomWebEnginePage(profile, self)
        self.custom_page.setBackgroundColor(Qt.GlobalColor.transparent)
        self.setPage(self.custom_page)
        
        # Enable various features
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True) # type: ignore
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True) # type: ignore
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True) # type: ignore
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True) # type: ignore
        
        # Enable persistent storage
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True) # type: ignore
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True) # type: ignore
        
        self.page().loadFinished.connect(self.show_custom_error_if_failed)
        
        # For audio state
        self.page().recentlyAudibleChanged.connect(self._on_audible_changed)
        self.page().audioMutedChanged.connect(self._on_mute_changed)

        # For handling link copying
        self.page().linkHovered.connect(self.store_hovered_link)
        self.hovered_link = None

    def store_hovered_link(self, url):
        self.hovered_link = url

    def _on_audible_changed(self, audible):
        self.audioStateChanged.emit(audible, self.page().isAudioMuted())

    def _on_mute_changed(self, muted):
        self.audioStateChanged.emit(self.page().recentlyAudible(), muted)

    def toggle_mute(self):
        self.page().setAudioMuted(not self.page().isAudioMuted())

    def enable_smooth_scrolling(self):
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True) # type: ignore
        
    def wheelEvent(self, event):
        """Handle wheel events for proper scrolling"""
        # Let the web engine handle the event first
        super().wheelEvent(event)
        
        # If the web content didn't handle it, scroll the view
        if not event.isAccepted(): # type: ignore
            self.page().runJavaScript("window.scrollBy(0, {});".format(event.angleDelta().y() / 3))
            event.accept()

    def createWindow(self, window_type):
        # For popups or new tabs from web content (e.g., window.open() or ctrl+click)
        if window_type == QWebEnginePage.WebWindowType.WebBrowserTab:
            return self.main_window.add_new_tab()
        elif window_type == QWebEnginePage.WebWindowType.WebBrowserPopup:
            # For simplicity and security, we open popups as new tabs.
            return self.main_window.add_new_tab()
        return super().createWindow(window_type)

    def contextMenuEvent(self, event):
        self.context_menu_pos = event.pos()
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup) # type: ignore
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        theme = self.main_window.theme
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['MENU_BG_COLOR']}; /* Use a consistent hover color */
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
                padding: 8px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
                font-weight: 700; /* Bold */
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
                min-width: 180px;
                background-color: transparent;
            }}
            QMenu::item:disabled {{
                color: {theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
            QMenu::icon {{
                padding-left: 5px;
            }}
            QMenu::right-arrow {{
                image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["forward"].replace("currentColor", theme['ICON_COLOR']))}');
                width: 16px;
                height: 16px;
                right: 8px;
            }}
        """)
        
        # Navigation actions
        back_action = menu.addAction(create_icon_from_svg(SVG_ICONS["back"], theme['ICON_COLOR']), "Back", self.back)
        back_action.setEnabled(self.history().canGoBack())

        forward_action = menu.addAction(create_icon_from_svg(SVG_ICONS["forward"], theme['ICON_COLOR']), "Forward", self.forward)
        forward_action.setEnabled(self.history().canGoForward())

        menu.addAction(create_icon_from_svg(SVG_ICONS["reload"], theme['ICON_COLOR']), "Reload", self.reload)
        menu.addSeparator()
        
        # Page actions
        save_page_action = menu.addAction(create_icon_from_svg(SVG_ICONS["downloads"], theme['ICON_COLOR']), "Save Page As...", lambda: self.triggerPageAction(QWebEnginePage.WebAction.SavePage)) # type: ignore
        
        url_string = self.url().toString()
        is_special_page = not url_string or url_string.startswith(("disunic:", "view-source:", "about:"))
        
        save_page_action.setEnabled(not is_special_page)
        if not is_special_page:
            menu.addAction(create_icon_from_svg(SVG_ICONS["qr_code"], theme['ICON_COLOR']), "Create QR code for this page", self.create_qr_code_for_page)
        menu.addSeparator()
        
        # Link actions (only if hovering over a link)
        if self.hovered_link:
            link_menu = menu.addMenu("Link")
            link_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            link_menu.addAction(create_icon_from_svg(SVG_ICONS["new_tab"], theme['ICON_COLOR']), "Open Link in New Tab", self.open_link_in_new_tab)
            link_menu.addAction(create_icon_from_svg(SVG_ICONS["new_window"], theme['ICON_COLOR']), "Open Link in New Window", self.open_link_in_new_window)
            link_menu.addAction(create_icon_from_svg(SVG_ICONS["copy_link"], theme['ICON_COLOR']), "Copy Link Address", self.copy_link_address)
            link_menu.addAction(create_icon_from_svg(SVG_ICONS["downloads"], theme['ICON_COLOR']), "Download Link", self.download_link)
            menu.addSeparator()
        
        # Text selection actions
        has_selection = self.page().hasSelection()
        text_actions_menu = menu.addMenu("Text")
        text_actions_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        copy_action = text_actions_menu.addAction("Copy")
        copy_action.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Copy)) # type: ignore
        copy_action.setEnabled(has_selection)

        cut_action = text_actions_menu.addAction("Cut")
        cut_action.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Cut)) # type: ignore
        cut_action.setEnabled(has_selection)

        paste_action = text_actions_menu.addAction("Paste")
        paste_action.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Paste)) # type: ignore

        select_all_action = text_actions_menu.addAction("Select All")
        select_all_action.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.SelectAll)) # type: ignore
        menu.addSeparator()
        
        # Developer tools
        menu.addAction(create_icon_from_svg(SVG_ICONS["view_source"], theme['ICON_COLOR']), "View Page Source", self.view_page_source)
        menu.addAction(create_icon_from_svg(SVG_ICONS["inspect"], theme['ICON_COLOR']), "Inspect Element", self.open_dev_tools)
        menu.addSeparator()
        
        # Add "Copy Page Link" option
        menu.addAction(create_icon_from_svg(SVG_ICONS["copy_link"], theme['ICON_COLOR']), "Copy Page Link", self.copy_page_link)
        
        menu.exec(event.globalPos()) # type: ignore
        self.context_menu_pos = None

    def copy_page_link(self):
        # Copy the current page URL to the clipboard
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.url().toString())

    def _copy_qr_url(self, url_string):
        """Copies the given URL string to the clipboard."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(url_string)
        self.main_window.update_status_message("URL copied to clipboard")

    def _download_qr_code(self, pil_image):
        """Saves the generated QR code PIL image to a file."""
        # Sanitize title for use as a filename
        safe_title = self.title().replace(" ", "_").replace("/", "-").replace("\\", "-")
        default_filename = f"{safe_title}_qr.png"
        
        # Get the default pictures directory
        pictures_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            os.path.join(pictures_dir, default_filename),
            "PNG Images (*.png)"
        )
        if path:
            try:
                pil_image.save(path)
                self.main_window.update_status_message(f"QR Code saved to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save QR code image: {e}")

    def create_qr_code_for_page(self):
        """Generates and displays a QR code for the current page's URL."""
        url_string = self.url().toString()
        if not url_string or url_string.startswith(("disunic:", "view-source:", "about:")):
            CustomMessageBox.information(
                self,
                "Cannot Create QR Code",
                "QR codes cannot be generated for internal or special pages."
            )
            return

        theme = self.main_window.theme
        try:
            import qrcode
            import io

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
            qr.add_data(url_string)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, "PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue(), "PNG")

            # --- Create Frameless Dialog ---
            dialog = DraggableFramelessDialog(self)

            # Container for all our content, which will be placed in the dialog's content_layout
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

            title_label = QLabel("Share this page")
            title_label.setObjectName("TitleLabel")
            
            dialog_close_btn = QPushButton()
            dialog_close_btn.setObjectName("DialogCloseBtn")
            dialog_close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))
            dialog_close_btn.clicked.connect(dialog.reject)

            title_bar_layout.addWidget(title_label)
            title_bar_layout.addStretch()
            title_bar_layout.addWidget(dialog_close_btn)
            container_layout.addWidget(title_bar)

            # --- Content Area ---
            content_area = QWidget()
            content_layout = QVBoxLayout(content_area)
            content_layout.setContentsMargins(20, 10, 20, 20)
            content_layout.setSpacing(15)

            # QR Code in a white card
            qr_card = QWidget()
            qr_card.setObjectName("QRCard")
            qr_card_layout = QVBoxLayout(qr_card)
            qr_label = QLabel()
            qr_label.setPixmap(pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            qr_card_layout.addWidget(qr_label)
            content_layout.addWidget(qr_card)

            # URL display
            url_label = QLabel(url_string)
            url_label.setObjectName("UrlLabel")
            url_label.setWordWrap(True)
            url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(url_label)

            # Buttons
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 15, 0, 0)
            button_layout.setSpacing(10)
            
            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(lambda: self._copy_qr_url(url_string))

            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda: self._download_qr_code(img))
            
            done_btn = QPushButton("Done")
            done_btn.setObjectName("AccentButton")
            done_btn.clicked.connect(dialog.accept)

            button_layout.addStretch()
            button_layout.addWidget(copy_btn)
            button_layout.addWidget(download_btn)
            button_layout.addWidget(done_btn)
            content_layout.addLayout(button_layout)

            content_area.setLayout(content_layout)
            container_layout.addWidget(content_area)

            # Add the container to the dialog's main layout
            dialog.content_layout.addWidget(container)

            dialog.shadow_container.setStyleSheet(f"""
                QDialog {{
                    border: 1px solid {theme['BORDER_COLOR']};
                    border-radius: 12px;
                }}
                #Container {{
                    background-color: {theme['BG_COLOR']};
                    border-radius: 11px;
                }}
                #ShadowContainer {{
                    background-color: {theme['BG_COLOR']};
                    border: 1px solid {theme['BORDER_COLOR']};
                    border-radius: 8px;
                }}
                #TitleBar {{
                    border-bottom: 1px solid {theme['BORDER_COLOR']};
                }}
                #DialogCloseBtn {{
                    background-color: transparent; border: none; border-radius: 4px;
                    padding: 4px; min-width: 28px; max-width: 28px;
                    min-height: 28px; max-height: 28px;
                }}
                #DialogCloseBtn:hover {{
                    background-color: {theme['DANGER_COLOR']};
                }}
                QLabel {{
                    color: {theme['TEXT_COLOR']};
                }}
                #TitleLabel {{
                    font-size: 16px;
                    font-weight: 700;
                }}
                #QRCard {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px; /* Padding around the QR code */
                }}
                #UrlLabel {{
                    background-color: {theme['URL_BAR_BG']};
                    color: {theme['TAB_TEXT_COLOR']};
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-family: "Consolas", "Courier New", monospace;
                    font-size: 13px;
                }}
                QPushButton {{
                    background-color: {theme['MSGBOX_BUTTON_BG']};
                    border: 1px solid {theme['BORDER_COLOR']};
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: 700;
                    color: {theme['TEXT_COLOR']};
                }}
                QPushButton:hover {{
                    background-color: {theme['BUTTON_HOVER_COLOR']};
                    border-color: {self.main_window.ACCENT_COLOR};
                }}
                #AccentButton {{
                    background-color: {self.main_window.ACCENT_COLOR};
                    border-color: {self.main_window.ACCENT_COLOR};
                    color: white;
                }}
                #AccentButton:hover {{
                    background-color: #5aa1f2;
                }}
            """)

            dialog.exec()

        except ImportError:
            CustomMessageBox.critical(
                self,
                "Missing Library Dependency",
                "This feature requires the 'qrcode' library and its 'Pillow' dependency for image creation.\n\n"
                "Please ensure they are installed by running:\n<b>pip install qrcode[pil]</b>"
            )
        except Exception as e:
            CustomMessageBox.critical(self, "Error", f"An error occurred while generating the QR code: {e}")
    
    def open_link_in_new_tab(self):
        if self.hovered_link:
            self.main_window.add_new_tab(self.hovered_link)
    
    def open_link_in_new_window(self):
        if self.hovered_link:
            self.main_window.open_new_window(url=self.hovered_link)
    
    def copy_link_address(self):
        if self.hovered_link:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.hovered_link)
    
    def download_link(self):
        if self.hovered_link:
            # Create a QUrl from the hovered link
            url = QUrl(self.hovered_link)
            
            # Use the page's download method
            self.page().download(url)
    
    def view_page_source(self):
        def handle_source(source):
            # Escape the HTML source to display it as text
            escaped_source = html.escape(source)

            # Create a new HTML document to display the source, wrapping it in <pre>
            # for preserving whitespace and formatting.
            theme = self.main_window.theme
            source_view_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>View Source: {html.escape(self.title())}</title>
                <style>
                    body {{
                        background-color: {theme['BG_COLOR']};
                        color: {theme['TEXT_COLOR']};
                        font-family: "Courier New", monospace; 
                        font-size: 10pt;
                        margin: 0;
                        padding: 10px;
                    }}
                    pre {{ margin: 0; }}
                </style>
            </head>
            <body><pre>{escaped_source}</pre></body>
            </html>
            """
            
            # Create a new tab and load the source view.
            new_tab = self.main_window.add_new_tab()
            original_url = self.url().toString()
            new_tab.setHtml(source_view_html, QUrl(f"view-source:{original_url}"))
        
        self.page().toHtml(handle_source)
    
    def open_dev_tools(self):
        dev_tools_tab = self.main_window.add_new_tab()
        dev_tools_tab.setUrl(QUrl("about:blank"))
        self.page().setDevToolsPage(dev_tools_tab.page())
        self.page().triggerAction(QWebEnginePage.WebAction.InspectElement) # type: ignore
    
    def show_custom_error_if_failed(self, ok):
        if ok:
            self.page_loaded_for_history.emit(self.url().toString(), self.title(), self.page().icon())
        # If 'ok' is False, do nothing. The QWebEngineView will show its default error page.