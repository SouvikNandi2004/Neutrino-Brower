<!--
MIT License

Copyright (c) 2021 Souvik Nandi, DisunicX

Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
-->

# DisunicX Browser

**A modern, production-ready, customizable, privacy-focused web browser proudly developed in India. Built with Python and PySide6, it leverages the Tor network for enhanced anonymity and security.**

---

## 📖 About The Project

DisunicX is a production-ready web browser, proudly developed in India, designed from the ground up with privacy as its core principle. It integrates seamlessly with the Tor network, routing your traffic through Tor's volunteer-run overlay network to conceal your location and browsing activity from surveillance and traffic analysis.

The entire user interface is crafted using PyQt6 (Qt for Python), providing a sleek, modern, and responsive dark-themed experience. It's a testament to what can be achieved with Python in the desktop application space.

### ✨ Key Features

#### Privacy & Security
*   **Tor Integration**: Automatically connects to and routes traffic through the Tor network. A status indicator in the status bar keeps you informed of the connection.
*   **Privacy-Focused Settings**: Control cookie policies, tracking protection, and set security levels (Standard, Safer, Safest) that manage JavaScript, plugins, and other potentially risky features.
*   **Modernized Security Icons**: A clear, modern lock icon indicates a secure connection.

#### Modern User Interface
*   **Customizable Theming Engine**: Choose from over a dozen built-in themes (Dark, Light, Solarized, Gruvbox, etc.) or create, edit, and save your own custom themes with the built-in theme editor.
*   **Polished UI Elements**: A beautiful, modern interface with a redesigned settings page, custom-drawn frameless window controls, and polished menus with bolder fonts and icons.
*   **Custom New Tab Page**: An elegant and functional new tab page featuring a search bar, quick links to your most visited sites, and a customizable background.
*   **Enhanced URL Bar**: A prominent URL bar with a thicker border and clear focus states.
*   **Consistent Dialogs**: All pop-ups and dialogs (including JavaScript alerts) share a consistent, modern style.

#### Productivity & Features 
*   **Tabbed Browsing**: A familiar and intuitive tabbed browsing experience with movable and closable tabs.
*   **Tab Muting**: Easily mute and unmute individual tabs with a clickable audio indicator.
*   **Session Restore**: Configure the browser to "Continue where you left off," restoring your tabs from the previous session.
*   **Bookmarks Bar with Folders**: A fully functional bookmarks bar that supports nested folders for better organization.
*   **Integrated Download Manager**: A built-in page (`disunic://downloads`) to manage all your downloads, with support for pausing, resuming, and canceling.
*   **Rich History Page**: A full-featured, searchable history page (`disunic://history`) to easily find pages you've visited.
*   **Find in Page**: Quickly search for text within the current webpage using Ctrl+F.
*   **Picture-in-Picture (PiP)**: Pop out videos into a floating window to watch while you browse other tabs.
*   **Extra Tools**:
    *   Save pages directly to PDF.
    *   Create a QR code for the current page URL.
    *   Clear all browsing data with a single click.

#### Developer & Advanced Features
*   **Application Builder**: A built-in tool to create your own standalone applications:
    *   **Site-Specific Apps**: Generate a lightweight, single-site browser for any website.
    *   **Custom Browsers**: Build and distribute your own custom-branded version of the full DisunicX browser.
*   **Developer Tools**: Includes essential developer features like "View Page Source" and "Inspect Element".
*   **Automatic Updates**: The browser automatically checks for new releases on GitHub and prompts you to download the latest version.
*   **Advanced Settings**: Toggle Tor network usage, manage hardware acceleration, and set a custom User-Agent.

### Built With

*   Python
*   PyQt6 (The official Python bindings for Qt)
*   Tor


## Tor Installation (Linux)

For Linux users, DisunicX relies on a system-wide Tor installation. Follow the instructions below to set up Tor on your system.

### Debian/Ubuntu

The easiest way to install Tor on Debian-based systems (like Ubuntu) is through the official Tor Project repository. This ensures you get the latest stable version.

1.  **Add the Tor Project repository:**
    Open a terminal and add the following lines to `/etc/apt/sources.list` or a new file in `/etc/apt/sources.list.d/tor.list`:

    ```
    deb     [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org <DISTRIBUTION> main
    deb-src [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org <DISTRIBUTION> main
    ```
    Replace `<DISTRIBUTION>` with your Debian/Ubuntu codename (e.g., `focal` for Ubuntu 20.04, `jammy` for Ubuntu 22.04, `bookworm` for Debian 12). You can find your distribution's codename by running `lsb_release -cs`.

2.  **Install the Tor Project's GPG key:**

    ```bash
    wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | sudo tee /usr/share/keyrings/tor-archive-keyring.gpg >/dev/null
    ```

3.  **Update your package lists and install Tor:**

    ```bash
    sudo apt update
    sudo apt install tor deb.torproject.org-keyring
    ```

### Fedora

On Fedora, you can install Tor from the official repositories:

```bash
sudo dnf install tor
```

### Arch Linux

On Arch Linux, Tor is available in the official repositories:

```bash
sudo pacman -S tor
```

### Other Distributions

For other Linux distributions, please refer to the official Tor Project documentation for installation instructions: https://community.torproject.org/relay/setup/bridge/debian-ubuntu/

### Starting and Enabling Tor

After installation, ensure the Tor service is running and enabled to start on boot:

```bash
sudo systemctl start tor
sudo systemctl enable tor
```

You can check the status of the Tor service with:

```bash
systemctl status tor
```

Once Tor is installed and running, DisunicX should automatically detect and use it.

---

##  Application Builder

DisunicX includes a powerful built-in tool that allows you to build and package new applications. This feature can be accessed by running `builder.py` from the project root.

### Site-Specific App Builder

This tool lets you create a lightweight, standalone desktop application for any website. It's perfect for turning your favorite web apps (like YouTube, Discord, or a project management tool) into native-feeling desktop experiences.

**Features:**
-   Creates a minimal browser window locked to a single URL.
-   The application gets its own taskbar icon and window.
-   Configurable options:
    -   **Application Name**: The name that appears in the window title.
    -   **Website URL**: The web address the application will load.
    -   **Application Icon**: A custom `.ico` file for the application's icon.

### Full Browser Builder

This mode allows you to create a complete, distributable, and custom-branded version of the DisunicX browser. You can customize it and share it with others.

-   **Browser Name**: The name for your custom browser.
-   **Application Icon**: A custom `.ico` file for the browser's icon.
-   **Update Check URL**: A URL for the browser's automatic update checker. This can be a GitHub repository (`user/repo`) or a direct link to a release JSON file.

---

## ⚠️ Disclaimer

The developer, Souvik Nandi, is not responsible for any illegal, harmful, or unethical activities performed using this browser. You use this software at your own risk.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact

Souvik Nandi - souviknandi.11.2004@gmail.com - Telegram: t.me/SouvikNandi1 

Project Link: https://github.com/SouvikNandi1/disunicx2021