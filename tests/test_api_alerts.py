#!/usr/bin/env python3
"""
Unit tests for the IOC-to-alerts endpoint in the API server.
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


class TestApiAlertsEndpoint(unittest.TestCase):
    """Tests for the IOC-to-alerts endpoint."""

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

        # Insert test alerts
        cursor.execute("""
            INSERT INTO alerts (id, name, severity, confidence, description, timestamp, threat_type, source)
            VALUES (1, 'Suspicious Network Connection', 'High', 85,
                   'Alert triggered by detection of domain example.com', 1651234567, 'Command and Control', 'SIEM')
        """)

        cursor.execute("""
            INSERT INTO alerts (id, name, severity, confidence, description, timestamp, threat_type, source)
            VALUES (2, 'Malware Detection', 'Critical', 92,
                   'Alert triggered by detection of domain example.com', 1667890123, 'Malware', 'EDR')
        """)

        # Insert IOC-Alert relationships
        cursor.execute("""
            INSERT INTO ioc_alert (alert_id, ioc_id, ioc_value)
            VALUES (1, 1, 'example.com')
        """)

        cursor.execute("""
            INSERT INTO ioc_alert (alert_id, ioc_id, ioc_value)
            VALUES (2, 1, 'example.com')
        """)

        conn.commit()
        conn.close()

    def test_get_ioc_alerts_success(self):
        """Test successful retrieval of alerts for an IOC."""
        # Test for example.com which should have 2 alerts
        response = self.app.get("/api/ioc/example.com/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ioc_value"], "example.com")
        self.assertEqual(data["total_alerts"], 2)
        self.assertEqual(len(data["alerts"]), 2)

        # Verify alerts are sorted by timestamp in reverse chronological order (newest first)
        self.assertEqual(data["alerts"][0]["id"], 2)  # Updated to match database IDs
        self.assertEqual(data["alerts"][1]["id"], 1)

    def test_get_ioc_alerts_case_insensitive(self):
        """Test that IOC matching is case-insensitive."""
        # Test with uppercase version of the IOC
        response = self.app.get("/api/ioc/EXAMPLE.COM/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_alerts"], 2)

    def test_get_ioc_alerts_not_found(self):
        """Test 404 response when IOC is not found."""
        response = self.app.get("/api/ioc/nonexistent-ioc.com/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "IOC not found")

    def test_get_ioc_alerts_empty_results(self):
        """Test successful response with empty results when no alerts are found."""
        # Add a new IOC with no alerts to the test database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        unique_ioc_value = "deadbeef12345unique"
        cursor.execute(
            """
            INSERT INTO iocs (id, ioc_type, ioc_value, score, first_seen_timestamp)
            VALUES (3, 'hash', ?, 5.0, 1651234567)
        """,
            (unique_ioc_value,),
        )

        conn.commit()
        conn.close()

        response = self.app.get(f"/api/ioc/{unique_ioc_value}/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ioc_value"], unique_ioc_value)
        self.assertEqual(data["total_alerts"], 0)
        self.assertEqual(data["alerts"], [])

    def test_api_stats_endpoint(self):
        """Test that the stats endpoint works with database."""
        response = self.app.get("/api/stats")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("total_iocs", data)
        self.assertIn("high_risk_iocs", data)
        self.assertIn("avg_score", data)
        self.assertEqual(data["total_iocs"], 2)  # We have 2 test IOCs

    def test_api_iocs_endpoint(self):
        """Test that the IOCs endpoint works with database."""
        response = self.app.get("/api/iocs")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("iocs", data)
        self.assertIn("total", data)
        self.assertEqual(len(data["iocs"]), 2)  # We have 2 test IOCs


if __name__ == "__main__":
    unittest.main()
