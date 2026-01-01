import urllib.parse
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
import sys, os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QTabBar, QStackedWidget, QPushButton, QSizePolicy
)
from PyQt6.QtGui import QIcon
from bin.utils import SVG_ICONS

class TabWidget(QWidget):
    """A widget that encapsulates QTabBar and QStackedWidget for tab management."""
    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)
    newTabRequested = pyqtSignal()
    tabContextMenuRequested = pyqtSignal(int, QPoint)

    def __init__(self, theme, style="modern", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.style_mode = style
        self.setObjectName("TabWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if self.style_mode == "classic": layout.setContentsMargins(0, 0, -1, 0)
        layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentStack")

        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setUsesScrollButtons(True)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        
        self.tab_bar.currentChanged.connect(self.stacked_widget.setCurrentIndex)
        self.tab_bar.currentChanged.connect(self.currentChanged)
        self.tab_bar.tabCloseRequested.connect(self.tabCloseRequested)

        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.on_context_menu)

        if self.style_mode == "classic":
            self.new_tab_btn = QPushButton("+", objectName="NewTabBtn")
            self.new_tab_btn.clicked.connect(self.newTabRequested)
            # Set the tab bar to not expand, so it only takes the space it needs.
            self.tab_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            layout.addWidget(self.tab_bar, 0)
            layout.addWidget(self.new_tab_btn)
            layout.addStretch(1) # Add a stretch to push tabs to the left on all platforms.
        else: # modern
            # The tab bar is not visually part of the layout.
            # This widget now primarily manages the QStackedWidget.
            self.tab_bar.hide()
            layout.addWidget(self.stacked_widget)
        
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Applies the stylesheet for the tab bar and related components."""
        # On macOS, use a different margin and radius for a seamless, Safari-like look.
        if sys.platform == "darwin":
            tab_margin = "6px 2px 0 2px"
            tab_border_radius = "8px 8px 0 0"
        else:
            # Windows/Linux get a slightly different, more compact style
            tab_margin = "4px 2px 0 2px"
            tab_border_radius = "6px 6px 0 0"

        if self.style_mode == "modern":
            self.setStyleSheet(f"""
                #ContentStack {{
                    background: {self.theme["BG_COLOR"]};
                    border: none; /* The border is now on the title bar */
                }}
            """)
        else: # classic
            icon_color = self.theme["ICON_COLOR"]
            self.setStyleSheet(f"""
                #ContentStack {{
                    background: {self.theme["BG_COLOR"]};
                    border: none;
                }}
                QTabBar {{
                    background: transparent;
                    border: none;
                    margin-left: 8px;
                }}
                #NewTabBtn {{
                    background-color: transparent;
                    color: {icon_color};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 8px;
                    margin: 8px 4px 0 4px; /* Align vertically with new tabs */
                    font-size: 18px;
                }}
                #NewTabBtn:hover {{
                    background-color: {self.theme["TAB_HOVER_COLOR"]};
                }}
                QTabBar::scroller QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 4px;
                    margin: 4px;
                }}
                QTabBar::scroller QPushButton:hover {{
                    background-color: {self.theme["TAB_HOVER_COLOR"]};
                }}
                QTabBar::left-arrow {{
                    image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["back"].replace("currentColor", icon_color))}');
                }}
                QTabBar::right-arrow {{
                    image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["forward"].replace("currentColor", icon_color))}');
                }}
                QTabBar::tab {{
                    background: {self.theme["TAB_HOVER_COLOR"]};
                    color: {self.theme["TAB_TEXT_COLOR"]};
                    padding: 8px 16px;
                    border: none;
                    border-radius: {tab_border_radius};
                    margin: {tab_margin};
                    min-width: 100px;
                    max-width: 200px;
                    border-bottom: 1px solid transparent;
                }}
                QTabBar::tab:!selected:hover {{
                    background: {self.theme["BUTTON_HOVER_COLOR"]};
                    color: {self.theme["TEXT_COLOR"]};
                }}
                QTabBar::tab:selected {{
                    background: {self.theme["TAB_ACTIVE_COLOR"]};
                    color: {self.theme["TAB_TEXT_SELECTED_COLOR"]};
                    font-weight: 700;
                    border-bottom: 1px solid {self.theme["TAB_ACTIVE_COLOR"]};
                }}
                QTabBar::close-button {{
                    image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["close"].replace("currentColor", self.theme["TAB_TEXT_COLOR"]))}');
                    subcontrol-position: right;
                    subcontrol-origin: padding;
                    margin: 2px;
                    background-color: transparent;
                    padding: 2px;
                    border-radius: 4px;
                }}
                QTabBar::close-button:selected {{
                    image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["close"].replace("currentColor", self.theme["TAB_TEXT_SELECTED_COLOR"]))}');
                }}
                QTabBar::close-button:hover {{
                    background-color: {self.theme["DANGER_COLOR"]};
                    image: url('data:image/svg+xml,{urllib.parse.quote(SVG_ICONS["close"].replace("currentColor", "#ffffff"))}');
                }}
            """)

    def add_tab(self, widget, title, icon=None):
        index = self.stacked_widget.addWidget(widget)
        tab_index = self.tab_bar.addTab(title)
        if icon:
            self.tab_bar.setTabIcon(tab_index, icon)
        else:
            self.tab_bar.setTabIcon(tab_index, QIcon()) # Placeholder
        self.tab_bar.setCurrentIndex(tab_index)
        return tab_index

    def remove_tab(self, index):
        widget = self.stacked_widget.widget(index)
        self.stacked_widget.removeWidget(widget)
        self.tab_bar.removeTab(index)
        return widget

    def on_context_menu(self, point):
        index = self.tab_bar.tabAt(point)
        if index != -1:
            self.tabContextMenuRequested.emit(index, self.tab_bar.mapToGlobal(point))

    def set_tab_text(self, index, text):
        self.tab_bar.setTabText(index, text)
    
    def set_tab_tooltip(self, index, text):
        self.tab_bar.setTabToolTip(index, text)

    def set_tab_icon(self, index, icon):
        self.tab_bar.setTabIcon(index, icon)

    def current_widget(self):
        return self.stacked_widget.currentWidget()

    def widget(self, index):
        return self.stacked_widget.widget(index)

    def count(self):
        return self.tab_bar.count()

    def index_of(self, widget):
        return self.stacked_widget.indexOf(widget)

    def set_current_index(self, index):
        self.tab_bar.setCurrentIndex(index)