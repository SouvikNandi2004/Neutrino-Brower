# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import os
import json
import sys
import subprocess
import tempfile
import shutil
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QGridLayout, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QLabel, QStackedWidget, QTabWidget,
    QFileDialog, QScrollArea, QApplication
)
from PyQt6.QtCore import (
    Qt, QStandardPaths, QSize, pyqtSignal, QThread, QObject
)
from PyQt6.QtGui import QIcon
from bin.utils import SVG_ICONS, create_icon_from_svg, DraggableFramelessDialog, CustomMessageBox

class SSB_BuilderWorker(QObject):
    """Worker object to run the DiusnicX builder (PyInstaller) in a separate thread."""
    finished = pyqtSignal(int, str)
    log_message = pyqtSignal(str)
    
    def __init__(self, cmd, cwd):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd

    def run(self):
        """Executes the PyInstaller command."""
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            process = subprocess.Popen(
                self.cmd, 
                cwd=self.cwd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, 
                encoding='utf-8', 
                errors='ignore', 
                creationflags=creationflags,
                bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                self.log_message.emit(line.strip())
            process.stdout.close()
            return_code = process.wait()
            self.finished.emit(return_code, "See build log for details.")
        except Exception as e:
            self.log_message.emit(f"Build failed with an exception: {e}")
            self.finished.emit(1, str(e))

class BuildProgressDialog(DraggableFramelessDialog):
    """A custom dialog to show build progress with a terminal-like output."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window
        self.setMinimumSize(700, 500)
        self._is_closable = False
        self.setWindowTitle("Build in Progress")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)

        self.title_label = QLabel("Building Application...")
        self.title_label.setObjectName("DialogTitleLabel")
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("LogOutput")
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("AccentButton")
        self.close_button.clicked.connect(self.accept)
        self.close_button.hide()

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.log_output, 1)
        container_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)
        
        self.content_layout.addWidget(container)
        self.apply_stylesheet()

    def on_build_finished(self, success):
        self._is_closable = True
        self.close_button.show()
        if success:
            self.title_label.setText("Build Successful!")
        else:
            self.title_label.setText("Build Failed!")

    def append_log(self, text):
        processed_text = text.replace("PyInstaller", "DiusnicX builder 1.0")
        if '<' in processed_text and '>' in processed_text:
            self.log_output.append(processed_text)
        else:
            color = "#e0e0e0"
            lower_text = processed_text.lower()
            if "info:" in lower_text: color = "#87ceeb"
            elif "warn:" in lower_text or "warning:" in lower_text: color = "#ffd700"
            elif "error:" in lower_text or "traceback" in lower_text or "failed" in lower_text: color = "#ff6347"
            elif "ok" in lower_text or "completed" in lower_text or "successful" in lower_text: color = "#98fb98"
            self.log_output.append(f'<font color="{color}">{processed_text}</font>')
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def apply_stylesheet(self):
        if not self.main_window: return
        theme = self.main_window.theme
        accent_color = self.main_window.ACCENT_COLOR
        self.shadow_container.setStyleSheet(f"""
            #ShadowContainer {{ background-color: {theme['BG_COLOR']}; border: 1px solid {theme['BORDER_COLOR']}; border-radius: 8px; }}
            #DialogTitleLabel {{ font-size: 18px; font-weight: 700; color: {theme['TEXT_COLOR']}; }}
            #LogOutput {{ background-color: #0c0c0c; color: #e0e0e0; font-family: "Consolas", "Courier New", monospace; border: 1px solid {theme['BORDER_COLOR']}; border-radius: 4px; font-size: 13px; padding: 5px; }}
            #LogOutput QScrollBar:vertical {{ border: none; background: #222; width: 12px; margin: 0; }}
            #LogOutput QScrollBar::handle:vertical {{ background: #555; min-height: 20px; border-radius: 6px; }}
            QPushButton#AccentButton {{ background-color: {accent_color}; color: white; border: none; padding: 8px 24px; border-radius: 6px; font-weight: 700; }}
            QPushButton#AccentButton:hover {{ background-color: #5aa1f2; }}
        """)
    
    def closeEvent(self, event):
        if self._is_closable:
            super().closeEvent(event)
        else:
            event.ignore()

class BuilderPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setObjectName("BuilderPage")
        self.init_ui()
        self.check_pyinstaller_and_update_ui()

    def init_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        self.ssb_stack = QStackedWidget()
        page_layout.addWidget(self.ssb_stack)

        # Page 1: The main builder UI with tabs
        self.ssb_stack.addWidget(self.create_builder_tabs())

        # Page 2: The "PyInstaller not found" message
        self.ssb_stack.addWidget(self.create_no_builder_view())

    def create_builder_tabs(self):
        tab_widget = QTabWidget()
        theme = self.main_window.theme
        accent_color = self.main_window.ACCENT_COLOR

        tab_widget.addTab(self.create_ssb_page(), "Site-Specific App")
        tab_widget.addTab(self.create_full_browser_page(), "Full Browser")

        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {theme['BG_COLOR']};
            }}
            QTabBar::tab {{
                background: transparent;
                color: {theme['TAB_TEXT_COLOR']};
                font-weight: 700;
                font-size: 14px;
                padding: 12px 25px;
                border: none;
                border-bottom: 3px solid transparent;
                min-width: 150px;
            }}
            QTabBar::tab:hover {{
                color: {theme['TEXT_COLOR']};
            }}
            QTabBar::tab:selected {{
                color: {accent_color};
                border-bottom: 3px solid {accent_color};
            }}
        """)
        return tab_widget

    def create_ssb_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        theme = self.main_window.theme
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: {theme['BG_COLOR']}; border: none; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {theme['BORDER_COLOR']}; min-height: 20px; border-radius: 6px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        content_widget = QWidget()
        content_widget.setObjectName("ScrollContentWidget")
        self.apply_builder_styles(content_widget)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(0)

        page_title = QLabel("Site-Specific App Builder")
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)

        self.ssb_name_edit = QLineEdit()
        self.ssb_name_edit.setPlaceholderText("e.g., My Web App")
        ssb_name_label = self.create_label_widget("Application Name", "The name of your standalone application.")
        layout.addWidget(self.create_setting_row(ssb_name_label, self.ssb_name_edit))

        self.ssb_url_edit = QLineEdit()
        self.ssb_url_edit.setPlaceholderText("https://example.com")
        ssb_url_label = self.create_label_widget("Website URL", "The full URL the application will open.")
        layout.addWidget(self.create_setting_row(ssb_url_label, self.ssb_url_edit))

        self.ssb_icon_path_edit = QLineEdit()
        self.ssb_icon_path_edit.setPlaceholderText("Optional: path to .ico file")
        self.ssb_icon_browse_btn = QPushButton("Browse...")
        self.ssb_icon_browse_btn.clicked.connect(self.select_ssb_icon)
        ssb_icon_label = self.create_label_widget("Application Icon", "Select a .ico file for your application's icon.")
        layout.addWidget(self.create_setting_row(ssb_icon_label, self.create_path_widget(self.ssb_icon_path_edit, self.ssb_icon_browse_btn)))

        ssb_build_btn = QPushButton("Build Application")
        ssb_build_btn.setObjectName("AccentButton")
        ssb_build_btn.clicked.connect(self.build_ssb)
        ssb_build_label = self.create_label_widget("Build", "Create a standalone .exe file for the specified site.")
        ssb_build_row = self.create_setting_row(ssb_build_label, ssb_build_btn)
        ssb_build_row.setObjectName("LastSettingRow")
        layout.addWidget(ssb_build_row)
        layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_full_browser_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        theme = self.main_window.theme
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: {theme['BG_COLOR']}; border: none; }}
            QScrollBar:vertical {{ border: none; background: transparent; width: 12px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {theme['BORDER_COLOR']}; min-height: 20px; border-radius: 6px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        content_widget = QWidget()
        content_widget.setObjectName("ScrollContentWidget")
        self.apply_builder_styles(content_widget)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(0)

        page_title = QLabel("Full Browser Builder")
        page_title.setObjectName("PageTitle")
        layout.addWidget(page_title)

        self.full_browser_name_edit = QLineEdit()
        self.full_browser_name_edit.setPlaceholderText("e.g., My Private Browser")
        full_browser_name_label = self.create_label_widget("Browser Name", "The name for your custom browser application.")
        layout.addWidget(self.create_setting_row(full_browser_name_label, self.full_browser_name_edit))

        self.full_browser_icon_path_edit = QLineEdit()
        self.full_browser_icon_path_edit.setPlaceholderText("Optional: path to .ico file")
        self.full_browser_icon_browse_btn = QPushButton("Browse...")
        self.full_browser_icon_browse_btn.clicked.connect(self.select_full_browser_icon)
        full_browser_icon_label = self.create_label_widget("Application Icon", "Select a .ico file for the application.")
        layout.addWidget(self.create_setting_row(full_browser_icon_label, self.create_path_widget(self.full_browser_icon_path_edit, self.full_browser_icon_browse_btn)))

        self.full_browser_update_url_edit = QLineEdit()
        self.full_browser_update_url_edit.setPlaceholderText("Optional: user/repo or full JSON URL")
        full_browser_update_label = self.create_label_widget("Update Check URL", "For GitHub repos, use 'user/repo'. Otherwise, provide a direct link to a release JSON file.")
        layout.addWidget(self.create_setting_row(full_browser_update_label, self.full_browser_update_url_edit))

        full_browser_build_btn = QPushButton("Build Browser")
        full_browser_build_btn.setObjectName("AccentButton")
        full_browser_build_btn.clicked.connect(self.build_full_browser)
        full_browser_build_label = self.create_label_widget("Build", "Create a complete, standalone browser based on DisunicX.")
        full_browser_build_row = self.create_setting_row(full_browser_build_label, full_browser_build_btn)
        full_browser_build_row.setObjectName("LastSettingRow")
        layout.addWidget(full_browser_build_row)
        layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_no_builder_view(self):
        not_found_widget = QWidget()
        not_found_widget.setObjectName("NoBuilderView")
        self.apply_builder_styles(not_found_widget)
        not_found_layout = QVBoxLayout(not_found_widget)
        not_found_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        not_found_layout.setSpacing(20)
        not_found_layout.setContentsMargins(40, 40, 40, 40)

        icon_label = QLabel()
        icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['critical'], self.main_window.DANGER_COLOR, QSize(64, 64)).pixmap(QSize(64, 64)))
        title_label = QLabel("Builder Component Not Found")
        title_label.setObjectName("PageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label = QLabel("The DiusnicX builder (PyInstaller) is required to create standalone applications.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        command_label = QLabel("Please install it by opening a command prompt or terminal and running:\n<b>pip install pyinstaller</b>")
        command_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        command_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        command_label.setObjectName("CommandLabel")
        retry_btn = QPushButton("I've installed it, check again")
        retry_btn.setObjectName("AccentButton")
        retry_btn.clicked.connect(self.check_pyinstaller_and_update_ui)

        not_found_layout.addStretch(1)
        not_found_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        not_found_layout.addWidget(title_label)
        not_found_layout.addWidget(info_label)
        not_found_layout.addWidget(command_label)
        not_found_layout.addWidget(retry_btn, 0, Qt.AlignmentFlag.AlignCenter)
        not_found_layout.addStretch(2)
        return not_found_widget

    def apply_builder_styles(self, widget):
        theme = self.main_window.theme
        widget.setStyleSheet(f"""
            #ScrollContentWidget, #NoBuilderView {{ background: transparent; }}
            QLabel#PageTitle {{ font-size: 32px; font-weight: 700; color: {theme['TEXT_COLOR']}; margin-bottom: 35px; }}
            #SettingRow {{
                padding: 40px 0;
                border-bottom: 1px solid {theme['BORDER_COLOR']};
            }}
            #LastSettingRow {{
                border-bottom: none;
            }}
            QLabel#SettingTitle {{ font-size: 15px; font-weight: 700; color: {theme['TEXT_COLOR']}; }}
            QLabel#SettingDescription {{ font-size: 13px; color: {theme['TAB_TEXT_COLOR']}; font-weight: 400; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {theme['URL_BAR_BG']}; color: {theme['TEXT_COLOR']}; border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 6px; padding: 10px; min-height: 22px; font-size: 14px; min-width: 250px;
            }}
            QLineEdit:focus {{ border-color: {self.main_window.ACCENT_COLOR}; }}
            QPushButton {{
                background-color: {theme['URL_BAR_BG']}; border: 1px solid {theme['BORDER_COLOR']};
                padding: 10px 18px; border-radius: 6px; font-weight: 700; color: {theme['TEXT_COLOR']};
            }}
            QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {theme['BORDER_COLOR']}; }}
            QPushButton#AccentButton {{ background-color: {self.main_window.ACCENT_COLOR}; color: white; border: none; }}
            QPushButton#AccentButton:hover {{ background-color: #5aa1f2; }}
            QLabel#CommandLabel {{
                background-color: {theme['URL_BAR_BG']}; color: {theme['TEXT_COLOR']};
                padding: 15px; border-radius: 6px;
                font-family: "Consolas", "Courier New", monospace; font-size: 14px;
                border: 1px solid {theme['BORDER_COLOR']}; margin-top: 10px;
            }}
            QLabel#CommandLabel b {{ color: {self.main_window.ACCENT_COLOR}; font-weight: 700; }}
            #NoBuilderView QLabel {{ font-weight: 700; }}
        """)

    def create_setting_row(self, label_widget, control_widget):
        row_widget = QWidget()
        row_widget.setObjectName("SettingRow")
        row_layout = QGridLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(25)
        row_layout.addWidget(label_widget, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(control_widget, 0, 1, Qt.AlignmentFlag.AlignVCenter)
        row_layout.setColumnStretch(0, 1)
        return row_widget

    def create_label_widget(self, title, description):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        title_label = QLabel(title)
        title_label.setObjectName("SettingTitle")
        layout.addWidget(title_label)
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("SettingDescription")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        return widget

    def create_path_widget(self, line_edit, browse_btn):
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0,0,0,0)
        path_layout.setSpacing(10)
        path_layout.addWidget(line_edit)
        path_layout.addWidget(browse_btn)
        return path_widget

    def check_pyinstaller_and_update_ui(self):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True, creationflags=creationflags)
            self.ssb_stack.setCurrentIndex(0)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ssb_stack.setCurrentIndex(1)

    def select_ssb_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon files (*.ico)")
        if path:
            self.ssb_icon_path_edit.setText(path)

    def select_full_browser_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon files (*.ico)")
        if path:
            self.full_browser_icon_path_edit.setText(path)

    def build_full_browser(self):
        app_name = self.full_browser_name_edit.text().strip()
        icon_path = self.full_browser_icon_path_edit.text().strip()
        update_url = self.full_browser_update_url_edit.text().strip()

        if not app_name:
            CustomMessageBox.warning(self, "Missing Information", "A Browser Name is required.")
            return

        if icon_path and not os.path.exists(icon_path):
            CustomMessageBox.warning(self, "Invalid Path", f"The icon file was not found at:\n{icon_path}")
            return

        if self.ssb_stack.currentIndex() == 1:
            CustomMessageBox.critical(self, "Builder Not Found", "The DiusnicX builder (PyInstaller) is required. Please install it and try again.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation))
        if not output_dir:
            return

        self.progress_dialog = BuildProgressDialog(self)
        self.progress_dialog.show()

        try:
            self.temp_build_dir = tempfile.TemporaryDirectory()
            temp_dir = self.temp_build_dir.name

            script_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(script_dir)

            template_path = os.path.join(script_dir, 'browser_builder_template.py')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            app_script_content = template_content.replace("{APP_NAME}", app_name)
            app_script_content = app_script_content.replace("{UPDATE_URL}", update_url)

            temp_script_path = os.path.join(temp_dir, f"build_{app_name.lower().replace(' ', '_')}.py")
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(app_script_content)

            disunic_exe_path = os.path.join(root_dir, 'disunic.exe')
            favicon_path = os.path.join(root_dir, 'favicon.ico')
            tor_config_path = os.path.join(root_dir, 'DisunicX')
            assets_path = os.path.join(root_dir, 'assets')

            pyinstaller_cmd = [
                'pyinstaller', '--noconsole', '--windowed', '--name', app_name, '--onefile',
                '--add-data', f'{script_dir}{os.pathsep}bin',
                '--add-data', f'{disunic_exe_path}{os.pathsep}.',
                '--add-data', f'{favicon_path}{os.pathsep}assets',
                '--add-data', f'{tor_config_path}{os.pathsep}.',
                '--add-data', f'{assets_path}{os.pathsep}assets',
                '--hidden-import', 'PyQt6.QtSvg', '--hidden-import', 'PyQt6.QtNetwork',
                '--hidden-import', 'PyQt6.QtWebChannel', '--hidden-import', 'PyQt6.QtWebEngineWidgets',
                '--hidden-import', 'PyQt6.QtPrintSupport',
                '--hidden-import', 'certifi',
                '--hidden-import', 'sqlite3',
                '--hidden-import', 'packaging',
                '--hidden-import', 'qrcode',
            ]
            if icon_path:
                pyinstaller_cmd.extend(['--icon', icon_path])
            pyinstaller_cmd.append(temp_script_path)

            self.thread = QThread()
            self.worker = SSB_BuilderWorker(pyinstaller_cmd, temp_dir)
            self.worker.moveToThread(self.thread)

            self.worker.log_message.connect(self.progress_dialog.append_log)
            self.worker.finished.connect(lambda rc, se: self.on_full_browser_build_finished(rc, se, app_name, output_dir))
            self.thread.started.connect(self.worker.run)
            self.thread.start()

        except Exception as e:
            self.progress_dialog.close()
            CustomMessageBox.critical(self, "Build Error", f"An unexpected error occurred: {e}")

    def build_ssb(self):
        self.ssb_app_name = self.ssb_name_edit.text().strip()
        self.ssb_app_url = self.ssb_url_edit.text().strip()
        self.ssb_icon_path = self.ssb_icon_path_edit.text().strip()

        if not self.ssb_app_name or not self.ssb_app_url:
            CustomMessageBox.warning(self, "Missing Information", "Application Name and Website URL are required.")
            return

        if not self.ssb_app_url.startswith(('http://', 'https://')):
            self.ssb_app_url = 'https://' + self.ssb_app_url

        if self.ssb_icon_path and not os.path.exists(self.ssb_icon_path):
            CustomMessageBox.warning(self, "Invalid Path", f"The icon file was not found at:\n{self.ssb_icon_path}")
            return
        
        if self.ssb_stack.currentIndex() == 1:
            CustomMessageBox.critical(self, "Builder Not Found", "The DiusnicX builder (PyInstaller) is required. Please install it and try again.")
            return

        self.ssb_output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation))
        if not self.ssb_output_dir:
            return

        self.progress_dialog = BuildProgressDialog(self)
        self.progress_dialog.show()

        try:
            self.temp_build_dir = tempfile.TemporaryDirectory()
            temp_dir = self.temp_build_dir.name

            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, 'ssb_template.py')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            final_icon_path = self.ssb_icon_path.replace('\\', '/') if self.ssb_icon_path else 'None'
            
            app_script_content = template_content.replace("{APP_URL}", self.ssb_app_url)
            app_script_content = app_script_content.replace("{APP_NAME}", self.ssb_app_name)
            app_script_content = app_script_content.replace("{APP_ICON_PATH}", final_icon_path)

            temp_script_path = os.path.join(temp_dir, "temp_ssb_app.py")
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(app_script_content)

            pyinstaller_cmd = [
                'pyinstaller', '--noconsole', '--windowed', '--name', self.ssb_app_name, '--onefile',
                '--hidden-import', 'PyQt6.QtSvg', '--hidden-import', 'PyQt6.QtNetwork',
                '--hidden-import', 'PyQt6.QtWebChannel', '--hidden-import', 'PyQt6.QtWebEngineWidgets',
                '--hidden-import', 'PyQt6.QtPrintSupport',
                '--hidden-import', 'sqlite3',
            ]
            if self.ssb_icon_path:
                pyinstaller_cmd.extend(['--icon', self.ssb_icon_path])
            pyinstaller_cmd.append(temp_script_path)

            self.thread = QThread()
            self.worker = SSB_BuilderWorker(pyinstaller_cmd, temp_dir)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.progress_dialog.append_log)
            self.worker.finished.connect(self.on_ssb_build_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog._is_closable = True
                self.progress_dialog.close()
            CustomMessageBox.critical(self, "Build Error", f"An unexpected error occurred before starting the build: {e}")
            if hasattr(self, 'temp_build_dir'):
                self.temp_build_dir.cleanup()

    def on_full_browser_build_finished(self, returncode, stderr, app_name, output_dir):
        success = (returncode == 0)
        self.progress_dialog.on_build_finished(success)

        if success:
            self.progress_dialog.append_log("\n<b>Build successful. Moving executable...</b>")
            try:
                source_exe_path = os.path.join(self.temp_build_dir.name, 'dist', f'{app_name}.exe')
                dest_exe_path = os.path.join(output_dir, f'{app_name}.exe')
                shutil.move(source_exe_path, dest_exe_path)
                self.progress_dialog.append_log(f"<b>Application '{app_name}.exe' created in:</b>\n{output_dir}")
            except Exception as e:
                self.progress_dialog.append_log(f"\n<b><font color='red'>ERROR:</font> Could not move the application executable: {e}</b>")
        else:
            self.progress_dialog.append_log(f"\n<b><font color='red'>Build failed with exit code {returncode}.</font></b>")

    def on_ssb_build_finished(self, returncode, stderr):
        success = (returncode == 0)
        self.progress_dialog.on_build_finished(success)

        if success:
            self.progress_dialog.append_log("\n<b>Build successful. Moving executable...</b>")
            try:
                source_exe_path = os.path.join(self.temp_build_dir.name, 'dist', f'{self.ssb_app_name}.exe')
                dest_exe_path = os.path.join(self.ssb_output_dir, f'{self.ssb_app_name}.exe')
                shutil.move(source_exe_path, dest_exe_path)
                self.progress_dialog.append_log(f"<b>Application '{self.ssb_app_name}.exe' created in:</b>\n{self.ssb_output_dir}")
            except Exception as e:
                self.progress_dialog.append_log(f"\n<b><font color='red'>ERROR:</font> Could not move the file: {e}</b>")
        else:
            self.progress_dialog.append_log(f"\n<b><font color='red'>Build failed with exit code {returncode}.</font></b>")

        if hasattr(self, 'temp_build_dir'):
            self.temp_build_dir.cleanup()
        self.temp_build_dir = None
        self.ssb_app_name = None
        self.ssb_app_url = None
        self.ssb_icon_path = None
        self.ssb_output_dir = None