:: MIT License
::
:: Copyright (c) 2021 Souvik Nandi, DisunicX
::
:: Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
::
:: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

@echo off
echo ============================================
echo Building Neutrino with PyInstaller...
echo ============================================

pyinstaller ^
--noconsole ^
--windowed ^
--name Neutrino ^
--add-data "favicon.png;." ^
--add-data "favicon.ico;." ^
--add-data "disunic.exe;." ^
--hidden-import PyQt6.QtSvg ^
--hidden-import PyQt6.QtNetwork ^
--hidden-import PyQt6.QtWebChannel ^
--hidden-import PyQt6.QtWebEngineWidgets ^
--icon=favicon.ico ^
main.py

echo.
echo ============================================
echo Build finished. Press Enter to exit.
echo ============================================
pause >nul
