#!/usr/bin/env python3
"""
Migration script to add the audit_logs table for tracking alert risk score overrides.
"""

import sqlite3
import logging
from pathlib import Path

# Use the same database URL from settings
from sentinelforge.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("audit_logs_migration")


def migrate_database():
    """Add audit_logs table if it doesn't exist."""
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

        # Check if audit_logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if cursor.fetchone():
            logger.info("audit_logs table already exists")
            conn.close()
            return True

        # Create audit_logs table
        logger.info("Creating audit_logs table")
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

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX idx_audit_logs_alert_id ON audit_logs(alert_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp)")

        conn.commit()
        logger.info("audit_logs table created successfully with indexes")

        # Close connection
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def update_main_migration():
    """Update the main migration script to include audit_logs table creation."""
    try:
        # Read the current migrate_alerts.py file
        with open("migrate_alerts.py", "r") as f:
            content = f.read()

        # Check if audit_logs table is already in the migration
        if "audit_logs" in content:
            logger.info("migrate_alerts.py already includes audit_logs table")
            return True

        # Find the alerts table creation and add audit_logs after it
        old_pattern = '''        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
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
            )
        """)'''

        new_pattern = '''        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
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
            )
        """)

        # Create audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
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

        # Create indexes for audit_logs
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_alert_id ON audit_logs(alert_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)")'''

        # Apply replacement
        content = content.replace(old_pattern, new_pattern)

        # Write back the updated content
        with open("migrate_alerts.py", "w") as f:
            f.write(content)

        logger.info("migrate_alerts.py updated successfully with audit_logs table")
        return True

    except Exception as e:
        logger.error(f"Failed to update migrate_alerts.py: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔧 Starting audit_logs table migration")

    # Run the migration
    if migrate_database():
        logger.info("✅ Database migration completed successfully")

        # Update the main migration script
        if update_main_migration():
            logger.info("✅ Main migration script updated successfully")
        else:
            logger.warning("⚠️ Failed to update main migration script")
    else:
        logger.error("❌ Database migration failed")
        exit(1)

    logger.info("🎯 Audit logging system database setup complete!")
