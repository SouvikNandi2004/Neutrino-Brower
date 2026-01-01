import sys
import os
import subprocess
from shutil import rmtree
from PyQt6.QtWidgets import QApplication
from bin.tor_browser import TorBrowser
from PyQt6.QtCore import QSettings, Qt
from bin.utils import start_tor, get_profile_path, resource_path

def perform_factory_reset_if_needed():
    """
    Checks for a reset flag in QSettings. If present, this function
    wipes all user data directories before the main application initializes them.
    This is called before Tor or the main application window are started.
    """
    settings = QSettings("Neutrino", "Browser")
    if settings.value("factory_reset_pending", False, type=bool):
        print("Factory reset pending, wiping all user data...")

        # Get paths to delete
        profile_path = get_profile_path()
        # The main.py script is in the root, so we need to construct the path to bin/themes.json
        bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
        themes_path = os.path.join(bin_dir, 'themes.json')

        # Delete the entire profile directory
        try:
            if os.path.exists(profile_path):
                rmtree(profile_path)
                print(f"Successfully removed profile directory: {profile_path}")
        except Exception as e:
            print(f"ERROR: Could not remove profile directory {profile_path}: {e}")

        # Delete custom themes file
        try:
            if os.path.exists(themes_path):
                os.remove(themes_path)
                print(f"Successfully removed custom themes file: {themes_path}")
        except Exception as e:
            print(f"Warning: Could not remove themes.json: {e}")
        
        # Clear all remaining QSettings and remove the flag
        settings.clear()
        settings.sync()
        
        print("Factory reset complete.")

# Enable GPU acceleration for a faster, more premium feel.
# These flags offload rendering tasks to the GPU, making animations,
# video playback, and scrolling much smoother.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu-rasterization "
    "--enable-zero-copy "
    "--ignore-gpu-blocklist "
    # Vulkan and WebRTCPipeWireCapturer can cause crashes on some systems (especially Windows).
    # Using a more stable feature set for broader compatibility.
    "--enable-features=ParallelDownloading"
)
# On macOS, explicitly prefer the Metal graphics backend for better performance and integration.
if sys.platform == "darwin":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " --enable-features=Metal"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Use INI file for settings instead of platform-native (e.g., Windows Registry)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    # Set application name and organization for QSettings
    app.setApplicationName("Neutrino")
    app.setOrganizationName("Neutrino")
    
    # Perform reset check BEFORE starting Tor or creating the main window
    perform_factory_reset_if_needed()

    # --- Tor Process Startup ---
    tor_process = None
    settings = QSettings("Neutrino", "Browser")
    if settings.value("use_proxy", True, type=bool):
        if sys.platform == "win32": # Only start Tor on Windows and Linux
            # On Windows, we expect a bundled Tor executable.
            tor_exe_path = "disunic.exe" # Default for development
            
            # Fallback: Check for tor.exe if disunic.exe is missing (useful for dev)
            if not os.path.exists(tor_exe_path) and os.path.exists("tor.exe"):
                tor_exe_path = "tor.exe"

            if getattr(sys, 'frozen', False):
                tor_exe_path = resource_path("disunic.exe")
            
            if os.path.exists(tor_exe_path):
                tor_process = start_tor(tor_executable_path=tor_exe_path)
            else:
                print(f"WARNING: Tor executable not found at {tor_exe_path}")
        elif sys.platform == "linux":
            # On Linux, we assume 'tor' is in the system PATH and use our config file.
            config_file_path = "disunicx" # Default for development
            if getattr(sys, 'frozen', False):
                config_file_path = resource_path('disunicx')
            tor_process = start_tor(config_file_path=config_file_path)

    main_window = TorBrowser()

    # Only show the window and run the app if the terms were accepted and
    # the __init__ method did not signal for a shutdown.
    if not main_window.is_shutting_down:
        main_window.show()
        exit_code = app.exec()
    else:
        exit_code = 0
        
    # When the application event loop finishes, terminate the Tor process
    if tor_process:
        print("Terminating Tor process...")
        tor_process.terminate()
        try:
            # Wait for a short period for the process to terminate
            tor_process.wait(timeout=5)
            print("Tor process terminated.")
        except subprocess.TimeoutExpired:
            print("Tor process did not terminate in time, killing it.")
            tor_process.kill()

    sys.exit(exit_code)