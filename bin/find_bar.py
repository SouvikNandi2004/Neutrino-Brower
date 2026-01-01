from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from bin.utils import create_icon_from_svg, SVG_ICONS

class FindBar(QWidget):
    """A widget for the 'Find in Page' feature."""
    findNext = pyqtSignal(str)
    findPrevious = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("FindBar")
        self.setVisible(False)
        self.setMaximumHeight(0) # Start hidden and with 0 height

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find in page")
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_input.returnPressed.connect(self.on_find_next)
        layout.addWidget(self.search_input)

        self.results_label = QLabel("")
        layout.addWidget(self.results_label)

        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(create_icon_from_svg(SVG_ICONS['back'], self.theme['ICON_COLOR']))
        self.prev_btn.setToolTip("Find Previous")
        self.prev_btn.clicked.connect(self.on_find_previous)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton()
        self.next_btn.setIcon(create_icon_from_svg(SVG_ICONS['forward'], self.theme['ICON_COLOR']))
        self.next_btn.setToolTip("Find Next")
        self.next_btn.clicked.connect(self.on_find_next)
        layout.addWidget(self.next_btn)

        self.close_btn = QPushButton()
        self.close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], self.theme['ICON_COLOR']))
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.hide_and_clear)
        layout.addWidget(self.close_btn)

        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        accent_color = self.parent().ACCENT_COLOR if self.parent() else "#4a90e2"
        self.setStyleSheet(f"""
            #FindBar {{
                background-color: {self.theme['TOOLBAR_COLOR']};
                border-top: 1px solid {self.theme['BORDER_COLOR']};
            }}
            #FindBar QLineEdit {{
                background-color: {self.theme['URL_BAR_BG']};
                color: {self.theme['TEXT_COLOR']};
                border: 1px solid {self.theme['BORDER_COLOR']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            #FindBar QLineEdit:focus {{
                border-color: {accent_color};
            }}
            #FindBar QLabel {{
                color: {self.theme['TAB_TEXT_COLOR']};
                font-size: 12px;
            }}
            #FindBar QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            #FindBar QPushButton:hover {{
                background-color: {self.theme['BUTTON_HOVER_COLOR']};
            }}
        """)

    def on_text_changed(self, text):
        self.findNext.emit(text)

    def on_find_next(self):
        self.findNext.emit(self.search_input.text())

    def on_find_previous(self):
        self.findPrevious.emit(self.search_input.text())

    def update_results(self, active_match, total_matches):
        if self.search_input.text():
            self.results_label.setText(f"{active_match + 1} of {total_matches}" if total_matches > 0 else "0 of 0")
        else:
            self.results_label.setText("")

    def show_bar(self):
        if self.isHidden():
            self.setVisible(True)
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.sizeHint().height())
            self.animation.start()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_and_clear(self):
        if self.isVisible():
            self.animation.setStartValue(self.height())
            self.animation.setEndValue(0)
            # Connect to finished signal to hide widget after animation
            self.animation.finished.connect(self._on_hide_finished)
            self.animation.start()

    def _on_hide_finished(self):
        try: self.animation.finished.disconnect(self._on_hide_finished)
        except RuntimeError: pass
        self.setVisible(False)
        self.search_input.clear()
        self.closed.emit()