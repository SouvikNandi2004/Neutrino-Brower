:: MIT License
::
:: Copyright (c) 2021 Souvik Nandi, DisunicX
::
:: Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
::
:: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

@echo off
echo ===============================================
echo Building Neutrino Builder with PyInstaller...
echo ===============================================

pyinstaller ^
--onefile ^
--windowed ^
--noconsole ^
--name "Neutrino Builder" ^
--add-data "favicon.png;." ^
--add-data "favicon.ico;." ^
--add-data "disunic.exe;." ^
--add-data "DisunicX;DisunicX" ^
--add-data "bin;bin" ^
--hidden-import PyQt6.QtSvg ^
--hidden-import sqlite3 ^
--icon=favicon.ico ^
builder.py

echo.
echo ============================================
echo Build finished. Press Enter to exit.
echo ============================================
pause >nul