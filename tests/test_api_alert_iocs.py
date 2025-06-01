#!/usr/bin/env python3
"""
Unit tests for the Alert IOCs endpoint in the API server.
"""

import json
import unittest
import sys
import os
import tempfile
import sqlite3

# Add the parent directory to sys.path to import api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import api_server
from api_server import app


class TestApiAlertIocsEndpoint(unittest.TestCase):
    """Tests for the Alert IOCs endpoint."""

    def setUp(self):
        """Set up the test client and mock database."""
        self.app = app.test_client()

        # Create a temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()

        # Create test database schema
        self.setup_test_database()

        # Mock the database connection to use our test database
        self.original_get_db_connection = api_server.get_db_connection
        api_server.get_db_connection = self.mock_get_db_connection

    def tearDown(self):
        """Clean up test database."""
        api_server.get_db_connection = self.original_get_db_connection
        os.unlink(self.test_db_path)

    def mock_get_db_connection(self):
        """Mock database connection for testing."""
        conn = sqlite3.connect(self.test_db_path)

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                if col[0]:
                    d[col[0]] = row[idx]
                    if col[0] == "ioc_value":
                        d["value"] = row[idx]
            return d

        conn.row_factory = dict_factory
        return conn

    def setup_test_database(self):
        """Set up test database with sample data."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE iocs (
                id INTEGER PRIMARY KEY,
                ioc_type TEXT,
                ioc_value TEXT,
                score REAL,
                first_seen_timestamp REAL,
                tags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                severity TEXT,
                confidence INTEGER,
                description TEXT,
                timestamp REAL,
                threat_type TEXT,
                source TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE ioc_alert (
                alert_id INTEGER,
                ioc_id INTEGER,
                ioc_value TEXT,
                FOREIGN KEY (alert_id) REFERENCES alerts (id),
                FOREIGN KEY (ioc_id) REFERENCES iocs (id)
            )
        """)

        # Insert test IOCs
        cursor.execute("""
            INSERT INTO iocs (id, ioc_type, ioc_value, score, first_seen_timestamp)
            VALUES (1, 'domain', 'example.com', 9.0, 1651234567)
        """)

        cursor.execute("""
            INSERT INTO iocs (id, ioc_type, ioc_value, score, first_seen_timestamp)
            VALUES (2, 'ip', '1.1.1.1', 7.2, 1651234567)
        """)

        cursor.execute("""
            INSERT INTO iocs (id, ioc_type, ioc_value, score, first_seen_timestamp)
            VALUES (3, 'url', 'https://malicious-site.com/download.exe', 8.5, 1651234567)
        """)

        # Insert test alerts
        cursor.execute("""
            INSERT INTO alerts (id, name, severity, confidence, description, timestamp, threat_type, source)
            VALUES (1, 'Suspicious Network Connection', 'High', 85,
                   'Alert triggered by detection of domain example.com', 1651234567, 'Command and Control', 'SIEM')
        """)

        cursor.execute("""
            INSERT INTO alerts (id, name, severity, confidence, description, timestamp, threat_type, source)
            VALUES (2, 'Multiple IOC Detection', 'Critical', 92,
                   'Multiple IOCs detected: domain example.com, IP 1.1.1.1, and URL https://malicious-site.com/download.exe',
                   1667890123, 'Malware', 'EDR')
        """)

        # Insert IOC-Alert relationships
        cursor.execute("""
            INSERT INTO ioc_alert (alert_id, ioc_id, ioc_value)
            VALUES (2, 1, 'example.com')
        """)

        cursor.execute("""
            INSERT INTO ioc_alert (alert_id, ioc_id, ioc_value)
            VALUES (2, 2, '1.1.1.1')
        """)

        cursor.execute("""
            INSERT INTO ioc_alert (alert_id, ioc_id, ioc_value)
            VALUES (2, 3, 'https://malicious-site.com/download.exe')
        """)

        conn.commit()
        conn.close()

    def test_get_alert_iocs_success(self):
        """Test successful retrieval of IOCs for an alert."""
        # Test for alert with multiple known IOCs (alert ID 2)
        response = self.app.get("/api/alert/2/iocs")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["alert_id"], 2)

        # We should have exactly 3 IOCs associated with this alert
        self.assertEqual(data["total_iocs"], 3)
        self.assertEqual(len(data["iocs"]), 3)

        # Verify that all expected IOCs are present
        ioc_values = [ioc.get("value") for ioc in data["iocs"]]
        self.assertIn("example.com", ioc_values)
        self.assertIn("1.1.1.1", ioc_values)
        self.assertIn("https://malicious-site.com/download.exe", ioc_values)

    def test_get_alert_iocs_single(self):
        """Test retrieval of IOCs for an alert with a single IOC."""
        # Test for alert with single IOC (alert ID 1)
        response = self.app.get("/api/alert/1/iocs")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["alert_id"], 1)
        self.assertEqual(
            data["total_iocs"], 0
        )  # Alert 1 has no IOC associations in our test data

    def test_get_alert_iocs_not_found(self):
        """Test 404 response when alert is not found."""
        response = self.app.get("/api/alert/999/iocs")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", data)

    def test_api_alerts_endpoint(self):
        """Test that the alerts endpoint works with database."""
        response = self.app.get("/api/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("alerts", data)
        self.assertIn("total", data)
        self.assertEqual(len(data["alerts"]), 2)  # We have 2 test alerts


if __name__ == "__main__":
    unittest.main()
