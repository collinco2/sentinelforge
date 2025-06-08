#!/usr/bin/env python3
"""
Example FastAPI application with integrated scheduled feed importer.

This demonstrates how to integrate the SentinelForge scheduled feed importer
into a FastAPI application with proper startup/shutdown handling and API endpoints.

Usage:
    pip install fastapi uvicorn
    python examples/fastapi_app_with_scheduler.py

    # Or with uvicorn directly:
    uvicorn examples.fastapi_app_with_scheduler:app --host 0.0.0.0 --port 8000
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.responses import JSONResponse
    import uvicorn

    FASTAPI_AVAILABLE = True
except ImportError:
    print("FastAPI not available. Install with: pip install fastapi uvicorn")
    sys.exit(1)

from services.background_tasks import setup_fastapi_importer
from config.scheduler_config import SchedulerConfig, setup_environment


def create_app() -> FastAPI:
    """Create and configure FastAPI application with scheduled importer."""

    # Setup environment
    setup_environment()

    # Validate configuration
    if not SchedulerConfig.validate():
        print("Configuration validation failed. Exiting.")
        sys.exit(1)

    # Create FastAPI app
    app = FastAPI(
        title="SentinelForge Feed Importer Service",
        description="Automated threat intelligence feed importer with scheduling",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, SchedulerConfig.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Setup scheduled importer
    importer = setup_fastapi_importer(
        app=app, cron_expression=SchedulerConfig.CRON_EXPRESSION, auto_start=True
    )

    # Root endpoint
    @app.get("/", tags=["Status"])
    async def root():
        """Service status and information."""
        is_running = (
            importer.importer
            and importer.importer.scheduler
            and importer.importer.scheduler.running
        )

        return {
            "service": "SentinelForge Feed Importer",
            "status": "running",
            "scheduler": {
                "running": is_running,
                "cron_expression": SchedulerConfig.CRON_EXPRESSION,
            },
            "config": {
                "db_path": SchedulerConfig.DB_PATH,
                "log_file": SchedulerConfig.LOG_FILE,
                "timeout": SchedulerConfig.REQUEST_TIMEOUT,
                "max_retries": SchedulerConfig.MAX_RETRIES,
            },
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/api/feeds/enabled", tags=["Feeds"])
    async def get_enabled_feeds():
        """Get list of enabled feeds."""
        try:
            if not importer.importer:
                importer.importer = importer.create_importer()

            feeds = importer.importer.get_enabled_feeds()
            return {"success": True, "feeds": feeds, "count": len(feeds)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get enabled feeds: {str(e)}",
            )

    @app.post("/api/feeds/{feed_id}/import", tags=["Feeds"])
    async def import_single_feed(feed_id: int):
        """Import a specific feed by ID."""
        try:
            if not importer.importer:
                importer.importer = importer.create_importer()

            # Get the specific feed
            feeds = importer.importer.get_enabled_feeds()
            feed = next((f for f in feeds if f["id"] == feed_id), None)

            if not feed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Feed with ID {feed_id} not found or not enabled",
                )

            # Import the feed (run in thread pool to avoid blocking)
            import asyncio

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, importer.importer.import_feed, feed
            )

            return {
                "success": True,
                "message": f"Import completed for feed: {feed['name']}",
                "result": result,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import feed: {str(e)}",
            )

    @app.get("/api/feeds/{feed_id}/status", tags=["Feeds"])
    async def get_feed_status(feed_id: int):
        """Get status and import readiness for a specific feed."""
        try:
            if not importer.importer:
                importer.importer = importer.create_importer()

            feeds = importer.importer.get_enabled_feeds()
            feed = next((f for f in feeds if f["id"] == feed_id), None)

            if not feed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Feed with ID {feed_id} not found",
                )

            should_import, reason = importer.importer.should_import_feed(feed)

            return {
                "feed_id": feed_id,
                "feed_name": feed["name"],
                "enabled": feed["enabled"],
                "url": feed["url"],
                "last_import": feed.get("last_import"),
                "import_interval_hours": feed.get("import_interval_hours", 24),
                "should_import": should_import,
                "reason": reason,
                "requires_auth": feed.get("requires_auth", False),
                "auth_configured": importer.importer._validate_auth_config(feed),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get feed status: {str(e)}",
            )

    @app.get("/api/config", tags=["Configuration"])
    async def get_config():
        """Get current configuration."""
        return {
            "config": SchedulerConfig.to_dict(),
            "cron_schedules": {
                "current": SchedulerConfig.CRON_EXPRESSION,
                "available": {
                    "every_hour": "0 * * * *",
                    "every_2_hours": "0 */2 * * *",
                    "every_6_hours": "0 */6 * * *",
                    "every_12_hours": "0 */12 * * *",
                    "daily_midnight": "0 0 * * *",
                    "daily_6am": "0 6 * * *",
                    "weekly_sunday": "0 0 * * 0",
                },
            },
        }

    @app.get("/api/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        try:
            # Check database connectivity
            if not importer.importer:
                importer.importer = importer.create_importer()

            conn = importer.importer.get_db_connection()
            cursor = conn.execute("SELECT COUNT(*) FROM threat_feeds")
            feed_count = cursor.fetchone()[0]
            conn.close()

            return {
                "status": "healthy",
                "database": "connected",
                "feed_count": feed_count,
                "scheduler_running": (
                    importer.importer
                    and importer.importer.scheduler
                    and importer.importer.scheduler.running
                ),
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Health check failed: {str(e)}",
            )

    # Exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "message": "The requested resource was not found",
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            },
        )

    return app


# Create the app instance
app = create_app()


def main():
    """Main function to run the FastAPI application."""

    # Get configuration
    host = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port = int(os.getenv("FASTAPI_PORT", 8000))
    reload = os.getenv("FASTAPI_RELOAD", "false").lower() == "true"

    print("Starting SentinelForge Feed Importer Service (FastAPI)")
    print(f"Server: http://{host}:{port}")
    print(f"Scheduler CRON: {SchedulerConfig.CRON_EXPRESSION}")
    print(f"Database: {SchedulerConfig.DB_PATH}")
    print(f"Log file: {SchedulerConfig.LOG_FILE}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"ReDoc Documentation: http://{host}:{port}/redoc")
    print("\nAPI Endpoints:")
    print("  GET  /                           - Service status")
    print("  GET  /api/health                 - Health check")
    print("  GET  /api/config                 - Configuration")
    print("  GET  /api/feeds/enabled          - List enabled feeds")
    print("  GET  /api/feeds/{id}/status      - Feed status")
    print("  POST /api/feeds/{id}/import      - Import specific feed")
    print("  POST /api/admin/feeds/import     - Manual import all feeds")
    print("  GET  /api/admin/feeds/scheduler/status - Scheduler status")
    print("  POST /api/admin/feeds/scheduler/start  - Start scheduler")
    print("  POST /api/admin/feeds/scheduler/stop   - Stop scheduler")
    print("\nPress Ctrl+C to stop the server")

    try:
        uvicorn.run(
            "examples.fastapi_app_with_scheduler:app",
            host=host,
            port=port,
            reload=reload,
            log_level=SchedulerConfig.LOG_LEVEL.lower(),
        )
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
