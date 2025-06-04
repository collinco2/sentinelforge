#!/usr/bin/env python3
"""
Simple test script to create audit_logs table.
"""

import sqlite3
import os


def create_audit_table():
    """Create audit_logs table if it doesn't exist."""
    db_path = "/Users/Collins/sentinelforge/ioc_store.db"

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if audit_logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if cursor.fetchone():
            print("audit_logs table already exists")
            conn.close()
            return True

        # Create audit_logs table
        print("Creating audit_logs table...")
        cursor.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                original_score INTEGER NOT NULL,
                override_score INTEGER NOT NULL,
                justification TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts (id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_audit_logs_alert_id ON audit_logs(alert_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp)")

        conn.commit()
        conn.close()
        print("audit_logs table created successfully!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    create_audit_table()
