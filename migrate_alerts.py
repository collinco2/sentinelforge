#!/usr/bin/env python3
"""
Migration script to add Alert table and IOC-Alert relationship table.
"""

import sqlite3
import logging
from pathlib import Path

# Use the same database URL from settings
from sentinelforge.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("alerts_migration")


def migrate_database():
    """Add Alert table and IOC-Alert junction table if they don't exist."""
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
            logger.info("Creating alerts table")
            cursor.execute("""
                CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    timestamp INTEGER NOT NULL,
                    formatted_time VARCHAR(50),
                    threat_type VARCHAR(100),
                    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
                    confidence INTEGER NOT NULL DEFAULT 50,
                    source VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Alerts table created successfully")
        else:
            logger.info("Alerts table already exists")

        # Check if ioc_alert junction table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ioc_alert'"
        )
        junction_table_exists = cursor.fetchone() is not None

        if not junction_table_exists:
            logger.info("Creating ioc_alert junction table")
            cursor.execute("""
                CREATE TABLE ioc_alert (
                    alert_id INTEGER NOT NULL,
                    ioc_type VARCHAR NOT NULL,
                    ioc_value VARCHAR NOT NULL,
                    PRIMARY KEY (alert_id, ioc_type, ioc_value),
                    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
                    FOREIGN KEY (ioc_type, ioc_value) REFERENCES iocs(ioc_type, ioc_value) ON DELETE CASCADE
                )
            """)
            logger.info("IOC-Alert junction table created successfully")
        else:
            logger.info("IOC-Alert junction table already exists")

        # Commit changes
        conn.commit()

        # Add some sample alert data for testing
        if not alerts_table_exists:
            logger.info("Adding sample alert data")
            sample_alerts = [
                (
                    "Suspicious Network Connection",
                    "Alert triggered by detection of domain example.com in network traffic.",
                    1651234567,
                    "2022-04-29 12:34:56",
                    "Command and Control",
                    "High",
                    85,
                    "SIEM",
                ),
                (
                    "Malicious File Download",
                    "Detected download from known malicious domain malicious-example.com",
                    1651234800,
                    "2022-04-29 12:40:00",
                    "Malware",
                    "Critical",
                    95,
                    "EDR",
                ),
                (
                    "Suspicious IP Communication",
                    "Communication detected with suspicious IP address 192.168.1.100",
                    1651235000,
                    "2022-04-29 12:43:20",
                    "Reconnaissance",
                    "Medium",
                    70,
                    "Firewall",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO alerts (name, description, timestamp, formatted_time, threat_type, severity, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                sample_alerts,
            )

            # Add some IOC-Alert relationships
            logger.info("Adding sample IOC-Alert relationships")

            # First, check if we have some IOCs to relate to
            cursor.execute("SELECT ioc_type, ioc_value FROM iocs LIMIT 3")
            existing_iocs = cursor.fetchall()

            if existing_iocs:
                # Create relationships between alerts and IOCs
                relationships = []
                for i, (ioc_type, ioc_value) in enumerate(existing_iocs):
                    # Associate each IOC with the first alert (alert_id = 1)
                    relationships.append((1, ioc_type, ioc_value))

                    # Associate some IOCs with multiple alerts
                    if i < 2:
                        relationships.append((2, ioc_type, ioc_value))

                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO ioc_alert (alert_id, ioc_type, ioc_value)
                    VALUES (?, ?, ?)
                """,
                    relationships,
                )

                logger.info(f"Added {len(relationships)} IOC-Alert relationships")
            else:
                logger.info("No existing IOCs found, skipping relationship creation")

            conn.commit()
            logger.info("Sample data added successfully")

        # Close connection
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if "conn" in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    logger.info("Starting alerts database migration")
    if migrate_database():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
