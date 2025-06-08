#!/usr/bin/env python3
"""
Example Flask application with integrated scheduled feed importer.

This demonstrates how to integrate the SentinelForge scheduled feed importer
into a Flask application with proper startup/shutdown handling and API endpoints.

Usage:
    python examples/flask_app_with_scheduler.py
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request
from services.background_tasks import setup_flask_importer
from config.scheduler_config import SchedulerConfig, setup_environment


def create_app():
    """Create and configure Flask application with scheduled importer."""

    # Setup environment
    setup_environment()

    # Validate configuration
    if not SchedulerConfig.validate():
        print("Configuration validation failed. Exiting.")
        sys.exit(1)

    # Create Flask app
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, SchedulerConfig.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Setup scheduled importer
    importer = setup_flask_importer(
        app=app, cron_expression=SchedulerConfig.CRON_EXPRESSION, auto_start=True
    )

    # Additional API endpoints
    @app.route("/")
    def index():
        """Home page with scheduler status."""
        is_running = (
            importer.importer
            and importer.importer.scheduler
            and importer.importer.scheduler.running
        )

        return jsonify(
            {
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
            }
        )

    @app.route("/api/feeds/enabled")
    def get_enabled_feeds():
        """Get list of enabled feeds."""
        try:
            if not importer.importer:
                importer.importer = importer.create_importer()

            feeds = importer.importer.get_enabled_feeds()
            return jsonify({"success": True, "feeds": feeds, "count": len(feeds)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/feeds/<int:feed_id>/import", methods=["POST"])
    def import_single_feed(feed_id):
        """Import a specific feed by ID."""
        try:
            if not importer.importer:
                importer.importer = importer.create_importer()

            # Get the specific feed
            feeds = importer.importer.get_enabled_feeds()
            feed = next((f for f in feeds if f["id"] == feed_id), None)

            if not feed:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Feed with ID {feed_id} not found or not enabled",
                    }
                ), 404

            # Import the feed
            result = importer.importer.import_feed(feed)

            return jsonify(
                {
                    "success": True,
                    "message": f"Import completed for feed: {feed['name']}",
                    "result": result,
                }
            )

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config")
    def get_config():
        """Get current configuration."""
        return jsonify(
            {
                "config": SchedulerConfig.to_dict(),
                "cron_schedules": {
                    "current": SchedulerConfig.CRON_EXPRESSION,
                    "available": {
                        "every_hour": "0 * * * *",
                        "every_6_hours": "0 */6 * * *",
                        "daily_midnight": "0 0 * * *",
                        "weekly_sunday": "0 0 * * 0",
                    },
                },
            }
        )

    @app.route("/api/health")
    def health_check():
        """Health check endpoint."""
        try:
            # Check database connectivity
            if not importer.importer:
                importer.importer = importer.create_importer()

            conn = importer.importer.get_db_connection()
            cursor = conn.execute("SELECT COUNT(*) FROM threat_feeds")
            feed_count = cursor.fetchone()[0]
            conn.close()

            return jsonify(
                {
                    "status": "healthy",
                    "database": "connected",
                    "feed_count": feed_count,
                    "scheduler_running": (
                        importer.importer
                        and importer.importer.scheduler
                        and importer.importer.scheduler.running
                    ),
                }
            )

        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {"error": "Not found", "message": "The requested resource was not found"}
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }
        ), 500

    return app


def main():
    """Main function to run the Flask application."""
    app = create_app()

    # Get configuration
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print(f"Starting SentinelForge Feed Importer Service")
    print(f"Server: http://{host}:{port}")
    print(f"Scheduler CRON: {SchedulerConfig.CRON_EXPRESSION}")
    print(f"Database: {SchedulerConfig.DB_PATH}")
    print(f"Log file: {SchedulerConfig.LOG_FILE}")
    print("\nAPI Endpoints:")
    print("  GET  /                           - Service status")
    print("  GET  /api/health                 - Health check")
    print("  GET  /api/config                 - Configuration")
    print("  GET  /api/feeds/enabled          - List enabled feeds")
    print("  POST /api/feeds/<id>/import      - Import specific feed")
    print("  POST /api/admin/feeds/import     - Manual import all feeds")
    print("  GET  /api/admin/feeds/scheduler/status - Scheduler status")
    print("  POST /api/admin/feeds/scheduler/start  - Start scheduler")
    print("  POST /api/admin/feeds/scheduler/stop   - Stop scheduler")
    print("\nPress Ctrl+C to stop the server")

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
