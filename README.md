# Neutrino Browser

A high-performance, privacy-focused desktop web browser built with Python and PyQt6, powered by Chromium (QtWebEngine) with native Tor network routing and modular components engineered for both Neutrino Browser and Qelaro Browser.

Fast. Secure. Anonymous. Customizable.
Developed by Souvik Nandi.

---

## Overview

Neutrino Browser is a desktop browser focused on privacy, security, and developer-grade extensibility. Built with Python and PyQt6 on top of QtWebEngine (Chromium), it combines native Tor network routing, advanced content blocking, intelligent memory optimization, and an embedded research scratchpad.

The core architecture in version 2.0 has been modularized and optimized so that its high-performance engines can be used directly within both Neutrino Browser and the modern Qelaro Browser ecosystem.

---

## Core Architecture and Modular Subsystems

Neutrino Browser provides several standalone modules in the `bin/` directory designed for seamless reuse in Qelaro Browser and custom browser distributions:

### 1. Privacy Shield Engine (`bin/privacy_shield.py`)
- O(1) Domain Lookup Engine: Replaces linear O(N) scanning over tens of thousands of hosts with hierarchical domain-label hash lookups. Performs instant subresource evaluation in milliseconds.
- Anti-Tracking and Telemetry Blocking: Intercepts analytics, tracking beacons, fingerprinting scripts, and third-party trackers.
- Global Privacy Control and DNT: Automatically injects `Sec-GPC: 1` and `DNT: 1` headers into every outgoing HTTP/HTTPS request.
- Whitelist and Exception Support: Domain-level bypass list persisted across browser sessions.
- Live Telemetry Metrics: Emits Qt signals with real-time statistics including blocked ads, blocked trackers, total requests analyzed, and estimated bandwidth saved.
- Qelaro Reusability: Fully standalone QWebEngineUrlRequestInterceptor subclass that can be dropped into any PyQt6 / PySide6 WebEngine profile.

### 2. Distraction-Free Reader Mode (`bin/reader_mode.py`)
- Intelligent DOM Extraction: Extracts clean article text, author bylines, reading time estimates, and headers while stripping advertisements, popups, sidebars, and navigation elements.
- Customizable Reader Themes: Includes four built-in viewing modes: Light, Sepia, Dark, and AMOLED Black.
- Typography Controls: Real-time font size adjustment (A- / A+) and font family switching (Serif, Sans-Serif, Monospace).
- Quick Toggle: Accessible via the URL bar reader icon, page context menu, or keyboard shortcut (`Ctrl+Alt+R`).
- Print and PDF Export: Integrated printing stylesheet for generating clean documents.

### 3. Smart Tab Memory and Lifecycle Manager (`bin/tab_memory_manager.py`)
- Background Tab Hibernation: Monitors tab inactivity and automatically puts background tabs to sleep after an idle threshold (default: 20 minutes) when three or more tabs are open.
- RAM and VRAM Reduction: Releases Chromium process buffers, drastically reducing multi-tab memory consumption. Wakes up instantaneously when the tab is clicked.
- Tab Pinning Protection: Pins tabs to prevent accidental closure during browsing sessions.
- Closed Tab Recovery Stack: Maintains a LIFO history of recently closed tabs, restored instantly with `Ctrl+Shift+T`.

### 4. Research Scratchpad and Notes Sidebar (`bin/notes_manager.py`)
- Side Panel Workspace: Collapsible sidebar panel accessible via `Ctrl+Shift+N` or toolbar action.
- Tab Citation Clipping: Single-click 'Clip Tab' button that captures the active page title, URL, and timestamp into the open note.
- Real-Time Search and Auto-Save: Instant search across note titles and content with automatic JSON persistence to the user profile directory.

---

## Privacy and Security Features

- Native Tor Network Routing: Routes web traffic through the local Tor SOCKS proxy with automatic SOCKS5 configuration.
- Onion Service Support: Native access to `.onion` hidden services with end-to-end encryption.
- Security Level Profiles: Configure JavaScript execution, WebGL, local storage access, and plugin permissions.
- Advanced Cookie and Cache Controls: Granular session clearing and one-click 'Clear Browsing Data' dialog (`neutrino://history`).
- Real-Time Connection Indicators: Visual SSL/TLS certificate indicators in the address bar with protocol state indicators.

---

## User Experience and Customization

- 15+ Built-in Color Themes: Dark, Light, Liquid Glass, Bluish, Hacker, Solarized Dark, Solarized Light, Gruvbox Dark, Gruvbox Light, Midnight, Sunset, Forest, Pastel, Retro, Neon, Ocean, Lavender, Coffee, Ice, Desert, Rose, Mint, Gold, High Contrast, and Plasma.
- Custom Theme Designer: Built-in theme editor allowing users to modify, preview, and save custom palettes.
- Frameless Window Frame: Custom-rendered title bar, rounded pill URL bar, and native window control integration.
- Configurable New Tab Dashboard: Displays local time, search engine query input, top visited sites, and quick links.
- Search Engine Integration: Support for DuckDuckGo, Google, Bing, Yahoo, StartPage, and Ecosia with customizable default preferences.
- Audio Tab Indicators: Real-time visual audio indicators on tab headers with one-click tab mute and unmute.
- Integrated Download Manager: Track active downloads, pause, resume, cancel, and reveal files in the local file explorer (`neutrino://downloads`).
- In-Page Search Bar: Interactive search bar (`Ctrl+F`) with match counts and next/previous navigation.
- Picture-in-Picture Video Mode: Detach video players into floating desktop overlays.
- QR Code Generator: Generate and save QR codes for any open URL to share links to mobile devices.

---

## Keyboard Shortcuts Reference

| Shortcut | Action |
| :--- | :--- |
| Ctrl + T | Open a new browser tab |
| Ctrl + W | Close the current tab |
| Ctrl + Shift + T | Restore the most recently closed tab |
| Ctrl + Shift + N | Toggle the Research Notes sidebar |
| Ctrl + Alt + R | Toggle Reader View on current article |
| Ctrl + F | Open in-page text search bar |
| Ctrl + R / F5 | Reload the active page |
| Ctrl + L / Alt + D | Focus address and search bar |
| Ctrl + + | Zoom in (increase page scale) |
| Ctrl + - | Zoom out (decrease page scale) |
| Ctrl + 0 | Reset zoom to 100% |
| Alt + Left Arrow | Navigate back in history |
| Alt + Right Arrow | Navigate forward in history |
| Ctrl + H | Open Browsing History (`neutrino://history`) |
| Ctrl + J | Open Download Manager (`neutrino://downloads`) |

---

## Installation and Requirements

### System Requirements

- Python 3.8 or higher
- Git
- Tor Service (required for anonymous routing)

### Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

Core dependencies include:
- `PyQt6` (GUI framework)
- `PyQt6-WebEngine` (Chromium web engine bindings)
- `certifi` (CA certificate bundle for secure downloads)
- `qrcode[pil]` (QR code generator)
- `packaging` (Version verification)
- `pyinstaller` (Optional, for building desktop executables)

### Linux Package Dependencies

#### Debian, Ubuntu, Kali Linux:

```bash
sudo apt update
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg python3-qrcode python3-pil python3-packaging tor
```

#### Arch Linux:

```bash
sudo pacman -S python-pyqt6 python-pyqt6-webengine python-pyqt6-svg python-qrcode python-pillow python-packaging tor
```

---

## Tor Network Configuration

To route all traffic through the Tor network, ensure the local Tor daemon is running:

### Linux (systemd)

```bash
sudo systemctl start tor
sudo systemctl enable tor
sudo systemctl status tor
```

### Windows

Neutrino Browser looks for `tor.exe` or `disunic.exe` in the application directory. You may also install the Tor Expert Bundle or Tor Browser and configure standard SOCKS port `9050` or `9150`.

If proxy routing is disabled in Settings, Neutrino Browser functions as a standard, high-speed direct browser.

---

## Running the Browser

To start Neutrino Browser from source:

```bash
python main.py
```

---

## Codebase Structure

```
Neutrino-Browser/
├── bin/
│   ├── adblocker.py             # Backwards-compatible content blocker wrapper
│   ├── privacy_shield.py        # O(1) Privacy Shield and tracker interceptor
│   ├── reader_mode.py           # Distraction-free article reader engine
│   ├── tab_memory_manager.py    # Auto-hibernation, pinning, and tab restore
│   ├── notes_manager.py         # Research scratchpad and sidebar panel
│   ├── browser_tab.py           # WebEngine view subclass with tab actions
│   ├── tor_browser.py           # Main application window and controller
│   ├── url_bar.py               # Custom URL input with protocol indicators
│   ├── tab_widget.py            # Custom tab bar supporting modern and classic styles
│   ├── tab_overview.py          # Visual tab grid and overview manager
│   ├── bookmarks_bar.py         # Interactive bookmarks toolbar
│   ├── bookmarks_manager.py     # Bookmark storage and persistence
│   ├── history_manager.py       # SQLite browsing history manager
│   ├── history_dialog.py        # History search and clear backend
│   ├── download_manager.py      # Download manager page and progress monitor
│   ├── settings_page.py         # Settings configuration interface
│   ├── find_bar.py              # In-page text search widget
│   ├── updater.py               # Application update verification
│   └── utils.py                 # Common utilities, SVG icon cache, profile paths
├── assets/
│   └── adblock_list.txt         # Bundled offline fallback blocklist
├── main.py                      # Application bootstrap and Tor process manager
├── requirements.txt             # Python dependency specification
├── version.txt                  # Build and release metadata
└── README.md                    # Project documentation
```

---

## Reusing Modules in Qelaro Browser

The subsystems developed for Neutrino Browser are structured as self-contained Python modules. To use them within Qelaro Browser:

1. **Privacy Shield**:
   ```python
   from bin.privacy_shield import PrivacyShieldInterceptor
   shield = PrivacyShieldInterceptor()
   shield.load_rules()
   profile.setUrlRequestInterceptor(shield)
   ```

2. **Reader Mode**:
   ```python
   from bin.reader_mode import ReaderModeManager
   reader = ReaderModeManager(parent=main_window)
   reader.toggle(browser_tab)
   ```

3. **Tab Memory Management**:
   ```python
   from bin.tab_memory_manager import TabMemoryManager
   memory_mgr = TabMemoryManager(main_window=self)
   # Connect Ctrl+Shift+T
   shortcut.activated.connect(memory_mgr.restore_last_closed_tab)
   ```

4. **Research Notes**:
   ```python
   from bin.notes_manager import NotesSidebarWidget
   notes_widget = NotesSidebarWidget(main_window=self)
   layout.addWidget(notes_widget)
   ```

---

## Building Executables

To package the browser into a standalone desktop executable:

### Windows

```bat
build.bat
```

Or manually using PyInstaller:

```bash
pyinstaller --noconfirm --onedir --windowed --icon "favicon.ico" --add-data "bin;bin" --add-data "assets;assets" main.py
```

---

## Disclaimer

Neutrino Browser is provided as-is under the MIT License. The developers assume no liability for misuse, illegal activities, or damages resulting from the use of this software. Users are solely responsible for ensuring compliance with all local laws and regulations regarding privacy and network security.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.

---

## Contact and Links

- Author: Souvik Nandi
- GitHub: [https://github.com/SouvikNandi2004/Neutrino-Brower](https://github.com/SouvikNandi2004/Neutrino-Brower)
- Telegram: [https://t.me/SouvikNandi1](https://t.me/SouvikNandi1)
- Email: [souviknandi.11.2004@gmail.com](mailto:souviknandi.11.2004@gmail.com)
