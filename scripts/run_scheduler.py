#!/usr/bin/env python3
"""
Standalone script to run the SentinelForge scheduled feed importer.

This script can be used to run the scheduler as a standalone service,
in a Docker container, or as a systemd service.

Usage:
    # Run once and exit
    python scripts/run_scheduler.py --run-once

    # Run with custom CRON schedule
    python scripts/run_scheduler.py --cron "0 */4 * * *"

    # Run with custom configuration
    python scripts/run_scheduler.py --db-path /path/to/db --log-file /path/to/log

    # Run as daemon (background service)
    python scripts/run_scheduler.py --daemon
"""

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.scheduled_importer import ScheduledFeedImporter
from config.scheduler_config import SchedulerConfig, setup_environment


class SchedulerDaemon:
    """Daemon wrapper for the scheduled importer."""

    def __init__(self, importer: ScheduledFeedImporter):
        self.importer = importer
        self.running = False
        self.logger = logging.getLogger("scheduler_daemon")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self, cron_expression: str = "0 */6 * * *"):
        """Start the daemon."""
        self.logger.info("Starting scheduler daemon...")
        self.running = True

        try:
            # Start the scheduler
            self.importer.start_scheduler(cron_expression)
            self.logger.info(f"Scheduler started with CRON: {cron_expression}")

            # Keep daemon running
            while self.running:
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
            raise
        finally:
            self.stop()

    def stop(self):
        """Stop the daemon."""
        if self.running:
            self.logger.info("Stopping scheduler daemon...")
            self.running = False

            if self.importer:
                self.importer.stop_scheduler()

            self.logger.info("Scheduler daemon stopped")


def setup_logging(log_file: str, log_level: str, daemon_mode: bool = False):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (unless in daemon mode)
    if not daemon_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="SentinelForge Scheduled Feed Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once and exit
  python scripts/run_scheduler.py --run-once
  
  # Run with custom schedule (every 4 hours)
  python scripts/run_scheduler.py --cron "0 */4 * * *"
  
  # Run as daemon with custom config
  python scripts/run_scheduler.py --daemon --db-path /opt/sentinelforge/db.sqlite
  
  # Test configuration
  python scripts/run_scheduler.py --test-config
        """,
    )

    # Configuration arguments
    parser.add_argument(
        "--db-path",
        default=None,
        help=f"Database path (default: {SchedulerConfig.DB_PATH})",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help=f"Log file path (default: {SchedulerConfig.LOG_FILE})",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help=f"Log level (default: {SchedulerConfig.LOG_LEVEL})",
    )
    parser.add_argument(
        "--cron",
        default=None,
        help=f"CRON expression (default: {SchedulerConfig.CRON_EXPRESSION})",
    )

    # Execution mode arguments
    parser.add_argument(
        "--run-once", action="store_true", help="Run import once and exit"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run as daemon (background service)"
    )
    parser.add_argument(
        "--test-config", action="store_true", help="Test configuration and exit"
    )

    # HTTP settings
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"HTTP timeout in seconds (default: {SchedulerConfig.REQUEST_TIMEOUT})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help=f"Maximum retries (default: {SchedulerConfig.MAX_RETRIES})",
    )

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # Override configuration with command line arguments
    if args.db_path:
        os.environ["SENTINELFORGE_DB_PATH"] = args.db_path
    if args.log_file:
        os.environ["SCHEDULER_LOG_FILE"] = args.log_file
    if args.log_level:
        os.environ["SCHEDULER_LOG_LEVEL"] = args.log_level
    if args.cron:
        os.environ["SCHEDULER_CRON"] = args.cron
    if args.timeout:
        os.environ["SCHEDULER_TIMEOUT"] = str(args.timeout)
    if args.max_retries:
        os.environ["SCHEDULER_MAX_RETRIES"] = str(args.max_retries)

    # Reload configuration
    SchedulerConfig.__dict__.update(
        {
            "DB_PATH": os.getenv("SENTINELFORGE_DB_PATH"),
            "LOG_FILE": os.getenv("SCHEDULER_LOG_FILE"),
            "LOG_LEVEL": os.getenv("SCHEDULER_LOG_LEVEL"),
            "CRON_EXPRESSION": os.getenv("SCHEDULER_CRON"),
            "REQUEST_TIMEOUT": int(os.getenv("SCHEDULER_TIMEOUT")),
            "MAX_RETRIES": int(os.getenv("SCHEDULER_MAX_RETRIES")),
        }
    )

    # Test configuration
    if args.test_config:
        print("Testing configuration...")
        print(f"Database path: {SchedulerConfig.DB_PATH}")
        print(f"Log file: {SchedulerConfig.LOG_FILE}")
        print(f"CRON expression: {SchedulerConfig.CRON_EXPRESSION}")
        print(f"Timeout: {SchedulerConfig.REQUEST_TIMEOUT}s")
        print(f"Max retries: {SchedulerConfig.MAX_RETRIES}")

        if SchedulerConfig.validate():
            print("✅ Configuration is valid")
            return 0
        else:
            print("❌ Configuration validation failed")
            return 1

    # Validate configuration
    if not SchedulerConfig.validate():
        print("Configuration validation failed. Use --test-config to see details.")
        return 1

    # Setup logging
    setup_logging(
        SchedulerConfig.LOG_FILE, SchedulerConfig.LOG_LEVEL, daemon_mode=args.daemon
    )

    logger = logging.getLogger("run_scheduler")

    # Create importer
    try:
        importer = ScheduledFeedImporter(
            db_path=SchedulerConfig.DB_PATH,
            log_file=SchedulerConfig.LOG_FILE,
            max_retries=SchedulerConfig.MAX_RETRIES,
            timeout=SchedulerConfig.REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.error(f"Failed to create importer: {e}")
        return 1

    # Execute based on mode
    try:
        if args.run_once:
            # Run once and exit
            logger.info("Running scheduled import once...")
            results = importer.run_once()

            print("Import completed:")
            print(f"  Successful: {results['successful_imports']}")
            print(f"  Failed: {results['failed_imports']}")
            print(f"  Skipped: {results['skipped_feeds']}")
            print(f"  IOCs imported: {results['total_iocs_imported']}")
            print(f"  Duration: {results['duration_seconds']}s")

            return 0 if results["failed_imports"] == 0 else 1

        elif args.daemon:
            # Run as daemon
            daemon = SchedulerDaemon(importer)
            daemon.start(SchedulerConfig.CRON_EXPRESSION)
            return 0

        else:
            # Interactive mode
            print("Starting SentinelForge Scheduled Feed Importer")
            print(f"CRON: {SchedulerConfig.CRON_EXPRESSION}")
            print(f"Database: {SchedulerConfig.DB_PATH}")
            print(f"Log: {SchedulerConfig.LOG_FILE}")
            print("Press Ctrl+C to stop...")

            importer.start_scheduler(SchedulerConfig.CRON_EXPRESSION)

            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
                importer.stop_scheduler()
                return 0

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
