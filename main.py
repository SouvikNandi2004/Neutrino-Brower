import sys
import os
import subprocess
from shutil import rmtree
from PyQt6.QtWidgets import QApplication
from bin.tor_browser import TorBrowser
from PyQt6.QtCore import QSettings, Qt
from bin.utils import start_tor, get_profile_path, resource_path

def perform_factory_reset_if_needed():
    settings = QSettings("Neutrino", "Browser")
    if settings.value("factory_reset_pending", False, type=bool):
        print("Factory reset pending, wiping all user data...")

        profile_path = get_profile_path()
        bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
        themes_path = os.path.join(bin_dir, 'themes.json')

        try:
            if os.path.exists(profile_path):
                rmtree(profile_path)
                print(f"Successfully removed profile directory: {profile_path}")
        except Exception as e:
            print(f"ERROR: Could not remove profile directory {profile_path}: {e}")

        try:
            if os.path.exists(themes_path):
                os.remove(themes_path)
                print(f"Successfully removed custom themes file: {themes_path}")
        except Exception as e:
            print(f"Warning: Could not remove themes.json: {e}")
        
        settings.clear()
        settings.sync()
        
        print("Factory reset complete.")

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu-rasterization "
    "--enable-zero-copy "
    "--ignore-gpu-blocklist "
    "--enable-features=ParallelDownloading"
)
if sys.platform == "darwin":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " --enable-features=Metal"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    app.setApplicationName("Neutrino")
    app.setOrganizationName("Neutrino")
    
    perform_factory_reset_if_needed()

    tor_process = None
    settings = QSettings("Neutrino", "Browser")
    if settings.value("use_proxy", True, type=bool):
        if sys.platform == "win32":
            tor_exe_path = "disunic.exe"
            
            if not os.path.exists(tor_exe_path) and os.path.exists("tor.exe"):
                tor_exe_path = "tor.exe"

            if getattr(sys, 'frozen', False):
                tor_exe_path = resource_path("disunic.exe")
            
            if os.path.exists(tor_exe_path):
                tor_process = start_tor(tor_executable_path=tor_exe_path)
            else:
                print(f"WARNING: Tor executable not found at {tor_exe_path}")
        elif sys.platform == "linux":
            config_file_path = "disunicx"
            if getattr(sys, 'frozen', False):
                config_file_path = resource_path('disunicx')
            tor_process = start_tor(config_file_path=config_file_path)

    main_window = TorBrowser()

    if not main_window.is_shutting_down:
        main_window.show()
        exit_code = app.exec()
    else:
        exit_code = 0
        
    if tor_process:
        print("Terminating Tor process...")
        tor_process.terminate()
        try:
            tor_process.wait(timeout=5)
            print("Tor process terminated.")
        except subprocess.TimeoutExpired:
            print("Tor process did not terminate in time, killing it.")
            tor_process.kill()

    sys.exit(exit_code)