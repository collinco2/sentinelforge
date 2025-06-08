#!/usr/bin/env python3
"""
Background Task Integration for SentinelForge

Provides integration classes for running the scheduled feed importer
as a background task in Flask or FastAPI applications.

Usage:
    # Flask integration
    from services.background_tasks import FlaskScheduledImporter
    app = Flask(__name__)
    importer = FlaskScheduledImporter(app)
    importer.start()

    # FastAPI integration
    from services.background_tasks import FastAPIScheduledImporter
    app = FastAPI()
    importer = FastAPIScheduledImporter(app)
    await importer.start()
"""

import asyncio
import logging
import threading
from typing import Dict, Optional

try:
    from flask import Flask

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from fastapi import FastAPI

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from services.scheduled_importer import ScheduledFeedImporter


class BaseScheduledImporter:
    """Base class for framework-specific scheduled importers."""

    def __init__(
        self,
        app,
        db_path: str = "/Users/Collins/sentinelforge/ioc_store.db",
        log_file: str = "scheduled_importer.log",
        cron_expression: str = "0 */6 * * *",
        auto_start: bool = False,
    ):
        self.app = app
        self.db_path = db_path
        self.log_file = log_file
        self.cron_expression = cron_expression
        self.importer = None
        self.logger = logging.getLogger("background_tasks")

        if auto_start:
            self.start()

    def create_importer(self) -> ScheduledFeedImporter:
        """Create and configure the scheduled importer."""
        return ScheduledFeedImporter(db_path=self.db_path, log_file=self.log_file)

    def start(self):
        """Start the scheduled importer (to be implemented by subclasses)."""
        raise NotImplementedError

    def stop(self):
        """Stop the scheduled importer (to be implemented by subclasses)."""
        raise NotImplementedError

    def run_manual_import(self) -> Dict:
        """Run a manual import and return results."""
        if not self.importer:
            self.importer = self.create_importer()
        return self.importer.run_once()


class FlaskScheduledImporter(BaseScheduledImporter):
    """Flask integration for scheduled feed importer."""

    def __init__(self, app: Optional[Flask] = None, **kwargs):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask not available. Install with: pip install flask")

        super().__init__(app, **kwargs)
        self._thread = None
        self._stop_event = threading.Event()

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the Flask app with the scheduled importer."""
        self.app = app

        # Register teardown handler
        @app.teardown_appcontext
        def shutdown_importer(exception):
            if exception:
                self.logger.error(f"Flask teardown with exception: {exception}")
            self.stop()

        # Add API endpoints for manual control
        @app.route("/api/admin/feeds/import", methods=["POST"])
        def manual_import():
            """Trigger a manual feed import."""
            try:
                results = self.run_manual_import()
                return {
                    "success": True,
                    "message": "Manual import completed",
                    "results": results,
                }, 200
            except Exception as e:
                self.logger.error(f"Manual import failed: {e}")
                return {"success": False, "error": str(e)}, 500

        @app.route("/api/admin/feeds/scheduler/status", methods=["GET"])
        def scheduler_status():
            """Get scheduler status."""
            is_running = (
                self.importer
                and self.importer.scheduler
                and self.importer.scheduler.running
            )
            return {
                "running": is_running,
                "cron_expression": self.cron_expression,
                "next_run": None,  # Could be enhanced to show next scheduled run
            }

        @app.route("/api/admin/feeds/scheduler/start", methods=["POST"])
        def start_scheduler():
            """Start the scheduler."""
            try:
                self.start()
                return {"success": True, "message": "Scheduler started"}
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @app.route("/api/admin/feeds/scheduler/stop", methods=["POST"])
        def stop_scheduler():
            """Stop the scheduler."""
            try:
                self.stop()
                return {"success": True, "message": "Scheduler stopped"}
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

    def start(self):
        """Start the scheduled importer in a background thread."""
        if self._thread and self._thread.is_alive():
            self.logger.warning("Scheduler already running")
            return

        self._stop_event.clear()

        def run_scheduler():
            try:
                self.importer = self.create_importer()
                self.importer.start_scheduler(self.cron_expression)

                # Keep thread alive until stop event
                while not self._stop_event.wait(1):
                    pass

            except Exception as e:
                self.logger.error(f"Scheduler thread error: {e}")
            finally:
                if self.importer:
                    self.importer.stop_scheduler()

        self._thread = threading.Thread(target=run_scheduler, daemon=True)
        self._thread.start()
        self.logger.info("Flask scheduled importer started")

    def stop(self):
        """Stop the scheduled importer."""
        if self._stop_event:
            self._stop_event.set()

        if self.importer:
            self.importer.stop_scheduler()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self.logger.info("Flask scheduled importer stopped")


class FastAPIScheduledImporter(BaseScheduledImporter):
    """FastAPI integration for scheduled feed importer."""

    def __init__(self, app: Optional[FastAPI] = None, **kwargs):
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI not available. Install with: pip install fastapi"
            )

        super().__init__(app, **kwargs)
        self._task = None

        if app:
            self.init_app(app)

    def init_app(self, app: FastAPI):
        """Initialize the FastAPI app with the scheduled importer."""
        self.app = app

        # Register startup and shutdown events
        @app.on_event("startup")
        async def startup_importer():
            await self.start()

        @app.on_event("shutdown")
        async def shutdown_importer():
            await self.stop()

        # Add API endpoints for manual control
        @app.post("/api/admin/feeds/import")
        async def manual_import():
            """Trigger a manual feed import."""
            try:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(None, self.run_manual_import)
                return {
                    "success": True,
                    "message": "Manual import completed",
                    "results": results,
                }
            except Exception as e:
                self.logger.error(f"Manual import failed: {e}")
                return {"success": False, "error": str(e)}

        @app.get("/api/admin/feeds/scheduler/status")
        async def scheduler_status():
            """Get scheduler status."""
            is_running = (
                self.importer
                and self.importer.scheduler
                and self.importer.scheduler.running
            )
            return {
                "running": is_running,
                "cron_expression": self.cron_expression,
                "next_run": None,  # Could be enhanced to show next scheduled run
            }

        @app.post("/api/admin/feeds/scheduler/start")
        async def start_scheduler():
            """Start the scheduler."""
            try:
                await self.start()
                return {"success": True, "message": "Scheduler started"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        @app.post("/api/admin/feeds/scheduler/stop")
        async def stop_scheduler():
            """Stop the scheduler."""
            try:
                await self.stop()
                return {"success": True, "message": "Scheduler stopped"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def start(self):
        """Start the scheduled importer as an async task."""
        if self._task and not self._task.done():
            self.logger.warning("Scheduler already running")
            return

        async def run_scheduler():
            try:
                # Run scheduler in thread pool
                loop = asyncio.get_event_loop()
                self.importer = self.create_importer()

                # Start scheduler in executor
                await loop.run_in_executor(
                    None, self.importer.start_scheduler, self.cron_expression
                )

                # Keep task alive
                while True:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                self.logger.info("Scheduler task cancelled")
                if self.importer:
                    self.importer.stop_scheduler()
                raise
            except Exception as e:
                self.logger.error(f"Scheduler task error: {e}")
                if self.importer:
                    self.importer.stop_scheduler()

        self._task = asyncio.create_task(run_scheduler())
        self.logger.info("FastAPI scheduled importer started")

    async def stop(self):
        """Stop the scheduled importer."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.importer:
            self.importer.stop_scheduler()

        self.logger.info("FastAPI scheduled importer stopped")


# Convenience functions for quick setup
def setup_flask_importer(
    app: Flask, cron_expression: str = "0 */6 * * *", auto_start: bool = True
) -> FlaskScheduledImporter:
    """
    Quick setup for Flask scheduled importer.

    Args:
        app: Flask application instance
        cron_expression: CRON expression for scheduling
        auto_start: Whether to start the scheduler immediately

    Returns:
        Configured FlaskScheduledImporter instance
    """
    return FlaskScheduledImporter(
        app=app, cron_expression=cron_expression, auto_start=auto_start
    )


def setup_fastapi_importer(
    app: FastAPI, cron_expression: str = "0 */6 * * *", auto_start: bool = True
) -> FastAPIScheduledImporter:
    """
    Quick setup for FastAPI scheduled importer.

    Args:
        app: FastAPI application instance
        cron_expression: CRON expression for scheduling
        auto_start: Whether to start the scheduler immediately

    Returns:
        Configured FastAPIScheduledImporter instance
    """
    return FastAPIScheduledImporter(
        app=app, cron_expression=cron_expression, auto_start=auto_start
    )
