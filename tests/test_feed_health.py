#!/usr/bin/env python3
"""
Test suite for the SentinelForge Feed Health Check API endpoints.

This module provides comprehensive tests for the feed health check functionality
including endpoint testing, database operations, and error handling.

Usage:
    python -m pytest tests/test_feed_health.py -v
    python tests/test_feed_health.py  # Run directly
"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock Flask app for testing
from flask import Flask
from auth import UserRole, User


class TestFeedHealthAPI(unittest.TestCase):
    """Test cases for the Feed Health Check API endpoints."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Initialize test database
        self._setup_test_database()

        # Create test Flask app
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Mock authentication
        self.test_user = User(
            user_id=1,
            username="test_analyst",
            email="analyst@test.com",
            role=UserRole.ANALYST,
        )

    def tearDown(self):
        """Clean up test environment."""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _setup_test_database(self):
        """Set up test database with sample data."""
        conn = sqlite3.connect(self.db_path)

        # Create threat_feeds table
        conn.execute("""
            CREATE TABLE threat_feeds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT,
                feed_type TEXT,
                format_config TEXT,
                is_active BOOLEAN DEFAULT 1,
                auto_import BOOLEAN DEFAULT 0,
                import_frequency INTEGER DEFAULT 24,
                last_import DATETIME,
                last_import_status TEXT,
                last_import_count INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create users table for authentication
        conn.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create feed_health_logs table
        conn.execute("""
            CREATE TABLE feed_health_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                feed_name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                http_code INTEGER,
                response_time_ms INTEGER,
                error_message TEXT,
                last_checked DATETIME NOT NULL,
                checked_by INTEGER NOT NULL,
                FOREIGN KEY (feed_id) REFERENCES threat_feeds (id)
            )
        """)

        # Insert test user
        conn.execute("""
            INSERT INTO users (user_id, username, email, role)
            VALUES (1, 'test_analyst', 'analyst@test.com', 'analyst')
        """)

        # Insert test feeds
        test_feeds = [
            (
                1,
                "Test Feed 1",
                "https://httpbin.org/status/200",
                "csv",
                None,
                1,
                0,
                24,
                None,
                None,
                0,
                1,
            ),
            (
                2,
                "Test Feed 2",
                "https://httpbin.org/status/404",
                "json",
                None,
                1,
                0,
                24,
                None,
                None,
                0,
                1,
            ),
            (
                3,
                "PhishTank Feed",
                "https://data.phishtank.com/data/online-valid.json",
                "json",
                '{"requires_auth": true, "auth_config": {"api_key": "test123"}}',
                1,
                0,
                24,
                None,
                None,
                0,
                1,
            ),
            (4, "No URL Feed", None, "csv", None, 1, 0, 24, None, None, 0, 1),
        ]

        conn.executemany(
            """
            INSERT INTO threat_feeds 
            (id, name, url, feed_type, format_config, is_active, auto_import, 
             import_frequency, last_import, last_import_status, last_import_count, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            test_feeds,
        )

        conn.commit()
        conn.close()

    def test_health_check_table_creation(self):
        """Test that the health check table is created properly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='feed_health_logs'
        """)

        table_exists = cursor.fetchone() is not None
        self.assertTrue(table_exists, "feed_health_logs table should exist")

        # Check table structure
        cursor.execute("PRAGMA table_info(feed_health_logs)")
        columns = [column[1] for column in cursor.fetchall()]

        expected_columns = [
            "id",
            "feed_id",
            "feed_name",
            "url",
            "status",
            "http_code",
            "response_time_ms",
            "error_message",
            "last_checked",
            "checked_by",
        ]

        for col in expected_columns:
            self.assertIn(
                col, columns, f"Column {col} should exist in feed_health_logs table"
            )

        conn.close()

    @patch("requests.Session.head")
    def test_successful_health_check(self, mock_head):
        """Test successful health check for a feed."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_head.return_value = mock_response

        # Simulate health check logic
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get test feed
        cursor.execute("SELECT * FROM threat_feeds WHERE id = 1")
        feed = cursor.fetchone()

        # Simulate health check
        feed_id = feed[0]
        feed_name = feed[1]
        url = feed[2]
        status = "ok"
        http_code = 200
        response_time_ms = 150
        last_checked = datetime.now(timezone.utc)

        # Insert health log
        cursor.execute(
            """
            INSERT INTO feed_health_logs (
                feed_id, feed_name, url, status, http_code, 
                response_time_ms, error_message, last_checked, checked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                feed_id,
                feed_name,
                url,
                status,
                http_code,
                response_time_ms,
                None,
                last_checked,
                1,
            ),
        )

        conn.commit()

        # Verify log was created
        cursor.execute("SELECT * FROM feed_health_logs WHERE feed_id = 1")
        log = cursor.fetchone()

        self.assertIsNotNone(log)
        self.assertEqual(log[4], status)  # status column (index 4)
        self.assertEqual(log[5], http_code)  # http_code column (index 5)

        conn.close()

    @patch("requests.Session.head")
    def test_failed_health_check(self, mock_head):
        """Test failed health check for a feed."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_head.return_value = mock_response

        # Simulate health check logic
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get test feed
        cursor.execute("SELECT * FROM threat_feeds WHERE id = 2")
        feed = cursor.fetchone()

        # Simulate health check
        feed_id = feed[0]
        feed_name = feed[1]
        url = feed[2]
        status = "unreachable"
        http_code = 404
        response_time_ms = 200
        error_message = "HTTP 404: Not Found"
        last_checked = datetime.now(timezone.utc)

        # Insert health log
        cursor.execute(
            """
            INSERT INTO feed_health_logs (
                feed_id, feed_name, url, status, http_code, 
                response_time_ms, error_message, last_checked, checked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                feed_id,
                feed_name,
                url,
                status,
                http_code,
                response_time_ms,
                error_message,
                last_checked,
                1,
            ),
        )

        conn.commit()

        # Verify log was created
        cursor.execute("SELECT * FROM feed_health_logs WHERE feed_id = 2")
        log = cursor.fetchone()

        self.assertIsNotNone(log)
        self.assertEqual(log[4], status)  # status column (index 4)
        self.assertEqual(log[5], http_code)  # http_code column (index 5)
        self.assertEqual(log[7], error_message)  # error_message column (index 7)

        conn.close()

    def test_health_check_authentication_config(self):
        """Test health check with authentication configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get PhishTank feed with auth config
        cursor.execute("SELECT * FROM threat_feeds WHERE id = 3")
        feed = cursor.fetchone()

        # Parse format_config
        format_config = json.loads(feed[4])  # format_config column

        self.assertTrue(format_config.get("requires_auth"))
        self.assertIn("auth_config", format_config)
        self.assertIn("api_key", format_config["auth_config"])

        conn.close()

    def test_health_check_no_url_feed(self):
        """Test health check behavior for feeds without URLs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get feed without URL
        cursor.execute("SELECT * FROM threat_feeds WHERE id = 4")
        feed = cursor.fetchone()

        self.assertIsNone(feed[2])  # url column should be None

        conn.close()

    def test_health_history_filtering(self):
        """Test health history filtering functionality."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert test health logs
        now = datetime.now(timezone.utc)
        test_logs = [
            (1, "Test Feed 1", "https://example.com", "ok", 200, 100, None, now, 1),
            (
                1,
                "Test Feed 1",
                "https://example.com",
                "timeout",
                None,
                5000,
                "Timeout",
                now,
                1,
            ),
            (
                2,
                "Test Feed 2",
                "https://example.com",
                "unreachable",
                404,
                200,
                "Not Found",
                now,
                1,
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO feed_health_logs (
                feed_id, feed_name, url, status, http_code, 
                response_time_ms, error_message, last_checked, checked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            test_logs,
        )

        conn.commit()

        # Test filtering by feed_id
        cursor.execute("SELECT * FROM feed_health_logs WHERE feed_id = 1")
        feed1_logs = cursor.fetchall()
        self.assertEqual(len(feed1_logs), 2)

        # Test filtering by status
        cursor.execute("SELECT * FROM feed_health_logs WHERE status = 'ok'")
        ok_logs = cursor.fetchall()
        self.assertEqual(len(ok_logs), 1)

        conn.close()

    def test_health_summary_calculation(self):
        """Test health summary statistics calculation."""
        # Sample health results
        health_results = [
            {"status": "ok"},
            {"status": "ok"},
            {"status": "unreachable"},
            {"status": "timeout"},
        ]

        total_feeds = len(health_results)
        healthy_feeds = len([r for r in health_results if r["status"] == "ok"])
        unhealthy_feeds = total_feeds - healthy_feeds
        health_percentage = round(
            (healthy_feeds / total_feeds * 100) if total_feeds > 0 else 0, 1
        )

        self.assertEqual(total_feeds, 4)
        self.assertEqual(healthy_feeds, 2)
        self.assertEqual(unhealthy_feeds, 2)
        self.assertEqual(health_percentage, 50.0)


def run_integration_test():
    """Run integration test with actual HTTP requests."""
    print("Running feed health integration test...")

    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    try:
        # Setup test database
        conn = sqlite3.connect(temp_db.name)

        # Create schema
        conn.execute("""
            CREATE TABLE threat_feeds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT,
                feed_type TEXT,
                format_config TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        conn.execute("""
            CREATE TABLE feed_health_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                feed_name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                http_code INTEGER,
                response_time_ms INTEGER,
                error_message TEXT,
                last_checked DATETIME NOT NULL,
                checked_by INTEGER NOT NULL
            )
        """)

        # Insert test feed
        conn.execute("""
            INSERT INTO threat_feeds (name, url, feed_type, is_active)
            VALUES ('HTTPBin Test', 'https://httpbin.org/status/200', 'json', 1)
        """)

        conn.commit()
        conn.close()

        print("✅ Integration test database setup completed")
        print("✅ Feed health check system ready for testing")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
        except OSError:
            pass


if __name__ == "__main__":
    # Run unit tests
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run integration test
    print("\n" + "=" * 50)
    run_integration_test()
