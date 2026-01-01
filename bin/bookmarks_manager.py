import sqlite3
import os
from datetime import datetime
from bin.utils import get_profile_path

class BookmarksManager:
    def __init__(self):
        db_path = os.path.join(get_profile_path(), "bookmarks.db")
        self.conn = sqlite3.connect(db_path)
        self.create_table()
        
    def create_table(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'")
            table_exists = cursor.fetchone()

            if not table_exists:
                cursor.execute("""
                    CREATE TABLE bookmarks (
                        id INTEGER PRIMARY KEY,
                        url TEXT NOT NULL UNIQUE,
                        title TEXT,
                        date_added TIMESTAMP NOT NULL,
                        icon TEXT,
                        order_index INTEGER
                    )
                """)
            else:
                cursor.execute("PRAGMA table_info(bookmarks)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'order_index' not in columns:
                    cursor.execute("ALTER TABLE bookmarks ADD COLUMN order_index INTEGER")
                    cursor.execute("SELECT id FROM bookmarks ORDER BY date_added ASC")
                    bookmark_ids = cursor.fetchall()
                    for index, (bookmark_id,) in enumerate(bookmark_ids):
                        cursor.execute("UPDATE bookmarks SET order_index = ? WHERE id = ?", (index, bookmark_id))

    def get_bookmarks(self):
        """Returns a list of all bookmarks."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, url, date_added, icon FROM bookmarks ORDER BY order_index ASC")
        return cursor.fetchall()
            
    def add_bookmark(self, title, url, icon_data=None):
        """Adds a new bookmark. Returns True if successful, False if it already exists."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT MAX(order_index) FROM bookmarks")
                max_index = cursor.fetchone()[0]
                next_index = 0 if max_index is None else max_index + 1

                self.conn.execute(
                    "INSERT INTO bookmarks (url, title, date_added, icon, order_index) VALUES (?, ?, ?, ?, ?)",
                    (url, title, datetime.now(), icon_data, next_index)
                )
            return True
        except sqlite3.IntegrityError:
            print(f"Bookmark for {url} already exists.")
            return False
        
    def remove_bookmark(self, url):
        """Removes a bookmark by its URL."""
        with self.conn:
            self.conn.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
        self.reindex_bookmarks()

    def reindex_bookmarks(self):
        """Re-calculates order_index for all bookmarks to remove gaps, preserving relative order."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM bookmarks ORDER BY order_index ASC")
            ids = cursor.fetchall()
            for index, (bookmark_id,) in enumerate(ids):
                cursor.execute("UPDATE bookmarks SET order_index = ? WHERE id = ?", (index, bookmark_id))

    def is_bookmarked(self, url):
        """Checks if a URL is already bookmarked."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM bookmarks WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def update_order(self, url_list):
        """Updates the order of all bookmarks based on a list of URLs."""
        with self.conn:
            for index, url in enumerate(url_list):
                self.conn.execute("UPDATE bookmarks SET order_index = ? WHERE url = ?", (index, url))