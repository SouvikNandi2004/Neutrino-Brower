# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
from bin.utils import create_icon_from_svg, SVG_ICONS
from PyQt6.QtWidgets import QWidget, QScrollArea, QGridLayout, QLabel, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QGraphicsDropShadowEffect, QLineEdit
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QDrag

class TabThumbnail(QWidget):
    """A widget to display a single tab's thumbnail, title, and close button."""
    tab_selected = pyqtSignal(int)
    tab_closed = pyqtSignal(int)
    title_changed = pyqtSignal(int, str)

    def __init__(self, index, title, pixmap, theme, parent=None):
        super().__init__(parent)
        self.index = index
        self.theme = theme
        self.setFixedSize(280, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._drag_start_pos = None

        # Add a shadow effect for a floating appearance
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Header (Title + Close Button) ---
        header = QWidget()
        header.setFixedHeight(35)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 5, 0)
        
        self.title_edit = QLineEdit(title)
        self.title_edit.setObjectName("ThumbnailTitle")
        self.title_edit.setReadOnly(True)
        self.title_edit.editingFinished.connect(self._on_title_edited)
        self.title_edit.setCursor(Qt.CursorShape.PointingHandCursor)

        self.close_btn = QPushButton()
        self.close_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], self.theme['TAB_TEXT_COLOR']))
        self.close_btn.setObjectName("ThumbnailCloseBtn")
        self.close_btn.clicked.connect(self._on_close)
        
        header_layout.addWidget(self.title_edit)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)

        # --- Thumbnail Image ---
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Scale pixmap to fit, keeping aspect ratio, and add padding
        scaled_pixmap = pixmap.scaled(280, 165, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.thumbnail_label.setPixmap(scaled_pixmap)

        layout.addWidget(header)
        layout.addWidget(self.thumbnail_label, 1)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        self.setStyleSheet(f"""
            TabThumbnail {{
                background-color: {self.theme['TOOLBAR_COLOR']};
                border-radius: 8px;
                border: 1px solid {self.theme['BORDER_COLOR']};
            }}
            TabThumbnail:hover {{
                border: 1px solid {self.parent().parent().parent().ACCENT_COLOR if self.parent() else self.theme['BORDER_COLOR']};
            }}
            #ThumbnailTitle {{
                color: {self.theme['TEXT_COLOR']};
                font-weight: 700;
                background: transparent;
                border: 1px solid transparent;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            #ThumbnailTitle:!read-only {{
                background: {self.theme['URL_BAR_BG']};
                border: 1px solid {self.theme['URL_BAR_BORDER']};
            }}
            #ThumbnailCloseBtn {{
                background: transparent;
                color: {self.theme['TAB_TEXT_COLOR']};
                border: none;
                border-radius: 12px; /* circular */
                padding: 4px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }}
            #ThumbnailCloseBtn:hover {{
                background-color: {self.theme['DANGER_COLOR']};
                color: white;
            }}
        """)

    def mouseDoubleClickEvent(self, event):
        # Check if the double-click is on the title edit area
        if self.title_edit.geometry().contains(event.pos()):
            self.title_edit.setReadOnly(False)
            self.title_edit.setFocus()
            self.title_edit.selectAll()
        else:
            super().mouseDoubleClickEvent(event)

    def _on_title_edited(self):
        self.title_edit.setReadOnly(True)
        self.title_changed.emit(self.index, self.title_edit.text())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self._drag_start_pos or (event.position().toPoint() - self._drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        # Use a custom mime type to identify our drag operation
        mime_data.setData("application/x-disunicx-tab-index", str(self.index).encode())
        drag.setMimeData(mime_data)

        # Create a semi-transparent pixmap for the drag visual
        pixmap = self.grab()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 180))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())

        # --- Alternative Method: Zombie Widget ---
        # Create a placeholder widget to take the place of the dragged item.
        # This "zombie" widget will be the one deleted during a repopulation,
        # preventing the original widget from being deleted while its method is still on the call stack.
        zombie_widget = QWidget()
        parent_overview = self.parent().parent() # TabThumbnail -> grid_container -> TabOverview
        if isinstance(parent_overview, TabOverview):
            # Find the position of the current widget in the grid
            idx = parent_overview.grid_layout.indexOf(self)
            row, col, _, _ = parent_overview.grid_layout.getItemPosition(idx)
            
            # Replace the original widget with the zombie
            parent_overview.grid_layout.takeAt(idx)
            parent_overview.grid_layout.addWidget(zombie_widget, row, col)
            self.hide()

            if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.IgnoreAction:
                # If drag was cancelled, put the original widget back and show it.
                parent_overview.grid_layout.replaceWidget(zombie_widget, self)
                self.show()
            zombie_widget.deleteLater()

    def mouseReleaseEvent(self, event):
        # Emit signal only if the close button wasn't the source
        if not self.close_btn.underMouse():
            self.tab_selected.emit(self.index)
        super().mouseReleaseEvent(event)
        
    def _on_close(self):
        self.tab_closed.emit(self.index)

class TabOverview(QWidget):
    """A grid view of all open tabs, similar to Safari's tab overview."""
    tab_selected = pyqtSignal(int)
    tab_closed = pyqtSignal(int)
    overview_closed = pyqtSignal()
    new_tab_requested = pyqtSignal()
    title_changed = pyqtSignal(int, str)
    close_all_tabs_requested = pyqtSignal()
    tabs_reordered = pyqtSignal(int, int) # from_index, to_index

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("TabOverview")
        self.setVisible(False)

        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Toolbar ---
        toolbar = QFrame()
        toolbar.setObjectName("OverviewToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 8, 20, 8)
        toolbar_layout.setSpacing(10)

        new_tab_btn = QPushButton()
        new_tab_btn.setIcon(create_icon_from_svg(SVG_ICONS['new_tab'], self.theme['ICON_COLOR']))
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.setObjectName("NewTabOverviewBtn")
        new_tab_btn.clicked.connect(self.new_tab_requested)
        toolbar_layout.addWidget(new_tab_btn)

        title_label = QLabel("Tabs")
        title_label.setObjectName("OverviewTitle")
        toolbar_layout.addWidget(title_label, 1, Qt.AlignmentFlag.AlignCenter)

        close_all_btn = QPushButton()
        close_all_btn.setIcon(create_icon_from_svg(SVG_ICONS['clear_data'], self.theme['DANGER_COLOR']))
        close_all_btn.setToolTip("Close All Tabs")
        close_all_btn.setObjectName("DangerButton")
        close_all_btn.clicked.connect(self.close_all_tabs_requested)
        toolbar_layout.addWidget(close_all_btn)

        close_btn = QPushButton("Done")
        close_btn.setObjectName("AccentButton")
        close_btn.clicked.connect(self.overview_closed)
        toolbar_layout.addWidget(close_btn)
        layout.addWidget(toolbar)

        # --- Scroll Area for Thumbnails ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setContentsMargins(50, 30, 50, 30)
        
        # --- Drop Indicator ---
        self._drop_indicator = QFrame(self.grid_container)
        self._drop_indicator.setObjectName("DropIndicator")
        self._drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self._drop_indicator.hide()

        scroll_area.setWidget(self.grid_container)
        layout.addWidget(scroll_area, 1)

        accent_color = self.parent().ACCENT_COLOR if self.parent() else '#3F51B5'
        self.setStyleSheet(f"""
            #TabOverview {{ 
                background-color: {self.theme['BG_COLOR']};
                background-image: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 1.5,
                    fx: 0.5, fy: 0.5,
                    stop: 0 {self.theme['TOOLBAR_COLOR']}, stop: 1 {self.theme['BG_COLOR']}
                );
            }}
            #OverviewTitle {{
                font-size: 18px;
                font-weight: 700;
            }}
            #OverviewToolbar {{ 
                background-color: transparent;
                border-bottom: 1px solid {self.theme['BORDER_COLOR']};
                padding: 8px 20px;
            }}
            #OverviewToolbar QPushButton {{
                background-color: {self.theme['MSGBOX_BUTTON_BG']};
                border: 1px solid {self.theme['BORDER_COLOR']};
                border-radius: 6px;
                font-weight: 700;
                color: {self.theme['TEXT_COLOR']};
                padding: 8px 16px;
            }}
            #OverviewToolbar QPushButton:hover {{
                background-color: {self.theme['BUTTON_HOVER_COLOR']};
                border-color: {accent_color};
            }}
            #OverviewToolbar QPushButton#AccentButton {{
                background-color: {accent_color};
                border-color: {accent_color};
                color: white;
            }}
            #OverviewToolbar QPushButton#AccentButton:hover {{
                background-color: {QColor(accent_color).lighter(115).name()};
            }}
            #OverviewToolbar QPushButton#DangerButton {{
                background-color: transparent;
                border: none;
                padding: 8px; /* Icon only */
            }}
            #OverviewToolbar QPushButton#DangerButton:hover {{
                background-color: {QColor(self.theme['DANGER_COLOR']).lighter(130).name()};
            }}
            #OverviewToolbar QPushButton#NewTabOverviewBtn {{
                background-color: transparent;
                border: none;
                padding: 8px; /* Icon only */
            }}
            #OverviewToolbar QPushButton#NewTabOverviewBtn:hover {{
                background-color: {self.theme['BUTTON_HOVER_COLOR']};
            }}

            QFrame#DropIndicator {{
                background-color: {accent_color};
                width: 4px;
            }}

            QScrollArea {{ border: none; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {self.theme['BORDER_COLOR']}; min-height: 20px; border-radius: 6px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def populate(self, tabs_data):
        # Clear existing thumbnails
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Populate with new thumbnails
        row, col = 0, 0
        for i, data in enumerate(tabs_data):
            thumbnail = TabThumbnail(data['index'], data['title'], data['pixmap'], self.theme)
            thumbnail.tab_selected.connect(self.tab_selected)
            thumbnail.tab_closed.connect(self.tab_closed)
            thumbnail.title_changed.connect(self.title_changed)
            self.grid_layout.addWidget(thumbnail, row, col)
            
            col += 1
            if col > 3: # 4 columns per row
                col = 0
                row += 1

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-disunicx-tab-index"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat("application/x-disunicx-tab-index"):
            event.ignore()
            return

        # Map the event position to the grid container's coordinates
        grid_pos = self.grid_container.mapFrom(self, event.position().toPoint())
        
        target_widget, _ = self._get_widget_at(grid_pos)
        
        if target_widget:
            # Position indicator to the left of the target widget
            self._drop_indicator.move(target_widget.pos().x() - 10, target_widget.pos().y())
            self._drop_indicator.setFixedHeight(target_widget.height())
            self._drop_indicator.show()
        else:
            self._drop_indicator.hide()
        
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drop_indicator.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._drop_indicator.hide()
        if not event.mimeData().hasFormat("application/x-disunicx-tab-index"):
            event.ignore()
            return

        source_index = int(event.mimeData().data("application/x-disunicx-tab-index").data().decode())
        
        grid_pos = self.grid_container.mapFrom(self, event.position().toPoint())
        target_widget, target_index = self._get_widget_at(grid_pos)

        if target_widget and source_index != target_index:
            self.tabs_reordered.emit(source_index, target_index)
        
        event.acceptProposedAction()

    def _get_widget_at(self, pos: QPoint):
        """Finds the widget and its layout index at a given position."""
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget and widget.geometry().contains(pos):
                return widget, widget.index
        return None, -1