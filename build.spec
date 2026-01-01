# c:/Users/Souvik/Desktop/ds/build.spec
# -*- mode: python ; coding: utf-8 -*-

# This is a PyInstaller spec file.
# To build the application, run from your terminal in the project directory:
# pyinstaller build.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('disunic.exe', '.')  # This bundles the Tor executable
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'PySide6.QtNetwork',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtPrintSupport',
        'packaging', # For the updater
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DisunicX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False for a windowed (GUI) application
    icon='icon.ico', # IMPORTANT: Provide a path to an .ico file for the application
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, upx_exclude=[], name='DisunicX')