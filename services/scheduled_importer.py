#!/usr/bin/env python3
"""
SentinelForge Scheduled Feed Importer

A CRON-based service for automatically importing threat intelligence feeds
on a scheduled interval. Supports retry logic, authentication handling,
and comprehensive logging.

Usage:
    # Run once
    python services/scheduled_importer.py

    # Run as background service with APScheduler
    from services.scheduled_importer import ScheduledFeedImporter
    importer = ScheduledFeedImporter()
    importer.start_scheduler()
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("APScheduler not available. Install with: pip install apscheduler")

from services.ingestion import FeedIngestionService


class ScheduledFeedImporter:
    """
    Scheduled threat feed importer with retry logic and comprehensive logging.
    """

    def __init__(
        self,
        db_path: str = "/Users/Collins/sentinelforge/ioc_store.db",
        log_file: str = "scheduled_importer.log",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        timeout: int = 30,
    ):
        self.db_path = db_path
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout

        # Initialize logging
        self.logger = self._setup_logging(log_file)

        # Initialize ingestion service
        self.ingestion_service = FeedIngestionService(db_path)

        # Initialize HTTP session with retry strategy
        self.session = self._setup_http_session()

        # Scheduler (if available)
        self.scheduler = None
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()

    def _setup_logging(self, log_file: str) -> logging.Logger:
        """Setup logging to both file and stdout."""
        logger = logging.getLogger("scheduled_importer")
        logger.setLevel(logging.INFO)

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatters
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _setup_http_session(self) -> requests.Session:
        """Setup HTTP session with retry strategy."""
        session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_enabled_feeds(self) -> List[Dict]:
        """Fetch all enabled feeds from the database."""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT id, name, url, format, requires_auth, auth_config, 
                       parser, enabled, last_import, import_interval_hours
                FROM threat_feeds 
                WHERE enabled = 1
                ORDER BY name
                """
            )
            feeds = []
            for row in cursor.fetchall():
                feed = dict(row)
                # Parse JSON fields
                if feed["auth_config"]:
                    try:
                        feed["auth_config"] = json.loads(feed["auth_config"])
                    except json.JSONDecodeError:
                        feed["auth_config"] = {}
                feeds.append(feed)
            return feeds
        finally:
            conn.close()

    def should_import_feed(self, feed: Dict) -> Tuple[bool, str]:
        """
        Determine if a feed should be imported based on schedule and last import.

        Returns:
            Tuple of (should_import, reason)
        """
        if not feed.get("enabled"):
            return False, "Feed is disabled"

        # Check if feed has URL (skip local/manual feeds)
        if not feed.get("url"):
            return False, "Feed has no URL (manual/local feed)"

        # Check authentication requirements
        if feed.get("requires_auth") and not self._validate_auth_config(feed):
            return False, "Authentication required but credentials missing/invalid"

        # Check import interval
        interval_hours = feed.get("import_interval_hours", 24)  # Default 24 hours
        last_import = feed.get("last_import")

        if last_import:
            try:
                last_import_dt = datetime.fromisoformat(
                    last_import.replace("Z", "+00:00")
                )
                now = datetime.now(timezone.utc)
                hours_since_import = (now - last_import_dt).total_seconds() / 3600

                if hours_since_import < interval_hours:
                    return (
                        False,
                        f"Too soon (last import {hours_since_import:.1f}h ago, interval {interval_hours}h)",
                    )
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"Invalid last_import timestamp for feed {feed['name']}: {e}"
                )

        return True, "Ready for import"

    def _validate_auth_config(self, feed: Dict) -> bool:
        """Validate authentication configuration for a feed."""
        if not feed.get("requires_auth"):
            return True

        auth_config = feed.get("auth_config", {})
        if not auth_config:
            return False

        # Check for required auth fields based on feed type
        feed_name = feed.get("name", "").lower()

        if "phishtank" in feed_name:
            return bool(auth_config.get("api_key"))
        elif "taxii" in feed_name or "anomali" in feed_name:
            return bool(auth_config.get("username") and auth_config.get("password"))
        elif "proofpoint" in feed_name:
            return bool(auth_config.get("api_key") or auth_config.get("token"))

        # Generic check for common auth fields
        return bool(
            auth_config.get("api_key")
            or auth_config.get("token")
            or (auth_config.get("username") and auth_config.get("password"))
        )

    def fetch_feed_data(self, feed: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Fetch data from a feed URL with retry logic.

        Returns:
            Tuple of (success, error_message, content)
        """
        url = feed["url"]
        auth_config = feed.get("auth_config", {})

        # Prepare request parameters
        headers = {"User-Agent": "SentinelForge-FeedImporter/1.0"}
        params = {}
        auth = None

        # Setup authentication
        if feed.get("requires_auth") and auth_config:
            if auth_config.get("api_key"):
                # API key authentication (various methods)
                if "phishtank" in feed["name"].lower():
                    params["format"] = "json"
                    params["api_key"] = auth_config["api_key"]
                else:
                    headers["Authorization"] = f"Bearer {auth_config['api_key']}"
            elif auth_config.get("username") and auth_config.get("password"):
                # Basic authentication
                auth = (auth_config["username"], auth_config["password"])

        # Attempt to fetch with exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Fetching {feed['name']} (attempt {attempt + 1})")

                response = self.session.get(
                    url, headers=headers, params=params, auth=auth, timeout=self.timeout
                )

                if response.status_code == 200:
                    return True, "", response.text
                elif response.status_code == 429:
                    # Rate limited - use exponential backoff
                    if attempt < self.max_retries:
                        delay = min(self.base_delay * (2**attempt), self.max_delay)
                        self.logger.warning(
                            f"Rate limited, waiting {delay}s before retry"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        return (
                            False,
                            f"Rate limited (HTTP 429) after {self.max_retries} retries",
                            None,
                        )
                elif response.status_code in [401, 403]:
                    return (
                        False,
                        f"Authentication failed (HTTP {response.status_code})",
                        None,
                    )
                else:
                    return (
                        False,
                        f"HTTP {response.status_code}: {response.reason}",
                        None,
                    )

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2**attempt), self.max_delay)
                    self.logger.warning(f"Timeout, waiting {delay}s before retry")
                    time.sleep(delay)
                    continue
                else:
                    return False, f"Timeout after {self.max_retries} retries", None

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2**attempt), self.max_delay)
                    self.logger.warning(
                        f"Request error: {e}, waiting {delay}s before retry"
                    )
                    time.sleep(delay)
                    continue
                else:
                    return (
                        False,
                        f"Request failed after {self.max_retries} retries: {e}",
                        None,
                    )

        return False, "Max retries exceeded", None

    def import_feed(self, feed: Dict) -> Dict:
        """
        Import a single feed and return results.

        Returns:
            Dictionary with import results and statistics
        """
        feed_id = feed["id"]
        feed_name = feed["name"]

        self.logger.info(f"Starting import for feed: {feed_name} (ID: {feed_id})")

        start_time = time.time()

        # Fetch feed data
        success, error_msg, content = self.fetch_feed_data(feed)

        if not success:
            self.logger.error(f"Failed to fetch {feed_name}: {error_msg}")
            return {
                "feed_id": feed_id,
                "feed_name": feed_name,
                "success": False,
                "error": error_msg,
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "duration_seconds": int(time.time() - start_time),
            }

        # Create temporary file for ingestion
        temp_file = f"/tmp/feed_{feed_id}_{int(time.time())}.{feed['format']}"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Import using ingestion service
            result = self.ingestion_service.import_from_file(
                file_path=temp_file,
                source_feed=feed_name,
                user_id=1,  # System user
                justification=f"Scheduled import from {feed['url']}",
                feed_id=feed_id,
            )

            # Update last import timestamp
            self._update_last_import(feed_id)

            duration = int(time.time() - start_time)

            if result.get("success"):
                self.logger.info(
                    f"Successfully imported {feed_name}: "
                    f"{result['imported_count']} imported, "
                    f"{result['skipped_count']} skipped, "
                    f"{result['error_count']} errors in {duration}s"
                )
            else:
                self.logger.error(
                    f"Import failed for {feed_name}: {result.get('error', 'Unknown error')}"
                )

            # Add metadata to result
            result.update(
                {
                    "feed_id": feed_id,
                    "feed_name": feed_name,
                    "duration_seconds": duration,
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Unexpected error importing {feed_name}: {e}")
            return {
                "feed_id": feed_id,
                "feed_name": feed_name,
                "success": False,
                "error": f"Unexpected error: {e}",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "duration_seconds": int(time.time() - start_time),
            }
        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception:
                pass

    def _update_last_import(self, feed_id: int):
        """Update the last import timestamp for a feed."""
        conn = self.get_db_connection()
        try:
            now = datetime.now(timezone.utc)
            conn.execute(
                "UPDATE threat_feeds SET last_import = ? WHERE id = ?",
                (now.isoformat(), feed_id),
            )
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update last_import for feed {feed_id}: {e}")
        finally:
            conn.close()

    def run_scheduled_import(self) -> Dict:
        """
        Run the scheduled import process for all enabled feeds.

        Returns:
            Summary of import results
        """
        self.logger.info("Starting scheduled feed import process")

        start_time = time.time()
        feeds = self.get_enabled_feeds()

        results = {
            "total_feeds": len(feeds),
            "processed_feeds": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "skipped_feeds": 0,
            "total_iocs_imported": 0,
            "total_iocs_skipped": 0,
            "total_errors": 0,
            "feed_results": [],
            "duration_seconds": 0,
        }

        self.logger.info(f"Found {len(feeds)} enabled feeds")

        for feed in feeds:
            # Check if feed should be imported
            should_import, reason = self.should_import_feed(feed)

            if not should_import:
                self.logger.info(f"Skipping {feed['name']}: {reason}")
                results["skipped_feeds"] += 1
                results["feed_results"].append(
                    {
                        "feed_id": feed["id"],
                        "feed_name": feed["name"],
                        "skipped": True,
                        "reason": reason,
                    }
                )
                continue

            # Import the feed
            import_result = self.import_feed(feed)
            results["feed_results"].append(import_result)
            results["processed_feeds"] += 1

            if import_result.get("success"):
                results["successful_imports"] += 1
                results["total_iocs_imported"] += import_result.get("imported_count", 0)
                results["total_iocs_skipped"] += import_result.get("skipped_count", 0)
                results["total_errors"] += import_result.get("error_count", 0)
            else:
                results["failed_imports"] += 1

        results["duration_seconds"] = int(time.time() - start_time)

        # Log summary
        self.logger.info(
            f"Scheduled import completed in {results['duration_seconds']}s: "
            f"{results['successful_imports']} successful, "
            f"{results['failed_imports']} failed, "
            f"{results['skipped_feeds']} skipped, "
            f"{results['total_iocs_imported']} IOCs imported"
        )

        return results

    def start_scheduler(self, cron_expression: str = "0 */6 * * *"):
        """
        Start the APScheduler with the specified CRON expression.

        Args:
            cron_expression: CRON expression (default: every 6 hours)
        """
        if not SCHEDULER_AVAILABLE:
            raise RuntimeError(
                "APScheduler not available. Install with: pip install apscheduler"
            )

        if not self.scheduler:
            self.scheduler = BackgroundScheduler()

        # Parse CRON expression
        cron_parts = cron_expression.split()
        if len(cron_parts) != 5:
            raise ValueError(
                "Invalid CRON expression. Expected format: 'minute hour day month day_of_week'"
            )

        minute, hour, day, month, day_of_week = cron_parts

        # Add job to scheduler
        self.scheduler.add_job(
            func=self.run_scheduled_import,
            trigger=CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            ),
            id="scheduled_feed_import",
            name="Scheduled Feed Import",
            replace_existing=True,
        )

        self.scheduler.start()
        self.logger.info(f"Scheduler started with CRON expression: {cron_expression}")

    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler stopped")

    def run_once(self):
        """Run the import process once (for manual execution or testing)."""
        return self.run_scheduled_import()


def main():
    """Main function for running the importer as a standalone script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SentinelForge Scheduled Feed Importer"
    )
    parser.add_argument(
        "--run-once", action="store_true", help="Run import once and exit"
    )
    parser.add_argument(
        "--cron",
        default="0 */6 * * *",
        help="CRON expression for scheduling (default: every 6 hours)",
    )
    parser.add_argument(
        "--db-path",
        default="/Users/Collins/sentinelforge/ioc_store.db",
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--log-file", default="scheduled_importer.log", help="Log file path"
    )

    args = parser.parse_args()

    # Create importer instance
    importer = ScheduledFeedImporter(db_path=args.db_path, log_file=args.log_file)

    if args.run_once:
        # Run once and exit
        results = importer.run_once()
        print(
            f"Import completed: {results['successful_imports']} successful, {results['failed_imports']} failed"
        )
        return results
    else:
        # Start scheduler
        try:
            importer.start_scheduler(args.cron)
            print(f"Scheduler started with CRON: {args.cron}")
            print("Press Ctrl+C to stop...")

            # Keep the script running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            importer.stop_scheduler()
            print("Scheduler stopped")


if __name__ == "__main__":
    main()
