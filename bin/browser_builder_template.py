# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
import base64
from datetime import datetime
import html
import urllib.parse

# If the app is frozen, add the bundled 'bin' directory to the Python path
# so that its modules can be imported.
if getattr(sys, 'frozen', False):
    # The resource_path function needs to find the 'bin' directory.
    sys.path.insert(0, os.path.join(sys._MEIPASS, 'bin'))

from bin.tor_browser import TorBrowser
from bin.utils import start_tor, SVG_ICONS, resource_path
from bin.updater import Updater

# --- PLACEHOLDERS ---
APP_NAME = "{APP_NAME}"
UPDATE_URL = "{UPDATE_URL}"
# --- END PLACEHOLDERS ---

class CustomAboutTorBrowser(TorBrowser):
    """ A subclass of the main browser to override the name and About page. """
    def __init__(self):
        # Set the app name for QSettings BEFORE calling super().__init__()
        # so that it uses a separate settings file (e.g., in AppData/Local/APP_NAME).
        QApplication.instance().setApplicationName(APP_NAME)
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} (v{self.__version__})")

    def get_about_page_html(self):
        """Generates the HTML for the custom about page."""
        theme = self.theme
        current_year = datetime.now().year

        # --- Logo Handling ---
        logo_html = ""
        try:
            # The build process bundles the original favicon into an 'assets' folder.
            favicon_path = resource_path('assets/favicon.ico')
            
            if os.path.exists(favicon_path):
                with open(favicon_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                    logo_html = f'<img src="data:image/x-icon;base64,{encoded_string}" alt="Logo">'
            else:
                # Fallback to SVG if no favicon is found
                logo_html = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)
        except Exception as e:
            print(f"Could not load logo for about page: {e}")
            # Fallback to SVG on any error
            logo_html = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)

        # Feature icons
        tor_icon = SVG_ICONS['tor_active'].replace('currentColor', self.ACCENT_COLOR)
        privacy_icon = SVG_ICONS['security_level'].replace('currentColor', self.ACCENT_COLOR)
        settings_icon = SVG_ICONS['settings_general'].replace('currentColor', self.ACCENT_COLOR)
        updates_icon = SVG_ICONS['downloads'].replace('currentColor', self.ACCENT_COLOR)

        update_button_html = ""
        # Only show the update button if a URL was provided during the build
        if UPDATE_URL:
            update_button_html = '<a href="disunic://check-for-updates" class="update-button">Check for Updates</a>'

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>About {APP_NAME}</title>
            <style>
                :root {{
                    --bg-color: {theme['BG_COLOR']};
                    --text-color: {theme['TEXT_COLOR']};
                    --toolbar-color: {theme['TOOLBAR_COLOR']};
                    --border-color: {theme['BORDER_COLOR']};
                    --accent-color: {self.ACCENT_COLOR};
                    --subtle-text-color: {theme['TAB_TEXT_COLOR']};
                }}
                body {{
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    margin: 0;
                    padding: 40px;
                    display: flex;
                    justify-content: center;
                    align-items: flex-start; /* Align to top */
                    min-height: 100vh;
                    box-sizing: border-box;
                }}
                .container {{
                    max-width: 700px;
                    width: 100%;
                }}
                .header {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    padding-bottom: 40px;
                    border-bottom: 1px solid var(--border-color);
                    margin-bottom: 40px;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    margin-bottom: 20px;
                }}
                .logo img, .logo svg {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                    border-radius: 16px;
                }}
                h1 {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin: 0;
                }}
                .version {{
                    font-size: 1rem;
                    color: var(--subtle-text-color);
                    margin-top: 8px;
                    background-color: var(--toolbar-color);
                    padding: 4px 12px;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                }}
                .description {{
                    font-size: 1.1rem;
                    line-height: 1.6;
                    color: var(--subtle-text-color);
                    max-width: 550px;
                    margin-top: 16px;
                }}
                .features-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .feature-card {{
                    background-color: var(--toolbar-color);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 20px;
                    display: flex;
                    align-items: flex-start;
                    gap: 15px;
                }}
                .feature-icon {{
                    width: 24px;
                    height: 24px;
                    flex-shrink: 0;
                }}
                .feature-text h3 {{
                    font-size: 1rem;
                    font-weight: 600;
                    margin: 0 0 5px 0;
                }}
                .feature-text p {{
                    font-size: 0.9rem;
                    color: var(--subtle-text-color);
                    margin: 0;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    padding-top: 30px;
                    border-top: 1px solid var(--border-color);
                }}
                .update-button {{
                    display: inline-block;
                    background-color: var(--accent-color);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    text-decoration: none;
                    transition: transform 0.2s, background-color 0.2s;
                    margin-bottom: 30px;
                }}
                .update-button:hover {{
                    transform: scale(1.05);
                }}
                .footer-links a {{
                    color: var(--subtle-text-color);
                    text-decoration: none;
                    margin: 0 12px;
                    font-size: 0.9rem;
                }}
                .footer-links a:hover {{
                    text-decoration: underline;
                }}
                .copyright {{
                    margin-top: 16px;
                    font-size: 0.8rem;
                    color: var(--subtle-text-color);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{logo_html}</div>
                    <h1>{APP_NAME}</h1>
                    <p class="version">Version {self.__version__}</p>
                    <p class="description">
                        This Browser is made possible by the DisunicX project and other open source software.
                    </p>
                </div>

                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">{tor_icon}</div>
                        <div class="feature-text">
                            <h3>Tor Integration</h3>
                            <p>Automatically routes traffic through the Tor network for enhanced anonymity.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{privacy_icon}</div>
                        <div class="feature-text">
                            <h3>Privacy Focused</h3>
                            <p>Control cookies, tracking, and security levels to protect your data.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{settings_icon}</div>
                        <div class="feature-text">
                            <h3>Customizable</h3>
                            <p>Personalize your experience with themes, settings, and a bookmarks bar.</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">{updates_icon}</div>
                        <div class="feature-text">
                            <h3>Automatic Updates</h3>
                            <p>Stay up-to-date with the latest features and security patches seamlessly.</p>
                        </div>
                    </div>
                </div>

                <div class="footer">
                    {update_button_html}
                    <div class="footer-links">
                        <a href="https://github.com/SouvikNandi1/disunicx2021" target="_blank">GitHub</a>
                        <a href="https://github.com/SouvikNandi1/disunicx2021/blob/main/LICENSE" target="_blank">License</a>
                    </div>
                    <p class="copyright">Powered by the DisunicX Project. Copyright © {current_year} Souvik Nandi.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def get_new_tab_html(self):
        """Generates the HTML for the modern new tab page, overriding the brand name."""
        settings = QSettings("DisunicX", "Browser")
        search_engine = settings.value("search_engine", "DuckDuckGo")
        theme = self.THEMES.get(self.theme_name, self.THEMES["dark"])

        # --- Background Image Logic ---
        background_image_css = ""
        try:
            # Go up one level from 'bin' to the project root
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Assume an image named 'background.jpg' exists in the project root
            bg_path = os.path.join(app_root, 'background.jpg')
            if os.path.exists(bg_path):
                with open(bg_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                    data_uri = f"data:image/jpeg;base64,{encoded_string}"
                    background_image_css = f"background-image: url('{data_uri}');"
            else:
                # Fallback to a gradient if local file not found
                background_image_css = f"background-image: linear-gradient(to bottom, {theme['TOOLBAR_COLOR']}, {theme['BG_COLOR']});"
        except Exception as e:
            print(f"Could not load background image: {e}")
            # Fallback to a gradient if all else fails
            background_image_css = f"background-image: linear-gradient(to bottom, {theme['TOOLBAR_COLOR']}, {theme['BG_COLOR']});"

        # A helper to convert hex to an RGB string for rgba()
        def hex_to_rgb_string(hex_str):
            h = hex_str.lstrip('#')
            return ', '.join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))

        search_bg_rgb = hex_to_rgb_string(theme['TOOLBAR_COLOR'])
        sidebar_bg_rgb = hex_to_rgb_string(theme['TOOLBAR_COLOR'])
        search_bg_alpha = '0.6' if self.theme_name == 'dark' else '0.85'
        # --- Top Sites Logic ---
        top_sites = self.history_manager.get_top_sites(limit=8)
        top_sites_html = ""
        if top_sites:
            for site in top_sites:
                site_title = site['title']
                try:
                    domain = urllib.parse.urlparse(site['url']).netloc.replace('www.', '')
                    if not site_title or len(site_title) > 20:
                        site_title = domain
                except Exception:
                    site_title = site['title'] if site['title'] else "Link"

                favicon_html = f'<img src="{site["favicon"]}" class="site-favicon" alt="" onerror="this.style.display=\'none\'; this.nextSibling.style.display=\'flex\';">' if site["favicon"] else ''
                placeholder_display = 'none' if site["favicon"] else 'flex'
                
                top_sites_html += f"""
                    <a href="{site['url']}" class="site-tile" title="{html.escape(site['title'])}">
                        <div class="favicon-container">
                            {favicon_html}
                            <div class="site-favicon-placeholder" style="display: {placeholder_display};">
                                {html.escape(site_title[0].upper())}
                            </div>
                        </div>
                        <span class="site-title">{html.escape(site_title)}</span>
                    </a>
                """
        else:
            star_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
            top_sites_html = f"""
                <div class="no-sites-message">
                    {star_icon_svg}
                    <h3>Quick Links</h3>
                    <p>Your frequently visited sites will appear here.</p>
                </div>
            """
        
        # Icons
        search_icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'.replace("currentColor", theme['TAB_TEXT_COLOR'])
        settings_icon_svg = SVG_ICONS['settings_general'].replace("currentColor", theme['TEXT_COLOR'])
        close_icon_svg = SVG_ICONS['close'].replace("currentColor", theme['TEXT_COLOR'])

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Tab</title>
    <style>
        html {{
            overflow: hidden; /* Prevent root-level scrollbars */
        }}
        .clock {{
            position: fixed;
            top: 24px;
            left: 24px;
            font-size: 1.5rem;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            text-shadow: 0 1px 5px rgba(0,0,0,0.3);
            z-index: 10;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        body {{
            background-color: {theme['BG_COLOR']};
            color: {theme['TEXT_COLOR']};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            overflow: hidden; /* Prevent scrollbars from the main body */
        }}
        .background-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            {background_image_css}
            background-size: cover;
            background-position: center;
            z-index: -1;
            filter: brightness(0.6) blur(4px); /* Darken and blur the image */
        }}
        body.background-hidden .background-overlay {{
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease-in-out;
        }}
        .main-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
        }}
        .container {{
            max-width: 600px;
            width: 100%;
            padding: 20px;
            animation: fadeIn 0.5s ease-out forwards;
        }}
        .logo {{
            font-size: 4rem;
            font-weight: 700;
            margin-bottom: 2rem;
            color: {theme['TEXT_COLOR']};
            text-shadow: 0 3px 15px rgba(0,0,0,0.2);
        }}
        .search-form {{
            position: relative;
            margin-bottom: 3rem;
        }}
        .search-input {{
            width: 100%;
            padding: 16px 24px 16px 56px;
            border-radius: 9999px;
            background-color: rgba({search_bg_rgb}, {search_bg_alpha});
            border: 1px solid rgba(255,255,255,0.1);
            color: {theme['TEXT_COLOR']};
            font-size: 1.1rem;
            outline: none;
            transition: all 0.2s ease;
            box-sizing: border-box;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 10px 20px rgba(0,0,0,0.1);
        }}
        body.background-hidden .search-input {{
            background-color: {theme['TOOLBAR_COLOR']};
            backdrop-filter: none;
        }}
        .search-input:hover {{
            border-color: rgba(255,255,255,0.3);
        }}
        .search-input:focus {{
            border-color: {self.ACCENT_COLOR};
            box-shadow: 0 0 0 3px rgba(63, 81, 181, 0.3);
        }}
        .search-input::placeholder {{
            color: {theme['TAB_TEXT_COLOR']};
        }}
        .search-icon {{
            position: absolute;
            left: 22px;
            top: 50%;
            transform: translateY(-50%);
            width: 22px;
            height: 22px;
            color: {theme['TAB_TEXT_COLOR']};
            pointer-events: none;
        }}
        .top-sites-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px; /* Increased gap */
            transition: opacity 0.3s, transform 0.3s;
        }}
        body.top-sites-hidden .top-sites-grid {{
            opacity: 0;
            transform: scale(0.95);
            pointer-events: none;
        }}
        .no-sites-message {{
            grid-column: 1 / -1; /* Span all columns */
            text-align: center;
            padding: 2rem;
            color: {theme['TAB_TEXT_COLOR']};
            background-color: rgba(0,0,0,0.2);
            border-radius: 12px;
            backdrop-filter: blur(5px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}
        .no-sites-message svg {{
            stroke: {theme['TAB_TEXT_COLOR']};
            margin-bottom: 0.5rem;
        }}
        .no-sites-message h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            margin: 0;
        }}
        .no-sites-message p {{
            font-size: 0.875rem;
            margin: 0;
        }}
        .site-tile {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 12px;
            border-radius: 12px; /* Increased radius */
            text-decoration: none;
            color: {theme['TEXT_COLOR']};
            background-color: rgba(0,0,0,0.2);
            transition: all 0.2s ease-in-out;
            backdrop-filter: blur(5px);
        }}
        body.background-hidden .site-tile {{
            background-color: {theme['TOOLBAR_COLOR']};
            backdrop-filter: none;
        }}
        .site-tile:hover {{
            background-color: rgba(0,0,0,0.4);
            transform: translateY(-4px); /* Increased transform */
            box-shadow: 0 8px 16px rgba(0,0,0,0.25);
        }}
        .site-tile:hover .favicon-container {{
            background-color: rgba(255,255,255,0.1);
        }}
        .favicon-container {{
            width: 48px;
            height: 48px;
            border-radius: 50%; /* Circular */
            background-color: rgba(255,255,255,0.05);
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 12px; /* Increased margin */
            transition: background-color 0.2s ease-in-out;
        }}
        .site-favicon {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
        }}
        .site-favicon-placeholder {{
            width: 100%;
            height: 100%;
            border-radius: 50%; /* Circular */
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 20px;
            font-weight: 700;
            color: {theme['TEXT_COLOR']};
            background-color: {theme['BORDER_COLOR']};
        }}
        .site-title {{
            font-size: 13px; /* Increased size */
            font-weight: 600; /* Semi-bold */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }}

        /* --- Settings Button --- */
        .settings-btn {{
            position: fixed;
            top: 24px;
            right: 24px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            z-index: 99;
        }}
        .settings-btn:hover {{
            background: rgba(0,0,0,0.5);
            transform: scale(1.05);
        }}
        .settings-btn svg {{
            width: 20px;
            height: 20px;
        }}

        /* --- Sidebar --- */
        .sidebar {{
            position: fixed;
            top: 0;
            right: -350px; /* Start off-screen, increased to fully hide */
            width: 300px;
            height: 100%;
            background-color: rgba({sidebar_bg_rgb}, 0.7);
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: -5px 0 25px rgba(0,0,0,0.3);
            z-index: 100;
            transition: right 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), background-color 0.3s;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        .sidebar.is-open {{
            right: 0; /* Slide in */
        }}
        .sidebar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }}
        .sidebar-header h2 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0;
        }}
        .sidebar-close-btn {{
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 5px;
            border-radius: 50%;
        }}
        .sidebar-close-btn:hover {{
            background-color: {theme['BUTTON_HOVER_COLOR']};
        }}
        .sidebar-close-btn svg {{
            width: 18px;
            height: 18px;
        }}
        .setting-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid {theme['BORDER_COLOR']};
        }}
        .setting-row label {{
            font-size: 14px;
        }}

        /* Simple CSS Toggle Switch */
        .toggle-switch {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
        }}
        .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: {theme['BORDER_COLOR']};
            transition: .4s;
            border-radius: 24px;
        }}
        .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }}
        input:checked + .slider {{
            background-color: {self.ACCENT_COLOR};
        }}
        input:checked + .slider:before {{
            transform: translateX(20px);
        }}
    </style>
</head>
<body>
    <div class="background-overlay"></div>

    <div id="clock" class="clock"></div>

    <div class="main-container">
        <div class="container">
            <h1 class="logo">{APP_NAME}</h1>
            <form id="search-form" class="search-form">
                <div class="search-icon">{search_icon_svg}</div>
                <input type="text" id="search-input" class="search-input"
                    placeholder="Search with {search_engine} or enter address" 
                    autocomplete="off" autofocus>
            </form>
            <div class="top-sites-grid">
                {top_sites_html}
            </div>
        </div>
    </div>

    <!-- Settings Button -->
    <button class="settings-btn" id="settings-btn" title="Customize New Tab">
        {settings_icon_svg}
    </button>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h2>Customize</h2>
            <button class="sidebar-close-btn" id="sidebar-close-btn">
                {close_icon_svg}
            </button>
        </div>
        <div class="sidebar-content">
            <div class="setting-row">
                <label for="show-top-sites-toggle">Show Top Sites</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="show-top-sites-toggle">
                    <span class="slider"></span>
                </label>
            </div>
            <div class="setting-row">
                <label for="show-background-toggle">Show Background Image</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="show-background-toggle">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const clockElement = document.getElementById('clock');
            function updateClock() {{
                const now = new Date();
                let hours = now.getHours();
                const minutes = now.getMinutes().toString().padStart(2, '0');
                const ampm = hours >= 12 ? 'PM' : 'AM';
                hours = hours % 12;
                hours = hours ? hours : 12; // Hour '0' should be '12'
                
                clockElement.textContent = `${{hours}}:${{minutes}} ${{ampm}}`;
            }}
            
            updateClock();
            setInterval(updateClock, 1000);

            const searchForm = document.getElementById('search-form');
            const searchInput = document.getElementById('search-input');
            const searchEngine = "{search_engine}";
            
            searchForm.addEventListener('submit', (e) => {{
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {{
                    if ((query.includes('.') && !query.includes(' ')) || query.startsWith('http')) {{
                        let url = query;
                        if (!url.startsWith('http://') && !url.startsWith('https://')) {{
                            url = 'https://' + url;
                        }}
                        window.location.href = url;
                        return;
                    }}

                    const encodedQuery = encodeURIComponent(query);
                    const urls = {{
                        'Google': `https://www.google.com/search?q=${{encodedQuery}}`,
                        'Bing': `https://www.bing.com/search?q=${{encodedQuery}}`,
                        'Yahoo': `https://search.yahoo.com/search?p=${{encodedQuery}}`,
                        'StartPage': `https://www.startpage.com/do/search?query=${{encodedQuery}}`,
                        'Ecosia': `https://www.ecosia.org/search?q=${{encodedQuery}}`,
                        'Disunic': `https://souviknandi1.github.io/search.html#gsc.tab=0&gsc.sort=&gsc.q=${{encodedQuery}}`,
                        'DuckDuckGo': `https://duckduckgo.com/?q=${{encodedQuery}}`
                    }};
                    window.location.href = urls[searchEngine] || urls['DuckDuckGo'];
                }}
            }});

            // --- New Sidebar and Settings Logic ---
            const settingsBtn = document.getElementById('settings-btn');
            const sidebar = document.getElementById('sidebar');
            const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
            const topSitesToggle = document.getElementById('show-top-sites-toggle');
            const backgroundToggle = document.getElementById('show-background-toggle');

            // Open sidebar
            settingsBtn.addEventListener('click', () => {{
                sidebar.classList.add('is-open');
            }});

            // Close sidebar
            sidebarCloseBtn.addEventListener('click', () => {{
                sidebar.classList.remove('is-open');
            }});

            // Handle toggle for showing/hiding top sites
            topSitesToggle.addEventListener('change', (e) => {{
                const show = e.target.checked;
                if (show) {{
                    document.body.classList.remove('top-sites-hidden');
                    localStorage.setItem('showTopSites', 'true');
                }} else {{
                    document.body.classList.add('top-sites-hidden');
                    localStorage.setItem('showTopSites', 'false');
                }}
            }});

            // Load saved preference on start
            const showTopSites = localStorage.getItem('showTopSites') !== 'false'; // Default to true
            topSitesToggle.checked = showTopSites;
            if (!showTopSites) {{
                document.body.classList.add('top-sites-hidden');
            }}

            // Handle toggle for showing/hiding background image
            backgroundToggle.addEventListener('change', (e) => {{
                const show = e.target.checked;
                if (show) {{
                    document.body.classList.remove('background-hidden');
                    localStorage.setItem('showBackgroundImage', 'true');
                }} else {{
                    document.body.classList.add('background-hidden');
                    localStorage.setItem('showBackgroundImage', 'false');
                }}
            }});

            // Load saved preference for background on start
            const showBackgroundImage = localStorage.getItem('showBackgroundImage') !== 'false'; // Default to true
            backgroundToggle.checked = showBackgroundImage;
            if (!showBackgroundImage) {{
                document.body.classList.add('background-hidden');
            }}
        }});
    </script>
</body>
</html>
"""

    def check_for_updates(self, force_check=False):
        """Overrides the default update check to use the custom URL or disable it."""
        if not UPDATE_URL:
            # If no update URL is provided, this feature is disabled.
            if hasattr(self, 'updater'):
                del self.updater
            return

        if not hasattr(self, 'updater') or force_check:
            # Pass the custom URL to the Updater instance.
            self.updater = Updater(current_version=self.__version__, parent=self, repo_or_url=UPDATE_URL)
        
        self.updater.check_for_updates(force_check=force_check)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DisunicX")

    # Determine path for bundled Tor executable
    tor_exe_path = "disunic" # Default for development
    if getattr(sys, 'frozen', False):
        tor_exe_path = resource_path('disunic.exe' if sys.platform == "win32" else 'disunic')

    tor_process = start_tor(tor_executable_path=tor_exe_path)
    main_window = CustomAboutTorBrowser()

    if not main_window.is_shutting_down:
        main_window.show()
        exit_code = app.exec()
    else:
        exit_code = 0
        
    if tor_process:
        tor_process.terminate()
        try:
            tor_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            tor_process.kill()

    sys.exit(exit_code)