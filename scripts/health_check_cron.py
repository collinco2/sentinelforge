#!/usr/bin/env python3
"""
SentinelForge Feed Health Check Cron Job

Standalone script for running feed health checks via cron.
Can be scheduled to run at regular intervals.

Usage:
    # Add to crontab for 1-minute intervals:
    * * * * * /usr/bin/python3 /path/to/sentinelforge/scripts/health_check_cron.py

    # Add to crontab for 5-minute intervals:
    */5 * * * * /usr/bin/python3 /path/to/sentinelforge/scripts/health_check_cron.py

    # Run manually:
    python3 scripts/health_check_cron.py
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_logging():
    """Setup logging for cron job."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "health_check_cron.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Main cron job execution."""
    logger = setup_logging()
    
    try:
        logger.info("Starting scheduled feed health check...")
        
        # Import and run health check
        from services.feed_health_monitor import FeedHealthMonitor
        
        monitor = FeedHealthMonitor()
        result = monitor.run_health_check(checked_by=0)  # System check
        
        if result.get("success"):
            summary = result["summary"]
            logger.info(
                f"Health check completed: {summary['healthy_feeds']}/{summary['total_feeds']} "
                f"feeds healthy ({summary['health_percentage']}%)"
            )
            
            # Log any unhealthy feeds
            unhealthy_feeds = [f for f in result["feeds"] if f["status"] != "ok"]
            if unhealthy_feeds:
                logger.warning(f"Found {len(unhealthy_feeds)} unhealthy feeds:")
                for feed in unhealthy_feeds:
                    logger.warning(
                        f"  - {feed['feed_name']}: {feed['status']} "
                        f"({feed.get('error_message', 'No details')})"
                    )
        else:
            logger.error(f"Health check failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except ImportError as e:
        logger.error(f"Failed to import health monitor: {e}")
        logger.error("Make sure you're running from the SentinelForge root directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Health check cron job failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
