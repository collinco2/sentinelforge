#!/usr/bin/env python3
"""
Migration script to add overridden_risk_score column to the alerts table.
"""

import sqlite3
import logging
from pathlib import Path

# Use the same database URL from settings
from sentinelforge.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("overridden_risk_score_migration")


def migrate_database():
    """Add overridden_risk_score column to alerts table if it doesn't exist."""
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

        # Check if alerts table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        )
        alerts_table_exists = cursor.fetchone() is not None

        if not alerts_table_exists:
            logger.error("Alerts table does not exist. Run migrate_alerts.py first.")
            conn.close()
            return False

        # Check if overridden_risk_score column already exists
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [column[1] for column in cursor.fetchall()]

        if "overridden_risk_score" not in columns:
            logger.info("Adding overridden_risk_score column to alerts table")
            cursor.execute(
                "ALTER TABLE alerts ADD COLUMN overridden_risk_score INTEGER"
            )

            conn.commit()
            logger.info("overridden_risk_score column added successfully")
        else:
            logger.info("overridden_risk_score column already exists")

        # Close connection
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if "conn" in locals():
            conn.rollback()
            conn.close()
        return False


def update_migration_script():
    """Update the main migration script to include overridden_risk_score in new alert creation."""
    logger.info("Updating migrate_alerts.py to include overridden_risk_score in schema")

    try:
        # Read the current migration script
        with open("migrate_alerts.py", "r") as f:
            content = f.read()

        # Check if overridden_risk_score is already included
        if "overridden_risk_score" in content:
            logger.info("migrate_alerts.py already includes overridden_risk_score")
            return True

        # Update the CREATE TABLE statement
        old_create = """CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    timestamp INTEGER NOT NULL,
                    formatted_time VARCHAR(50),
                    threat_type VARCHAR(100),
                    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
                    confidence INTEGER NOT NULL DEFAULT 50,
                    risk_score INTEGER NOT NULL DEFAULT 50,
                    source VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""

        new_create = """CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    timestamp INTEGER NOT NULL,
                    formatted_time VARCHAR(50),
                    threat_type VARCHAR(100),
                    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
                    confidence INTEGER NOT NULL DEFAULT 50,
                    risk_score INTEGER NOT NULL DEFAULT 50,
                    overridden_risk_score INTEGER,
                    source VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""

        # Apply replacement
        content = content.replace(old_create, new_create)

        # Write back the updated content
        with open("migrate_alerts.py", "w") as f:
            f.write(content)

        logger.info("migrate_alerts.py updated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to update migrate_alerts.py: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting overridden_risk_score database migration")
    if migrate_database():
        logger.info("Migration completed successfully")
        # Also update the main migration script for future use
        update_migration_script()
    else:
        logger.error("Migration failed")
