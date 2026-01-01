from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QHBoxLayout, QPushButton, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from bin.history_manager import HistoryManager
from bin.utils import base64_to_qicon, create_icon_from_svg, SVG_ICONS

class HistoryDialog(QDialog):
    # Theme Colors - consistent with TorBrowser
    BG_COLOR = "#1a1d24"
    TEXT_COLOR = "#e0e6f0"
    TOOLBAR_COLOR = "#232730"
    ACCENT_COLOR = "#4a90e2"
    BORDER_COLOR = "#303642"
    DANGER_COLOR = "#e74c3c"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = HistoryManager()
        self.parent_browser = parent

        self.setWindowTitle("History")
        self.setMinimumSize(800, 600)
        self.setObjectName("HistoryDialog")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar ---
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 10, 10, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self.on_search)
        top_bar_layout.addWidget(self.search_input)

        clear_btn = QPushButton("Clear Browsing History")
        clear_btn.clicked.connect(self.clear_history)
        top_bar_layout.addWidget(clear_btn)
        
        main_layout.addWidget(top_bar)

        # --- History Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Title", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.itemDoubleClicked.connect(self.open_history_item)
        
        main_layout.addWidget(self.table)
        
        self.load_history()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        self.setStyleSheet(f"""
            #HistoryDialog {{ background-color: {self.BG_COLOR}; }}
            #TopBar {{ background-color: {self.TOOLBAR_COLOR}; border-bottom: 1px solid {self.BORDER_COLOR}; }}
            QLineEdit {{ background-color: rgba(255, 255, 255, 0.07); color: {self.TEXT_COLOR}; border: 1px solid {self.BORDER_COLOR}; border-radius: 4px; padding: 8px; }}
            QPushButton {{ background-color: {self.DANGER_COLOR}; color: white; border: none; border-radius: 4px; padding: 8px 12px; font-weight: 500; }}
            QPushButton:hover {{ background-color: #c0392b; }}
            QTableWidget {{ background-color: {self.BG_COLOR}; color: {self.TEXT_COLOR}; border: none; gridline-color: {self.BORDER_COLOR}; }}
            QHeaderView::section {{ background-color: {self.TOOLBAR_COLOR}; color: {self.TEXT_COLOR}; padding: 8px; border: none; border-bottom: 1px solid {self.BORDER_COLOR}; }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {self.BORDER_COLOR}; }}
            QTableWidget::item:selected {{ background-color: {self.ACCENT_COLOR}; color: {self.TEXT_COLOR}; }}

            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.BORDER_COLOR};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: transparent;
                height: 0px; /* Hide horizontal scrollbar */
            }}
        """)

    def load_history(self, search_term=None):
        self.table.setRowCount(0)
        if search_term:
            history_items = self.history_manager.search_history(search_term)
        else:
            history_items = self.history_manager.get_history()

        for row, (url, title, visit_time, favicon_b64) in enumerate(history_items):
            self.table.insertRow(row)

            # Favicon
            if favicon_b64:
                icon = base64_to_qicon(favicon_b64)
            else:
                icon = create_icon_from_svg(SVG_ICONS['info'], '#aaa') # Placeholder
            
            icon_item = QTableWidgetItem()
            icon_item.setIcon(icon)
            self.table.setItem(row, 0, icon_item)

            # Title
            title_text = title if title else url
            title_item = QTableWidgetItem(title_text)
            title_item.setData(Qt.ItemDataRole.UserRole, url) # Store URL in item
            self.table.setItem(row, 1, title_item)

            # URL
            url_item = QTableWidgetItem(url)
            url_item.setForeground(QColor("#9ca3af"))
            self.table.setItem(row, 2, url_item)

    def on_search(self, text):
        self.load_history(text)

    def open_history_item(self, item):
        url = self.table.item(item.row(), 1).data(Qt.ItemDataRole.UserRole)
        if url:
            self.parent_browser.add_new_tab(url)
            self.accept()

    def clear_history(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Clear History")
        msg_box.setText("Are you sure you want to clear all browsing history?")
        msg_box.setInformativeText("This action cannot be undone.")
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
            QMessageBox QPushButton#AccentButton {{ background-color: {self.DANGER_COLOR}; border-color: {self.DANGER_COLOR}; color: white; }}
            QMessageBox QPushButton#AccentButton:hover {{ background-color: #c0392b; }}
        """)
        
        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.load_history()