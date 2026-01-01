# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

from PyQt6.QtCore import QUrl, QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QStyle, QMenu, QSizePolicy
from PyQt6.QtGui import QAction, QPainter, QColor, QBrush, QPen
from bin.utils import create_icon_from_svg, SVG_ICONS

class UrlBar(QWidget):
    """A custom URL bar widget with integrated security and bookmark icons."""
    bookmarkButtonClicked = pyqtSignal()

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.main_window = parent
        self.full_url = QUrl()  # Store the full URL
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(4, 0, 4, 0)
        self.layout.setSpacing(4)

        self.security_icon = QPushButton()
        self.security_icon.setObjectName("UrlBarButton")
        self.security_icon.setFlat(True)
        
        self.url_edit = QLineEdit()
        self.url_edit.setObjectName("UrlEdit")
        self.url_edit.setPlaceholderText("Search or enter URL")
        self.url_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.url_edit.customContextMenuRequested.connect(self.show_context_menu)

        self.bookmark_button = QPushButton()
        self.bookmark_button.setObjectName("UrlBarButton")
        self.bookmark_button.setFlat(True)
        self.bookmark_button.setCheckable(True)
        self.bookmark_button.clicked.connect(self.bookmarkButtonClicked)
        
        self.layout.addWidget(self.security_icon)
        self.layout.addWidget(self.url_edit)
        self.layout.addWidget(self.bookmark_button)
        
        self.setProperty("hasFocus", False)
        self.url_edit.installEventFilter(self)
        self.setLayout(self.layout)

    def show_context_menu(self, pos):
        """Shows a custom, styled context menu for the URL edit line."""
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.theme['MENU_BG_COLOR']}; /* Use a consistent hover color */
                color: {self.theme['TEXT_COLOR']};
                border: 1px solid {self.theme['BORDER_COLOR']};
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
                min-width: 150px;
            }}
            QMenu::item:selected {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: {self.theme['DISABLED_TEXT_COLOR']};
                background-color: transparent;
            }}
            QMenu::separator {{
                height: 1px;
                background: {self.theme['MENU_SEPARATOR_COLOR']};
                margin: 8px 4px;
            }}
        """)

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self.url_edit.cut)
        cut_action.setEnabled(self.url_edit.hasSelectedText())
        menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.url_edit.copy)
        copy_action.setEnabled(self.url_edit.hasSelectedText())
        menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.url_edit.paste)
        menu.addAction(paste_action)

        menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.url_edit.selectAll)
        menu.addAction(select_all_action)

        menu.exec(self.url_edit.mapToGlobal(pos))

    def _update_display(self):
        """Centralized method to update the URL bar's text based on focus."""
        # Special handling for the new tab page to always keep the bar empty for typing.
        if self.full_url.toString() == "disunic://newtab":
            self.url_edit.clear()
            return

        # This logic is now smarter to avoid overwriting user input.
        if self.url_edit.hasFocus():
            # Only expand to the full URL if the "pretty" URL is currently displayed.
            # This prevents overwriting text the user has started typing.
            if self.url_edit.text() == self.format_url_for_display():
                self.url_edit.setText(self.full_url.toString())
        else:
            self.url_edit.setText(self.format_url_for_display())

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.url_edit:
            if event.type() == QEvent.Type.FocusIn:
                self.setProperty("hasFocus", True)
                self.style().unpolish(self); self.style().polish(self)
                # If focus is returning from a popup (like the context menu),
                # don't run the display update logic, which might clear user input.
                if event.reason() != Qt.FocusReason.PopupFocusReason:
                    self._update_display()
                    self.url_edit.selectAll()
            elif event.type() == QEvent.Type.FocusOut:
                # If focus is lost because a popup (like our context menu) is shown,
                # we don't want to change the text. This preserves user input.
                if event.reason() != Qt.FocusReason.PopupFocusReason:
                    self.setProperty("hasFocus", False)
                    self.style().unpolish(self); self.style().polish(self)
                    self._update_display()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        """
        Custom paint event to draw a perfectly rounded pill shape.
        This gives us more control than stylesheets alone for complex shapes.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine colors based on theme and focus state
        bg_color = QColor(self.theme["URL_BAR_BG"])
        border_color = QColor(self.theme["URL_BAR_BORDER"])
        if self.property("hasFocus"):
            border_color = QColor(self.main_window.ACCENT_COLOR)

        # Draw the rounded rectangle (pill shape)
        rect = self.rect().adjusted(1, 1, -1, -1) # Adjust for the border
        radius = rect.height() / 2.0
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.5)) # Use a slightly thicker pen for a crisper look
        painter.drawRoundedRect(rect, radius, radius)

    def setUrl(self, url: QUrl, secure_color="#2ecc71", insecure_color="#e74c3c"):
        """Sets the URL for the bar, updating the text and icon."""
        self.full_url = url
        self._update_display()
        self.set_security_icon(url.scheme() in ['https', 'disunic'], secure_color, insecure_color)

    def format_url_for_display(self) -> str:
        """Creates a simplified 'pretty' version of the URL for display."""
        if self.full_url.scheme() == "disunic":
            host = self.full_url.host()
            if host == "newtab":
                return ""  # Keep placeholder text for new tab
            else:
                # Show a clean name for internal pages like "Settings", "History", etc.
                return host.capitalize()
        if self.full_url.scheme() in ['http', 'https', 'view-source']:
            # In PyQt6, the formatting flags are passed directly to toString().
            options = QUrl.UrlFormattingOption.RemoveScheme | QUrl.UrlFormattingOption.StripTrailingSlash

            display_text = self.full_url.toString(options).lstrip('/').lstrip('view-source:')

            if display_text.lower().startswith('www.'):
                display_text = display_text[4:]
            return display_text
        return self.full_url.toDisplayString()

    def set_security_icon(self, is_secure, secure_color, insecure_color):
        if is_secure:
            self.security_icon.setIcon(create_icon_from_svg(SVG_ICONS["lock"], secure_color))
            self.security_icon.setToolTip("Secure Connection")
        else:
            self.security_icon.setIcon(create_icon_from_svg(SVG_ICONS["info"], insecure_color))
            self.security_icon.setToolTip("Connection is not secure")

    def set_bookmark_icon(self, is_bookmarked, color):
        icon_name = "bookmark_filled" if is_bookmarked else "bookmark_outline"
        self.bookmark_button.setIcon(create_icon_from_svg(SVG_ICONS[icon_name], color))
        self.bookmark_button.setChecked(is_bookmarked)
        self.bookmark_button.setToolTip("Remove from bookmarks" if is_bookmarked else "Add to bookmarks")

    def set_ambient_color(self, text_color):
        """Updates the text color of the URL bar for ambient mode."""
        self.url_edit.setStyleSheet(f"color: {text_color};")