#!/usr/bin/env python3
"""
Migration script to add the explanation_data column to the iocs table.
"""

import sqlite3
import logging
from pathlib import Path

# Use the same database URL from settings
from sentinelforge.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("db_migration")


def migrate_database():
    """Add explanation_data column to the iocs table if it doesn't exist."""
    # Parse the SQLite database path from the URL
    db_path = settings.database_url.replace("sqlite:///", "").replace("./", "")
    logger.info(f"Using database at: {db_path}")

    # Check if the database file exists
    if not Path(db_path).exists():
        logger.error(f"Database file not found at {db_path}")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if explanation_data column exists
        cursor.execute("PRAGMA table_info(iocs)")
        columns = [column[1] for column in cursor.fetchall()]

        if "explanation_data" not in columns:
            logger.info("Adding explanation_data column to iocs table")
            cursor.execute("ALTER TABLE iocs ADD COLUMN explanation_data JSON")
            conn.commit()
            logger.info("Column added successfully")
        else:
            logger.info("explanation_data column already exists")

        # Close connection
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting database migration")
    if migrate_database():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
