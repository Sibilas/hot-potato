import sqlite3
import os
import threading
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SQLITE_BACKUP_PATH = os.environ.get("SQLITE_BACKUP_PATH", "app/data/hotpotato.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS enrollments (
    id TEXT PRIMARY KEY,
    queue TEXT NOT NULL,
    target_url TEXT NOT NULL,
    subscription_args TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class DatabaseManager:
    def __init__(self, backup_path=SQLITE_BACKUP_PATH):
        self.backup_path = backup_path
        self.lock = threading.Lock()
        # Create an in-memory database; using check_same_thread=False to allow usage from multiple threads.
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._restore_from_disk()

    def _init_db(self):
        """Initializes the database schema if not already present."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.executescript(SCHEMA)
            self.conn.commit()
            logger.info("Initialized in-memory SQLite database with required schema.")

    def _restore_from_disk(self):
        """
        Restores the in-memory database from the persistent backup file,
        if it exists and is not empty.
        """
        if os.path.exists(self.backup_path) and os.path.getsize(self.backup_path) > 0:
            try:
                disk_conn = sqlite3.connect(self.backup_path)
                disk_conn.row_factory = sqlite3.Row
                disk_conn.backup(self.conn)
                disk_conn.close()
                logger.info("Restored in-memory database from disk backup '%s'.", self.backup_path)
            except Exception as e:
                logger.error("Failed to restore from disk: %s", e)
        else:
            logger.info("No valid disk backup found at '%s'; starting with a fresh in-memory database.", self.backup_path)

    def backup_to_disk(self):
        """
        Backs up the current in-memory database to the persistent file.
        This method is intended to run in a separate thread.
        """
        with self.lock:
            try:
                disk_conn = sqlite3.connect(self.backup_path)
                disk_conn.row_factory = sqlite3.Row
                self.conn.backup(disk_conn)
                disk_conn.commit()
                disk_conn.close()
                logger.info("Backed up in-memory database to disk at '%s'.", self.backup_path)
            except Exception as e:
                logger.error("Backup to disk failed: %s", e)

    def execute(self, query, params=None):
        """
        Executes a given SQL query (INSERT, UPDATE, DELETE) and commits the change.
        Instead of blocking until the backup is finished, the backup is scheduled to run in a separate thread.
        """
        with self.lock:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
        # Schedule backup_to_disk() to run in a separate daemon thread.
        threading.Thread(target=self.backup_to_disk, daemon=True).start()
        return cursor

    def query(self, query, params=None):
        """Executes a query and returns all fetched rows."""
        with self.lock:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return rows

    def close(self):
        """Closes the in-memory database connection."""
        with self.lock:
            self.conn.close()
            logger.info("Closed in-memory database connection.")

# Singleton instance for use throughout the application.
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Example usage for testing.
    enrollment_id = "test-123"
    db_manager.execute(
        "INSERT OR REPLACE INTO enrollments (id, queue, target_url, subscription_args) VALUES (?, ?, ?, ?)",
        (enrollment_id, "chat.test", "http://client-app/api/messages", '{"durable": true}')
    )
    rows = db_manager.query("SELECT * FROM enrollments")
    for row in rows:
        print(dict(row))
    # Trigger a manual backup (if needed).
    db_manager.backup_to_disk()
