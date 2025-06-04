#!/usr/bin/env python3
"""
Migration script to add risk_score column to the alerts table.
"""

import sqlite3
import logging
import random
from pathlib import Path

# Use the same database URL from settings
from sentinelforge.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("risk_score_migration")


def migrate_database():
    """Add risk_score column to alerts table if it doesn't exist."""
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

        # Check if risk_score column already exists
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [column[1] for column in cursor.fetchall()]

        if "risk_score" not in columns:
            logger.info("Adding risk_score column to alerts table")
            cursor.execute(
                "ALTER TABLE alerts ADD COLUMN risk_score INTEGER NOT NULL DEFAULT 50"
            )

            # Update existing alerts with diverse risk scores based on severity and confidence
            logger.info("Updating existing alerts with calculated risk scores")

            # Get all existing alerts
            cursor.execute("SELECT id, severity, confidence FROM alerts")
            alerts = cursor.fetchall()

            for alert_id, severity, confidence in alerts:
                # Calculate risk score based on severity and confidence
                risk_score = calculate_risk_score(severity, confidence, alert_id)
                cursor.execute(
                    "UPDATE alerts SET risk_score = ? WHERE id = ?",
                    (risk_score, alert_id),
                )

            conn.commit()
            logger.info(
                f"Risk score column added and {len(alerts)} alerts updated successfully"
            )
        else:
            logger.info("Risk score column already exists")

        # Close connection
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if "conn" in locals():
            conn.rollback()
            conn.close()
        return False


def calculate_risk_score(severity, confidence, alert_id):
    """Calculate risk score based on severity, confidence, and some randomization."""
    # Base score from severity
    severity_scores = {
        "critical": 85,
        "high": 70,
        "medium": 50,
        "low": 25,
    }

    base_score = severity_scores.get(severity.lower() if severity else "medium", 50)

    # Adjust based on confidence (0-100)
    confidence_factor = (confidence or 50) / 100.0
    adjusted_score = base_score * (
        0.7 + 0.3 * confidence_factor
    )  # 70-100% of base score

    # Add some controlled randomization based on alert_id for consistency
    random.seed(alert_id)
    variation = random.randint(-10, 10)
    final_score = int(adjusted_score + variation)

    # Ensure score is within 0-100 range
    return max(0, min(100, final_score))


def update_migration_script():
    """Update the main migration script to include risk_score in new alert creation."""
    logger.info("Updating migrate_alerts.py to include risk_score in sample data")

    try:
        # Read the current migration script
        with open("migrate_alerts.py", "r") as f:
            content = f.read()

        # Check if risk_score is already included
        if "risk_score" in content:
            logger.info("migrate_alerts.py already includes risk_score")
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
                    source VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""

        # Update sample data to include risk_score
        old_sample = """sample_alerts = [
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
            ]"""

        new_sample = """sample_alerts = [
                (
                    "Suspicious Network Connection",
                    "Alert triggered by detection of domain example.com in network traffic.",
                    1651234567,
                    "2022-04-29 12:34:56",
                    "Command and Control",
                    "High",
                    85,
                    78,  # risk_score
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
                    92,  # risk_score
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
                    55,  # risk_score
                    "Firewall",
                ),
            ]"""

        # Update INSERT statement
        old_insert = """INSERT INTO alerts (name, description, timestamp, formatted_time, threat_type, severity, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

        new_insert = """INSERT INTO alerts (name, description, timestamp, formatted_time, threat_type, severity, confidence, risk_score, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        # Apply replacements
        content = content.replace(old_create, new_create)
        content = content.replace(old_sample, new_sample)
        content = content.replace(old_insert, new_insert)

        # Write back the updated content
        with open("migrate_alerts.py", "w") as f:
            f.write(content)

        logger.info("migrate_alerts.py updated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to update migrate_alerts.py: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting risk_score database migration")
    if migrate_database():
        logger.info("Migration completed successfully")
        # Also update the main migration script for future use
        update_migration_script()
    else:
        logger.error("Migration failed")
