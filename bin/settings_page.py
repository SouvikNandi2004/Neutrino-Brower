# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
import json, sys
from PyQt6.QtWidgets import ( # type: ignore
    QVBoxLayout, QWidget, QFormLayout, QFrame,
    QComboBox, QLineEdit, QPushButton, QHBoxLayout, QLabel, QSpinBox, QGridLayout,
    QMessageBox, QFileDialog, QScrollArea, QApplication, QListWidget, QStackedWidget, QListWidgetItem,
    QAbstractButton, QColorDialog, QDialog, QGroupBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import ( # type: ignore
    QSettings, Qt, QStandardPaths, QSize, QPoint, QPointF, QPropertyAnimation, pyqtProperty, QEasingCurve, pyqtSignal ,QTimer, QProcess
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QIcon
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from bin.utils import get_profile_path, SVG_ICONS, create_icon_from_svg, DraggableFramelessDialog, CustomMessageBox

# A mapping for user-friendly names in the theme editor
THEME_KEY_NAMES = {
    "BG_COLOR": "Page Background", "TEXT_COLOR": "Primary Text", "TOOLBAR_COLOR": "Toolbar Background",
    "URL_BAR_BG": "URL & Search Bar", "BORDER_COLOR": "Borders & Separators", "TAB_ACTIVE_COLOR": "Active Tab Background",
    "TAB_HOVER_COLOR": "Tab Hover", "TAB_TEXT_COLOR": "Inactive Tab Text",
    "TAB_TEXT_SELECTED_COLOR": "Active Tab Text", "ICON_COLOR": "Icons",
    "STATUS_BAR_TEXT_COLOR": "Status Bar Text", "BUTTON_HOVER_COLOR": "Button Hover",
    "BUTTON_PRESSED_COLOR": "Button Pressed", "MENU_BG_COLOR": "Menu Background",
    "MENU_SEPARATOR_COLOR": "Menu Separator", "DISABLED_TEXT_COLOR": "Disabled Text",
    "MSGBOX_BUTTON_BG": "Message Box Button", "DANGER_COLOR": "Danger/Error Color",
    "SECURE_COLOR": "Success/Secure Color", "URL_BAR_COLOR": "URL Bar (Legacy)",
    "URL_BAR_BORDER": "URL Bar Border",
}

class ToggleSwitch(QAbstractButton):
    """A custom animated toggle switch widget."""
    # Define a new signal that mimics QCheckBox's stateChanged for easier replacement
    stateChanged = pyqtSignal(int)

    def __init__(self, parent=None, track_color_off="#777", track_color_on="#4a90e2", handle_color="#fff", border_color="#888"):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setFixedSize(50, 28)
 
        self._track_color_off = QColor(track_color_off)
        self._border_color = QColor(border_color)
        self._track_color_on = QColor(track_color_on)
        self._handle_color = QColor(handle_color)
        self._handle_padding = 3
        
        self._handle_position = self._handle_padding if not self.isChecked() else self.width() - self.height() + self._handle_padding
        self.animation = QPropertyAnimation(self, b"handle_position", self) # type: ignore
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # The base `toggled` signal drives the animation
        self.toggled.connect(self.on_state_changed)
        # We also connect `toggled` to a new slot that emits our Qt.CheckState signal
        self.toggled.connect(self._emit_state_changed)

    def _emit_state_changed(self, checked):
        """A private slot to convert toggled(bool) to stateChanged(int)."""
        state = Qt.CheckState.Checked.value if checked else Qt.CheckState.Unchecked.value
        self.stateChanged.emit(state)
        
    def sizeHint(self):
        return self.size()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_radius = self.height() / 2.0

        # Paint track
        track_color = self._track_color_off
        if self.isChecked():
            track_color = self._track_color_on

        # Draw border first
        painter.setPen(QPen(self._border_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect(), track_radius, track_radius)

        # Then draw the inner track fill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), track_radius - 1, track_radius - 1)

        # Finally, paint the handle on top
        handle_radius = (self.height() / 2.0) - self._handle_padding
        
        painter.setBrush(self._handle_color)
        painter.drawEllipse(QPointF(self._handle_position + handle_radius, self._handle_padding + handle_radius), handle_radius, handle_radius)

    def on_state_changed(self, checked):
        self.animation.stop()
        if checked:
            self.animation.setEndValue(self.width() - self.height() + self._handle_padding)
        else:
            self.animation.setEndValue(self._handle_padding)
        self.animation.start()

    @pyqtProperty(int)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()

class ThemeEditorDialog(DraggableFramelessDialog):
    """A dialog for creating and editing browser themes."""
    def __init__(self, theme_data, theme_name, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 700)

        # Get reference to main window
        self.main_window = parent.main_window

        self.theme_data = theme_data.copy()
        self.original_theme_name = theme_name.lower()
        self.color_buttons = {}

        # --- New Frameless Structure ---
        container = QWidget(self)
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

        title_label = QLabel("Theme Editor")
        title_label.setObjectName("DialogTitleLabel")

        self.close_btn = QPushButton()
        self.close_btn.setObjectName("DialogCloseBtn")
        self.close_btn.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_btn)
        container_layout.addWidget(title_bar)

        # --- Content Area ---
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)

        # Original content moved into the new structure
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("<b>Theme Name:</b>"))
        self.name_edit = QLineEdit(theme_name)
        self.name_edit.setPlaceholderText("Enter a name for your theme")
        name_layout.addWidget(self.name_edit)
        content_layout.addLayout(name_layout)

        self.preview_widget = QGroupBox("Preview")
        preview_layout = QHBoxLayout(self.preview_widget)
        self.preview_label = QLabel("This is some sample text.")
        self.preview_button = QPushButton("Sample Button")
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_button)
        content_layout.addWidget(self.preview_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.pickers_layout = QFormLayout(scroll_widget)
        self.pickers_layout.setSpacing(10)
        self.pickers_layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(scroll_widget)
        content_layout.addWidget(scroll_area)

        container_layout.addWidget(content_widget)

        # --- Buttons Footer ---
        button_widget = QWidget(self)
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("AccentButton")
        self.save_btn.clicked.connect(self.save_theme)
        button_layout.addWidget(self.save_btn)

        container_layout.addWidget(button_widget)
        self.content_layout.addWidget(container)

        # Populate pickers and apply styles
        self.populate_pickers()
        self.update_preview()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        theme = self.main_window.theme
        self.close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))

        self.setStyleSheet(f"""
            QDialog {{ border: 1px solid {theme['BORDER_COLOR']}; border-radius: 12px; }}
            #Container {{ background-color: {theme['BG_COLOR']}; border-radius: 11px; }}
            
            #TitleBar {{ border-bottom: 1px solid {theme['BORDER_COLOR']}; }}
            #DialogTitleLabel {{ font-size: 16px; font-weight: 700; color: {theme['TEXT_COLOR']}; }}
            #DialogCloseBtn {{
                background-color: transparent; border: none; border-radius: 4px;
                padding: 4px; min-width: 28px; max-width: 28px;
                min-height: 28px; max-height: 28px;
            }}
            #DialogCloseBtn:hover {{ background-color: {theme['DANGER_COLOR']}; }}

            /* Content styles */
            QLabel {{
                color: {theme['TEXT_COLOR']};
                background-color: transparent;
            }}
            QLineEdit {{
                background-color: {theme['URL_BAR_BG']};
                color: {theme['TEXT_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 6px;
                padding: 8px;
            }}
            QLineEdit:focus {{ border-color: {self.main_window.ACCENT_COLOR}; }}
            QScrollArea {{
                background: {theme['TOOLBAR_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 6px;
            }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QGroupBox {{ font-weight: 700; }}

            /* Footer styles */
            #ButtonWidget {{ 
                background-color: {theme['TOOLBAR_COLOR']}; 
                border-top: 1px solid {theme['BORDER_COLOR']}; 
                border-bottom-left-radius: 11px; 
                border-bottom-right-radius: 11px; 
            }}
            #ButtonWidget QPushButton {{ 
                background-color: {theme['MSGBOX_BUTTON_BG']}; 
                border: 1px solid {theme['BORDER_COLOR']}; 
                padding: 8px 16px; 
                border-radius: 6px; 
                color: {theme['TEXT_COLOR']}; 
                min-width: 90px; 
                font-weight: 700; 
            }}
            #ButtonWidget QPushButton:hover {{ 
                background-color: {theme['BUTTON_HOVER_COLOR']}; 
                border-color: {self.main_window.ACCENT_COLOR}; 
            }}
            #AccentButton {{ 
                background-color: {self.main_window.ACCENT_COLOR}; 
                border-color: {self.main_window.ACCENT_COLOR}; 
                color: white; 
            }}
            #AccentButton:hover {{ background-color: #5aa1f2; }}
        """)

    def populate_pickers(self):
        """Create a color picker row for each color in the theme data."""
        for key in sorted(self.theme_data.keys()):
            color_str = self.theme_data[key]
            label_text = THEME_KEY_NAMES.get(key, key)
            
            button = QPushButton()
            button.setFixedSize(120, 28)
            button.setToolTip(f"Click to change {label_text}")
            # Use a lambda with a default argument to capture the current key
            button.clicked.connect(lambda checked=False, k=key: self.open_color_picker(k))
            
            self.color_buttons[key] = button
            self.update_button_color(key, color_str)
            self.pickers_layout.addRow(label_text, button)

    def open_color_picker(self, key):
        """Open a QColorDialog to select a new color."""
        current_color_str = self.theme_data[key]
        initial_color = QColor(current_color_str)

        options = QColorDialog.ColorDialogOption()
        if 'rgba' in current_color_str or initial_color.alpha() < 255:
            options |= QColorDialog.ColorDialogOption.ShowAlphaChannel

        color = QColorDialog.getColor(initial_color, self, f"Select {THEME_KEY_NAMES.get(key, key)}", options)

        if color.isValid():
            # If the original was rgba or the new color has alpha, save as rgba
            if 'rgba' in current_color_str or color.alpha() < 255:
                color_str = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alphaF():.2f})"
            else:
                color_str = color.name()  # #rrggbb
            
            self.theme_data[key] = color_str
            self.update_button_color(key, color_str)
            self.update_preview()

    def update_button_color(self, key, color_str):
        """Update the background color of a picker button."""
        theme = self.main_window.theme
        self.color_buttons[key].setStyleSheet(f"background-color: {color_str}; border: 1px solid {theme['BORDER_COLOR']};")

    def update_preview(self):
        """Update the preview widget with the current theme colors."""
        bg = self.theme_data.get("BG_COLOR", "#fff")
        text = self.theme_data.get("TEXT_COLOR", "#000")
        btn_bg = self.theme_data.get("MSGBOX_BUTTON_BG", "#eee")
        btn_hover = self.theme_data.get("BUTTON_HOVER_COLOR", "#ddd")
        border = self.theme_data.get("BORDER_COLOR", "#ccc")
        
        self.preview_widget.setStyleSheet(f"""
            QGroupBox {{
                background-color: {bg};
                border: 1px solid {border};
                color: {text};
                margin-top: 10px;
                border-radius: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }}
            QLabel {{ color: {text}; background-color: transparent; }}
            QPushButton {{
                color: {text};
                background-color: {btn_bg};
                border: 1px solid {border};
                padding: 5px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)

    def save_theme(self):
        """Validate and save the new theme to themes.json."""
        theme_name = self.name_edit.text().strip()
        if not theme_name:
            CustomMessageBox.warning(self, "Invalid Name", "Theme name cannot be empty.")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        themes_path = os.path.join(script_dir, 'themes.json')

        try:
            all_themes = {}
            if os.path.exists(themes_path):
                with open(themes_path, 'r', encoding='utf-8') as f:
                    all_themes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            CustomMessageBox.critical(self, "Error", f"Could not load themes.json: {e}")
            return

        if theme_name.lower() in all_themes and theme_name.lower() != self.original_theme_name:
            reply = CustomMessageBox.question(
                self, "Overwrite Theme",
                f"A theme named '{theme_name}' already exists. Do you want to overwrite it?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        all_themes[theme_name.lower()] = self.theme_data

        try:
            with open(themes_path, 'w', encoding='utf-8') as f:
                json.dump(all_themes, f, indent=4)
            self.accept()
        except Exception as e:
            CustomMessageBox.critical(self, "Error", f"Failed to save themes.json: {e}")

class RestartDialog(DraggableFramelessDialog):
    """A custom frameless dialog to prompt for a restart."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.setMinimumWidth(450)

        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Title Bar ---
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(50)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 0, 10, 0)
        title_label = QLabel("Restart Required")
        title_label.setObjectName("DialogTitleLabel")
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("DialogCloseBtn")
        self.close_btn.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_btn)
        container_layout.addWidget(title_bar)

        # --- Content Area ---
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(15)
        
        text_label = QLabel("Some changes (like theme or proxy settings) require a restart to take full effect.")
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(text_label)
        container_layout.addWidget(content_widget)

        # --- Button Footer ---
        button_widget = QWidget(self)
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(10)
        button_layout.addStretch()

        self.later_btn = QPushButton("Later")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)

        self.restart_btn = QPushButton("Restart Now")
        self.restart_btn.setObjectName("AccentButton")
        self.restart_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.restart_btn)
        container_layout.addWidget(button_widget)

        self.content_layout.addWidget(container)
        self.apply_stylesheet()

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
            #DialogTitleLabel {{ font-size: 16px; font-weight: 700; color: {theme['TEXT_COLOR']}; }}
            #DialogCloseBtn {{ background-color: transparent; border: none; border-radius: 4px; padding: 4px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }}
            #DialogCloseBtn:hover {{ background-color: {theme['DANGER_COLOR']}; }}
            QLabel {{ font-size: 14px; color: {theme['TEXT_COLOR']}; font-weight: 700; }}
            #ButtonWidget {{ background-color: {theme['TOOLBAR_COLOR']}; border-top: 1px solid {theme['BORDER_COLOR']}; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }}
            #ButtonWidget QPushButton {{ background-color: {theme['MSGBOX_BUTTON_BG']}; border: 1px solid {theme['BORDER_COLOR']}; padding: 8px 16px; border-radius: 6px; color: {theme['TEXT_COLOR']}; min-width: 90px; font-weight: 700; }}
            #ButtonWidget QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {accent_color}; }}
            #AccentButton {{ background-color: {accent_color}; border-color: {accent_color}; color: white; }}
            #AccentButton:hover {{ background-color: #5aa1f2; }}
        """)

class CountdownDialog(DraggableFramelessDialog):
    """A dialog that shows a countdown and then closes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.setMinimumWidth(400)
        self.setWindowTitle("Restarting")
        
        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(15)

        self.title_label = QLabel("Factory Reset Complete")
        self.title_label.setObjectName("DialogTitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.countdown_label = QLabel("The browser will restart in 3 seconds...")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.countdown_label)
        
        self.content_layout.addWidget(container)
        
        self.countdown = 3
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)
        
        self.apply_stylesheet()

    def apply_stylesheet(self):
        if not self.main_window: return
        theme = self.main_window.theme
        self.shadow_container.setStyleSheet(f"""
            #ShadowContainer {{
                background-color: {theme['BG_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
            }}
            #DialogTitleLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
            }}
            QLabel {{
                font-size: 14px;
                color: {theme['TAB_TEXT_COLOR']};
                font-weight: 700;
            }}
        """)

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.countdown_label.setText(f"The browser will restart in {self.countdown} seconds...")
        else:
            self.timer.stop()
            self.accept()

    def exec(self):
        self.timer.start()
        return super().exec()

class SettingsPage(QWidget):
    def __init__(self, profile, main_window, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.main_window = main_window # Store reference to main window
        self.settings = QSettings("DisunicX", "Browser")
        self.setObjectName("SettingsPage")
        # Store icon names for dynamic coloring
        self.tab_icon_names = [
            'settings_general',
            'settings_privacy',
            'settings_advanced'
        ]
        self.previous_row = 0
        self.current_page_index = 0
        self.init_ui()
        self.load_settings()
        self.connect_signals()

    def init_ui(self):
        theme = self.main_window.theme
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Main Content Area (Sidebar + Pages) ---
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("SidebarWidget")
        sidebar_widget.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar_widget) # type: ignore
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_title = QLabel("Settings")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(sidebar_title)

        # Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(20, 20))
        sidebar_layout.addWidget(self.nav_list)

        # Pages Stack
        self.pages_stack = QStackedWidget()
        self.pages_stack.setObjectName("PagesStack")

        content_layout.addWidget(sidebar_widget)
        content_layout.addWidget(self.pages_stack, 1)
        main_layout.addWidget(content_area, 1)

        # Create and add pages
        self.pages_stack.addWidget(self.create_general_page())
        self.pages_stack.addWidget(self.create_privacy_page())
        self.pages_stack.addWidget(self.create_advanced_page())

        # Create and add nav items # type: ignore
        self.nav_list.addItem(self.create_nav_item("General", "settings_general"))
        self.nav_list.addItem(self.create_nav_item("Privacy & Security", "settings_privacy"))
        self.nav_list.addItem(self.create_nav_item("Advanced", "settings_advanced"))

        self.nav_list.currentRowChanged.connect(self.slide_to_page)
        self.nav_list.currentRowChanged.connect(self.update_nav_list_icons)
        self.nav_list.setCurrentRow(0)
        self.previous_row = 0 # Initialize before first call
        self.update_nav_list_icons(0) # Set initial selected icon color
        
        # --- Main Dialog Stylesheet ---
        self.setStyleSheet(f"""
            #SettingsPage {{
                background-color: {theme['TOOLBAR_COLOR']};
                color: {theme['TEXT_COLOR']};
            }}
            #SidebarWidget {{
                background-color: {theme['TOOLBAR_COLOR']};
                border-right: 1px solid {theme['BORDER_COLOR']};
            }}
            #SidebarTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
                padding: 25px 20px 15px 20px;
            }}
            #NavList {{
                background-color: transparent;
                border: none;
                outline: 0; /* Remove focus border */
            }}
            #NavList::item {{
                padding: 12px 20px;
                margin: 4px 10px; /* Vertical and horizontal margin */
                border-radius: 8px; /* Rounded corners for all items */
                color: {theme['TAB_TEXT_COLOR']};
                font-weight: 700;
            }}
            #NavList::item:hover {{
                background-color: {theme['TAB_HOVER_COLOR']};
                color: {theme['TEXT_COLOR']};
                margin: 4px 10px; /* Ensure margin is consistent on hover */
            }}
            #NavList::item:selected {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff; /* White text on accent background */
                font-weight: 700;
                margin: 4px 10px;
            }}
            #NavList::item:selected:!active {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff;
            }}
            QLabel#PageTitle {{
                font-size: 32px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
                margin-bottom: 25px;
            }}
            QLabel#SectionTitle {{
                font-size: 16px;
                font-weight: 700;
                color: {theme['TAB_TEXT_COLOR']};
                margin-top: 35px;
                margin-bottom: 15px;
            }}
            #SettingRow {{ padding: 18px 0; }}
            QLabel#SettingTitle {{
                font-size: 14px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
            }}
            QLabel#SettingDescription {{
                font-size: 13px;
                color: {theme['TAB_TEXT_COLOR']};
                font-weight: 400;
            }}
            #PageContentContainer {{
                background-color: {theme.get('CONTENT_BG_COLOR', theme['BG_COLOR'])};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 12px;
            }}
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background: transparent;
                border: none;
            }}
            QFrame#SectionSeparator {{
                border: none;
                border-top: 1px solid {theme['BORDER_COLOR']};
                margin: 15px 0;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {theme['URL_BAR_BG']}; color: {theme['TEXT_COLOR']}; border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 6px; padding: 10px; min-height: 22px; font-size: 14px; min-width: 250px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {self.main_window.ACCENT_COLOR}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{
                image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="{theme['ICON_COLOR'].replace("#", "%23")}" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/></svg>');
                width: 12px; height: 12px;
            }}
            QPushButton {{
                background-color: {theme['URL_BAR_BG']}; border: 1px solid {theme['BORDER_COLOR']};
                padding: 10px 18px; border-radius: 6px; font-weight: 700; color: {theme['TEXT_COLOR']};
            }}
            QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {self.main_window.ACCENT_COLOR}; }}
            QPushButton#AccentButton {{ background-color: {self.main_window.ACCENT_COLOR}; color: white; border: none; }}
            QPushButton#AccentButton:hover {{ background-color: #5aa1f2; }}
            QPushButton#DangerButton {{ background-color: {self.main_window.DANGER_COLOR}; color: white; border: none; }}
            QPushButton#DangerButton:hover {{ background-color: #c0392b; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {theme['BORDER_COLOR']}; min-height: 20px; border-radius: 6px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px;
            }}
            #NavList::item:selected {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff; /* White text on accent background */
                font-weight: 700;
                margin: 4px 10px;
            }}
            #NavList::item:selected:!active {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff;
            }}
        """)

    def slide_to_page(self, index):
        """Animates a slide transition between pages in the QStackedWidget."""
        if index == self.current_page_index:
            return

        current_widget = self.pages_stack.currentWidget()
        next_widget = self.pages_stack.widget(index)
        
        # Determine slide direction
        slide_left = index > self.current_page_index
        offset = self.pages_stack.width()

        # Position the next widget to slide in
        next_widget.setGeometry(offset if slide_left else -offset, 0, self.pages_stack.width(), self.pages_stack.height())
        next_widget.show()
        self.pages_stack.setCurrentWidget(next_widget)

        # Animate the current widget sliding out
        self.anim_current = QPropertyAnimation(current_widget, b"pos")
        self.anim_current.setDuration(250)
        self.anim_current.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_current.setEndValue(QPoint(-offset if slide_left else offset, 0))

        # Animate the next widget sliding in
        self.anim_next = QPropertyAnimation(next_widget, b"pos")
        self.anim_next.setDuration(250)
        self.anim_next.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_next.setEndValue(QPoint(0, 0))

        self.anim_current.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.anim_next.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        self.current_page_index = index

    def update_nav_list_icons(self, current_row):
        """Updates the color of nav list icons based on selection."""
        theme = self.main_window.theme
        
        # Reset previous item's icon color
        if self.previous_row is not None and self.previous_row != current_row:
            prev_item = self.nav_list.item(self.previous_row)
            if prev_item:
                icon_name = self.tab_icon_names[self.previous_row]
                prev_item.setIcon(create_icon_from_svg(SVG_ICONS[icon_name], theme['TAB_TEXT_COLOR']))

        # Set current item's icon color to the accent color
        current_item = self.nav_list.item(current_row)
        if current_item:
            icon_name = self.tab_icon_names[current_row]
            current_item.setIcon(create_icon_from_svg(SVG_ICONS[icon_name], self.main_window.ACCENT_COLOR))

        self.previous_row = current_row

    def create_nav_item(self, text, icon_name):
        item = QListWidgetItem(text)
        theme = self.main_window.theme
        item.setIcon(create_icon_from_svg(SVG_ICONS[icon_name], theme['TAB_TEXT_COLOR']))
        return item

    def create_setting_row(self, label_widget, control_widget):
        """Creates a styled row for a setting."""
        row_widget = QWidget()
        row_widget.setObjectName("SettingRow") # For styling
        # Use a QGridLayout for more robust alignment control.
        row_layout = QGridLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(25)

        row_layout.addWidget(label_widget, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(control_widget, 0, 1, Qt.AlignmentFlag.AlignVCenter)
        row_layout.setColumnStretch(0, 1)
        
        return row_widget

    def create_label_widget(self, title, description):
        """Creates a standard widget for a setting's title and description."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setObjectName("SettingTitle")
        layout.addWidget(title_label) # Add title

        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("SettingDescription")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        return widget

    def create_toggle(self):
        """Creates a themed ToggleSwitch."""
        theme = self.main_window.theme
        track_off = theme['BORDER_COLOR']
        track_on = self.main_window.ACCENT_COLOR
        handle_color = "#ffffff" # White handle for both themes for contrast
        border_color = QColor(theme['BORDER_COLOR']).lighter(120).name()
        
        return ToggleSwitch(
            track_color_off=track_off,
            track_color_on=track_on,
            handle_color=handle_color,
            border_color=border_color
        )

    def _handle_setting_changed(self, *args):
        self.save_settings()

    def _create_page_container(self, content_widget):
        """Wraps the page content in a scroll area and a shadow container for depth effect."""
        # This is the main container for the page content that will have the border and shadow.
        container = QWidget()
        container.setObjectName("PageContentContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(50, 40, 50, 40) # Padding inside the card
        container_layout.addWidget(content_widget)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("PageScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)
        return scroll_area
    
    def create_general_page(self):
        content_widget = QWidget()
        content_widget.setObjectName("ScrollContentWidget")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        page_title = QLabel("General")
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)

        # --- Appearance Section ---
        appearance_title = QLabel("Appearance")
        appearance_title.setObjectName("SectionTitle")
        layout.addWidget(appearance_title)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setObjectName("SectionSeparator")
        layout.addWidget(separator1)

        self.theme_combo = QComboBox()
        self.update_theme_combo()
        theme_label = self.create_label_widget("Theme", "Choose the appearance of the browser interface.")

        # --- Theme Editor Buttons ---
        self.create_theme_btn = QPushButton("Create New...")
        self.create_theme_btn.setObjectName("AccentButton")
        self.edit_theme_btn = QPushButton("Edit")
        self.delete_theme_btn = QPushButton("Delete")
        self.delete_theme_btn.setObjectName("DangerButton")

        self.create_theme_btn.clicked.connect(lambda: self.open_theme_editor(create_new=True))
        self.edit_theme_btn.clicked.connect(self.open_theme_editor)
        self.delete_theme_btn.clicked.connect(self.delete_current_theme)

        theme_controls_widget = QWidget()
        theme_controls_layout = QHBoxLayout(theme_controls_widget)
        theme_controls_layout.setContentsMargins(0,0,0,0)
        theme_controls_layout.addWidget(self.theme_combo, 1)
        theme_controls_layout.addWidget(self.create_theme_btn)
        theme_controls_layout.addWidget(self.edit_theme_btn)
        theme_controls_layout.addWidget(self.delete_theme_btn)

        layout.addWidget(self.create_setting_row(theme_label, theme_controls_widget))

        self.tab_style_combo = QComboBox()
        self.tab_style_combo.addItems(["Modern (Overview only)", "Classic (Top tab bar)"])
        tab_style_label = self.create_label_widget("Tab Style", "Choose how to display and manage your tabs. Requires restart.")
        layout.addWidget(self.create_setting_row(tab_style_label, self.tab_style_combo))

        # --- Startup Section ---
        startup_title = QLabel("Startup")
        startup_title.setObjectName("SectionTitle")
        layout.addWidget(startup_title)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setObjectName("SectionSeparator")
        layout.addWidget(separator2)

        self.startup_combo = QComboBox()
        self.startup_combo.addItems([
            "Show the New Tab page",
            "Continue where you left off",
            "Show a blank page"
        ])
        startup_label = self.create_label_widget("On startup", "Choose what to see when you open the browser.")
        layout.addWidget(self.create_setting_row(startup_label, self.startup_combo))

        # --- Search Section ---
        search_title = QLabel("Search")
        search_title.setObjectName("SectionTitle")
        layout.addWidget(search_title)
        
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setObjectName("SectionSeparator")
        layout.addWidget(separator3)
        
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["Disunic","DuckDuckGo", "Google", "Bing", "Yahoo", "StartPage", "Ecosia"])
        search_engine_label = self.create_label_widget("Search engine", "The default search engine used in the address bar and new tab page.")
        layout.addWidget(self.create_setting_row(search_engine_label, self.search_engine_combo))
        
        self.default_search_check = self.create_toggle() #QCheckBox("Use the default search engine when you type in the address bar")
        default_search_label = self.create_label_widget("Address bar search", "Use the default search engine when you type in the address bar.")
        layout.addWidget(self.create_setting_row(default_search_label, self.default_search_check))

        # --- Downloads Section ---
        downloads_title = QLabel("Downloads")
        downloads_title.setObjectName("SectionTitle")
        layout.addWidget(downloads_title)
        
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.Shape.HLine)
        separator4.setObjectName("SectionSeparator")
        layout.addWidget(separator4)

        self.download_path_edit = QLineEdit()
        self.download_path_edit.setReadOnly(True)
        self.download_path_btn = QPushButton("Browse...")
        self.download_path_btn.clicked.connect(self.select_download_path)
        
        # Create a composite widget for the path editor and button
        path_widget = QWidget()
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0,0,0,0)
        path_layout.setSpacing(10)
        path_layout.addWidget(self.download_path_edit)
        path_layout.addWidget(self.download_path_btn)
        path_widget.setLayout(path_layout)

        download_path_label = self.create_label_widget("Download location", "Where to save downloaded files.")
        layout.addWidget(self.create_setting_row(download_path_label, path_widget))
        
        self.ask_save_check = self.create_toggle() #QCheckBox("Always ask for the location before downloading a file")
        ask_save_label = self.create_label_widget("Ask where to save", "Always ask for the location before downloading a file.")
        layout.addWidget(self.create_setting_row(ask_save_label, self.ask_save_check))
        
        layout.addStretch(1)

        return self._create_page_container(content_widget)

    def create_privacy_page(self):
        content_widget = QWidget()
        content_widget.setObjectName("ScrollContentWidget")
        layout = QVBoxLayout(content_widget) # type: ignore
        layout.setContentsMargins(0, 0, 0, 0)
        page_title = QLabel("Privacy & Security")
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)
        
        # --- Cookies & Site Data Section ---
        cookies_title = QLabel("Cookies & Site Data")
        cookies_title.setObjectName("SectionTitle")
        layout.addWidget(cookies_title)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setObjectName("SectionSeparator")
        layout.addWidget(separator1)

        self.cookies_combo = QComboBox()
        self.cookies_combo.addItems(["Allow all cookies", "Block all cookies"])
        cookies_label = self.create_label_widget("Cookies", "Control how websites can use cookies to track you.")
        layout.addWidget(self.create_setting_row(cookies_label, self.cookies_combo))
        
        self.clear_on_exit_check = self.create_toggle() #QCheckBox("Clear cookies and site data when you close the browser")
        clear_on_exit_label = self.create_label_widget("Clear data on exit", "Automatically clear cookies and other site data when you close the browser.")
        layout.addWidget(self.create_setting_row(clear_on_exit_label, self.clear_on_exit_check))

        clear_now_btn = QPushButton("Clear data now...")
        clear_now_btn.clicked.connect(self.clear_cookies_now)
        clear_now_label = self.create_label_widget("Clear Browsing Data", "Remove history, cookies, cache, and more.")
        layout.addWidget(self.create_setting_row(clear_now_label, clear_now_btn))
        
        # --- Tracking Protection Section ---
        tracking_title = QLabel("Tracking Protection")
        tracking_title.setObjectName("SectionTitle")
        layout.addWidget(tracking_title)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setObjectName("SectionSeparator")
        layout.addWidget(separator2)

        self.tracking_combo = QComboBox()
        self.tracking_combo.addItems(["Standard protection", "Strict protection", "Custom"])
        tracking_label = self.create_label_widget("Protection level", "Higher levels may cause some sites to break.")
        layout.addWidget(self.create_setting_row(tracking_label, self.tracking_combo))
        
        self.tracking_check = self.create_toggle() #QCheckBox("Block known trackers")
        self.tracking_check.setChecked(True) # Default to on
        block_trackers_label = self.create_label_widget("Block known trackers", "Block content from companies that track you across sites.")
        layout.addWidget(self.create_setting_row(block_trackers_label, self.tracking_check))
        
        self.fingerprinting_check = self.create_toggle() #QCheckBox("Block fingerprinting")
        fingerprinting_label = self.create_label_widget("Block fingerprinting", "Prevent sites from creating a unique profile of your device and browser.")
        layout.addWidget(self.create_setting_row(fingerprinting_label, self.fingerprinting_check))
        
        self.cryptomining_check = self.create_toggle() #QCheckBox("Block cryptominers")
        cryptomining_label = self.create_label_widget("Block cryptominers", "Stop sites from using your computer's resources to mine cryptocurrency.")
        layout.addWidget(self.create_setting_row(cryptomining_label, self.cryptomining_check))

        # --- Ad Blocker ---
        self.adblock_check = self.create_toggle() #QCheckBox("Block ads and trackers")
        adblock_label = self.create_label_widget("Block Ads & Trackers", "Block requests to known advertising and tracking domains. Requires restart.")
        layout.addWidget(self.create_setting_row(adblock_label, self.adblock_check))

        # --- Ad Blocker Update ---
        self.update_adblock_btn = QPushButton("Update Now")
        self.update_adblock_btn.clicked.connect(self.force_adblock_update)
        self.adblock_status_label = self.create_label_widget(
            "Update Ad Block List", 
            f"Lists are updated automatically. Last check: Never"
        )
        layout.addWidget(self.create_setting_row(self.adblock_status_label, self.update_adblock_btn))
        # Connect the signal from the adblocker to update the status label
        if self.main_window and hasattr(self.main_window, 'adblocker'):
            self.main_window.adblocker.signals.rules_updated.connect(self.on_adblock_rules_updated)
        
        # --- Permissions Section ---
        permissions_title = QLabel("Permissions")
        permissions_title.setObjectName("SectionTitle")
        layout.addWidget(permissions_title)
        
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setObjectName("SectionSeparator")
        layout.addWidget(separator3)

        self.location_check = self.create_toggle() #QCheckBox("Ask for your location")
        location_label = self.create_label_widget("Location", "Allow sites to ask for your physical location.")
        layout.addWidget(self.create_setting_row(location_label, self.location_check))

        self.camera_check = self.create_toggle() #QCheckBox("Ask to use your camera")
        camera_label = self.create_label_widget("Camera", "Allow sites to ask to use your camera.")
        layout.addWidget(self.create_setting_row(camera_label, self.camera_check))

        self.microphone_check = self.create_toggle() #QCheckBox("Ask to use your microphone")
        microphone_label = self.create_label_widget("Microphone", "Allow sites to ask to use your microphone.")
        layout.addWidget(self.create_setting_row(microphone_label, self.microphone_check))

        # Update initial adblock status
        self.update_adblock_status_label()

        layout.addStretch(1)

        return self._create_page_container(content_widget)

    def force_adblock_update(self):
        """Triggers the adblocker to force an update of its rules."""
        if self.main_window and hasattr(self.main_window, 'adblocker'):
            self.main_window.adblocker.force_update_rules()
            self.adblock_status_label.findChild(QLabel, "SettingDescription").setText("Update check started in background...")

    def on_adblock_rules_updated(self, rule_count):
        """Slot to handle the signal that rules have been updated."""
        self.update_adblock_status_label(rule_count)

    def update_adblock_status_label(self, rule_count=None):
        """Updates the text on the settings page about the adblock list status."""
        from datetime import datetime

        desc_label = self.adblock_status_label.findChild(QLabel, "SettingDescription")
        if not desc_label: return

        if rule_count is None:
            rule_count = len(self.main_window.adblocker.rules) if self.main_window and hasattr(self.main_window, 'adblocker') else 0
        
        last_updated_str = "Never"
        if self.main_window and hasattr(self.main_window, 'adblocker'):
            cache_path = self.main_window.adblocker.cache_path
            if os.path.exists(cache_path):
                try:
                    mtime = os.path.getmtime(cache_path)
                    dt_object = datetime.fromtimestamp(mtime)
                    if dt_object.date() == datetime.today().date():
                        last_updated_str = f"Today at {dt_object.strftime('%I:%M %p')}"
                    else:
                        last_updated_str = dt_object.strftime('%B %d, %Y')
                except Exception:
                    pass # Keep "Never" on error

        desc_label.setText(f"Blocklist contains {rule_count:,} rules. Last updated: {last_updated_str}")

    def open_theme_editor(self, create_new=False):
        """Opens the theme editor dialog to edit or create a theme."""
        current_theme_name = self.theme_combo.currentText()
        theme_data = self.main_window.THEMES.get(current_theme_name.lower(), {}).copy()

        if create_new:
            # Start with a copy of the current theme as a base
            dialog = ThemeEditorDialog(theme_data, "My Custom Theme", self)
        else:
            # Edit the selected theme
            dialog = ThemeEditorDialog(theme_data, current_theme_name, self)

        if dialog.exec(): # User clicked "Save"
            # On successful save, reload themes and update UI
            self.main_window.load_themes()
            
            new_theme_name = dialog.name_edit.text().strip()
            self.update_theme_combo(new_selection=new_theme_name)

            # Trigger a settings save to apply the new theme and prompt for restart
            self.save_settings()

    def delete_current_theme(self):
        """Deletes the currently selected theme from themes.json."""
        theme_name_to_delete = self.theme_combo.currentText().lower()

        # A theme is only deletable if it is NOT a default theme.
        if theme_name_to_delete in self.main_window.DEFAULT_THEMES:
            CustomMessageBox.warning(self, "Cannot Delete", "Default themes (like Dark and Light) cannot be deleted.")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Deletion")
        msg_box.setText(f"Are you sure you want to permanently delete the '{self.theme_combo.currentText()}' theme?")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setObjectName("DangerButton")

        theme = self.main_window.theme
        msg_box.setStyleSheet(f"""
            QMessageBox {{ background-color: {theme['TOOLBAR_COLOR']}; border: 1px solid {theme['BORDER_COLOR']}; }}
            QMessageBox QLabel {{ color: {theme['TEXT_COLOR']}; font-size: 14px; }}
            QMessageBox QPushButton {{ background-color: {theme['MSGBOX_BUTTON_BG']}; border: 1px solid {theme['BORDER_COLOR']}; padding: 8px 16px; border-radius: 4px; color: {theme['TEXT_COLOR']}; min-width: 80px; font-weight: 700; }}
            QMessageBox QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border: 1px solid {self.main_window.ACCENT_COLOR}; }}
            QMessageBox QPushButton#DangerButton {{ background-color: {self.main_window.DANGER_COLOR}; border-color: {self.main_window.DANGER_COLOR}; color: white; }}
            QMessageBox QPushButton#DangerButton:hover {{ background-color: #c0392b; }}
        """)
        
        if msg_box.exec() == QMessageBox.StandardButton.No:
            return

        # Proceed with deletion
        script_dir = os.path.dirname(os.path.abspath(__file__))
        themes_path = os.path.join(script_dir, 'themes.json')

        try:
            with open(themes_path, 'r', encoding='utf-8') as f:
                all_themes = json.load(f)
            
            if theme_name_to_delete in all_themes:
                del all_themes[theme_name_to_delete]

            with open(themes_path, 'w', encoding='utf-8') as f:
                json.dump(all_themes, f, indent=4)

            self.main_window.load_themes()
            self.update_theme_combo(new_selection="dark")
            self.save_settings()
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            CustomMessageBox.critical(self, "Error", f"Failed to delete theme: {e}")

    def create_advanced_page(self):
        content_widget = QWidget()
        content_widget.setObjectName("ScrollContentWidget")
        layout = QVBoxLayout(content_widget) # type: ignore
        layout.setContentsMargins(0, 0, 0, 0)
        page_title = QLabel("Advanced")
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)
        
        # --- Network Section ---
        network_title = QLabel("Network")
        network_title.setObjectName("SectionTitle")
        layout.addWidget(network_title)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setObjectName("SectionSeparator")
        layout.addWidget(separator1)

        if sys.platform != "darwin":
            self.proxy_check = self.create_toggle() #QCheckBox("Use the Tor network")
            proxy_label = self.create_label_widget("Use Dark Web (Tor)", "Route your traffic through the Tor network for enhanced privacy. Requires restart.")
            layout.addWidget(self.create_setting_row(proxy_label, self.proxy_check))

        # The proxy host and port are no longer user-configurable from the UI.
        # The browser will use the default values (127.0.0.1:9050).
        
        # --- Performance Section ---
        perf_title = QLabel("Performance")
        perf_title.setObjectName("SectionTitle")
        layout.addWidget(perf_title)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setObjectName("SectionSeparator")
        layout.addWidget(separator2)

        self.hw_accel_check = self.create_toggle() #QCheckBox("Use hardware acceleration when available")
        hw_accel_label = self.create_label_widget("Hardware Acceleration", "Use your computer's GPU to speed up graphics-intensive tasks like video playback.")
        layout.addWidget(self.create_setting_row(hw_accel_label, self.hw_accel_check))
        
        self.cache_check = self.create_toggle() #QCheckBox("Enable disk cache")
        cache_label = self.create_label_widget("Disk Cache", "Store parts of pages, like images, to speed up loading on your next visit.")
        layout.addWidget(self.create_setting_row(cache_label, self.cache_check))
        
        self.prefetch_check = self.create_toggle() #QCheckBox("Prefetch resources to load pages faster")
        prefetch_label = self.create_label_widget("Prefetch Resources", "Allow the browser to predict and load resources for pages you might visit next.")
        layout.addWidget(self.create_setting_row(prefetch_label, self.prefetch_check))
        
        # --- Troubleshooting Section ---
        reset_title = QLabel("Troubleshooting")
        reset_title.setObjectName("SectionTitle")
        layout.addWidget(reset_title)
        
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setObjectName("SectionSeparator")
        layout.addWidget(separator3)

        reset_btn = QPushButton("Reset settings to their original defaults")
        reset_btn.setObjectName("DangerButton")
        reset_btn.clicked.connect(self.confirm_reset)
        reset_label = self.create_label_widget("Reset All Settings", "This will restore all settings to their original state. This action cannot be undone.")
        layout.addWidget(self.create_setting_row(reset_label, reset_btn))

        layout.addStretch(1)

        return self._create_page_container(content_widget)

    def select_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if path:
            self.download_path_edit.setText(path)

    def clear_cookies_now(self):
        reply = CustomMessageBox.question(
            self,
            "Clear Cookies",
            "Are you sure you want to clear all cookies and site data?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            CustomMessageBox.information(self, "Cookies Cleared", "All cookies and site data have been cleared.")
    
    def confirm_reset(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reset Settings")
        msg_box.setText("Are you sure you want to reset all settings to their defaults? This action cannot be undone.")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setObjectName("DangerButton")

        theme = self.main_window.theme
        msg_box.setStyleSheet(f"""
            QMessageBox {{ background-color: {theme['TOOLBAR_COLOR']}; border: 1px solid {theme['BORDER_COLOR']}; }}
            QMessageBox QLabel {{ color: {theme['TEXT_COLOR']}; font-size: 14px; }}
            QMessageBox QPushButton {{ background-color: {theme['MSGBOX_BUTTON_BG']}; border: 1px solid {theme['BORDER_COLOR']}; padding: 8px 16px; border-radius: 4px; color: {theme['TEXT_COLOR']}; min-width: 80px; font-weight: 700; }}
            QMessageBox QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border: 1px solid {self.main_window.ACCENT_COLOR}; }}
            QMessageBox QPushButton#DangerButton {{ background-color: {self.main_window.DANGER_COLOR}; border-color: {self.main_window.DANGER_COLOR}; color: white; }}
            QMessageBox QPushButton#DangerButton:hover {{ background-color: #c0392b; }}
        """)
        
        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_settings()

    def reset_settings(self):
        """Flags the application for a factory reset and restarts the browser after a countdown."""
        # Set a flag in QSettings to indicate a reset is needed on the next launch.
        self.settings.setValue("factory_reset_pending", True)
        self.settings.sync()

        # Show countdown dialog
        countdown_dialog = CountdownDialog(self)
        countdown_dialog.exec()
        
        # After countdown, restart the browser.
        self.restart_browser()

    def update_theme_combo(self, new_selection=None):
        """Clears and repopulates the theme combo box."""
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        theme_names = [name.capitalize() for name in self.main_window.THEMES.keys()]
        self.theme_combo.addItems(theme_names)
        if new_selection:
            self.theme_combo.setCurrentText(new_selection.capitalize())
        self.theme_combo.blockSignals(False)

    def update_theme_buttons_state(self, text=None):
        """Enable/disable theme action buttons based on the selected theme."""
        selected_theme_name = self.theme_combo.currentText().lower()

        # A theme is deletable if it is NOT a default theme.
        is_deletable = selected_theme_name not in self.main_window.DEFAULT_THEMES
        self.delete_theme_btn.setEnabled(is_deletable)

    def load_settings(self):
        # General settings
        theme_name = self.settings.value("theme", "dark", type=str)
        self.update_theme_combo(new_selection=theme_name)
        self.tab_style_combo.setCurrentIndex(self.settings.value("tab_style", 0, type=int))
        self.startup_combo.setCurrentIndex(self.settings.value("startup_behavior", 0, type=int))
        self.update_theme_buttons_state()
        self.search_engine_combo.setCurrentText(self.settings.value("search_engine", "DuckDuckGo"))
        self.default_search_check.setChecked(self.settings.value("default_search", True, type=bool))
        self.download_path_edit.setPlaceholderText(self.settings.value("download_path", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)))
        self.ask_save_check.setChecked(self.settings.value("ask_save_location", True, type=bool))
        
        # Privacy settings
        # Map old cookie policy values to new indices to avoid errors on update
        # Old: 0=Allow, 1=Block 3rd, 2=Block All
        # New: 0=Allow, 1=Block All
        old_cookie_policy = int(self.settings.value("cookie_policy", 0))
        new_cookie_index = 0
        if old_cookie_policy == 2: # "Block All" is now at index 1
            new_cookie_index = 1
        self.cookies_combo.setCurrentIndex(new_cookie_index)
        self.clear_on_exit_check.setChecked(self.settings.value("clear_cookies_on_exit", False, type=bool))
        self.tracking_combo.setCurrentIndex(int(self.settings.value("tracking_protection", 0)))
        self.tracking_check.setChecked(self.settings.value("block_trackers", True, type=bool))
        self.fingerprinting_check.setChecked(self.settings.value("block_fingerprinting", True, type=bool))
        self.cryptomining_check.setChecked(self.settings.value("block_cryptominers", True, type=bool))
        self.adblock_check.setChecked(self.settings.value("adblocker_enabled", True, type=bool))
        self.location_check.setChecked(self.settings.value("ask_location", True, type=bool))
        self.camera_check.setChecked(self.settings.value("ask_camera", True, type=bool))
        self.microphone_check.setChecked(self.settings.value("ask_microphone", True, type=bool))
        
        # Advanced settings
        if hasattr(self, 'proxy_check'):
            self.proxy_check.setChecked(self.settings.value("use_proxy", True, type=bool))
        self.hw_accel_check.setChecked(self.settings.value("hardware_acceleration", True, type=bool))
        self.cache_check.setChecked(self.settings.value("disk_cache", True, type=bool))
        self.prefetch_check.setChecked(self.settings.value("prefetch_resources", False, type=bool))
    
    def connect_signals(self): # type: ignore
        """Connects all widget signals to the auto-save handler."""
        # General
        self.theme_combo.currentTextChanged.connect(self._handle_setting_changed)
        self.theme_combo.currentTextChanged.connect(self.update_theme_buttons_state)
        self.tab_style_combo.currentIndexChanged.connect(self._handle_setting_changed)
        self.startup_combo.currentIndexChanged.connect(self._handle_setting_changed)
        self.search_engine_combo.currentTextChanged.connect(self._handle_setting_changed)
        self.default_search_check.stateChanged.connect(self._handle_setting_changed)
        self.download_path_edit.editingFinished.connect(self._handle_setting_changed)
        self.ask_save_check.stateChanged.connect(self._handle_setting_changed)

        # Privacy
        self.cookies_combo.currentIndexChanged.connect(self._handle_setting_changed)
        self.clear_on_exit_check.stateChanged.connect(self._handle_setting_changed)
        self.tracking_combo.currentIndexChanged.connect(self._handle_setting_changed)
        self.tracking_check.stateChanged.connect(self._handle_setting_changed)
        self.fingerprinting_check.stateChanged.connect(self._handle_setting_changed)
        self.cryptomining_check.stateChanged.connect(self._handle_setting_changed)
        self.adblock_check.stateChanged.connect(self._handle_setting_changed)
        self.location_check.stateChanged.connect(self._handle_setting_changed)
        self.camera_check.stateChanged.connect(self._handle_setting_changed)
        self.microphone_check.stateChanged.connect(self._handle_setting_changed)

        # Advanced
        if hasattr(self, 'proxy_check'):
            self.proxy_check.stateChanged.connect(self._handle_setting_changed)
        self.hw_accel_check.stateChanged.connect(self._handle_setting_changed)
        self.cache_check.stateChanged.connect(self._handle_setting_changed)
        self.prefetch_check.stateChanged.connect(self._handle_setting_changed)

    def save_settings(self):
        """Saves all settings and applies them where possible. Prompts for restart if needed."""
        previous_proxy = self.settings.value("use_proxy", True, type=bool)
        new_proxy = self.proxy_check.isChecked() if hasattr(self, 'proxy_check') else False
        if sys.platform == "darwin":
            new_proxy = False
        previous_theme = self.settings.value("theme", "dark", type=str)
        new_theme = self.theme_combo.currentText().lower()
        previous_tab_style = self.settings.value("tab_style", 0, type=int)
        new_tab_style = self.tab_style_combo.currentIndex()
        # New checks for restart
        previous_hw_accel = self.settings.value("hardware_acceleration", True, type=bool)
        new_hw_accel = self.hw_accel_check.isChecked()
        previous_adblocker = self.settings.value("adblocker_enabled", True, type=bool)
        new_adblocker = self.adblock_check.isChecked()

        # General settings
        self.settings.setValue("search_engine", self.search_engine_combo.currentText())
        self.settings.setValue("theme", new_theme)
        self.settings.setValue("tab_style", new_tab_style)
        self.settings.setValue("startup_behavior", self.startup_combo.currentIndex())
        self.settings.setValue("default_search", self.default_search_check.isChecked())
        self.settings.setValue("download_path", self.download_path_edit.text() or self.download_path_edit.placeholderText())
        self.settings.setValue("ask_save_location", self.ask_save_check.isChecked())
        
        # Privacy settings
        self.settings.setValue("cookie_policy", self.cookies_combo.currentIndex()) # type: ignore
        self.settings.setValue("clear_cookies_on_exit", self.clear_on_exit_check.isChecked())
        self.settings.setValue("tracking_protection", self.tracking_combo.currentIndex())
        self.settings.setValue("block_trackers", self.tracking_check.isChecked())
        self.settings.setValue("block_fingerprinting", self.fingerprinting_check.isChecked())
        self.settings.setValue("block_cryptominers", self.cryptomining_check.isChecked())
        self.settings.setValue("adblocker_enabled", new_adblocker)
        self.settings.setValue("ask_location", self.location_check.isChecked())
        self.settings.setValue("ask_camera", self.camera_check.isChecked())
        self.settings.setValue("ask_microphone", self.microphone_check.isChecked())
        
        # Advanced settings
        self.settings.setValue("use_proxy", new_proxy)  # Save user choice
        self.settings.setValue("hardware_acceleration", new_hw_accel)
        
        # Force settings to be written to persistent storage immediately
        self.settings.sync()
        
        # Apply settings to the current browser session
        self.apply_settings()
        
        # Show restart notification if critical settings changed
        restart_needed = (
            previous_theme != new_theme or
            previous_tab_style != new_tab_style or
            previous_proxy != new_proxy or
            previous_hw_accel != new_hw_accel or previous_adblocker != new_adblocker
        )
        if restart_needed and self.main_window:
            self.show_restart_dialog()

    def show_restart_dialog(self):
        """Shows a custom frameless dialog to prompt for restart."""
        dialog = RestartDialog(self)
        if dialog.exec(): # Returns 1 (Accepted) if "Restart Now" is clicked
            self.restart_browser()

    def restart_browser(self):
        if self.main_window:
            # Ensure all data is flushed before we quit.
            self.settings.sync()
            QApplication.instance().processEvents() # Process any pending events

            # Get the path to the python executable and the main script
            python_executable = sys.executable
            main_script = sys.argv[0]

            # Detach the new process from the current one using the recommended Qt method
            QProcess.startDetached(f'"{python_executable}" "{main_script}"')
            
            # Quit the current application instance
            QApplication.instance().quit()

    def apply_settings(self):
        # Apply proxy settings
        use_proxy = False
        if hasattr(self, 'proxy_check'):
            use_proxy = self.proxy_check.isChecked()
        if sys.platform == "darwin":
            use_proxy = False
        if use_proxy:
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.ProxyType.Socks5Proxy)
            proxy.setHostName(str(self.settings.value("proxy_host", "127.0.0.1")))
            proxy.setPort(self.settings.value("proxy_port", 9050, type=int))
            QNetworkProxy.setApplicationProxy(proxy)
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        
        # Apply user agent
        
        # Apply cache settings
        if self.cache_check.isChecked():
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        else:
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        
        # Apply cookie policy
        # New: 0=Allow, 1=Block All
        cookie_policy = self.cookies_combo.currentIndex()
        if cookie_policy == 0:  # Allow all
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        elif cookie_policy == 1:  # Block all
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        
        # Apply security level and other web settings
        dev_tools_enabled = self.settings.value("dev_tools_enabled", True, type=bool)
        settings = self.profile.settings()

        # Determine final state of settings, assuming "Standard" security
        js_enabled = True
        plugins_enabled = True
        clipboard_read_access = True
        clipboard_write_access = True
        windows_can_be_opened = True
        
        # The dev tools checkbox can still disable JS
        if not dev_tools_enabled:
            js_enabled = False

        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_enabled)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, plugins_enabled)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, clipboard_read_access)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, clipboard_write_access)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, windows_can_be_opened)
        
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, dev_tools_enabled)
