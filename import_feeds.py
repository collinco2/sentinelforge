#!/usr/bin/env python3
"""
SentinelForge Feed Configuration Import Script

This script reads feed configurations from feeds_config.json and registers
them with the SentinelForge API server running on localhost:5059.

Usage:
    python import_feeds.py [--token YOUR_BEARER_TOKEN]

Environment Variables:
    SENTINELFORGE_TOKEN - Bearer token for API authentication
"""

import json
import sys
import argparse
import os
import requests
from typing import Dict, List, Optional


def load_feed_config(config_file: str = "feeds_config.json") -> List[Dict]:
    """Load feed configurations from JSON file."""
    try:
        with open(config_file, "r") as f:
            feeds = json.load(f)
        print(f"✓ Loaded {len(feeds)} feed configurations from {config_file}")
        return feeds
    except FileNotFoundError:
        print(f"❌ Error: Configuration file '{config_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{config_file}': {e}")
        sys.exit(1)


def register_feed(feed_config: Dict, api_url: str, token: Optional[str] = None) -> bool:
    """Register a single feed with the SentinelForge API."""
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            f"{api_url}/api/feeds", json=feed_config, headers=headers, timeout=30
        )

        if response.status_code == 201:
            print(f"✓ Successfully registered feed: {feed_config['name']}")
            return True
        elif response.status_code == 409:
            print(f"⚠️  Feed already exists: {feed_config['name']}")
            return True
        elif response.status_code == 401:
            print(f"❌ Authentication failed for feed: {feed_config['name']}")
            return False
        elif response.status_code == 403:
            print(f"❌ Insufficient permissions for feed: {feed_config['name']}")
            return False
        else:
            print(
                f"❌ Failed to register feed '{feed_config['name']}': "
                f"HTTP {response.status_code} - {response.text}"
            )
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {api_url}")
        print("   Make sure the SentinelForge API server is running on port 5059")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error while registering feed: {feed_config['name']}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for feed '{feed_config['name']}': {e}")
        return False


def main():
    """Main function to import feed configurations."""
    parser = argparse.ArgumentParser(
        description="Import SentinelForge feed configurations"
    )
    parser.add_argument("--token", help="Bearer token for API authentication")
    parser.add_argument(
        "--config",
        default="feeds_config.json",
        help="Path to feed configuration file (default: feeds_config.json)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:5059",
        help="SentinelForge API URL (default: http://localhost:5059)",
    )
    parser.add_argument(
        "--enabled-only",
        action="store_true",
        help="Only import feeds marked as enabled",
    )

    args = parser.parse_args()

    # Get token from argument or environment variable
    token = args.token or os.getenv("SENTINELFORGE_TOKEN")

    if not token:
        print("⚠️  Warning: No authentication token provided")
        print("   Use --token argument or set SENTINELFORGE_TOKEN environment variable")
        print("   Some feeds may require authentication to register")
        print()

    # Load feed configurations
    feeds = load_feed_config(args.config)

    # Filter enabled feeds if requested
    if args.enabled_only:
        feeds = [feed for feed in feeds if feed.get("enabled", False)]
        print(f"📋 Importing {len(feeds)} enabled feeds only")
    else:
        print(f"📋 Importing all {len(feeds)} feeds")

    print(f"🎯 Target API: {args.api_url}")
    print("-" * 50)

    # Register each feed
    success_count = 0
    failure_count = 0

    for feed in feeds:
        if register_feed(feed, args.api_url, token):
            success_count += 1
        else:
            failure_count += 1

    # Summary
    print("-" * 50)
    print("📊 Import Summary:")
    print(f"   ✓ Successful: {success_count}")
    print(f"   ❌ Failed: {failure_count}")
    print(f"   📋 Total: {len(feeds)}")

    if failure_count > 0:
        print("\n💡 Troubleshooting tips:")
        print("   • Ensure SentinelForge API server is running (python app.py)")
        print("   • Check if authentication token is valid")
        print("   • Verify network connectivity to external feed URLs")
        sys.exit(1)
    else:
        print("\n🎉 All feeds imported successfully!")


if __name__ == "__main__":
    main()
