import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QLabel, QPushButton, QMessageBox
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QPoint
from PyQt6.QtGui import QIcon, QAction

# --- PLACEHOLDERS ---
# These values are replaced by the DisunicX builder script.
APP_URL = "{APP_URL}"
APP_NAME = "{APP_NAME}"
APP_ICON_PATH = "{APP_ICON_PATH}"
# --- END PLACEHOLDERS ---

class SSBWebView(QWebEngineView):
    """A custom QWebEngineView to provide a browser-like context menu."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(43, 43, 43, 0.95);
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-weight: 700;
            }
            QMenu::item {
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #3F51B5; /* A default accent color */
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #777;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 8px 4px;
            }
        """)

        # Standard navigation actions
        menu.addAction("Back", self.page().back).setEnabled(self.page().history().canGoBack())
        menu.addAction("Forward", self.page().forward).setEnabled(self.page().history().canGoForward())
        menu.addAction("Reload", self.page().reload)
        menu.addSeparator()

        # Standard text editing actions
        menu.addAction("Copy", self.page().triggerAction, QWebEnginePage.WebAction.Copy).setEnabled(self.page().hasSelection())
        menu.addAction("Paste", self.page().triggerAction, QWebEnginePage.WebAction.Paste)
        menu.addAction("Select All", self.page().triggerAction, QWebEnginePage.WebAction.SelectAll)

        menu.exec(event.globalPos())

class SiteSpecificBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        if APP_ICON_PATH and APP_ICON_PATH != 'None':
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.browser = SSBWebView(self)
        self.browser.setUrl(QUrl(APP_URL))
        self.setCentralWidget(self.browser)
        self.resize(1280, 720)

        # --- Status Bar ---
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_bar.addWidget(self.status_label, 1) # stretch = 1
        self.browser.page().linkHovered.connect(self.update_status_message)

        # --- Menu Button in Status Bar ---
        self.url_action = QAction("Loading...", self)
        self.url_action.setEnabled(False)
        self.browser.urlChanged.connect(self.update_menu_url)
        self.update_menu_url(self.browser.url()) # Set initial URL

        self.menu_button = QPushButton("☰")
        self.menu_button.setObjectName("StatusBarMenuButton")
        self.menu_button.setFlat(True)
        self.menu_button.clicked.connect(self.show_status_menu)
        self.status_bar.addPermanentWidget(self.menu_button)

        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2b2b2b;
                border-top: 1px solid #444;
                padding: 0 4px;
            }
            QStatusBar::item {
                border: none;
                margin: 2px;
            }
            QLabel#StatusLabel {
                color: #a1a1aa;
                font-weight: 700;
                padding: 2px 8px;
            }
            QPushButton#StatusBarMenuButton {
                color: #a1a1aa;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 0 8px;
            }
            QPushButton#StatusBarMenuButton:hover {
                color: white;
            }
        """)

    def update_menu_url(self, url):
        """Updates the URL action in the status bar menu."""
        url_str = url.toString()
        display_text = url_str if len(url_str) < 60 else url_str[:57] + "..."
        self.url_action.setText(display_text)
        self.url_action.setToolTip(url_str)

    def show_status_menu(self):
        """Shows the menu from the status bar button."""
        menu = QMenu(self)
        # Use the same style as the context menu for consistency
        menu.setStyleSheet("""            QMenu {
                background-color: rgba(43, 43, 43, 0.95);
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-weight: 700;
            }
            QMenu::item { padding: 8px 20px; margin: 0; border-radius: 6px; }
            QMenu::item:selected { background-color: #3F51B5; color: #ffffff; }
            QMenu::item:disabled { color: #777; }
            QMenu::separator { height: 1px; background: #444; margin: 8px 4px; }
        """)
        menu.addAction(self.url_action)
        menu.addSeparator()
        about_action = menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

        # Position the menu above the button, right-aligned
        button_pos = self.menu_button.mapToGlobal(QPoint(0, 0))
        menu_pos = QPoint(button_pos.x() - menu.sizeHint().width() + self.menu_button.width(), button_pos.y() - menu.sizeHint().height())
        menu.exec(menu_pos)

    def show_about_dialog(self):
        """Shows a simple about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>This is a site-specific browser application created with the DiusnicX builder.</p>"
            f"<p><b>URL:</b> {self.browser.url().toString()}</p>"
        )

    def update_status_message(self, url: str):
        if url:
            display_text = url if len(url) < 100 else url[:97] + "..."
            self.status_label.setText(display_text)
        else:
            self.status_label.setText("Ready")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiteSpecificBrowser()
    window.show()
    sys.exit(app.exec())