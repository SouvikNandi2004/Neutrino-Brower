from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QMenu, QFrame
from PyQt6.QtCore import QSize, pyqtSignal, Qt, QEvent, QMimeData, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QDrag
from bin.utils import create_icon_from_svg, SVG_ICONS, base64_to_qicon
from PyQt6.QtWidgets import QApplication

class BookmarksBar(QToolBar):
    """A toolbar to display saved bookmarks."""
    bookmarkClicked = pyqtSignal(str) # emits URL
    removeBookmarkRequested = pyqtSignal(str) # emits URL
    bookmarksReordered = pyqtSignal(list) # emits new list of URLs in order

    def __init__(self, theme, parent=None):
        super().__init__("BookmarksBar", parent)
        self.theme = theme
        self.main_window = parent # Store a direct reference to the main window
        self.setAcceptDrops(True)
        self._dragged_button = None
        self._drag_start_pos = None

        self.setVisible(False)
        self.setMaximumHeight(0)
        self._animation = QPropertyAnimation(self, b"maximumHeight")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))

        # --- Drop Indicator ---
        self._drop_indicator = QFrame(self)
        self._drop_indicator.setObjectName("DropIndicator")
        self._drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self._drop_indicator.hide()

        self.apply_stylesheet()

    def show_animated(self):
        if self.isHidden():
            self.setVisible(True)
            self._animation.setStartValue(0)
            self._animation.setEndValue(self.sizeHint().height())
            self._animation.start()

    def hide_animated(self):
        if self.isVisible():
            self._animation.setStartValue(self.height())
            self._animation.setEndValue(0)
            self._animation.finished.connect(self._on_hide_finished)
            self._animation.start()

    def _on_hide_finished(self):
        try: self._animation.finished.disconnect(self._on_hide_finished)
        except RuntimeError: pass
        self.setVisible(False)

    def apply_stylesheet(self):
        accent_color = self.parent().ACCENT_COLOR if self.parent() else "#4a90e2"
        self.setStyleSheet(f"""
            QToolBar#BookmarksBar {{
                background-color: rgba(0, 0, 0, 0.1); /* Subtle dark background */
                border-top: 1px solid {self.theme['BORDER_COLOR']};
                border-bottom: 1px solid {self.theme['BORDER_COLOR']};
                padding: 2px 8px;
                spacing: 4px;
            }}
            #BookmarksBar QPushButton {{
                background-color: transparent;
                color: {self.theme["TEXT_COLOR"]};
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 700;
                text-align: left;
                max-width: 150px; /* Reduced for a more compact look */
            }}
            #BookmarksBar QPushButton:hover {{
                background-color: {self.theme["BUTTON_HOVER_COLOR"]};
                color: {self.theme['TAB_TEXT_SELECTED_COLOR']};
            }}
            #BookmarksBar QPushButton:pressed {{
                background-color: {self.theme["BUTTON_PRESSED_COLOR"]};
            }}
            QFrame#DropIndicator {{
                background-color: {accent_color};
                width: 2px;
            }}
        """)

    def populate_bookmarks(self, bookmarks):
        self.clear()
        for title, url, date_added, icon_data in bookmarks:
            btn = QPushButton()
            btn.setToolTip(f"{title}\n{url}")
            btn.setText(title)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.setProperty("url", url) # Store URL for easy access
            btn.customContextMenuRequested.connect(lambda pos, u=url, b=btn: self.show_context_menu(pos, u, b))

            if icon_data:
                btn.setIcon(base64_to_qicon(icon_data))
            else:
                # Use the dimmer icon color to match the text
                btn.setIcon(create_icon_from_svg(SVG_ICONS['bookmark_outline'], self.theme['TAB_TEXT_COLOR']))

            btn.installEventFilter(self)
            btn.clicked.connect(lambda checked, u=url: self.bookmarkClicked.emit(u))
            self.addWidget(btn)

    def show_context_menu(self, pos, url, button):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup) # type: ignore
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.theme['MENU_BG_COLOR']};
                color: {self.theme['TEXT_COLOR']};
                border: 1px solid {self.theme['BORDER_COLOR']};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            QMenu::item {{
                padding: 8px 20px;
                margin: 0;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {self.main_window.ACCENT_COLOR};
                color: #ffffff;
            }}
        """)
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(lambda: self.removeBookmarkRequested.emit(url))
        menu.addAction(remove_action)
        menu.exec(button.mapToGlobal(pos))

    def eventFilter(self, watched, event):
        if not isinstance(watched, QPushButton) or watched.parent() is not self:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._dragged_button = watched
                self._drag_start_pos = event.globalPosition()

        elif event.type() == QEvent.Type.MouseMove:
            if event.buttons() & Qt.MouseButton.LeftButton and self._dragged_button:
                if (event.globalPosition() - self._drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                    drag = QDrag(self)
                    mime_data = QMimeData()
                    mime_data.setData("application/x-disunicx-bookmark-url", self._dragged_button.property("url").encode())
                    drag.setMimeData(mime_data)
                    
                    pixmap = self._dragged_button.grab()
                    drag.setPixmap(pixmap)
                    drag.setHotSpot(self._dragged_button.mapFromGlobal(event.globalPosition().toPoint()))

                    self._dragged_button.hide()
                    
                    # Execute the drag. If the drop is successful, dropEvent will handle
                    # moving the button. If it's cancelled, we need to show it again.
                    if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.IgnoreAction and self._dragged_button:
                        self._dragged_button.show()
                    
                    self._dragged_button = None
                    self._drag_start_pos = None
                    return True

        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._dragged_button = None
            self._drag_start_pos = None
        
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-disunicx-bookmark-url"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat("application/x-disunicx-bookmark-url"):
            event.ignore()
            return

        target_action = self.actionAt(event.position().toPoint())
        
        if target_action:
            target_widget = self.widgetForAction(target_action)
            # Position indicator to the left of the target widget, centered vertically
            self._drop_indicator.move(target_widget.pos().x(), (self.height() - target_widget.height()) // 2)
            self._drop_indicator.setFixedHeight(target_widget.height())
            self._drop_indicator.show()
        else:
            # We are at the end. Find the last visible widget.
            last_visible_widget = None
            for action in reversed(self.actions()):
                widget = self.widgetForAction(action)
                if widget and widget.isVisible():
                    last_visible_widget = widget
                    break
            
            if last_visible_widget:
                # Position indicator to the right of the last widget
                self._drop_indicator.move(last_visible_widget.pos().x() + last_visible_widget.width(), (self.height() - last_visible_widget.height()) // 2)
                self._drop_indicator.setFixedHeight(last_visible_widget.height())
                self._drop_indicator.show()
            else:
                # Bar is empty or all items are hidden.
                self._drop_indicator.hide()
                
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drop_indicator.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._drop_indicator.hide()
        if not event.mimeData().hasFormat("application/x-disunicx-bookmark-url"):
            event.ignore()
            return

        url = event.mimeData().data("application/x-disunicx-bookmark-url").data().decode()
        source_button = None
        for child in self.findChildren(QPushButton):
            if child.property("url") == url:
                source_button = child
                break
        
        if not source_button:
            event.ignore()
            return

        target_action = self.actionAt(event.position().toPoint())
        
        source_action = None
        for action in self.actions():
            if self.widgetForAction(action) == source_button:
                source_action = action
                break
        
        if source_action:
            self.removeAction(source_action)
            self.insertWidget(target_action, source_button)
        
        source_button.show()
        event.acceptProposedAction()

        new_order = []
        for action in self.actions():
            widget = self.widgetForAction(action)
            if isinstance(widget, QPushButton) and widget.property("url"):
                new_order.append(widget.property("url"))
        
        self.bookmarksReordered.emit(new_order)