#!/usr/bin/env python3
"""
Configuration for SentinelForge Scheduled Feed Importer

This module provides configuration settings and environment-based
configuration for the scheduled feed importer service.
"""

import os
from typing import Dict, Any


class SchedulerConfig:
    """Configuration class for the scheduled feed importer."""

    # Database settings
    DB_PATH = os.getenv(
        "SENTINELFORGE_DB_PATH", "/Users/Collins/sentinelforge/ioc_store.db"
    )

    # Logging settings
    LOG_FILE = os.getenv("SCHEDULER_LOG_FILE", "scheduled_importer.log")
    LOG_LEVEL = os.getenv("SCHEDULER_LOG_LEVEL", "INFO")

    # Scheduler settings
    CRON_EXPRESSION = os.getenv("SCHEDULER_CRON", "0 */6 * * *")  # Every 6 hours
    TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")

    # HTTP settings
    REQUEST_TIMEOUT = int(os.getenv("SCHEDULER_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("SCHEDULER_MAX_RETRIES", "3"))
    BASE_DELAY = float(os.getenv("SCHEDULER_BASE_DELAY", "1.0"))
    MAX_DELAY = float(os.getenv("SCHEDULER_MAX_DELAY", "60.0"))

    # Feed settings
    DEFAULT_IMPORT_INTERVAL_HOURS = int(os.getenv("DEFAULT_IMPORT_INTERVAL", "24"))
    SKIP_AUTH_VALIDATION = os.getenv("SKIP_AUTH_VALIDATION", "false").lower() == "true"

    # Performance settings
    MAX_CONCURRENT_IMPORTS = int(os.getenv("MAX_CONCURRENT_IMPORTS", "3"))
    TEMP_DIR = os.getenv("SCHEDULER_TEMP_DIR", "/tmp")

    # Security settings
    USER_AGENT = os.getenv("SCHEDULER_USER_AGENT", "SentinelForge-FeedImporter/1.0")

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and not callable(getattr(cls, key))
        }

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        errors = []

        # Check database path
        if not os.path.exists(os.path.dirname(cls.DB_PATH)):
            errors.append(
                f"Database directory does not exist: {os.path.dirname(cls.DB_PATH)}"
            )

        # Check CRON expression format
        cron_parts = cls.CRON_EXPRESSION.split()
        if len(cron_parts) != 5:
            errors.append(f"Invalid CRON expression: {cls.CRON_EXPRESSION}")

        # Check numeric values
        if cls.REQUEST_TIMEOUT <= 0:
            errors.append(f"Invalid timeout: {cls.REQUEST_TIMEOUT}")

        if cls.MAX_RETRIES < 0:
            errors.append(f"Invalid max retries: {cls.MAX_RETRIES}")

        if cls.BASE_DELAY <= 0:
            errors.append(f"Invalid base delay: {cls.BASE_DELAY}")

        if cls.MAX_DELAY <= cls.BASE_DELAY:
            errors.append(f"Max delay must be greater than base delay")

        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True


# Predefined CRON expressions for common schedules
CRON_SCHEDULES = {
    "every_hour": "0 * * * *",
    "every_2_hours": "0 */2 * * *",
    "every_6_hours": "0 */6 * * *",
    "every_12_hours": "0 */12 * * *",
    "daily_midnight": "0 0 * * *",
    "daily_6am": "0 6 * * *",
    "daily_noon": "0 12 * * *",
    "daily_6pm": "0 18 * * *",
    "weekly_sunday": "0 0 * * 0",
    "weekly_monday": "0 0 * * 1",
    "business_hours": "0 9-17 * * 1-5",  # Every hour 9-5, Mon-Fri
}


# Feed-specific configurations
FEED_CONFIGS = {
    "phishtank": {
        "requires_api_key": True,
        "rate_limit_delay": 5,  # seconds between requests
        "max_requests_per_hour": 100,
    },
    "alienvault_otx": {
        "custom_parser": True,
        "delimiter": "#",
        "skip_malformed": True,
    },
    "urlhaus": {
        "skip_comments": True,
        "comment_prefix": "#",
        "validate_urls": True,
    },
    "taxii": {
        "requires_auth": True,
        "auth_type": "basic",
        "timeout": 60,  # TAXII can be slow
    },
}


def get_feed_config(feed_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific feed.

    Args:
        feed_name: Name of the feed

    Returns:
        Configuration dictionary for the feed
    """
    feed_name_lower = feed_name.lower()

    for config_key, config in FEED_CONFIGS.items():
        if config_key in feed_name_lower:
            return config.copy()

    # Return default configuration
    return {
        "requires_api_key": False,
        "rate_limit_delay": 1,
        "max_requests_per_hour": 1000,
        "custom_parser": False,
        "skip_comments": False,
        "validate_urls": False,
    }


def setup_environment():
    """Setup environment variables with defaults if not set."""
    env_defaults = {
        "SENTINELFORGE_DB_PATH": "/Users/Collins/sentinelforge/ioc_store.db",
        "SCHEDULER_LOG_FILE": "scheduled_importer.log",
        "SCHEDULER_LOG_LEVEL": "INFO",
        "SCHEDULER_CRON": "0 */6 * * *",
        "SCHEDULER_TIMEZONE": "UTC",
        "SCHEDULER_TIMEOUT": "30",
        "SCHEDULER_MAX_RETRIES": "3",
        "SCHEDULER_BASE_DELAY": "1.0",
        "SCHEDULER_MAX_DELAY": "60.0",
        "DEFAULT_IMPORT_INTERVAL": "24",
        "SKIP_AUTH_VALIDATION": "false",
        "MAX_CONCURRENT_IMPORTS": "3",
        "SCHEDULER_TEMP_DIR": "/tmp",
        "SCHEDULER_USER_AGENT": "SentinelForge-FeedImporter/1.0",
    }

    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value


def print_config():
    """Print current configuration settings."""
    print("SentinelForge Scheduler Configuration:")
    print("=" * 40)

    config_dict = SchedulerConfig.to_dict()
    for key, value in sorted(config_dict.items()):
        print(f"{key:25}: {value}")

    print("\nAvailable CRON schedules:")
    print("-" * 25)
    for name, cron in CRON_SCHEDULES.items():
        print(f"{name:20}: {cron}")


if __name__ == "__main__":
    # Setup environment and validate configuration
    setup_environment()

    print_config()

    print(f"\nConfiguration valid: {SchedulerConfig.validate()}")
