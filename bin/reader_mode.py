# MIT License
#
# Copyright (c) 2021-2026 Souvik Nandi
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

"""
Reader Mode Engine
==================
Distraction-free article reader mode for Neutrino Browser and Qelaro Browser.
Extracts core article text, eliminates advertisements and clutter, and presents
responsive typography with customizable themes.
"""

import json
import html as html_lib
import urllib.parse
from typing import Optional, Dict
from PyQt6.QtCore import QUrl, QObject, pyqtSignal

# JavaScript DOM extractor to find article content and metadata
READER_EXTRACTION_SCRIPT = r"""
(function() {
    function getArticleContent() {
        var selectors = [
            'article',
            '[role="article"]',
            '.post-content',
            '.article-content',
            '.entry-content',
            '.story-body',
            '.main-content',
            'main'
        ];
        
        var element = null;
        for (var i = 0; i < selectors.length; i++) {
            var found = document.querySelector(selectors[i]);
            if (found && found.innerText && found.innerText.trim().length > 200) {
                element = found;
                break;
            }
        }
        
        if (!element) {
            var paragraphs = document.querySelectorAll('p');
            var parentCounts = new Map();
            paragraphs.forEach(function(p) {
                var text = p.innerText.trim();
                if (text.length > 50) {
                    var parent = p.parentElement;
                    if (parent) {
                        parentCounts.set(parent, (parentCounts.get(parent) || 0) + text.length);
                    }
                }
            });
            
            var bestParent = null;
            var maxLen = 0;
            parentCounts.forEach(function(len, node) {
                if (len > maxLen && node.tagName !== 'BODY') {
                    maxLen = len;
                    bestParent = node;
                }
            });
            element = bestParent || document.body;
        }

        var clone = element.cloneNode(true);

        var removeSelectors = [
            'script', 'style', 'iframe', 'noscript', 'nav', 'header', 'footer',
            'aside', '.ad', '.ads', '.advertisement', '.social-share',
            '.comments', '#comments', '.newsletter-signup', '.cookie-banner',
            '[aria-hidden="true"]', 'form', 'button'
        ];
        removeSelectors.forEach(function(sel) {
            var items = clone.querySelectorAll(sel);
            items.forEach(function(el) { el.remove(); });
        });

        var title = "";
        var h1 = document.querySelector('h1');
        if (h1 && h1.innerText.trim()) {
            title = h1.innerText.trim();
        } else {
            title = document.title || "Article";
        }

        var byline = "";
        var authorEl = document.querySelector('[rel="author"], .author, .byline, meta[name="author"]');
        if (authorEl) {
            byline = authorEl.getAttribute('content') || authorEl.innerText || "";
            byline = byline.trim();
        }

        var fullText = clone.innerText || "";
        var wordCount = fullText.trim().split(/\s+/).filter(Boolean).length;
        var readTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));

        return {
            title: title,
            byline: byline,
            wordCount: wordCount,
            readingTime: readTimeMinutes,
            contentHtml: clone.innerHTML,
            originUrl: window.location.href,
            siteName: window.location.hostname
        };
    }
    return JSON.stringify(getArticleContent());
})();
"""

READER_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}} - Reader View</title>
    <style>
        :root {
            --bg-color: #1e1e24;
            --text-color: #e4e4e7;
            --accent-color: #3b82f6;
            --border-color: #2e2e38;
            --header-bg: rgba(30, 30, 36, 0.95);
            --meta-color: #9ca3af;
            --font-family: Georgia, Cambria, "Times New Roman", Times, serif;
            --font-size: 19px;
            --line-height: 1.75;
            --content-width: 740px;
        }

        body.theme-light {
            --bg-color: #ffffff;
            --text-color: #1f2937;
            --header-bg: rgba(255, 255, 255, 0.95);
            --border-color: #e5e7eb;
            --meta-color: #6b7280;
        }

        body.theme-sepia {
            --bg-color: #fbf0d9;
            --text-color: #433422;
            --header-bg: rgba(251, 240, 217, 0.95);
            --border-color: #e6d3b3;
            --meta-color: #7d6b53;
        }

        body.theme-oled {
            --bg-color: #000000;
            --text-color: #d1d5db;
            --header-bg: rgba(0, 0, 0, 0.95);
            --border-color: #1f2937;
            --meta-color: #6b7280;
        }

        body.font-sans {
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        }
        body.font-serif {
            --font-family: Georgia, Cambria, "Times New Roman", Times, serif;
        }
        body.font-mono {
            --font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-family);
            font-size: var(--font-size);
            line-height: var(--line-height);
            transition: background-color 0.2s ease, color 0.2s ease;
        }

        .reader-toolbar {
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 20px;
            background: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(8px);
        }

        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }

        .btn-primary {
            background: var(--accent-color);
            color: #ffffff !important;
            border-color: var(--accent-color);
        }

        .article-container {
            max-width: var(--content-width);
            margin: 40px auto 100px auto;
            padding: 0 24px;
        }

        .article-header {
            margin-bottom: 35px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }

        h1.article-title {
            font-size: 2.2rem;
            line-height: 1.25;
            font-weight: 800;
            margin-bottom: 15px;
            letter-spacing: -0.02em;
        }

        .article-meta {
            color: var(--meta-color);
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .article-body p {
            margin-bottom: 1.4em;
        }

        .article-body h2, .article-body h3, .article-body h4 {
            margin-top: 1.8em;
            margin-bottom: 0.8em;
            line-height: 1.3;
            font-weight: 700;
        }

        .article-body ul, .article-body ol {
            margin-bottom: 1.4em;
            padding-left: 28px;
        }

        .article-body li {
            margin-bottom: 0.5em;
        }

        .article-body blockquote {
            border-left: 4px solid var(--accent-color);
            padding-left: 18px;
            margin: 1.8em 0;
            color: var(--meta-color);
            font-style: italic;
        }

        .article-body img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 20px auto;
            display: block;
        }

        .article-body a {
            color: var(--accent-color);
            text-decoration: underline;
        }

        .article-body pre, .article-body code {
            background: rgba(125, 125, 125, 0.15);
            border-radius: 4px;
            font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
        }

        .article-body pre {
            padding: 16px;
            overflow-x: auto;
            margin-bottom: 1.4em;
        }

        .article-body code {
            padding: 2px 6px;
            font-size: 0.9em;
        }

        @media (max-width: 600px) {
            h1.article-title { font-size: 1.7rem; }
            .reader-toolbar { padding: 8px 12px; }
            .btn { padding: 4px 8px; font-size: 12px; }
        }
    </style>
</head>
<body class="theme-dark font-serif">

    <div class="reader-toolbar">
        <div class="toolbar-group">
            <button class="btn btn-primary" onclick="window.history.back()">Exit Reader</button>
            <a class="btn" href="{{ORIGIN_URL}}">Original Page</a>
        </div>

        <div class="toolbar-group">
            <button class="btn" onclick="setTheme('light')" title="Light Theme">Light</button>
            <button class="btn" onclick="setTheme('sepia')" title="Sepia Theme">Sepia</button>
            <button class="btn" onclick="setTheme('dark')" title="Dark Theme">Dark</button>
            <button class="btn" onclick="setTheme('oled')" title="AMOLED Black">Black</button>

            <button class="btn" onclick="setFont('serif')" title="Serif Font">Serif</button>
            <button class="btn" onclick="setFont('sans')" title="Sans-serif Font">Sans</button>

            <button class="btn" onclick="adjustFontSize(-2)" title="Decrease Font">A-</button>
            <button class="btn" onclick="adjustFontSize(2)" title="Increase Font">A+</button>
            <button class="btn" onclick="window.print()" title="Print / PDF">Print</button>
        </div>
    </div>

    <main class="article-container">
        <header class="article-header">
            <h1 class="article-title">{{TITLE}}</h1>
            <div class="article-meta">{{META_HTML}}</div>
        </header>

        <article class="article-body">
            {{CONTENT_HTML}}
        </article>
    </main>

    <script>
        var currentFontSize = 19;

        function setTheme(name) {
            document.body.classList.remove('theme-light', 'theme-sepia', 'theme-dark', 'theme-oled');
            document.body.classList.add('theme-' + name);
            try { localStorage.setItem('reader_theme', name); } catch(e) {}
        }

        function setFont(family) {
            document.body.classList.remove('font-sans', 'font-serif', 'font-mono');
            document.body.classList.add('font-' + family);
            try { localStorage.setItem('reader_font', family); } catch(e) {}
        }

        function adjustFontSize(delta) {
            currentFontSize = Math.max(14, Math.min(32, currentFontSize + delta));
            document.documentElement.style.setProperty('--font-size', currentFontSize + 'px');
            try { localStorage.setItem('reader_size', currentFontSize); } catch(e) {}
        }

        try {
            var savedTheme = localStorage.getItem('reader_theme');
            if (savedTheme) setTheme(savedTheme);
            var savedFont = localStorage.getItem('reader_font');
            if (savedFont) setFont(savedFont);
            var savedSize = localStorage.getItem('reader_size');
            if (savedSize) {
                currentFontSize = parseInt(savedSize, 10);
                document.documentElement.style.setProperty('--font-size', currentFontSize + 'px');
            }
        } catch(e) {}
    </script>
</body>
</html>
"""


class ReaderModeManager(QObject):
    """
    Coordinates extraction of articles and loads reader view HTML.
    Designed for reuse across Neutrino Browser and Qelaro Browser.
    """
    readerModeToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_urls: Dict[int, str] = {}

    def is_active(self, browser_tab) -> bool:
        """Returns True if the given browser tab is currently in Reader Mode."""
        return getattr(browser_tab, "in_reader_mode", False)

    def toggle(self, browser_tab):
        """Toggles reader mode on or off for the given tab."""
        if self.is_active(browser_tab):
            self.exit_reader(browser_tab)
        else:
            self.enter_reader(browser_tab)

    def enter_reader(self, browser_tab):
        """Extracts article content and loads the distraction-free reader template."""
        if not browser_tab or not browser_tab.url().isValid():
            return

        current_url = browser_tab.url().toString()
        if current_url.startswith(("neutrino:", "disunic:", "about:", "qelaro:")):
            return

        tab_id = id(browser_tab)
        self.original_urls[tab_id] = current_url

        def on_extracted(result_json):
            if not result_json:
                return
            try:
                data = json.loads(result_json)
                if not data or not data.get("contentHtml"):
                    return
                html = self.generate_reader_html(data)
                browser_tab.in_reader_mode = True
                browser_tab.reader_data = data
                browser_tab.setHtml(html, QUrl(current_url))
                self.readerModeToggled.emit(True)
            except Exception as e:
                print(f"ReaderMode: Failed to load reader view: {e}")

        browser_tab.page().runJavaScript(READER_EXTRACTION_SCRIPT, on_extracted)

    def exit_reader(self, browser_tab):
        """Restores the original web page for the given tab."""
        tab_id = id(browser_tab)
        orig_url = self.original_urls.pop(tab_id, None)
        browser_tab.in_reader_mode = False
        browser_tab.reader_data = None
        self.readerModeToggled.emit(False)

        if orig_url:
            browser_tab.setUrl(QUrl(orig_url))
        else:
            browser_tab.reload()

    def generate_reader_html(self, data: Dict) -> str:
        """Builds clean, self-contained, responsive Reader Mode HTML."""
        title = data.get("title", "Article")
        byline = data.get("byline", "")
        site_name = data.get("siteName", "")
        reading_time = data.get("readingTime", 1)
        word_count = data.get("wordCount", 0)
        content_html = data.get("contentHtml", "")
        origin_url = data.get("originUrl", "#")

        meta_parts = []
        if site_name:
            meta_parts.append(f"<span>{html_lib.escape(site_name)}</span>")
        if byline:
            meta_parts.append(f"<span>By {html_lib.escape(byline)}</span>")
        meta_parts.append(f"<span>{reading_time} min read ({word_count} words)</span>")
        meta_html = " • ".join(meta_parts)

        return (
            READER_HTML_TEMPLATE
            .replace("{{TITLE}}", html_lib.escape(title))
            .replace("{{META_HTML}}", meta_html)
            .replace("{{CONTENT_HTML}}", content_html)
            .replace("{{ORIGIN_URL}}", origin_url)
        )
