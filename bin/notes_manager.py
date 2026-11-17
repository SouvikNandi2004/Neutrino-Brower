# MIT License
#
# Copyright (c) 2021-2026 Souvik Nandi
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

"""
Research Scratchpad & Quick Notes
=================================
Embedded research notebook sidebar designed for Neutrino Browser and Qelaro Browser.
Allows users to jot down quick thoughts, capture web citations and URLs, and search
notes with automatic persistent storage.
"""

import os
import json
import time
from typing import List, Dict, Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTextEdit, QListWidget, QListWidgetItem, QLabel, QSplitter,
    QFrame, QMessageBox
)
from .utils import get_profile_path, create_icon_from_svg, SVG_ICONS


class NotesSidebarWidget(QWidget):
    """
    A sleek, collapsible research notes sidebar that integrates into the browser UI.
    """
    noteChanged = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.notes_file = os.path.join(get_profile_path(), "research_notes.json")
        self.notes: List[Dict] = []
        self.current_note_index: int = -1

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(self._persist_notes)

        self.init_ui()
        self.load_notes()

    def init_ui(self):
        self.setObjectName("NotesSidebarWidget")
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        title_label = QLabel("Research Notes")
        title_label.setObjectName("NotesHeaderLabel")
        title_label.setStyleSheet("font-weight: 700; font-size: 14px;")

        self.add_note_btn = QPushButton("+ New")
        self.add_note_btn.setObjectName("NotesActionBtn")
        self.add_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_note_btn.clicked.connect(self.create_new_note)

        self.clip_url_btn = QPushButton("Clip Tab")
        self.clip_url_btn.setObjectName("NotesActionBtn")
        self.clip_url_btn.setToolTip("Append current page URL and title to this note")
        self.clip_url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clip_url_btn.clicked.connect(self.clip_current_tab)

        self.close_btn = QPushButton("x")
        self.close_btn.setObjectName("NotesCloseBtn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(lambda: getattr(self.main_window, 'toggle_notes_sidebar', self.hide)())

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_note_btn)
        header_layout.addWidget(self.clip_url_btn)
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # Search filter
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search notes...")
        self.search_edit.setObjectName("NotesSearchEdit")
        self.search_edit.textChanged.connect(self.filter_notes)
        main_layout.addWidget(self.search_edit)

        # Splitter between list and editor
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)

        # Notes list
        self.notes_list = QListWidget()
        self.notes_list.setObjectName("NotesListWidget")
        self.notes_list.currentRowChanged.connect(self.on_note_selected)
        splitter.addWidget(self.notes_list)

        # Editor container
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 4, 0, 0)
        editor_layout.setSpacing(6)

        self.note_title_edit = QLineEdit()
        self.note_title_edit.setPlaceholderText("Note title...")
        self.note_title_edit.setObjectName("NoteTitleEdit")
        self.note_title_edit.textChanged.connect(self.on_content_modified)
        editor_layout.addWidget(self.note_title_edit)

        self.note_body_edit = QTextEdit()
        self.note_body_edit.setPlaceholderText("Write notes, insights, or paste citations here...")
        self.note_body_edit.setObjectName("NoteBodyEdit")
        self.note_body_edit.textChanged.connect(self.on_content_modified)
        editor_layout.addWidget(self.note_body_edit)

        # Delete button at bottom
        editor_bottom_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Note")
        self.delete_btn.setObjectName("NotesDeleteBtn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_current_note)
        editor_bottom_layout.addStretch()
        editor_bottom_layout.addWidget(self.delete_btn)
        editor_layout.addLayout(editor_bottom_layout)

        splitter.addWidget(editor_widget)
        splitter.setSizes([140, 260])
        main_layout.addWidget(splitter)

    def load_notes(self):
        """Loads notes array from profile JSON file."""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except Exception as e:
                print(f"NotesManager: Failed loading notes: {e}")
                self.notes = []

        if not self.notes:
            self.notes = [{
                "title": "Welcome to Notes",
                "body": "Welcome to your built-in research scratchpad!\n\n- Press 'Clip Tab' to save the current page\n- Organize your findings seamlessly alongside browsing\n- All notes save automatically.",
                "created_at": time.time()
            }]

        self.refresh_notes_list()
        if self.notes:
            self.notes_list.setCurrentRow(0)

    def _persist_notes(self):
        """Writes notes to disk."""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            self.noteChanged.emit()
        except Exception as e:
            print(f"NotesManager: Failed saving notes: {e}")

    def refresh_notes_list(self, filter_text: str = ""):
        """Populates the list widget."""
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        filter_lower = filter_text.lower().strip()

        for idx, note in enumerate(self.notes):
            title = note.get("title", "Untitled").strip() or "Untitled"
            body = note.get("body", "")
            if filter_lower and filter_lower not in title.lower() and filter_lower not in body.lower():
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.notes_list.addItem(item)

        self.notes_list.blockSignals(False)

    def filter_notes(self, text: str):
        self.refresh_notes_list(text)

    def on_note_selected(self, row: int):
        if row < 0 or row >= self.notes_list.count():
            return
        item = self.notes_list.item(row)
        if not item:
            return
        real_idx = item.data(Qt.ItemDataRole.UserRole)
        if real_idx is not None and 0 <= real_idx < len(self.notes):
            self.current_note_index = real_idx
            note = self.notes[real_idx]
            self.note_title_edit.blockSignals(True)
            self.note_body_edit.blockSignals(True)
            self.note_title_edit.setText(note.get("title", ""))
            self.note_body_edit.setPlainText(note.get("body", ""))
            self.note_title_edit.blockSignals(False)
            self.note_body_edit.blockSignals(False)

    def on_content_modified(self):
        if self.current_note_index < 0 or self.current_note_index >= len(self.notes):
            return
        title = self.note_title_edit.text()
        body = self.note_body_edit.toPlainText()
        self.notes[self.current_note_index]["title"] = title
        self.notes[self.current_note_index]["body"] = body

        # Update title in list without breaking selection
        current_item = self.notes_list.currentItem()
        if current_item:
            current_item.setText(title.strip() or "Untitled")

        self.save_timer.start()

    def create_new_note(self):
        new_note = {
            "title": f"Note {len(self.notes) + 1}",
            "body": "",
            "created_at": time.time()
        }
        self.notes.insert(0, new_note)
        self.refresh_notes_list(self.search_edit.text())
        self.notes_list.setCurrentRow(0)
        self.note_title_edit.setFocus()
        self.note_title_edit.selectAll()
        self._persist_notes()

    def delete_current_note(self):
        if self.current_note_index < 0 or self.current_note_index >= len(self.notes):
            return
        del self.notes[self.current_note_index]
        self.current_note_index = -1
        self.refresh_notes_list(self.search_edit.text())
        if self.notes:
            self.notes_list.setCurrentRow(0)
        else:
            self.note_title_edit.clear()
            self.note_body_edit.clear()
        self._persist_notes()

    def clip_current_tab(self):
        """Appends the active tab URL and title into the current note."""
        browser = getattr(self.main_window, "current_browser", lambda: None)()
        if not browser or not hasattr(browser, "url"):
            return
        url = browser.url().toString()
        title = browser.title() if hasattr(browser, "title") else "Web Page"
        if not url:
            return

        clip_text = f"\n\nSource: [{title}]({url})\nCaptured: {time.strftime('%Y-%m-%d %H:%M')}\n"
        if self.current_note_index < 0 or not self.notes:
            self.create_new_note()

        current_body = self.note_body_edit.toPlainText()
        self.note_body_edit.setPlainText(current_body + clip_text)
        self.on_content_modified()
        if hasattr(self.main_window, "update_status_message"):
            self.main_window.update_status_message("Clipped current tab to notes")

    def apply_theme(self, theme: Dict):
        """Applies stylesheet matching current theme."""
        bg = theme.get("BG_COLOR", "#1e1e1e")
        text = theme.get("TEXT_COLOR", "#e0e0e0")
        border = theme.get("BORDER_COLOR", "rgba(255, 255, 255, 0.1)")
        accent = getattr(self.main_window, "ACCENT_COLOR", "#3b82f6")
        btn_hover = theme.get("BUTTON_HOVER_COLOR", "rgba(255, 255, 255, 0.1)")

        self.setStyleSheet(f"""
            QWidget#NotesSidebarWidget {{
                background-color: {bg};
                border-left: 1px solid {border};
                color: {text};
            }}
            QLineEdit#NotesSearchEdit, QLineEdit#NoteTitleEdit {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px 10px;
                color: {text};
                font-size: 13px;
            }}
            QLineEdit#NotesSearchEdit:focus, QLineEdit#NoteTitleEdit:focus {{
                border-color: {accent};
            }}
            QTextEdit#NoteBodyEdit {{
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px;
                color: {text};
                font-size: 13px;
                line-height: 1.5;
            }}
            QTextEdit#NoteBodyEdit:focus {{
                border-color: {accent};
            }}
            QListWidget#NotesListWidget {{
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid {border};
                border-radius: 6px;
                color: {text};
                padding: 4px;
            }}
            QListWidget#NotesListWidget::item {{
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QListWidget#NotesListWidget::item:selected {{
                background-color: {accent};
                color: #ffffff;
            }}
            QListWidget#NotesListWidget::item:hover:!selected {{
                background-color: {btn_hover};
            }}
            QPushButton#NotesActionBtn {{
                background-color: {accent};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton#NotesCloseBtn {{
                background-color: transparent;
                color: {text};
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#NotesCloseBtn:hover {{
                color: #ef4444;
            }}
            QPushButton#NotesDeleteBtn {{
                background-color: transparent;
                color: #ef4444;
                border: 1px solid #ef4444;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton#NotesDeleteBtn:hover {{
                background-color: #ef4444;
                color: white;
            }}
        """)
