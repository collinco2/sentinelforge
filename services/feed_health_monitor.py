#!/usr/bin/env python3
"""
SentinelForge Feed Health Monitor Service

Provides automated health checking for threat intelligence feeds with:
- Standalone health check execution
- Database logging to feed_health_logs table
- Cron job scheduling support
- Server startup integration
- Real-time status caching

Usage:
    # One-time health check
    python services/feed_health_monitor.py --check-now

    # Start cron scheduler (1-minute interval for testing)
    python services/feed_health_monitor.py --start-cron

    # Check specific feed
    python services/feed_health_monitor.py --feed-id 5
"""

import sys
import os
import sqlite3
import requests
import time
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.schedulers.background import BackgroundScheduler

    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️  APScheduler not available. Install with: pip install apscheduler")


class FeedHealthMonitor:
    """Comprehensive feed health monitoring service with real-time progress tracking."""

    def __init__(self, db_path: str = "ioc_store.db", log_level: str = "INFO"):
        self.db_path = db_path
        self.logger = self._setup_logging(log_level)
        self.scheduler = None
        self._health_cache = {}
        self._cache_lock = threading.Lock()

        # Progress tracking for real-time updates
        self._progress_sessions = {}
        self._progress_lock = threading.Lock()

        # HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _setup_logging(self, log_level: str) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("feed_health_monitor")
        logger.setLevel(getattr(logging, log_level.upper()))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection with error handling."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None

    def ensure_health_logs_table(self) -> bool:
        """Ensure feed_health_logs table exists."""
        conn = self.get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feed_health_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_id INTEGER NOT NULL,
                    feed_name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    http_code INTEGER,
                    response_time_ms INTEGER,
                    error_message TEXT,
                    last_checked DATETIME NOT NULL,
                    checked_by INTEGER DEFAULT 0,
                    FOREIGN KEY (feed_id) REFERENCES threat_feeds (id)
                )
            """)

            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feed_health_logs_feed_id 
                ON feed_health_logs(feed_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feed_health_logs_last_checked 
                ON feed_health_logs(last_checked)
            """)

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to create health logs table: {e}")
            return False
        finally:
            conn.close()

    def get_active_feeds(self) -> List[Dict]:
        """Get all active feeds with URLs."""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, url, feed_type, format_config, is_active, api_key
                FROM threat_feeds
                WHERE is_active = 1 AND url IS NOT NULL AND url != ''
                ORDER BY name
            """)

            feeds = []
            for row in cursor.fetchall():
                feeds.append(dict(row))

            return feeds
        except Exception as e:
            self.logger.error(f"Failed to get active feeds: {e}")
            return []
        finally:
            conn.close()

    def check_feed_health(self, feed: Dict) -> Dict:
        """Check health of a single feed."""
        feed_id = feed["id"]
        feed_name = feed["name"]
        url = feed["url"]

        self.logger.debug(f"Checking health for feed: {feed_name} ({url})")

        start_time = time.time()
        status = "unknown"
        http_code = None
        error_message = None
        response = None

        try:
            # Prepare headers
            headers = {"User-Agent": "SentinelForge-HealthMonitor/1.0", "Accept": "*/*"}

            # Add API key if available
            if feed.get("api_key"):
                headers["Authorization"] = f"Bearer {feed['api_key']}"

            # Determine request method based on feed type
            method = "HEAD" if feed.get("feed_type") in ["txt", "csv"] else "GET"

            # Make request with timeout
            if method == "HEAD":
                response = self.session.head(
                    url, headers=headers, timeout=30, allow_redirects=True
                )
            else:
                response = self.session.get(
                    url, headers=headers, timeout=30, allow_redirects=True, stream=True
                )
                # For GET requests, only read first 1KB to check availability
                if hasattr(response, "iter_content"):
                    next(response.iter_content(1024), None)

            http_code = response.status_code

            # Determine status based on response
            if 200 <= http_code < 300:
                status = "ok"
            elif http_code == 401:
                status = "unauthorized"
                error_message = "Authentication required"
            elif http_code == 403:
                status = "forbidden"
                error_message = "Access forbidden"
            elif http_code == 404:
                status = "not_found"
                error_message = "Feed URL not found"
            elif http_code == 429:
                status = "rate_limited"
                error_message = "Rate limit exceeded"
            elif 500 <= http_code < 600:
                status = "server_error"
                error_message = f"Server error: {http_code}"
            else:
                status = "error"
                error_message = f"Unexpected status code: {http_code}"

        except requests.exceptions.Timeout:
            status = "timeout"
            error_message = "Request timed out"
        except requests.exceptions.ConnectionError:
            status = "unreachable"
            error_message = "Connection failed"
        except requests.exceptions.SSLError:
            status = "ssl_error"
            error_message = "SSL certificate error"
        except requests.exceptions.RequestException as e:
            status = "error"
            error_message = f"Request failed: {str(e)}"
        except Exception as e:
            status = "error"
            error_message = f"Unexpected error: {str(e)}"

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        last_checked = datetime.now(timezone.utc)

        # Create health result
        health_result = {
            "feed_id": feed_id,
            "feed_name": feed_name,
            "url": url,
            "status": status,
            "http_code": http_code,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "last_checked": last_checked,
            "is_active": bool(feed["is_active"]),
        }

        self.logger.debug(
            f"Health check result for {feed_name}: {status} ({response_time_ms}ms)"
        )
        return health_result

    def log_health_result(self, health_result: Dict, checked_by: int = 0) -> bool:
        """Log health check result to database."""
        conn = self.get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO feed_health_logs (
                    feed_id, feed_name, url, status, http_code,
                    response_time_ms, error_message, last_checked, checked_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    health_result["feed_id"],
                    health_result["feed_name"],
                    health_result["url"],
                    health_result["status"],
                    health_result["http_code"],
                    health_result["response_time_ms"],
                    health_result["error_message"],
                    health_result["last_checked"].isoformat(),
                    checked_by,
                ),
            )

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to log health result: {e}")
            return False
        finally:
            conn.close()

    def update_health_cache(self, health_results: List[Dict]):
        """Update in-memory health cache for fast API responses."""
        with self._cache_lock:
            self._health_cache = {
                result["feed_id"]: result for result in health_results
            }
            self._health_cache["_last_update"] = datetime.now(timezone.utc)

    def get_cached_health(self) -> Dict:
        """Get cached health results."""
        with self._cache_lock:
            return self._health_cache.copy()

    def create_progress_session(
        self, session_id: str, total_feeds: int, checked_by: int = 0
    ) -> Dict:
        """Create a new progress tracking session."""
        with self._progress_lock:
            session_data = {
                "session_id": session_id,
                "total_feeds": total_feeds,
                "completed_feeds": 0,
                "current_feed": None,
                "status": "starting",
                "start_time": datetime.now(timezone.utc),
                "estimated_completion": None,
                "results": [],
                "errors": [],
                "checked_by": checked_by,
                "cancelled": False,
            }
            self._progress_sessions[session_id] = session_data
            return session_data.copy()

    def update_progress(self, session_id: str, **updates) -> Dict:
        """Update progress for a specific session."""
        with self._progress_lock:
            if session_id not in self._progress_sessions:
                return {"error": "Session not found"}

            session = self._progress_sessions[session_id]
            session.update(updates)

            # Calculate estimated completion time
            if session["completed_feeds"] > 0 and session["status"] == "running":
                elapsed = (
                    datetime.now(timezone.utc) - session["start_time"]
                ).total_seconds()
                avg_time_per_feed = elapsed / session["completed_feeds"]
                remaining_feeds = session["total_feeds"] - session["completed_feeds"]
                estimated_seconds = remaining_feeds * avg_time_per_feed
                session["estimated_completion"] = (
                    datetime.now(timezone.utc).timestamp() + estimated_seconds
                )

            return session.copy()

    def get_progress(self, session_id: str) -> Dict:
        """Get current progress for a session."""
        with self._progress_lock:
            if session_id not in self._progress_sessions:
                return {"error": "Session not found"}
            return self._progress_sessions[session_id].copy()

    def cancel_progress_session(self, session_id: str) -> bool:
        """Cancel a progress session."""
        with self._progress_lock:
            if session_id in self._progress_sessions:
                self._progress_sessions[session_id]["cancelled"] = True
                self._progress_sessions[session_id]["status"] = "cancelled"
                return True
            return False

    def cleanup_progress_session(self, session_id: str):
        """Clean up a completed progress session."""
        with self._progress_lock:
            self._progress_sessions.pop(session_id, None)

    def run_health_check(
        self,
        feed_id: Optional[int] = None,
        checked_by: int = 0,
        progress_session_id: Optional[str] = None,
    ) -> Dict:
        """Run health check for all feeds or specific feed with optional progress tracking."""
        self.logger.info("Starting feed health check...")

        if not self.ensure_health_logs_table():
            return {"error": "Failed to initialize health logs table"}

        # Get feeds to check
        if feed_id:
            conn = self.get_db_connection()
            if not conn:
                return {"error": "Database connection failed"}

            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, name, url, feed_type, format_config, is_active, api_key
                    FROM threat_feeds
                    WHERE id = ? AND is_active = 1
                """,
                    (feed_id,),
                )

                feed_row = cursor.fetchone()
                if not feed_row:
                    return {"error": f"Feed {feed_id} not found or inactive"}

                feeds = [dict(feed_row)]
            finally:
                conn.close()
        else:
            feeds = self.get_active_feeds()

        if not feeds:
            self.logger.warning("No active feeds found")
            return {"error": "No active feeds found"}

        # Initialize progress tracking if session provided
        if progress_session_id:
            self.update_progress(
                progress_session_id, status="running", total_feeds=len(feeds)
            )

        # Check health for each feed
        health_results = []
        for i, feed in enumerate(feeds):
            # Check if session was cancelled
            if progress_session_id:
                session = self.get_progress(progress_session_id)
                if session.get("cancelled"):
                    self.logger.info(
                        f"Health check cancelled for session {progress_session_id}"
                    )
                    return {
                        "error": "Health check cancelled",
                        "partial_results": health_results,
                    }

                # Update current feed being checked
                self.update_progress(
                    progress_session_id,
                    current_feed={
                        "name": feed["name"],
                        "url": feed["url"],
                        "index": i + 1,
                    },
                )

            try:
                health_result = self.check_feed_health(feed)
                health_results.append(health_result)

                # Update progress with completed feed
                if progress_session_id:
                    self.update_progress(
                        progress_session_id, completed_feeds=i + 1, current_feed=None
                    )

                    # Add result to progress session
                    session = self.get_progress(progress_session_id)
                    session["results"].append(health_result)

                # Log to database
                if not self.log_health_result(health_result, checked_by):
                    self.logger.warning(
                        f"Failed to log health result for feed {feed['name']}"
                    )

            except Exception as e:
                error_msg = f"Health check failed for feed {feed['name']}: {e}"
                self.logger.error(error_msg)

                # Add error to progress session
                if progress_session_id:
                    session = self.get_progress(progress_session_id)
                    session["errors"].append(
                        {
                            "feed_name": feed["name"],
                            "error": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

        # Mark progress as completed
        if progress_session_id:
            self.update_progress(
                progress_session_id, status="completed", current_feed=None
            )

        # Update cache
        self.update_health_cache(health_results)

        # Calculate summary
        total_feeds = len(health_results)
        healthy_feeds = len([r for r in health_results if r["status"] == "ok"])
        unhealthy_feeds = total_feeds - healthy_feeds

        result = {
            "success": True,
            "summary": {
                "total_feeds": total_feeds,
                "healthy_feeds": healthy_feeds,
                "unhealthy_feeds": unhealthy_feeds,
                "health_percentage": round(
                    (healthy_feeds / total_feeds * 100) if total_feeds > 0 else 0, 1
                ),
            },
            "feeds": health_results,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checked_by": "system" if checked_by == 0 else f"user_{checked_by}",
            "session_id": progress_session_id,
        }

        self.logger.info(
            f"Health check completed: {healthy_feeds}/{total_feeds} feeds healthy"
        )
        return result

    def start_cron_scheduler(self, interval_minutes: int = 1):
        """Start cron scheduler for regular health checks."""
        if not SCHEDULER_AVAILABLE:
            self.logger.error("APScheduler not available. Cannot start cron scheduler.")
            return False

        try:
            self.scheduler = BackgroundScheduler()

            # Add job for regular health checks
            self.scheduler.add_job(
                func=self.run_health_check,
                trigger="interval",
                minutes=interval_minutes,
                id="feed_health_check",
                name="Feed Health Check",
                replace_existing=True,
            )

            self.scheduler.start()
            self.logger.info(
                f"Cron scheduler started with {interval_minutes}-minute interval"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to start cron scheduler: {e}")
            return False

    def stop_cron_scheduler(self):
        """Stop the cron scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Cron scheduler stopped")

    def get_scheduler_status(self) -> Dict:
        """Get scheduler status information."""
        if not self.scheduler:
            return {"running": False, "jobs": []}

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
            )

        return {"running": self.scheduler.running, "jobs": jobs}


def run_startup_health_check():
    """Run initial health check on server startup."""
    print("🏥 Running startup health check...")

    monitor = FeedHealthMonitor()
    result = monitor.run_health_check(checked_by=0)

    if result.get("success"):
        summary = result["summary"]
        print(f"✅ Startup health check completed:")
        print(
            f"   📊 {summary['healthy_feeds']}/{summary['total_feeds']} feeds healthy ({summary['health_percentage']}%)"
        )

        # Show unhealthy feeds
        unhealthy = [f for f in result["feeds"] if f["status"] != "ok"]
        if unhealthy:
            print(f"   ⚠️  Unhealthy feeds:")
            for feed in unhealthy:
                print(
                    f"      - {feed['feed_name']}: {feed['status']} ({feed.get('error_message', 'No details')})"
                )
    else:
        print(f"❌ Startup health check failed: {result.get('error', 'Unknown error')}")

    return result


def main():
    """Main CLI interface for feed health monitor."""
    import argparse

    parser = argparse.ArgumentParser(description="SentinelForge Feed Health Monitor")
    parser.add_argument(
        "--check-now", action="store_true", help="Run one-time health check"
    )
    parser.add_argument(
        "--start-cron", action="store_true", help="Start cron scheduler"
    )
    parser.add_argument(
        "--interval", type=int, default=1, help="Cron interval in minutes (default: 1)"
    )
    parser.add_argument("--feed-id", type=int, help="Check specific feed ID")
    parser.add_argument(
        "--startup", action="store_true", help="Run startup health check"
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    args = parser.parse_args()

    if args.startup:
        run_startup_health_check()
        return

    monitor = FeedHealthMonitor(log_level=args.log_level)

    if args.check_now:
        print("🔍 Running one-time health check...")
        result = monitor.run_health_check(feed_id=args.feed_id)

        if result.get("success"):
            summary = result["summary"]
            print(f"✅ Health check completed:")
            print(
                f"   📊 {summary['healthy_feeds']}/{summary['total_feeds']} feeds healthy ({summary['health_percentage']}%)"
            )

            # Show detailed results
            for feed in result["feeds"]:
                status_emoji = "✅" if feed["status"] == "ok" else "❌"
                print(
                    f"   {status_emoji} {feed['feed_name']}: {feed['status']} ({feed['response_time_ms']}ms)"
                )
                if feed.get("error_message"):
                    print(f"      Error: {feed['error_message']}")
        else:
            print(f"❌ Health check failed: {result.get('error', 'Unknown error')}")

    elif args.start_cron:
        print(f"⏰ Starting cron scheduler with {args.interval}-minute interval...")

        if monitor.start_cron_scheduler(args.interval):
            print("✅ Cron scheduler started successfully")
            print("   Press Ctrl+C to stop")

            try:
                # Keep main thread alive
                import time

                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping cron scheduler...")
                monitor.stop_cron_scheduler()
                print("✅ Cron scheduler stopped")
        else:
            print("❌ Failed to start cron scheduler")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
