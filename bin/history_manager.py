import sqlite3
import os
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse, urlunparse
from bin.utils import get_profile_path

class HistoryManager:
    def __init__(self):
        db_path = os.path.join(get_profile_path(), "history.db")
        self.conn = sqlite3.connect(db_path)
        self.create_table()
        self.create_downloads_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    visit_time TIMESTAMP NOT NULL,
                    favicon TEXT
                )
            """)

    def create_downloads_table(self):
        """Creates the table for storing persistent download history."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY,
                    url TEXT,
                    path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    total_bytes INTEGER,
                    state TEXT NOT NULL,
                    end_time TIMESTAMP NOT NULL
                )
            """)

    def add_visit(self, url, title, favicon_base64=None):
        if url.startswith("disunic://") or url.startswith("about:"):
            return
        with self.conn:
            self.conn.execute(
                "INSERT INTO history (url, title, visit_time, favicon) VALUES (?, ?, ?, ?)",
                (url, title, datetime.now(), favicon_base64)
            )

    def get_top_sites(self, limit=8):
        """
        Gets the most frequently visited sites (by domain).
        Returns a list of dicts: {'title': str, 'url': str, 'favicon': str}
        """
        cursor = self.conn.cursor()
        # Fetch all URLs and titles, we'll process them in Python
        cursor.execute("SELECT url, title, favicon FROM history ORDER BY visit_time DESC")
        all_visits = cursor.fetchall()

        if not all_visits:
            return []

        domain_info = {}
        domain_counts = Counter()

        for url_str, title, favicon in all_visits:
            if url_str.startswith(("disunic://", "about:")):
                continue
            try:
                parsed_url = urlparse(url_str)
                domain = parsed_url.netloc
                if domain:
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    domain_counts[domain] += 1
                    
                    # Store the most recent title and favicon for this domain, and the base URL
                    if domain not in domain_info:
                        base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
                        domain_info[domain] = {
                            'title': title if title else domain, 
                            'url': base_url, 
                            'favicon': favicon
                        }
            except Exception:
                continue # Ignore parsing errors

        top_sites_result = []
        for domain, _ in domain_counts.most_common(limit):
            if domain in domain_info:
                top_sites_result.append(domain_info[domain])
        
        return top_sites_result

    def get_history(self, limit=200):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, url, title, visit_time, favicon FROM history ORDER BY visit_time DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def search_history(self, term):
        cursor = self.conn.cursor()
        search_term = f"%{term}%"
        cursor.execute(
            "SELECT id, url, title, visit_time, favicon FROM history WHERE title LIKE ? OR url LIKE ? ORDER BY visit_time DESC",
            (search_term, search_term)
        )
        return cursor.fetchall()

    def remove_visit(self, history_id):
        """Removes a specific history entry by its ID."""
        with self.conn:
            self.conn.execute("DELETE FROM history WHERE id = ?", (history_id,))

    def clear_history(self):
        with self.conn:
            self.conn.execute("DELETE FROM history")

    def add_finished_download(self, data):
        """Adds a completed download record to the database."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO downloads (url, path, filename, total_bytes, state, end_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data['url'],
                    data['path'],
                    data['filename'],
                    data['total_bytes'],
                    data['state'],
                    data['end_time']
                )
            )

    def get_all_downloads(self):
        """Returns a list of all persisted downloads."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT url, path, filename, total_bytes, state, end_time FROM downloads ORDER BY end_time DESC")
        return cursor.fetchall()

    def remove_download(self, path):
        """Removes a download record by its path."""
        with self.conn:
            self.conn.execute("DELETE FROM downloads WHERE path = ?", (path,))

    def clear_all_downloads(self):
        """Removes all download records."""
        with self.conn:
            self.conn.execute("DELETE FROM downloads")