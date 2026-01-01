import os
import socket
import sys
import subprocess
import base64
from PyQt6.QtCore import QStandardPaths, QSize, Qt, QBuffer, QIODevice, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QGraphicsDropShadowEffect

# This function is crucial for finding bundled files (like the 'bin' folder)
# when the application is frozen by PyInstaller.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, we assume the script is run from the project root.
        # The utils.py script is in 'bin', so we need to go up one level.
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# --- SVG Icon Data ---
SVG_ICONS = {
    "back": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/></svg>',
    "forward": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/></svg>',
    "reload": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8.354 1.146a.5.5 0 0 0-.708 0l-6 6A.5.5 0 0 0 1.5 7.5v7a.5.5 0 0 0 .5.5h4.5a.5.5 0 0 0 .5-.5v-4h2v4a.5.5 0 0 0 .5.5H14a.5.5 0 0 0 .5-.5v-7a.5.5 0 0 0-.146-.354L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293L8.354 1.146zM2.5 14V7.707l5.5-5.5 5.5 5.5V14H10v-4a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5v4H2.5z"/></svg>',
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M208,80H176V56a48,48,0,0,0-96,0V80H48a16,16,0,0,0-16,16V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V96A16,16,0,0,0,208,80Zm-80,84a12,12,0,1,1,12-12A12,12,0,0,1,128,164Zm32-84H96V56a32,32,0,0,1,64,0Z"></path></svg>',
    "info": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24a104,104,0,1,0,104,104A104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm16-40a8,8,0,0,1-8,8,16,16,0,0,1-16-16V128a8,8,0,0,1,0-16,16,16,0,0,1,16,16v40A8,8,0,0,1,144,176ZM112,84a12,12,0,1,1,12,12A12,12,0,0,1,112,84Z"></path></svg>',
    "question": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24a104,104,0,1,0,104,104A104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm-8-80a8,8,0,0,1-8-8,28,28,0,0,1,28-28,8,8,0,0,1,0,16,12,12,0,0,0-12,12A8,8,0,0,1,120,136Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,172Z"></path></svg>',
    "critical": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24a104,104,0,1,0,104,104A104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm48.49-136.49a12,12,0,0,1,0,17L145,128l31.51,31.51a12,12,0,0,1-17,17L128,145l-31.51,31.51a12,12,0,0,1-17-17L111,128,79.51,96.49a12,12,0,0,1,17-17L128,111l31.51-31.52A12,12,0,0,1,176.49,79.51Z"></path></svg>',
    "bookmark_filled": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2 2v13.5a.5.5 0 0 0 .74.439L8 13.069l5.26 2.87A.5.5 0 0 0 14 15.5V2a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z"/></svg>',
    "history": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M136,80v45.66l37.66,21.75a8,8,0,0,1-8,13.86L120,140.62V80a8,8,0,0,1,16,0Zm91.83,44.18A104.3,104.3,0,0,1,132,232a103.87,103.87,0,0,1-99.18-72.18a8,8,0,1,1,15.62-4.2,88,88,0,1,0-26.27-83.24,8,8,0,0,1-11.05-11.54,104,104,0,1,1,118.68,83.34Zm-75-11.32L128,96l24.83-14.34a8,8,0,0,0,4-11.31,80,80,0,0,0-112,0,8,8,0,0,0,4,11.31L72,96l-24.83,14.34a8,8,0,1,0,8,13.86L80,112.54V136a8,8,0,0,0,16,0V112.54l24.83-14.33a8,8,0,0,0,8-13.86Z"></path></svg>',
    "save_pdf": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Zm-42.23-93.57a8,8,0,0,1,8.46,6.5,24,24,0,0,1-4.1,17.5,39.81,39.81,0,0,1-16.26,13.14,8,8,0,1,1-6.2-14.7,24.1,24.1,0,0,0,9.75-7.87,8,8,0,0,1-1.4-9.39,8,8,0,0,1,9.78-4.61ZM120,184a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h24A8,8,0,0,1,120,184Zm-32-24H72a8,8,0,0,1,0-16h16a8,8,0,0,1,0,16Zm48-8a8,8,0,0,1-8,8H112a8,8,0,0,1,0-16h16A8,8,0,0,1,136,152Z"></path></svg>',
    "clear_data": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M216,48H176V40a16,16,0,0,0-16-16H96A16,16,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40h64V48H96Zm96,168H64V64H192Zm-80-104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"></path></svg>',
    "downloads": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm45.66-106.34a8,8,0,0,1-11.32,11.32L136,94.34V168a8,8,0,0,1-16,0V94.34L91.66,121a8,8,0,0,1-11.32-11.32l40-40a8,8,0,0,1,11.32,0Z"></path></svg>',
    "close": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M208.49,191.51a12,12,0,0,1-17,17L128,145,64.49,208.49a12,12,0,0,1-17-17L111,128,47.51,64.49a12,12,0,0,1,17-17L128,111l63.51-63.52a12,12,0,0,1,17,17L145,128Z"></path></svg>',
    "bookmark_outline": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13.5a.5.5 0 0 1-.777.416L8 13.101l-5.223 2.815A.5.5 0 0 1 2 15.5V2zm2-1a1 1 0 0 0-1 1v12.566l4.723-2.482a.5.5 0 0 1 .554 0L13 14.566V2a1 1 0 0 0-1-1H4z"/></svg>',
    "tor_active": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.338 1.59a61.44 61.44 0 0 0-2.837.856.481.481 0 0 0-.328.39c-.554 4.157.726 7.19 2.253 9.188a10.725 10.725 0 0 0 2.287 2.233c.346.244.652.42.893.533.12.057.218.095.293.118a.55.55 0 0 0 .101.025.615.615 0 0 0 .1-.025c.076-.023.174-.06.294-.118.24-.113.547-.29.893-.533a10.726 10.726 0 0 0 2.287-2.233c1.527-1.997 2.807-5.031 2.253-9.188a.48.48 0 0 0-.328-.39c-.95-.324-1.88-.652-2.837-.856C11.223 1.084 10.16 1.028 9.07 1H8.93C7.84 1 6.777 1.028 5.79 1.084zM5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453 7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/><path d="M10.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/></svg>',
    "security_level": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453 7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/><path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/></svg>',
    "settings_general": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311a1.464 1.464 0 0 1-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413-1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.858 2.929 2.929 0 0 1 0 5.858z"/></svg>',
    "settings_privacy": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453 7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/></svg>',
    "settings_advanced": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M6 1v3H1V1h5zM1 0a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1H1zm14 12v3h-5v-3h5zm-5-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1h-5zM6 8v7H1V8h5zM1 7a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1H1zm14-6v7h-5V1h5zm-5-1a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V1a1 1 0 0 0-1-1h-5z"/></svg>',
    "qr_code": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2 2h2v2H2V2Z"/><path d="M6 0v6H0V0h6ZM5 1H1v4h4V1ZM4 12H2v2h2v-2Z"/><path d="M6 10v6H0v-6h6Zm-1 1H1v4h4v-4ZM16 0h-5v6h5V0h-4Zm-1 1v4h-3V1h3ZM10 12h2v2h-2v-2Z"/><path d="M16 10v6h-6v-6h6Zm-1 1h-4v4h4v-4Z"/></svg>',
    "new_tab": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>',
    "new_window": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M200,64V168a8,8,0,0,1-16,0V85.66l-82.34,82.35a8,8,0,0,1-11.32-11.32L170.34,72H88a8,8,0,0,1,0-16H192A8,8,0,0,1,200,64ZM88,24H48A16,16,0,0,0,32,40V216a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V168a8,8,0,0,0-16,0v48H48V40H88a8,8,0,0,0,0-16Z"></path></svg>',
    "copy_link": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4.715 6.542 3.343 7.914a3 3 0 1 0 4.243 4.243l1.828-1.829A3 3 0 0 0 8.586 5.5L8 6.086a1.002 1.002 0 0 0-.154.199 2 2 0 0 1 .861 3.337L6.88 11.45a2 2 0 1 1-2.83-2.83l.793-.792a4.018 4.018 0 0 1-.128-1.287z"/><path d="M6.586 4.672A3 3 0 0 0 7.414 9.5l.775-.776a2 2 0 0 1-.896-3.346L9.12 3.55a2 2 0 1 1 2.83 2.83l-.793.792c.112.42.155.855.128 1.287l1.372-1.372a3 3 0 1 0-4.243-4.243L6.586 4.672z"/></svg>',
    "view_source": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.478 1.647a.5.5 0 1 0-.956-.294l-4 13a.5.5 0 0 0 .956.294l4-13zM4.854 4.146a.5.5 0 0 1 0 .708L1.707 8l3.147 3.146a.5.5 0 0 1-.708.708l-3.5-3.5a.5.5 0 0 1 0-.708l3.5-3.5a.5.5 0 0 1 .708 0zm6.292 0a.5.5 0 0 0 0 .708L14.293 8l-3.147 3.146a.5.5 0 0 0 .708.708l3.5-3.5a.5.5 0 0 0 0-.708l-3.5-3.5a.5.5 0 0 0-.708 0z"/></svg>',
    "inspect": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.879.646a.5.5 0 0 0-.707 0L8.025 4.793 4.879.646a.5.5 0 0 0-.707 0L.646 4.17a.5.5 0 0 0 0 .707l3.525 3.525L.646 11.929a.5.5 0 0 0 0 .707l3.525 3.525a.5.5 0 0 0 .707 0L8.025 12.02l3.147 4.146a.5.5 0 0 0 .707 0l3.525-3.525a.5.5 0 0 0 0-.707L12.02 8.025l3.525-3.525a.5.5 0 0 0 0-.707L12.879.646zM8 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>',
    "audio_playing": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z"/><path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z"/><path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z"/></svg>',
    "audio_muted": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06zm7.137 2.096a.5.5 0 0 1 0 .708L12.207 8l1.647 1.646a.5.5 0 0 1-.708.708L11.5 8.707l-1.646 1.647a.5.5 0 0 1-.708-.708L10.793 8 9.146 6.354a.5.5 0 1 1 .708-.708L11.5 7.293l1.646-1.647a.5.5 0 0 1 .708 0z"/></svg>',
    "find_in_page": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg>',
    "tab_grid": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M1.5 3A1.5 1.5 0 0 1 3 1.5h10A1.5 1.5 0 0 1 14.5 3v8a1.5 1.5 0 0 1-1.5 1.5H3A1.5 1.5 0 0 1 1.5 11V3zM3 2.5a.5.5 0 0 0-.5.5v8a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V3a.5.5 0 0 0-.5-.5H3z"/><path d="M0 4.5A1.5 1.5 0 0 1 1.5 3h13A1.5 1.5 0 0 1 16 4.5v8a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 12.5v-8zM1.5 4a.5.5 0 0 0-.5.5v8a.5.5 0 0 0 .5.5h13a.5.5 0 0 0 .5-.5v-8a.5.5 0 0 0-.5-.5h-13z"/></svg>',
    "download_pause": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216ZM112,96v64a8,8,0,0,1-16,0V96a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V96a8,8,0,0,1,16,0Z"/></svg>',
    "download_resume": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm36.43-123.88-64,40a8,8,0,0,0,0,13.76l64,40A8,8,0,0,0,176,160V88a8,8,0,0,0-11.57-7.88ZM160,146.24,113.71,120,160,93.76Z"/></svg>',
    "open_folder": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M232,88V200a16,16,0,0,1-16,16H40a16,16,0,0,1-16-16V56A16,16,0,0,1,40,40H93.58a16,16,0,0,1,11.31,4.69l19.43,19.42a8,8,0,0,0,5.66,2.34H216A16,16,0,0,1,232,88Zm-16,0H129.94a16,16,0,0,1-11.31-4.69L99.21,63.89A8,8,0,0,0,93.58,61.5H40a1.4,1.4,0,0,0-1.5,1.5V200H216Z"/></svg>',
    "file_icon": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/></svg>',
}

# --- Icon Caching ---
_ICON_CACHE = {}

def create_icon_from_svg(svg_data: str, color: str, size: QSize = QSize(20, 20)) -> QIcon:
    """Renders an SVG string into a QIcon with a specified color, using a cache for performance."""
    cache_key = (svg_data, color, size.width(), size.height())
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    colored_svg = svg_data.replace('currentColor', color).encode('utf-8')
    renderer = QSvgRenderer(colored_svg)
    
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon

def find_main_window(widget):
    """Traverses parent hierarchy to find the main window instance."""
    parent = widget
    while parent is not None:
        if isinstance(parent, QMainWindow):
            return parent
        parent = parent.parent()
    # Fallback if no QMainWindow is found (e.g., running dialog standalone)
    # This is unlikely in this app but good practice.
    if hasattr(widget, 'main_window'):
        return widget.main_window
    return None

class DraggableFramelessDialog(QDialog):
    """A custom frameless dialog that can be dragged by its title bar area and has a fade-in animation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Qt.Tool hint prevents it from showing up in the taskbar, which is good for a utility dialog
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.Tool) # type: ignore
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0) # Start fully transparent
        self._drag_pos = None

        # The main layout of the dialog will contain the shadow_container with margins for the shadow
        # The dialog itself is transparent, so the shadow is visible.
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(15, 15, 15, 15) # Space for shadow

        # Create a central container that will hold the actual content and have the shadow
        self.shadow_container = QWidget()
        self.shadow_container.setObjectName("ShadowContainer")
        dialog_layout.addWidget(self.shadow_container)

        # The shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow_container.setGraphicsEffect(shadow)

        # Child classes will now add their layouts and widgets to this content_layout
        self.content_layout = QVBoxLayout(self.shadow_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

    def showEvent(self, event):
        """Override showEvent to trigger fade-in animation."""
        # Animate opacity
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.opacity_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        super().showEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Define a draggable area, e.g., the top 50 pixels.
            # Adjust y() check because of the new margins
            if event.position().y() < 50: # A draggable area of 50px from the top
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

class CustomMessageBox(DraggableFramelessDialog):
    """A custom, modern, frameless message box to replace QMessageBox."""
    ICON_MAP = {
        'information': ('info', 'ACCENT_COLOR'),
        'question': ('question', 'ACCENT_COLOR'),
        'warning': ('security_level', '#f59e0b'),  # Amber/Gold color
        'critical': ('critical', 'DANGER_COLOR'),
    }

    def __init__(self, parent, title, text, icon_type='information', buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
        super().__init__(parent)
        self.main_window = find_main_window(parent)
        self.setMinimumWidth(400)

        container = QWidget()
        # self.content_layout is provided by DraggableFramelessDialog
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0) # The container itself has no margins
        container_layout.setSpacing(0)

        # --- Content Area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("DialogTitleLabel")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setObjectName("DialogTextLabel")
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(text_label)
        container_layout.addWidget(content_widget)

        # --- Button Footer ---
        button_widget = QWidget()
        button_widget.setObjectName("ButtonWidget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(10)
        button_layout.addStretch()

        button_map = {
            QMessageBox.StandardButton.Ok: "OK",
            QMessageBox.StandardButton.Yes: "Yes",
            QMessageBox.StandardButton.No: "No",
            QMessageBox.StandardButton.Cancel: "Cancel",
            QMessageBox.StandardButton.Save: "Save",
            QMessageBox.StandardButton.Close: "Close",
        }

        for btn_flag, btn_text in button_map.items():
            if buttons & btn_flag:
                btn = QPushButton(btn_text)
                btn.clicked.connect(lambda b=btn_flag: self.done(b))
                if btn_flag == defaultButton:
                    btn.setDefault(True)
                    btn.setFocus()
                
                # Style the primary action button
                is_destructive = icon_type in ['warning', 'critical'] or (icon_type == 'question' and btn_flag == QMessageBox.StandardButton.Yes)
                is_confirm = icon_type == 'information' and btn_flag == QMessageBox.StandardButton.Ok
                if is_destructive or is_confirm or btn_flag == QMessageBox.StandardButton.Save:
                     btn.setObjectName("AccentButton")

                button_layout.addWidget(btn)

        container_layout.addWidget(button_widget)
        self.content_layout.addWidget(container) # Add main container to the shadow layout
        self.apply_stylesheet(icon_type)

    def apply_stylesheet(self, icon_type):
        theme = self.main_window.theme
        accent_color = theme['DANGER_COLOR'] if icon_type in ['warning', 'critical'] else self.main_window.ACCENT_COLOR
        hover_accent_color = QColor(accent_color).lighter(115).name() # Calculate a brighter hover color

        self.shadow_container.setStyleSheet(f"""
            #ShadowContainer {{
                background-color: {theme['BG_COLOR']};
                border: 1px solid {theme['BORDER_COLOR']};
                border-radius: 8px;
            }}
            #DialogTitleLabel {{ font-size: 16px; font-weight: 700; color: {theme['TEXT_COLOR']}; }}
            #DialogTextLabel {{ font-size: 14px; color: {theme['TAB_TEXT_COLOR']}; }}
            #ButtonWidget {{ background-color: {theme['TOOLBAR_COLOR']}; border-top: 1px solid {theme['BORDER_COLOR']}; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }}
            #ButtonWidget QPushButton {{ background-color: {theme['MSGBOX_BUTTON_BG']}; border: 1px solid {theme['BORDER_COLOR']}; padding: 8px 16px; border-radius: 6px; color: {theme['TEXT_COLOR']}; min-width: 90px; font-weight: 700; }}
            #ButtonWidget QPushButton:hover {{ background-color: {theme['BUTTON_HOVER_COLOR']}; border-color: {self.main_window.ACCENT_COLOR}; }}
            #ButtonWidget QPushButton:focus {{ border-color: {self.main_window.ACCENT_COLOR}; }}
            #AccentButton {{ background-color: {accent_color}; border-color: {accent_color}; color: white; }}
            #AccentButton:hover {{ background-color: {hover_accent_color}; }}
        """)

    @staticmethod
    def _create_and_exec(parent, title, text, icon_type, buttons, defaultButton):
        dialog = CustomMessageBox(parent, title, text, icon_type, buttons, defaultButton)
        return dialog.exec()

    @staticmethod
    def information(parent, title, text):
        return CustomMessageBox._create_and_exec(parent, title, text, 'information', QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, defaultButton=QMessageBox.StandardButton.No):
        return CustomMessageBox._create_and_exec(parent, title, text, 'question', buttons, defaultButton)

    @staticmethod
    def warning(parent, title, text, buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.Ok):
        return CustomMessageBox._create_and_exec(parent, title, text, 'warning', buttons, defaultButton)

    @staticmethod
    def critical(parent, title, text, buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.Ok):
        return CustomMessageBox._create_and_exec(parent, title, text, 'critical', buttons, defaultButton)

def qicon_to_base64(icon: QIcon) -> str | None:
    """Converts a QIcon to a base64 encoded PNG data URI."""
    if icon.isNull():
        return None
    pixmap = icon.pixmap(16, 16)
    if pixmap.isNull():
        return None
    
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    
    base64_data = base64.b64encode(buffer.data().data()).decode('utf-8')
    return f"data:image/png;base64,{base64_data}"

def qpixmap_to_base64(pixmap: QPixmap) -> str | None:
    """Converts a QPixmap to a base64 encoded PNG data URI."""
    if pixmap.isNull():
        return None
    
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    
    base64_data = base64.b64encode(buffer.data().data()).decode('utf-8')
    return f"data:image/png;base64,{base64_data}"

def base64_to_qicon(base64_str: str) -> QIcon:
    """Converts a base64 data URI back to a QIcon."""
    if not base64_str or 'base64,' not in base64_str:
        return QIcon()
    encoded_data = base64_str.split(',')[1]
    pixmap_data = base64.b64decode(encoded_data)
    pixmap = QPixmap()
    pixmap.loadFromData(pixmap_data)
    return QIcon(pixmap)

# Function to check if Tor is running
def is_tor_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", 9050)) == 0

# Create a persistent profile directory
def get_profile_path():
    data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    profile_path = os.path.join(data_path, "DisunicX", "Profiles", "Default")
    os.makedirs(profile_path, exist_ok=True)
    return profile_path

# Start Tor in the background
def start_tor(tor_executable_path=None, config_file_path=None):
    # Set creationflags to hide console window on Windows
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    if sys.platform == "win32":
        # On Windows, run the bundled executable with command-line arguments
        if not tor_executable_path:
            print("ERROR: Tor executable path not provided on Windows.")
            return None
        
        profile_path = get_profile_path()
        tor_data_path = os.path.join(profile_path, "tor_data")
        cookie_auth_file = os.path.join(tor_data_path, "control_auth_cookie")
        os.makedirs(tor_data_path, exist_ok=True)

        cmd = [
                tor_executable_path,
                "--ControlPort", "9051",
                "--CookieAuthentication", "1",
                "--CookieAuthFile", cookie_auth_file,
                "--DataDirectory", tor_data_path,
            ]
    else:
        # On Linux/macOS, run the system 'tor' command with the config file
        if not config_file_path:
            print("ERROR: Tor config file path not provided on Linux/macOS.")
            return None
        
        # The 'disunicx' config file already contains the necessary port and auth settings.
        # Tor will automatically create its data directory based on its own defaults.
        cmd = ["tor", "-f", config_file_path]

    try:
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags
        )
    except FileNotFoundError:
        print(f"ERROR: Could not find the command '{cmd[0]}'. Please ensure it is installed and in your system's PATH.")
        return None