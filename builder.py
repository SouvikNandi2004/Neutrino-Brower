import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QSettings, Qt, QPoint, QSize, QEvent
from PyQt6.QtGui import QIcon

# Add the 'bin' directory to the Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bin'))

from bin.builder_page import BuilderPage
from bin.utils import SVG_ICONS, create_icon_from_svg

DEFAULT_THEMES = {
    "dark": { "BG_COLOR": "#09090B", "TEXT_COLOR": "#FAFAFA", "TOOLBAR_COLOR": "#27272A", "URL_BAR_COLOR": "#18181B", "BORDER_COLOR": "#303036", "TAB_ACTIVE_COLOR": "#27272A", "TAB_HOVER_COLOR": "rgba(250, 250, 250, 0.08)", "TAB_TEXT_COLOR": "#A1A1AA", "TAB_TEXT_SELECTED_COLOR": "#FAFAFA", "ICON_COLOR": "#FAFAFA", "STATUS_BAR_TEXT_COLOR": "#A1A1AA", "URL_BAR_BG": "#18181B", "URL_BAR_BORDER": "#303036", "BUTTON_HOVER_COLOR": "rgba(255, 255, 255, 0.1)", "BUTTON_PRESSED_COLOR": "rgba(255, 255, 255, 0.05)", "MENU_BG_COLOR": "rgba(24, 24, 27, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(255, 255, 255, 0.1)", "DISABLED_TEXT_COLOR": "#62626B", "MSGBOX_BUTTON_BG": "rgba(255, 255, 255, 0.1)", "DANGER_COLOR": "#991B1B", "SECURE_COLOR": "#2ecc71" },
    "light": { "BG_COLOR": "#FFFFFF", "TEXT_COLOR": "#09090B", "TOOLBAR_COLOR": "#F5F5F5", "URL_BAR_COLOR": "#E5E5E5", "BORDER_COLOR": "#E5E5E5", "TAB_ACTIVE_COLOR": "#FFFFFF", "TAB_HOVER_COLOR": "rgba(9, 9, 11, 0.05)", "TAB_TEXT_COLOR": "#71717A", "TAB_TEXT_SELECTED_COLOR": "#09090B", "ICON_COLOR": "#71717A", "STATUS_BAR_TEXT_COLOR": "#71717A", "URL_BAR_BG": "#F5F5F5", "URL_BAR_BORDER": "#E5E5E5", "BUTTON_HOVER_COLOR": "rgba(0, 0, 0, 0.08)", "BUTTON_PRESSED_COLOR": "rgba(0, 0, 0, 0.12)", "MENU_BG_COLOR": "rgba(255, 255, 255, 0.98)", "MENU_SEPARATOR_COLOR": "rgba(0, 0, 0, 0.1)", "DISABLED_TEXT_COLOR": "#CCCCCC", "MSGBOX_BUTTON_BG": "rgba(0, 0, 0, 0.05)", "DANGER_COLOR": "#F43F5E", "SECURE_COLOR": "#27ae60" },
    "hacker": { "BG_COLOR": "#000000", "TEXT_COLOR": "#00FF41", "TOOLBAR_COLOR": "#0D0D0D", "URL_BAR_COLOR": "#0A0A0A", "BORDER_COLOR": "#00FF41", "TAB_ACTIVE_COLOR": "#000000", "TAB_HOVER_COLOR": "rgba(0, 255, 65, 0.15)", "TAB_TEXT_COLOR": "#00CC33", "TAB_TEXT_SELECTED_COLOR": "#00FF41", "ICON_COLOR": "#00FF41", "STATUS_BAR_TEXT_COLOR": "#00CC33", "URL_BAR_BG": "#000000", "URL_BAR_BORDER": "#00FF41", "BUTTON_HOVER_COLOR": "rgba(0, 255, 65, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(0, 255, 65, 0.1)", "MENU_BG_COLOR": "rgba(0, 0, 0, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(0, 255, 65, 0.2)", "DISABLED_TEXT_COLOR": "#004400", "MSGBOX_BUTTON_BG": "rgba(0, 255, 65, 0.1)", "DANGER_COLOR": "#FF0033", "SECURE_COLOR": "#00FF41" },
    "bluish": { "BG_COLOR": "#0D1B2A", "TEXT_COLOR": "#E0E6ED", "TOOLBAR_COLOR": "#1B263B", "URL_BAR_COLOR": "#1E3A5F", "BORDER_COLOR": "#3A506B", "TAB_ACTIVE_COLOR": "#1B263B", "TAB_HOVER_COLOR": "rgba(59, 130, 246, 0.15)", "TAB_TEXT_COLOR": "#94A3B8", "TAB_TEXT_SELECTED_COLOR": "#3B82F6", "ICON_COLOR": "#60A5FA", "STATUS_BAR_TEXT_COLOR": "#94A3B8", "URL_BAR_BG": "#0F172A", "URL_BAR_BORDER": "#3A506B", "BUTTON_HOVER_COLOR": "rgba(59, 130, 246, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(59, 130, 246, 0.1)", "MENU_BG_COLOR": "rgba(15, 23, 42, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(59, 130, 246, 0.2)", "DISABLED_TEXT_COLOR": "#334155", "MSGBOX_BUTTON_BG": "rgba(59, 130, 246, 0.1)", "DANGER_COLOR": "#EF4444", "SECURE_COLOR": "#3B82F6" },
    "solarized_dark": { "BG_COLOR": "#002b36", "TEXT_COLOR": "#93a1a1", "TOOLBAR_COLOR": "#073642", "URL_BAR_COLOR": "#073642", "BORDER_COLOR": "#586e75", "TAB_ACTIVE_COLOR": "#002b36", "TAB_HOVER_COLOR": "rgba(131, 148, 150, 0.2)", "TAB_TEXT_COLOR": "#93a1a1", "TAB_TEXT_SELECTED_COLOR": "#b58900", "ICON_COLOR": "#268bd2", "STATUS_BAR_TEXT_COLOR": "#586e75", "URL_BAR_BG": "#073642", "URL_BAR_BORDER": "#586e75", "BUTTON_HOVER_COLOR": "rgba(38, 139, 210, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(38, 139, 210, 0.1)", "MENU_BG_COLOR": "rgba(0, 43, 54, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(88, 110, 117, 0.2)", "DISABLED_TEXT_COLOR": "#586e75", "MSGBOX_BUTTON_BG": "rgba(38, 139, 210, 0.1)", "DANGER_COLOR": "#dc322f", "SECURE_COLOR": "#859900" },
    "solarized_light": { "BG_COLOR": "#fdf6e3", "TEXT_COLOR": "#586e75", "TOOLBAR_COLOR": "#eee8d5", "URL_BAR_COLOR": "#eee8d5", "BORDER_COLOR": "#93a1a1", "TAB_ACTIVE_COLOR": "#fdf6e3", "TAB_HOVER_COLOR": "rgba(38, 139, 210, 0.15)", "TAB_TEXT_COLOR": "#657b83", "TAB_TEXT_SELECTED_COLOR": "#268bd2", "ICON_COLOR": "#268bd2", "STATUS_BAR_TEXT_COLOR": "#93a1a1", "URL_BAR_BG": "#fdf6e3", "URL_BAR_BORDER": "#93a1a1", "BUTTON_HOVER_COLOR": "rgba(38, 139, 210, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(38, 139, 210, 0.1)", "MENU_BG_COLOR": "rgba(253, 246, 227, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(88, 110, 117, 0.2)", "DISABLED_TEXT_COLOR": "#b2b8b5", "MSGBOX_BUTTON_BG": "rgba(38, 139, 210, 0.1)", "DANGER_COLOR": "#dc322f", "SECURE_COLOR": "#859900" },
    "gruvbox_dark": { "BG_COLOR": "#282828", "TEXT_COLOR": "#ebdbb2", "TOOLBAR_COLOR": "#3c3836", "URL_BAR_COLOR": "#3c3836", "BORDER_COLOR": "#504945", "TAB_ACTIVE_COLOR": "#282828", "TAB_HOVER_COLOR": "rgba(235, 219, 178, 0.1)", "TAB_TEXT_COLOR": "#a89984", "TAB_TEXT_SELECTED_COLOR": "#fabd2f", "ICON_COLOR": "#d79921", "STATUS_BAR_TEXT_COLOR": "#bdae93", "URL_BAR_BG": "#3c3836", "URL_BAR_BORDER": "#504945", "BUTTON_HOVER_COLOR": "rgba(250, 189, 47, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(250, 189, 47, 0.1)", "MENU_BG_COLOR": "rgba(40, 40, 40, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(250, 189, 47, 0.2)", "DISABLED_TEXT_COLOR": "#665c54", "MSGBOX_BUTTON_BG": "rgba(250, 189, 47, 0.1)", "DANGER_COLOR": "#fb4934", "SECURE_COLOR": "#b8bb26" },
    "gruvbox_light": { "BG_COLOR": "#fbf1c7", "TEXT_COLOR": "#3c3836", "TOOLBAR_COLOR": "#ebdbb2", "URL_BAR_COLOR": "#ebdbb2", "BORDER_COLOR": "#a89984", "TAB_ACTIVE_COLOR": "#fbf1c7", "TAB_HOVER_COLOR": "rgba(250, 189, 47, 0.15)", "TAB_TEXT_COLOR": "#7c6f64", "TAB_TEXT_SELECTED_COLOR": "#d79921", "ICON_COLOR": "#d79921", "STATUS_BAR_TEXT_COLOR": "#928374", "URL_BAR_BG": "#fbf1c7", "URL_BAR_BORDER": "#a89984", "BUTTON_HOVER_COLOR": "rgba(215, 153, 33, 0.15)", "BUTTON_PRESSED_COLOR": "rgba(215, 153, 33, 0.1)", "MENU_BG_COLOR": "rgba(251, 241, 199, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(215, 153, 33, 0.2)", "DISABLED_TEXT_COLOR": "#bdae93", "MSGBOX_BUTTON_BG": "rgba(215, 153, 33, 0.1)", "DANGER_COLOR": "#cc241d", "SECURE_COLOR": "#98971a" },
    "midnight": { "BG_COLOR": "#0f172a", "TEXT_COLOR": "#e2e8f0", "TOOLBAR_COLOR": "#1e293b", "URL_BAR_COLOR": "#1e293b", "BORDER_COLOR": "#334155", "TAB_ACTIVE_COLOR": "#0f172a", "TAB_HOVER_COLOR": "rgba(96, 165, 250, 0.15)", "TAB_TEXT_COLOR": "#94a3b8", "TAB_TEXT_SELECTED_COLOR": "#60a5fa", "ICON_COLOR": "#3b82f6", "STATUS_BAR_TEXT_COLOR": "#64748b", "URL_BAR_BG": "#1e293b", "URL_BAR_BORDER": "#334155", "BUTTON_HOVER_COLOR": "rgba(59, 130, 246, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(59, 130, 246, 0.1)", "MENU_BG_COLOR": "rgba(15, 23, 42, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(96, 165, 250, 0.2)", "DISABLED_TEXT_COLOR": "#475569", "MSGBOX_BUTTON_BG": "rgba(59, 130, 246, 0.1)", "DANGER_COLOR": "#ef4444", "SECURE_COLOR": "#22d3ee" },
    "sunset": { "BG_COLOR": "#2d1b2d", "TEXT_COLOR": "#fbcfe8", "TOOLBAR_COLOR": "#451a3e", "URL_BAR_COLOR": "#5b2139", "BORDER_COLOR": "#9333ea", "TAB_ACTIVE_COLOR": "#2d1b2d", "TAB_HOVER_COLOR": "rgba(236, 72, 153, 0.15)", "TAB_TEXT_COLOR": "#f472b6", "TAB_TEXT_SELECTED_COLOR": "#ec4899", "ICON_COLOR": "#f472b6", "STATUS_BAR_TEXT_COLOR": "#f9a8d4", "URL_BAR_BG": "#451a3e", "URL_BAR_BORDER": "#9333ea", "BUTTON_HOVER_COLOR": "rgba(236, 72, 153, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(236, 72, 153, 0.1)", "MENU_BG_COLOR": "rgba(45, 27, 45, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(236, 72, 153, 0.2)", "DISABLED_TEXT_COLOR": "#7e2553", "MSGBOX_BUTTON_BG": "rgba(236, 72, 153, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#9333ea" },
    "forest": { "BG_COLOR": "#0b2414", "TEXT_COLOR": "#d1fae5", "TOOLBAR_COLOR": "#14532d", "URL_BAR_COLOR": "#166534", "BORDER_COLOR": "#22c55e", "TAB_ACTIVE_COLOR": "#0b2414", "TAB_HOVER_COLOR": "rgba(34, 197, 94, 0.15)", "TAB_TEXT_COLOR": "#86efac", "TAB_TEXT_SELECTED_COLOR": "#22c55e", "ICON_COLOR": "#4ade80", "STATUS_BAR_TEXT_COLOR": "#86efac", "URL_BAR_BG": "#14532d", "URL_BAR_BORDER": "#22c55e", "BUTTON_HOVER_COLOR": "rgba(34, 197, 94, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(34, 197, 94, 0.1)", "MENU_BG_COLOR": "rgba(11, 36, 20, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(34, 197, 94, 0.2)", "DISABLED_TEXT_COLOR": "#14532d", "MSGBOX_BUTTON_BG": "rgba(34, 197, 94, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#22c55e" },
    "pastel": { "BG_COLOR": "#fdf2f8", "TEXT_COLOR": "#4a044e", "TOOLBAR_COLOR": "#fce7f3", "URL_BAR_COLOR": "#fbcfe8", "BORDER_COLOR": "#f472b6", "TAB_ACTIVE_COLOR": "#fdf2f8", "TAB_HOVER_COLOR": "rgba(236, 72, 153, 0.15)", "TAB_TEXT_COLOR": "#db2777", "TAB_TEXT_SELECTED_COLOR": "#be185d", "ICON_COLOR": "#ec4899", "STATUS_BAR_TEXT_COLOR": "#be185d", "URL_BAR_BG": "#fbcfe8", "URL_BAR_BORDER": "#f472b6", "BUTTON_HOVER_COLOR": "rgba(236, 72, 153, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(236, 72, 153, 0.1)", "MENU_BG_COLOR": "rgba(253, 242, 248, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(236, 72, 153, 0.2)", "DISABLED_TEXT_COLOR": "#fda4af", "MSGBOX_BUTTON_BG": "rgba(236, 72, 153, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#22c55e" },
    "retro": { "BG_COLOR": "#1d1f21", "TEXT_COLOR": "#c5c8c6", "TOOLBAR_COLOR": "#282a2e", "URL_BAR_COLOR": "#373b41", "BORDER_COLOR": "#969896", "TAB_ACTIVE_COLOR": "#1d1f21", "TAB_HOVER_COLOR": "rgba(181, 137, 0, 0.2)", "TAB_TEXT_COLOR": "#b294bb", "TAB_TEXT_SELECTED_COLOR": "#f0c674", "ICON_COLOR": "#81a2be", "STATUS_BAR_TEXT_COLOR": "#969896", "URL_BAR_BG": "#282a2e", "URL_BAR_BORDER": "#373b41", "BUTTON_HOVER_COLOR": "rgba(240, 198, 116, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(240, 198, 116, 0.1)", "MENU_BG_COLOR": "rgba(29, 31, 33, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(240, 198, 116, 0.2)", "DISABLED_TEXT_COLOR": "#5f6368", "MSGBOX_BUTTON_BG": "rgba(240, 198, 116, 0.1)", "DANGER_COLOR": "#cc342b", "SECURE_COLOR": "#198844" },
    "neon": { "BG_COLOR": "#0f0f0f", "TEXT_COLOR": "#f5f5f5", "TOOLBAR_COLOR": "#1a1a1a", "URL_BAR_COLOR": "#111111", "BORDER_COLOR": "#00ffff", "TAB_ACTIVE_COLOR": "#0f0f0f", "TAB_HOVER_COLOR": "rgba(255, 0, 255, 0.2)", "TAB_TEXT_COLOR": "#00ffff", "TAB_TEXT_SELECTED_COLOR": "#ff00ff", "ICON_COLOR": "#39ff14", "STATUS_BAR_TEXT_COLOR": "#ff00ff", "URL_BAR_BG": "#1a1a1a", "URL_BAR_BORDER": "#00ffff", "BUTTON_HOVER_COLOR": "rgba(0, 255, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(0, 255, 255, 0.1)", "MENU_BG_COLOR": "rgba(15, 15, 15, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(255, 0, 255, 0.2)", "DISABLED_TEXT_COLOR": "#333333", "MSGBOX_BUTTON_BG": "rgba(255, 0, 255, 0.1)", "DANGER_COLOR": "#ff073a", "SECURE_COLOR": "#00ff9f" },
    "ocean": { "BG_COLOR": "#011627", "TEXT_COLOR": "#d6deeb", "TOOLBAR_COLOR": "#1d3b53", "URL_BAR_COLOR": "#133a5e", "BORDER_COLOR": "#82aaff", "TAB_ACTIVE_COLOR": "#011627", "TAB_HOVER_COLOR": "rgba(130, 170, 255, 0.2)", "TAB_TEXT_COLOR": "#82aaff", "TAB_TEXT_SELECTED_COLOR": "#22d3ee", "ICON_COLOR": "#82aaff", "STATUS_BAR_TEXT_COLOR": "#7b8794", "URL_BAR_BG": "#133a5e", "URL_BAR_BORDER": "#82aaff", "BUTTON_HOVER_COLOR": "rgba(130, 170, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(130, 170, 255, 0.1)", "MENU_BG_COLOR": "rgba(1, 22, 39, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(130, 170, 255, 0.2)", "DISABLED_TEXT_COLOR": "#475569", "MSGBOX_BUTTON_BG": "rgba(130, 170, 255, 0.1)", "DANGER_COLOR": "#ef4444", "SECURE_COLOR": "#22d3ee" },
    "lavender": { "BG_COLOR": "#2e1a47", "TEXT_COLOR": "#f3e8ff", "TOOLBAR_COLOR": "#4c1d95", "URL_BAR_COLOR": "#5b21b6", "BORDER_COLOR": "#8b5cf6", "TAB_ACTIVE_COLOR": "#2e1a47", "TAB_HOVER_COLOR": "rgba(139, 92, 246, 0.2)", "TAB_TEXT_COLOR": "#c4b5fd", "TAB_TEXT_SELECTED_COLOR": "#a78bfa", "ICON_COLOR": "#c084fc", "STATUS_BAR_TEXT_COLOR": "#c4b5fd", "URL_BAR_BG": "#4c1d95", "URL_BAR_BORDER": "#8b5cf6", "BUTTON_HOVER_COLOR": "rgba(139, 92, 246, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(139, 92, 246, 0.1)", "MENU_BG_COLOR": "rgba(46, 26, 71, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(139, 92, 246, 0.2)", "DISABLED_TEXT_COLOR": "#5b21b6", "MSGBOX_BUTTON_BG": "rgba(139, 92, 246, 0.1)", "DANGER_COLOR": "#f43f5e", "SECURE_COLOR": "#8b5cf6" },
    "coffee": { "BG_COLOR": "#2c1810", "TEXT_COLOR": "#f5f5dc", "TOOLBAR_COLOR": "#4a3222", "URL_BAR_COLOR": "#5c3d2e", "BORDER_COLOR": "#d6b370", "TAB_ACTIVE_COLOR": "#2c1810", "TAB_HOVER_COLOR": "rgba(214, 179, 112, 0.2)", "TAB_TEXT_COLOR": "#d6b370", "TAB_TEXT_SELECTED_COLOR": "#f5deb3", "ICON_COLOR": "#e6be8a", "STATUS_BAR_TEXT_COLOR": "#cbb67c", "URL_BAR_BG": "#4a3222", "URL_BAR_BORDER": "#d6b370", "BUTTON_HOVER_COLOR": "rgba(214, 179, 112, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(214, 179, 112, 0.1)", "MENU_BG_COLOR": "rgba(44, 24, 16, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(214, 179, 112, 0.2)", "DISABLED_TEXT_COLOR": "#5c3d2e", "MSGBOX_BUTTON_BG": "rgba(214, 179, 112, 0.1)", "DANGER_COLOR": "#cc241d", "SECURE_COLOR": "#b8bb26" },
    "ice": { "BG_COLOR": "#e0f7fa", "TEXT_COLOR": "#006064", "TOOLBAR_COLOR": "#b2ebf2", "URL_BAR_COLOR": "#80deea", "BORDER_COLOR": "#26c6da", "TAB_ACTIVE_COLOR": "#e0f7fa", "TAB_HOVER_COLOR": "rgba(0, 188, 212, 0.2)", "TAB_TEXT_COLOR": "#00acc1", "TAB_TEXT_SELECTED_COLOR": "#00838f", "ICON_COLOR": "#00acc1", "STATUS_BAR_TEXT_COLOR": "#0097a7", "URL_BAR_BG": "#b2ebf2", "URL_BAR_BORDER": "#26c6da", "BUTTON_HOVER_COLOR": "rgba(0, 188, 212, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(0, 188, 212, 0.1)", "MENU_BG_COLOR": "rgba(224, 247, 250, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(0, 188, 212, 0.2)", "DISABLED_TEXT_COLOR": "#80deea", "MSGBOX_BUTTON_BG": "rgba(0, 188, 212, 0.1)", "DANGER_COLOR": "#f44336", "SECURE_COLOR": "#00838f" },
    "desert": { "BG_COLOR": "#edc9af", "TEXT_COLOR": "#3e2723", "TOOLBAR_COLOR": "#d7b899", "URL_BAR_COLOR": "#cba57f", "BORDER_COLOR": "#a1887f", "TAB_ACTIVE_COLOR": "#edc9af", "TAB_HOVER_COLOR": "rgba(161, 136, 127, 0.2)", "TAB_TEXT_COLOR": "#795548", "TAB_TEXT_SELECTED_COLOR": "#5d4037", "ICON_COLOR": "#8d6e63", "STATUS_BAR_TEXT_COLOR": "#6d4c41", "URL_BAR_BG": "#d7b899", "URL_BAR_BORDER": "#a1887f", "BUTTON_HOVER_COLOR": "rgba(161, 136, 127, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(161, 136, 127, 0.1)", "MENU_BG_COLOR": "rgba(237, 201, 175, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(161, 136, 127, 0.2)", "DISABLED_TEXT_COLOR": "#cba57f", "MSGBOX_BUTTON_BG": "rgba(161, 136, 127, 0.1)", "DANGER_COLOR": "#d84315", "SECURE_COLOR": "#6d4c41" },
    "rose": { "BG_COLOR": "#ffe4e6", "TEXT_COLOR": "#9d174d", "TOOLBAR_COLOR": "#fecdd3", "URL_BAR_COLOR": "#fda4af", "BORDER_COLOR": "#f43f5e", "TAB_ACTIVE_COLOR": "#ffe4e6", "TAB_HOVER_COLOR": "rgba(244, 63, 94, 0.15)", "TAB_TEXT_COLOR": "#e11d48", "TAB_TEXT_SELECTED_COLOR": "#be123c", "ICON_COLOR": "#f43f5e", "STATUS_BAR_TEXT_COLOR": "#be123c", "URL_BAR_BG": "#fecdd3", "URL_BAR_BORDER": "#f43f5e", "BUTTON_HOVER_COLOR": "rgba(244, 63, 94, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(244, 63, 94, 0.1)", "MENU_BG_COLOR": "rgba(255, 228, 230, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(244, 63, 94, 0.2)", "DISABLED_TEXT_COLOR": "#fda4af", "MSGBOX_BUTTON_BG": "rgba(244, 63, 94, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#22c55e" },
    "mint": { "BG_COLOR": "#ecfdf5", "TEXT_COLOR": "#064e3b", "TOOLBAR_COLOR": "#d1fae5", "URL_BAR_COLOR": "#a7f3d0", "BORDER_COLOR": "#10b981", "TAB_ACTIVE_COLOR": "#ecfdf5", "TAB_HOVER_COLOR": "rgba(16, 185, 129, 0.2)", "TAB_TEXT_COLOR": "#059669", "TAB_TEXT_SELECTED_COLOR": "#047857", "ICON_COLOR": "#34d399", "STATUS_BAR_TEXT_COLOR": "#047857", "URL_BAR_BG": "#d1fae5", "URL_BAR_BORDER": "#10b981", "BUTTON_HOVER_COLOR": "rgba(16, 185, 129, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(16, 185, 129, 0.1)", "MENU_BG_COLOR": "rgba(236, 253, 245, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(16, 185, 129, 0.2)", "DISABLED_TEXT_COLOR": "#a7f3d0", "MSGBOX_BUTTON_BG": "rgba(16, 185, 129, 0.1)", "DANGER_COLOR": "#dc2626", "SECURE_COLOR": "#047857" },
    "gold": { "BG_COLOR": "#fff8e1", "TEXT_COLOR": "#78350f", "TOOLBAR_COLOR": "#ffecb3", "URL_BAR_COLOR": "#ffe082", "BORDER_COLOR": "#fbbf24", "TAB_ACTIVE_COLOR": "#fff8e1", "TAB_HOVER_COLOR": "rgba(251, 191, 36, 0.2)", "TAB_TEXT_COLOR": "#d97706", "TAB_TEXT_SELECTED_COLOR": "#b45309", "ICON_COLOR": "#f59e0b", "STATUS_BAR_TEXT_COLOR": "#b45309", "URL_BAR_BG": "#ffecb3", "URL_BAR_BORDER": "#fbbf24", "BUTTON_HOVER_COLOR": "rgba(251, 191, 36, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(251, 191, 36, 0.1)", "MENU_BG_COLOR": "rgba(255, 248, 225, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(251, 191, 36, 0.2)", "DISABLED_TEXT_COLOR": "#ffe082", "MSGBOX_BUTTON_BG": "rgba(251, 191, 36, 0.1)", "DANGER_COLOR": "#d97706", "SECURE_COLOR": "#22c55e" },
    "high_contrast": { "BG_COLOR": "#000000", "TEXT_COLOR": "#ffffff", "TOOLBAR_COLOR": "#000000", "URL_BAR_COLOR": "#000000", "BORDER_COLOR": "#ffffff", "TAB_ACTIVE_COLOR": "#000000", "TAB_HOVER_COLOR": "rgba(255, 255, 255, 0.2)", "TAB_TEXT_COLOR": "#ffffff", "TAB_TEXT_SELECTED_COLOR": "#ffff00", "ICON_COLOR": "#ffffff", "STATUS_BAR_TEXT_COLOR": "#ffffff", "URL_BAR_BG": "#000000", "URL_BAR_BORDER": "#ffffff", "BUTTON_HOVER_COLOR": "rgba(255, 255, 255, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(255, 255, 255, 0.1)", "MENU_BG_COLOR": "rgba(0, 0, 0, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(255, 255, 255, 0.2)", "DISABLED_TEXT_COLOR": "#666666", "MSGBOX_BUTTON_BG": "rgba(255, 255, 255, 0.1)", "DANGER_COLOR": "#ff0000", "SECURE_COLOR": "#00ff00" },
    "aqua": { "BG_COLOR": "#e0f2f1", "TEXT_COLOR": "#004d40", "TOOLBAR_COLOR": "#b2dfdb", "URL_BAR_COLOR": "#80cbc4", "BORDER_COLOR": "#26a69a", "TAB_ACTIVE_COLOR": "#e0f2f1", "TAB_HOVER_COLOR": "rgba(38, 166, 154, 0.2)", "TAB_TEXT_COLOR": "#00897b", "TAB_TEXT_SELECTED_COLOR": "#00695c", "ICON_COLOR": "#26a69a", "STATUS_BAR_TEXT_COLOR": "#00695c", "URL_BAR_BG": "#b2dfdb", "URL_BAR_BORDER": "#26a69a", "BUTTON_HOVER_COLOR": "rgba(38, 166, 154, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(38, 166, 154, 0.1)", "MENU_BG_COLOR": "rgba(224, 242, 241, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(38, 166, 154, 0.2)", "DISABLED_TEXT_COLOR": "#80cbc4", "MSGBOX_BUTTON_BG": "rgba(38, 166, 154, 0.1)", "DANGER_COLOR": "#d32f2f", "SECURE_COLOR": "#388e3c" },
    "plasma": { "BG_COLOR": "#1a002b", "TEXT_COLOR": "#f3f4f6", "TOOLBAR_COLOR": "#2c003e", "URL_BAR_COLOR": "#40005a", "BORDER_COLOR": "#e11d48", "TAB_ACTIVE_COLOR": "#1a002b", "TAB_HOVER_COLOR": "rgba(225, 29, 72, 0.2)", "TAB_TEXT_COLOR": "#f472b6", "TAB_TEXT_SELECTED_COLOR": "#db2777", "ICON_COLOR": "#ec4899", "STATUS_BAR_TEXT_COLOR": "#f472b6", "URL_BAR_BG": "#2c003e", "URL_BAR_BORDER": "#e11d48", "BUTTON_HOVER_COLOR": "rgba(225, 29, 72, 0.2)", "BUTTON_PRESSED_COLOR": "rgba(225, 29, 72, 0.1)", "MENU_BG_COLOR": "rgba(26, 0, 43, 0.95)", "MENU_SEPARATOR_COLOR": "rgba(225, 29, 72, 0.2)", "DISABLED_TEXT_COLOR": "#5b21b6", "MSGBOX_BUTTON_BG": "rgba(225, 29, 72, 0.1)", "DANGER_COLOR": "#e11d48", "SECURE_COLOR": "#22c55e" }
}

class MockMainWindow:
    """A mock main window to provide theme and color info to the BuilderPage."""
    def __init__(self):
        self.load_themes()
        # Use a default dark theme for the standalone builder, but allow it to be overridden by custom themes
        self.theme_name = "dark"
        self.theme = self.THEMES.get(self.theme_name, DEFAULT_THEMES["dark"])

        self.ACCENT_COLOR = "#3F51B5"
        self.DANGER_COLOR = self.theme.get("DANGER_COLOR", "#991B1B")

    def load_themes(self):
        """Loads default themes and merges custom themes from themes.json."""
        self.THEMES = DEFAULT_THEMES.copy()
        try:
            # The builder.py script is in the root, so we need to construct the path to bin/themes.json
            script_dir = os.path.dirname(os.path.abspath(__file__))
            themes_path = os.path.join(script_dir, 'bin', 'themes.json')
            if os.path.exists(themes_path):
                with open(themes_path, 'r', encoding='utf-8') as f:
                    custom_themes = json.load(f)
                    self.THEMES.update(custom_themes)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load custom themes from themes.json: {e}")

class BuilderWindow(QMainWindow):
    __version__ = "1.0.0"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"DisunicX Builder v{self.__version__}")
        self.setMinimumSize(800, 700)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = QPoint()

        mock_main = MockMainWindow()
        self.theme = mock_main.theme
        self.ACCENT_COLOR = mock_main.ACCENT_COLOR
        self.DANGER_COLOR = mock_main.DANGER_COLOR
        
        # Set window icon
        self.setWindowIcon(create_icon_from_svg(SVG_ICONS['new_window'], self.theme['ICON_COLOR']))

        # Main container for shadow and border
        self.main_container = QWidget()
        self.main_container.setObjectName("MainContainer")
        
        # Main layout
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(1, 1, 1, 1) # To show the border
        main_layout.setSpacing(0)

        # --- Custom Title Bar ---
        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setPixmap(create_icon_from_svg(SVG_ICONS['new_window'], self.theme['ICON_COLOR'], QSize(18,18)).pixmap(QSize(18,18)))
        title_bar_layout.addWidget(icon_label)

        title_label = QLabel(f"DisunicX Builder v{self.__version__}")
        title_label.setObjectName("TitleLabel")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        # Window controls
        self.minimize_btn = QPushButton("—")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("✕")
        self.minimize_btn.setObjectName("WindowControlBtn")
        self.maximize_btn.setObjectName("WindowControlBtn")
        self.close_btn.setObjectName("CloseBtn")
        
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.close)

        title_bar_layout.addWidget(self.minimize_btn)
        title_bar_layout.addWidget(self.maximize_btn)
        title_bar_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(self.title_bar)

        # Builder Page
        self.builder_page = BuilderPage(mock_main, self)
        main_layout.addWidget(self.builder_page)
        
        self.setCentralWidget(self.main_container)
        self.apply_stylesheet()

    def apply_stylesheet(self, is_maximized=False):
        theme = self.theme
        border_radius = "0px" if is_maximized else "8px"
        border = "none" if is_maximized else f"1px solid {theme['BORDER_COLOR']}"
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: transparent; }}
            #MainContainer {{ 
                background-color: {theme['BG_COLOR']}; 
                border: {border};
                border-radius: {border_radius};
            }}
            #TitleBar {{
                background-color: {theme['TOOLBAR_COLOR']};
                border-top-left-radius: {border_radius};
                border-top-right-radius: {border_radius};
            }}
            #TitleLabel {{
                color: {theme['TEXT_COLOR']};
                font-weight: bold;
                padding-left: 8px;
            }}
            .WindowControlBtn, #CloseBtn {{
                background-color: transparent;
                color: {theme['TEXT_COLOR']};
                border: none;
                font-family: "Segoe UI Symbol", "sans-serif";
                width: 46px;
                height: 40px;
            }}
            .WindowControlBtn:hover {{
                background-color: {theme['BUTTON_HOVER_COLOR']};
            }}
            #CloseBtn {{
                border-top-right-radius: {border_radius};
            }}
            #CloseBtn:hover {{
                background-color: {theme['DANGER_COLOR']};
            }}
        """)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            is_maximized = bool(self.windowState() & Qt.WindowState.WindowMaximized)
            self.apply_stylesheet(is_maximized=is_maximized)
            if is_maximized:
                self.maximize_btn.setText("❐")
                self.main_container.layout().setContentsMargins(0, 0, 0, 0)
            else:
                self.maximize_btn.setText("□")
                self.main_container.layout().setContentsMargins(1, 1, 1, 1)
        super().changeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            if self.isMaximized():
                self.toggle_maximize()
                self._drag_pos = QPoint(int(self.width() * (event.position().x() / self.width())), 15)
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    app.setApplicationName("DisunicXBuilder")
    app.setOrganizationName("DisunicX")

    window = BuilderWindow()
    window.show()
    sys.exit(app.exec())