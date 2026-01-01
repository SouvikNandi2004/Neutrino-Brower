# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QProgressBar, QMessageBox,
    QPushButton, QScrollArea, QFrame, QFileDialog, QStackedWidget
) # type: ignore
from PyQt6.QtCore import Qt, QSize, QSettings, QStandardPaths, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from bin.utils import create_icon_from_svg, SVG_ICONS, CustomMessageBox

def format_bytes(size):
    """Formats bytes into KB, MB, GB, etc."""
    if size == -1:
        return ""
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < len(power_labels):
        size /= power
        n += 1
    return f"{size:.1f} {power_labels[n]}"

class DownloadItemWidget(QFrame):
    remove_requested = pyqtSignal(object)
    download_finished = pyqtSignal(dict)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setObjectName("DownloadItemWidget")
        self.download_item = None
        self.download_path = None

        # Internal state for progress tracking
        self._bytes_received = 0
        self._bytes_total = -1
        # Add speed tracking variables
        self._speed = 0
        self._last_speed_update_time = None
        self._last_speed_update_bytes = 0
        self._speed_calc_timer = QTimer(self)
        self._speed_calc_timer.setInterval(1000) # 1 second
        self._speed_calc_timer.timeout.connect(self._calculate_speed)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # Icon
        theme = self.main_window.theme
        self.icon_label = QLabel()
        self.icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['file_icon'], theme['ICON_COLOR'], QSize(40, 40)).pixmap(QSize(40, 40)))
        main_layout.addWidget(self.icon_label)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.filename_label = QLabel("Waiting for filename...")
        self.filename_label.setObjectName("FilenameLabel")
        info_layout.addWidget(self.filename_label)

        # Progress layout (bar + status text)
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.status_label = QLabel("Starting...")
        self.status_label.setObjectName("StatusLabel")
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.status_label)
        info_layout.addLayout(progress_layout)
        
        main_layout.addLayout(info_layout, 1)

        # Buttons section
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.pause_resume_btn = QPushButton()
        self.pause_resume_btn.setToolTip("Pause")
        self.pause_resume_btn.setIcon(create_icon_from_svg(SVG_ICONS['download_pause'], theme['ICON_COLOR']))
        self.pause_resume_btn.clicked.connect(self.toggle_pause)

        self.cancel_btn = QPushButton()
        self.cancel_btn.setToolTip("Cancel")
        self.cancel_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))
        self.cancel_btn.clicked.connect(self.cancel_or_remove)

        self.open_folder_btn = QPushButton()
        self.open_folder_btn.setToolTip("Open containing folder")
        self.open_folder_btn.setIcon(create_icon_from_svg(SVG_ICONS['open_folder'], theme['ICON_COLOR']))
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.open_folder_btn.setVisible(False)

        buttons_layout.addWidget(self.pause_resume_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.open_folder_btn)
        main_layout.addLayout(buttons_layout)

    def set_live_download(self, download_item: QWebEngineDownloadRequest):
        self.download_item = download_item
        self.download_path = os.path.join(download_item.downloadDirectory(), download_item.downloadFileName())

        self.filename_label.setText(os.path.basename(download_item.downloadFileName()) or "Waiting for filename...")
        self.status_label.setText("Starting...")

        # Reset speed tracking and start timer
        self._speed = 0
        self._last_speed_update_time = datetime.now()
        self._last_speed_update_bytes = 0
        self._speed_calc_timer.start()

        # Connect signals
        self.download_item.receivedBytesChanged.connect(self._on_received_changed)
        self.download_item.totalBytesChanged.connect(self._on_total_changed)
        self.download_item.stateChanged.connect(self.update_state)

    def set_historical_download(self, historical_data):
        # historical_data is a tuple: (url, path, filename, total_bytes, state, end_time)
        url, path, filename, total_bytes, state, end_time = historical_data
        self.download_path = path

        self.filename_label.setText(filename)
        self.status_label.setText(f"{state} - {format_bytes(total_bytes)}")
        self.progress_bar.setValue(100 if state == "Completed" else 0)
        self.pause_resume_btn.setVisible(False)

        theme = self.main_window.theme
        self.cancel_btn.setToolTip("Remove from list")
        self.cancel_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))

        if state == "Completed":
            self.open_folder_btn.setVisible(True)
            self.open_folder_btn.setIcon(create_icon_from_svg(SVG_ICONS['open_folder'], self.main_window.ACCENT_COLOR))
            self.icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['downloads'], self.main_window.SECURE_COLOR, QSize(40, 40)).pixmap(QSize(40, 40)))
        else: # Cancelled or Interrupted
            self.open_folder_btn.setVisible(False)
            self.icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['close'], self.main_window.DANGER_COLOR, QSize(40, 40)).pixmap(QSize(40, 40)))

    def cancel_or_remove(self):
        """Cancels an active download or requests removal for a finished one."""
        if self.download_item and self.download_item.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
            self.download_item.cancel()
        else:
            self.remove_requested.emit(self)

    def toggle_pause(self):
        if self.download_item:
            if self.download_item.isPaused():
                self.download_item.resume()
            else:
                self.download_item.pause()

    def open_folder(self):
        path_to_open = ""
        if self.download_item: # Live download
            path_to_open = self.download_item.downloadDirectory()
        elif self.download_path: # Historical download
            # For a file, we want to open its containing directory
            path_to_open = os.path.dirname(self.download_path)

        if path_to_open and os.path.exists(path_to_open):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path_to_open))

    def _on_received_changed(self):
        self._bytes_received = self.download_item.receivedBytes()
        self._update_progress_display()

    def _on_total_changed(self):
        self._bytes_total = self.download_item.totalBytes()
        self._update_progress_display()

    def _calculate_speed(self):
        """Calculates download speed once per second."""
        if not self.download_item or self.download_item.isPaused() or not self._last_speed_update_time:
            self._speed = 0
        else:
            now = datetime.now()
            time_delta = (now - self._last_speed_update_time).total_seconds()
            if time_delta > 0:
                bytes_delta = self._bytes_received - self._last_speed_update_bytes
                self._speed = bytes_delta / time_delta
            
            self._last_speed_update_time = now
            self._last_speed_update_bytes = self._bytes_received
        
        # Update the display with the new speed
        self._update_progress_display()

    def _update_progress_display(self):
        if self.download_item and self.download_item.isPaused():
            self.status_label.setText("Paused")
            return

        is_active = self.download_item is not None
        speed_str = f" ({format_bytes(self._speed)}/s)" if self._speed > 0 and is_active else ""

        if self._bytes_total <= 0:
            self.progress_bar.setRange(0, 0) # Indeterminate
            self.status_label.setText(f"{format_bytes(self._bytes_received)} downloaded{speed_str}")
        else:
            self.progress_bar.setRange(0, 100)
            progress = int((self._bytes_received / self._bytes_total) * 100) if self._bytes_total > 0 else 0
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"{format_bytes(self._bytes_received)} / {format_bytes(self._bytes_total)}{speed_str}")

    def update_state(self, state):
        if not self.download_item:
            return

        theme = self.main_window.theme
        if state == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
            # The filename is guaranteed to be available now.
            self.filename_label.setText(os.path.basename(self.download_item.downloadFileName()))
            
            # Set cancel button to danger color during active download
            self.cancel_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], self.main_window.DANGER_COLOR))
            self.cancel_btn.setToolTip("Cancel")

            # A download in progress can be paused. Check for it.
            if self.download_item.isPaused():
                self.pause_resume_btn.setToolTip("Resume")
                self.pause_resume_btn.setIcon(create_icon_from_svg(SVG_ICONS['download_resume'], theme['ICON_COLOR']))
                self._update_progress_display() # This will set the label to "Paused"
            else:
                # If resuming, reset the timer's reference points
                if not self._speed_calc_timer.isActive():
                    self._last_speed_update_time = datetime.now()
                    self._last_speed_update_bytes = self._bytes_received
                    self._speed_calc_timer.start()

                self._update_progress_display() # Show normal progress
                self.pause_resume_btn.setToolTip("Pause")
                self.pause_resume_btn.setIcon(create_icon_from_svg(SVG_ICONS['download_pause'], theme['ICON_COLOR']))

        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self._speed_calc_timer.stop()
            self.status_label.setText("Completed")
            self.progress_bar.setRange(0, 100) # Ensure determinate state
            self.progress_bar.setValue(100)
            self.pause_resume_btn.setVisible(False)

            # Cancel button is now a "remove" button, use standard color
            self.cancel_btn.setToolTip("Remove from list")
            self.cancel_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))

            self.open_folder_btn.setVisible(True)
            # Make open folder button use accent color for emphasis
            self.open_folder_btn.setIcon(create_icon_from_svg(SVG_ICONS['open_folder'], self.main_window.ACCENT_COLOR))

            self.icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['downloads'], self.main_window.SECURE_COLOR, QSize(40, 40)).pixmap(QSize(40, 40)))

        elif state in [QWebEngineDownloadRequest.DownloadState.DownloadCancelled, QWebEngineDownloadRequest.DownloadState.DownloadInterrupted]:
            self._speed_calc_timer.stop()
            self.status_label.setText("Cancelled" if state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled else "Interrupted")
            self.pause_resume_btn.setVisible(False)
            # Cancel button is now a "remove" button, use standard color
            self.cancel_btn.setToolTip("Remove from list")
            self.cancel_btn.setIcon(create_icon_from_svg(SVG_ICONS['close'], theme['ICON_COLOR']))
            self.icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['close'], self.main_window.DANGER_COLOR, QSize(40, 40)).pixmap(QSize(40, 40)))
        
        # If the download is finished, emit a signal to save it to the database
        if state in [QWebEngineDownloadRequest.DownloadState.DownloadCompleted, QWebEngineDownloadRequest.DownloadState.DownloadCancelled, QWebEngineDownloadRequest.DownloadState.DownloadInterrupted]:
            self._speed_calc_timer.stop()
            state_map = {
                QWebEngineDownloadRequest.DownloadState.DownloadCompleted: "Completed",
                QWebEngineDownloadRequest.DownloadState.DownloadCancelled: "Cancelled",
                QWebEngineDownloadRequest.DownloadState.DownloadInterrupted: "Interrupted"
            }
            finished_data = {
                'url': self.download_item.url().toString(),
                'path': os.path.join(self.download_item.downloadDirectory(), self.download_item.downloadFileName()),
                'filename': self.download_item.downloadFileName(),
                'total_bytes': self.download_item.totalBytes(),
                'state': state_map[state],
                'end_time': datetime.now()
            }
            self.download_finished.emit(finished_data)

            # Disconnect signals to prevent further updates for this item
            try:
                self.download_item.receivedBytesChanged.disconnect()
                self.download_item.totalBytesChanged.disconnect()
                self.download_item.stateChanged.disconnect()
            except RuntimeError:
                pass # Signals might already be disconnected if the object is destroyed
            self.download_item = None # It's no longer a "live" item

class DownloadManagerPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setObjectName("DownloadManagerPage")
        self.history_manager = self.main_window.history_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        header = QWidget()
        header.setObjectName("DownloadsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        title_label = QLabel("Downloads")
        title_label.setObjectName("PageTitle")
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setObjectName("DangerButton")
        clear_all_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_all_btn)
        main_layout.addWidget(header)

        # --- "No Downloads" View ---
        self.no_downloads_widget = QWidget()
        self.no_downloads_widget.setObjectName("NoDownloadsView")
        no_downloads_layout = QVBoxLayout(self.no_downloads_widget)
        no_downloads_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_downloads_layout.setSpacing(15)
        
        no_downloads_icon = QLabel()
        no_downloads_icon.setObjectName("NoDownloadsIcon")
        no_downloads_layout.addWidget(no_downloads_icon, 0, Qt.AlignmentFlag.AlignCenter)

        no_downloads_label = QLabel("No downloads yet")
        no_downloads_label.setObjectName("NoDownloadsLabel")
        no_downloads_layout.addWidget(no_downloads_label, 0, Qt.AlignmentFlag.AlignCenter)

        no_downloads_sub_label = QLabel("Files you download will appear here.")
        no_downloads_sub_label.setObjectName("NoDownloadsSubLabel")
        no_downloads_layout.addWidget(no_downloads_sub_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # --- Scroll Area for Downloads ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.viewport().setObjectName("DownloadScrollViewport")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("ScrollContentWidget")
        self.downloads_layout = QVBoxLayout(self.content_widget)
        self.downloads_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.downloads_layout.setSpacing(10)
        self.downloads_layout.setContentsMargins(15, 10, 15, 10) # Adjusted in stylesheet
        
        self.scroll_area.setWidget(self.content_widget)

        # Use a stacked widget to easily switch between views
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.scroll_area)
        self.stacked_widget.addWidget(self.no_downloads_widget)
        
        main_layout.addWidget(self.stacked_widget, 1)
        
        self.load_historical_downloads()
        self.apply_stylesheet()
        self._update_view()

    def load_historical_downloads(self):
        """Loads finished downloads from the database."""
        historical_items = self.history_manager.get_all_downloads()
        for item_data in historical_items:
            widget = DownloadItemWidget(self.main_window, self)
            widget.set_historical_download(item_data)
            widget.remove_requested.connect(self.remove_download_widget)
            self.downloads_layout.addWidget(widget)

    def _update_view(self):
        """Shows the download list or the 'no downloads' message."""
        if self.downloads_layout.count() > 0:
            self.stacked_widget.setCurrentWidget(self.scroll_area)
        else:
            self.stacked_widget.setCurrentWidget(self.no_downloads_widget)
            # Set the icon for the empty view
            icon_label = self.no_downloads_widget.findChild(QLabel, "NoDownloadsIcon")
            if icon_label:
                theme = self.main_window.theme
                icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['downloads'], theme['TAB_TEXT_COLOR'], QSize(64, 64)).pixmap(QSize(64, 64)))
            
    def add_download(self, download_item: QWebEngineDownloadRequest):
        # Configure the download path first.
        settings = QSettings("DisunicX", "Browser")
        default_path = settings.value("download_path", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation))
        
        if not settings.value("ask_save_location", True, type=bool):
            save_path = os.path.join(default_path, download_item.suggestedFileName())
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download_item.setDownloadDirectory(os.path.dirname(save_path))
            download_item.setDownloadFileName(os.path.basename(save_path))
            download_item.accept()
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", os.path.join(default_path, download_item.suggestedFileName()))
            if path:
                download_item.setDownloadDirectory(os.path.dirname(path))
                download_item.setDownloadFileName(os.path.basename(path))
                download_item.accept()
            else:
                # User cancelled the file dialog.
                download_item.cancel()
                return # Do not create a widget.

        # If we reach here, the download was accepted. Now create the widget.
        widget = DownloadItemWidget(self.main_window, self)
        widget.set_live_download(download_item)
        widget.remove_requested.connect(self.remove_download_widget)
        widget.download_finished.connect(self.persist_download)
        self.downloads_layout.insertWidget(0, widget)
        self._update_view()

    def persist_download(self, data):
        """Saves the finished download info to the database."""
        self.history_manager.add_finished_download(data)

    def has_active_downloads(self):
        """Checks if there are any downloads currently in progress."""
        for i in range(self.downloads_layout.count()):
            item = self.downloads_layout.itemAt(i)
            widget = item.widget()
            if widget and widget.download_item:
                if widget.download_item.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
                    return True
        return False

    def cancel_active_downloads(self):
        """Cancels any downloads that are currently in progress."""
        for i in range(self.downloads_layout.count()):
            item = self.downloads_layout.itemAt(i)
            widget = item.widget()
            if widget and widget.download_item:
                if widget.download_item.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
                    widget.download_item.cancel()

    def remove_download_widget(self, widget: DownloadItemWidget):
        """Removes a specific download widget from the list."""
        if widget.download_path:
            self.history_manager.remove_download(widget.download_path)

        self.downloads_layout.removeWidget(widget)
        widget.deleteLater()
        self._update_view()

    def clear_all(self):
        """Prompts the user and then removes all download items from the list."""
        if self.downloads_layout.count() == 0:
            return

        reply = CustomMessageBox.question(
            self,
            "Clear All Downloads",
            "Are you sure you want to clear the entire download list? This will cancel any active downloads and cannot be undone.",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_all_downloads()
            while self.downloads_layout.count() > 0:
                item = self.downloads_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    # Cancel any active downloads before removing
                    if widget.download_item and widget.download_item.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
                        widget.download_item.cancel()
                    widget.deleteLater()
            self._update_view()

    def apply_stylesheet(self):
        theme = self.main_window.theme
        self.setStyleSheet(f"""
            #DownloadManagerPage {{
                background-color: {theme['BG_COLOR']};
            }}
            #DownloadsHeader {{
                background-color: {theme['BG_COLOR']};
                border-bottom: 1px solid {theme['BORDER_COLOR']};
            }}
            #PageTitle {{
                font-size: 24px;
                font-weight: 700; /* Bolder */
                color: {theme['TEXT_COLOR']};
            }}
            #DownloadsHeader QPushButton {{
                background-color: {theme['MSGBOX_BUTTON_BG']};
                border: 1px solid {theme['BORDER_COLOR']};
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 700;
                color: {theme['TEXT_COLOR']};
            }}
            #DownloadsHeader QPushButton:hover {{
                background-color: {theme['BUTTON_HOVER_COLOR']};
                border-color: {self.main_window.ACCENT_COLOR};
            }}
            #DownloadsHeader QPushButton#DangerButton {{
                background-color: {self.main_window.DANGER_COLOR};
                border-color: {self.main_window.DANGER_COLOR};
                color: white;
            }}
            #DownloadsHeader QPushButton#DangerButton:hover {{
                background-color: #c0392b; /* darker red hover */
                border-color: #c0392b;
            }}
            QScrollArea {{
                background-color: {theme['BG_COLOR']};
                border: none;
            }}
            /* This ensures the viewport and the content widget inside are transparent,
               preventing a default white background from showing. */
            #ScrollContentWidget {{
                background: transparent;
            }}            
            #NoDownloadsView {{
                background: transparent;
            }}
            #NoDownloadsLabel {{
                color: {theme['TEXT_COLOR']};
                font-size: 20px;
                font-weight: 700;
            }}
            #NoDownloadsSubLabel {{
                color: {theme['TAB_TEXT_COLOR']};
                font-size: 14px;
                font-weight: 700;
            }}
            #NoDownloadsIcon {{
                margin-bottom: 10px;
            }}
            #DownloadItemWidget {{
                background-color: {theme['TOOLBAR_COLOR']};
                border-radius: 12px; /* Larger radius */
                border: 1px solid {theme['BORDER_COLOR']};
            }}
            #FilenameLabel {{
                font-size: 14px;
                font-weight: 700; /* Bolder */
                color: {theme['TEXT_COLOR']};
            }}
            #StatusLabel {{
                font-size: 12px;
                color: {theme['TAB_TEXT_COLOR']};
            }}
            QProgressBar {{
                border: none;
                background-color: {theme['BORDER_COLOR']};
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.main_window.ACCENT_COLOR};
                border-radius: 4px;
            }}
            #DownloadItemWidget QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 14px; /* circular */
                padding: 6px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }}
            #DownloadItemWidget QPushButton:hover {{
                background-color: {theme['BUTTON_HOVER_COLOR']};
            }}
            /* Custom Scrollbar */
            QScrollArea {{
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['BORDER_COLOR']};
                min-height: 20px;
                border-radius: 6px;
            }}
        """)
