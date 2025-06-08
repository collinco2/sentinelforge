#!/usr/bin/env python3
"""
Test suite for the SentinelForge Scheduled Feed Importer.

This module provides comprehensive tests for the scheduled importer functionality
including configuration validation, feed processing, error handling, and integration tests.

Usage:
    python -m pytest tests/test_scheduled_importer.py -v
    python tests/test_scheduled_importer.py  # Run directly
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.scheduled_importer import ScheduledFeedImporter
from config.scheduler_config import SchedulerConfig


class TestScheduledImporter(unittest.TestCase):
    """Test cases for the ScheduledFeedImporter class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Create temporary log file
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
        self.temp_log.close()
        self.log_path = self.temp_log.name

        # Initialize test database
        self._setup_test_database()

        # Create importer instance
        self.importer = ScheduledFeedImporter(
            db_path=self.db_path,
            log_file=self.log_path,
            max_retries=2,
            base_delay=0.1,
            max_delay=1.0,
            timeout=5,
        )

    def tearDown(self):
        """Clean up test environment."""
        # Stop scheduler if running
        if self.importer.scheduler and self.importer.scheduler.running:
            self.importer.stop_scheduler()

        # Clean up temporary files
        try:
            os.unlink(self.db_path)
            os.unlink(self.log_path)
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
                format TEXT,
                requires_auth BOOLEAN DEFAULT 0,
                auth_config TEXT,
                parser TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_import TEXT,
                import_interval_hours INTEGER DEFAULT 24
            )
        """)

        # Create feed_import_logs table
        conn.execute("""
            CREATE TABLE feed_import_logs (
                id INTEGER PRIMARY KEY,
                feed_id INTEGER,
                timestamp TEXT,
                status TEXT,
                imported_count INTEGER,
                skipped_count INTEGER,
                error_count INTEGER,
                errors TEXT,
                FOREIGN KEY (feed_id) REFERENCES threat_feeds (id)
            )
        """)

        # Insert test feeds
        test_feeds = [
            (
                1,
                "Test Feed 1",
                "https://example.com/feed1.csv",
                "csv",
                0,
                None,
                "standard_csv",
                1,
                None,
                24,
            ),
            (
                2,
                "Test Feed 2",
                "https://example.com/feed2.json",
                "json",
                1,
                '{"api_key": "test123"}',
                "phishtank_json",
                1,
                None,
                12,
            ),
            (
                3,
                "Disabled Feed",
                "https://example.com/feed3.txt",
                "txt",
                0,
                None,
                "generic_txt",
                0,
                None,
                24,
            ),
            (
                4,
                "Recent Import",
                "https://example.com/feed4.csv",
                "csv",
                0,
                None,
                "standard_csv",
                1,
                datetime.now(timezone.utc).isoformat(),
                24,
            ),
        ]

        conn.executemany(
            """
            INSERT INTO threat_feeds 
            (id, name, url, format, requires_auth, auth_config, parser, enabled, last_import, import_interval_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            test_feeds,
        )

        conn.commit()
        conn.close()

    def test_get_enabled_feeds(self):
        """Test getting enabled feeds from database."""
        feeds = self.importer.get_enabled_feeds()

        # Should return 3 enabled feeds (excluding disabled one)
        self.assertEqual(len(feeds), 3)

        # Check feed names
        feed_names = [feed["name"] for feed in feeds]
        self.assertIn("Test Feed 1", feed_names)
        self.assertIn("Test Feed 2", feed_names)
        self.assertNotIn("Disabled Feed", feed_names)

    def test_should_import_feed(self):
        """Test feed import decision logic."""
        feeds = self.importer.get_enabled_feeds()

        # Test normal feed (should import)
        feed1 = next(f for f in feeds if f["name"] == "Test Feed 1")
        should_import, reason = self.importer.should_import_feed(feed1)
        self.assertTrue(should_import)
        self.assertEqual(reason, "Ready for import")

        # Test recently imported feed (should skip)
        feed4 = next(f for f in feeds if f["name"] == "Recent Import")
        should_import, reason = self.importer.should_import_feed(feed4)
        self.assertFalse(should_import)
        self.assertIn("Too soon", reason)

    def test_validate_auth_config(self):
        """Test authentication configuration validation."""
        feeds = self.importer.get_enabled_feeds()

        # Test feed without auth requirement
        feed1 = next(f for f in feeds if f["name"] == "Test Feed 1")
        self.assertTrue(self.importer._validate_auth_config(feed1))

        # Test feed with auth requirement and valid config
        feed2 = next(f for f in feeds if f["name"] == "Test Feed 2")
        self.assertTrue(self.importer._validate_auth_config(feed2))

        # Test feed with auth requirement but invalid config
        feed2["auth_config"] = {}
        self.assertFalse(self.importer._validate_auth_config(feed2))

    @patch("services.scheduled_importer.requests.Session.get")
    def test_fetch_feed_data_success(self, mock_get):
        """Test successful feed data fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "test,data\nvalue1,type1\nvalue2,type2"
        mock_get.return_value = mock_response

        feeds = self.importer.get_enabled_feeds()
        feed = next(f for f in feeds if f["name"] == "Test Feed 1")

        success, error, content = self.importer.fetch_feed_data(feed)

        self.assertTrue(success)
        self.assertEqual(error, "")
        self.assertIn("test,data", content)

    @patch("services.scheduled_importer.requests.Session.get")
    def test_fetch_feed_data_retry_logic(self, mock_get):
        """Test retry logic for transient errors."""
        # Mock rate limited response, then success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.text = "success,data"

        mock_get.side_effect = [mock_response_429, mock_response_200]

        feeds = self.importer.get_enabled_feeds()
        feed = next(f for f in feeds if f["name"] == "Test Feed 1")

        success, error, content = self.importer.fetch_feed_data(feed)

        self.assertTrue(success)
        self.assertEqual(mock_get.call_count, 2)

    @patch("services.scheduled_importer.requests.Session.get")
    def test_fetch_feed_data_auth_failure(self, mock_get):
        """Test authentication failure handling."""
        # Mock authentication failure
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_get.return_value = mock_response

        feeds = self.importer.get_enabled_feeds()
        feed = next(f for f in feeds if f["name"] == "Test Feed 2")

        success, error, content = self.importer.fetch_feed_data(feed)

        self.assertFalse(success)
        self.assertIn("Authentication failed", error)
        self.assertIsNone(content)

    @patch("services.scheduled_importer.ScheduledFeedImporter.fetch_feed_data")
    @patch("services.ingestion.FeedIngestionService.import_from_file")
    def test_import_feed_success(self, mock_import, mock_fetch):
        """Test successful feed import."""
        # Mock successful fetch
        mock_fetch.return_value = (True, "", "test,data\nvalue1,ip\nvalue2,domain")

        # Mock successful import
        mock_import.return_value = {
            "success": True,
            "imported_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "errors": [],
        }

        feeds = self.importer.get_enabled_feeds()
        feed = next(f for f in feeds if f["name"] == "Test Feed 1")

        result = self.importer.import_feed(feed)

        self.assertTrue(result["success"])
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["feed_name"], "Test Feed 1")

    @patch("services.scheduled_importer.ScheduledFeedImporter.fetch_feed_data")
    def test_import_feed_fetch_failure(self, mock_fetch):
        """Test feed import with fetch failure."""
        # Mock fetch failure
        mock_fetch.return_value = (False, "Connection timeout", None)

        feeds = self.importer.get_enabled_feeds()
        feed = next(f for f in feeds if f["name"] == "Test Feed 1")

        result = self.importer.import_feed(feed)

        self.assertFalse(result["success"])
        self.assertIn("Connection timeout", result["error"])
        self.assertEqual(result["imported_count"], 0)

    def test_update_last_import(self):
        """Test updating last import timestamp."""
        feed_id = 1

        # Update last import
        self.importer._update_last_import(feed_id)

        # Verify update
        conn = self.importer.get_db_connection()
        cursor = conn.execute(
            "SELECT last_import FROM threat_feeds WHERE id = ?", (feed_id,)
        )
        last_import = cursor.fetchone()[0]
        conn.close()

        self.assertIsNotNone(last_import)

        # Parse and verify timestamp is recent
        import_time = datetime.fromisoformat(last_import.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        time_diff = (now - import_time).total_seconds()
        self.assertLess(time_diff, 10)  # Should be within 10 seconds

    @patch("services.scheduled_importer.ScheduledFeedImporter.import_feed")
    def test_run_scheduled_import(self, mock_import_feed):
        """Test running scheduled import for all feeds."""
        # Mock import results
        mock_import_feed.side_effect = [
            {
                "success": True,
                "imported_count": 10,
                "skipped_count": 2,
                "error_count": 0,
                "feed_name": "Test Feed 1",
            },
            {
                "success": False,
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 1,
                "error": "Connection failed",
                "feed_name": "Test Feed 2",
            },
        ]

        results = self.importer.run_scheduled_import()

        # Verify results
        self.assertEqual(results["processed_feeds"], 2)
        self.assertEqual(results["successful_imports"], 1)
        self.assertEqual(results["failed_imports"], 1)
        self.assertEqual(results["total_iocs_imported"], 10)
        self.assertEqual(results["total_iocs_skipped"], 2)

    def test_scheduler_start_stop(self):
        """Test scheduler start and stop functionality."""
        if not hasattr(self.importer, "scheduler") or self.importer.scheduler is None:
            self.skipTest("APScheduler not available")

        # Start scheduler
        self.importer.start_scheduler("0 */6 * * *")
        self.assertTrue(self.importer.scheduler.running)

        # Stop scheduler
        self.importer.stop_scheduler()
        self.assertFalse(self.importer.scheduler.running)


class TestSchedulerConfig(unittest.TestCase):
    """Test cases for scheduler configuration."""

    def test_config_validation_valid(self):
        """Test configuration validation with valid settings."""
        # Temporarily set valid configuration
        original_db_path = SchedulerConfig.DB_PATH
        original_cron = SchedulerConfig.CRON_EXPRESSION
        original_timeout = SchedulerConfig.REQUEST_TIMEOUT

        try:
            SchedulerConfig.DB_PATH = "/tmp/test.db"
            SchedulerConfig.CRON_EXPRESSION = "0 */6 * * *"
            SchedulerConfig.REQUEST_TIMEOUT = 30

            # Create directory for test
            os.makedirs(os.path.dirname(SchedulerConfig.DB_PATH), exist_ok=True)

            self.assertTrue(SchedulerConfig.validate())

        finally:
            # Restore original values
            SchedulerConfig.DB_PATH = original_db_path
            SchedulerConfig.CRON_EXPRESSION = original_cron
            SchedulerConfig.REQUEST_TIMEOUT = original_timeout

    def test_config_validation_invalid_cron(self):
        """Test configuration validation with invalid CRON expression."""
        original_cron = SchedulerConfig.CRON_EXPRESSION

        try:
            SchedulerConfig.CRON_EXPRESSION = "invalid cron"
            self.assertFalse(SchedulerConfig.validate())
        finally:
            SchedulerConfig.CRON_EXPRESSION = original_cron

    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config_dict = SchedulerConfig.to_dict()

        self.assertIsInstance(config_dict, dict)
        self.assertIn("DB_PATH", config_dict)
        self.assertIn("CRON_EXPRESSION", config_dict)
        self.assertIn("REQUEST_TIMEOUT", config_dict)


def run_integration_test():
    """Run integration test with actual database."""
    print("Running integration test...")

    # Create temporary database with real schema
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    try:
        # Setup test database (you would copy from actual schema)
        conn = sqlite3.connect(temp_db.name)

        # Create minimal schema for testing
        conn.execute("""
            CREATE TABLE threat_feeds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT,
                format TEXT,
                requires_auth BOOLEAN DEFAULT 0,
                auth_config TEXT,
                parser TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_import TEXT,
                import_interval_hours INTEGER DEFAULT 24
            )
        """)

        # Insert a test feed
        conn.execute("""
            INSERT INTO threat_feeds 
            (name, url, format, enabled, import_interval_hours)
            VALUES ('Test Integration Feed', 'https://httpbin.org/json', 'json', 1, 1)
        """)

        conn.commit()
        conn.close()

        # Create importer and run test
        importer = ScheduledFeedImporter(db_path=temp_db.name)

        # Test getting feeds
        feeds = importer.get_enabled_feeds()
        print(f"Found {len(feeds)} enabled feeds")

        # Test import decision
        if feeds:
            should_import, reason = importer.should_import_feed(feeds[0])
            print(f"Should import: {should_import}, Reason: {reason}")

        print("Integration test completed successfully!")

    except Exception as e:
        print(f"Integration test failed: {e}")
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
