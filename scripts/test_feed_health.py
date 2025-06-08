#!/usr/bin/env python3
"""
Manual test script for the SentinelForge Feed Health Check API.

This script demonstrates how to use the feed health check endpoints
and provides examples of the expected responses.

Usage:
    python scripts/test_feed_health.py
    python scripts/test_feed_health.py --api-url http://localhost:5059
"""

import argparse
import json
import requests
import sys
from datetime import datetime


def test_feed_health_api(api_url, token=None):
    """Test the feed health check API endpoints."""

    print(f"🔍 Testing Feed Health API at {api_url}")
    print("=" * 60)

    # Setup headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("⚠️  No authentication token provided. Some endpoints may fail.")

    # Test 1: Check all feeds health
    print("\n1️⃣  Testing GET /api/feeds/health")
    try:
        response = requests.get(
            f"{api_url}/api/feeds/health", headers=headers, timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful!")

            # Print summary
            summary = data.get("summary", {})
            print(f"📊 Summary:")
            print(f"   Total feeds: {summary.get('total_feeds', 0)}")
            print(f"   Healthy feeds: {summary.get('healthy_feeds', 0)}")
            print(f"   Unhealthy feeds: {summary.get('unhealthy_feeds', 0)}")
            print(f"   Health percentage: {summary.get('health_percentage', 0)}%")

            # Print feed details
            feeds = data.get("feeds", [])
            if feeds:
                print(f"\n📋 Feed Details:")
                for feed in feeds[:5]:  # Show first 5 feeds
                    status_emoji = "✅" if feed["status"] == "ok" else "❌"
                    print(f"   {status_emoji} {feed['feed_name']}")
                    print(f"      URL: {feed['url']}")
                    print(f"      Status: {feed['status']}")
                    print(f"      HTTP Code: {feed.get('http_code', 'N/A')}")
                    print(
                        f"      Response Time: {feed.get('response_time_ms', 'N/A')}ms"
                    )
                    if feed.get("error_message"):
                        print(f"      Error: {feed['error_message']}")
                    print()

                if len(feeds) > 5:
                    print(f"   ... and {len(feeds) - 5} more feeds")

        elif response.status_code == 401:
            print("❌ Authentication required. Please provide a valid token.")
        elif response.status_code == 403:
            print("❌ Insufficient permissions. Analyst role or higher required.")
        else:
            print(f"❌ Request failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    # Test 2: Check health history
    print("\n2️⃣  Testing GET /api/feeds/health/history")
    try:
        params = {"limit": 10, "hours": 24}
        response = requests.get(
            f"{api_url}/api/feeds/health/history",
            headers=headers,
            params=params,
            timeout=10,
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Health history retrieved!")

            health_logs = data.get("health_logs", [])
            pagination = data.get("pagination", {})

            print(f"📊 Found {pagination.get('total', 0)} health check records")

            if health_logs:
                print(f"\n📋 Recent Health Checks:")
                for log in health_logs[:3]:  # Show first 3 logs
                    status_emoji = "✅" if log["status"] == "ok" else "❌"
                    print(f"   {status_emoji} {log['feed_name']}")
                    print(f"      Checked: {log['last_checked']}")
                    print(f"      Status: {log['status']}")
                    print(
                        f"      Response Time: {log.get('response_time_ms', 'N/A')}ms"
                    )
                    print()
            else:
                print("📝 No health check history found")

        else:
            print(f"❌ Request failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    # Test 3: Check specific feed health (if feeds exist)
    print("\n3️⃣  Testing GET /api/feeds/1/health")
    try:
        response = requests.get(
            f"{api_url}/api/feeds/1/health", headers=headers, timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Single feed health check successful!")

            current_health = data.get("current_health", {})
            recent_checks = data.get("recent_checks", [])

            print(f"📊 Current Health:")
            print(f"   Feed: {current_health.get('feed_name', 'Unknown')}")
            print(f"   Status: {current_health.get('status', 'Unknown')}")
            print(f"   HTTP Code: {current_health.get('http_code', 'N/A')}")
            print(
                f"   Response Time: {current_health.get('response_time_ms', 'N/A')}ms"
            )

            if recent_checks:
                print(f"\n📋 Recent Checks: {len(recent_checks)} records")

        elif response.status_code == 404:
            print("❌ Feed not found (ID: 1)")
        else:
            print(f"❌ Request failed: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    print("\n" + "=" * 60)
    print("🏁 Feed Health API testing completed!")


def test_sample_requests():
    """Show sample request/response examples."""

    print("\n📖 Sample API Usage Examples")
    print("=" * 60)

    print("\n🔍 1. Check all feeds health:")
    print("GET /api/feeds/health")
    print("Headers: Authorization: Bearer <token>")

    sample_response = {
        "success": True,
        "summary": {
            "total_feeds": 5,
            "healthy_feeds": 3,
            "unhealthy_feeds": 2,
            "health_percentage": 60.0,
        },
        "feeds": [
            {
                "feed_id": 1,
                "feed_name": "IPsum Project",
                "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
                "status": "ok",
                "http_code": 200,
                "response_time_ms": 245,
                "last_checked": "2024-01-15T10:30:00Z",
                "is_active": True,
                "error_message": None,
            },
            {
                "feed_id": 2,
                "feed_name": "PhishTank",
                "url": "https://data.phishtank.com/data/online-valid.json",
                "status": "unauthorized",
                "http_code": 401,
                "response_time_ms": 180,
                "last_checked": "2024-01-15T10:30:01Z",
                "is_active": True,
                "error_message": "HTTP 401: Unauthorized",
            },
        ],
        "checked_at": "2024-01-15T10:30:00Z",
        "checked_by": "analyst_user",
    }

    print("Response:")
    print(json.dumps(sample_response, indent=2))

    print("\n🔍 2. Get health history:")
    print("GET /api/feeds/health/history?limit=10&hours=24&status=ok")

    print("\n🔍 3. Check specific feed:")
    print("GET /api/feeds/1/health")

    print("\n📊 Status Values:")
    statuses = [
        ("ok", "Feed is accessible and responding normally"),
        ("unreachable", "Feed URL is not accessible"),
        ("unauthorized", "Authentication failed (401/403)"),
        ("timeout", "Request timed out"),
        ("rate_limited", "Rate limited (HTTP 429)"),
        ("server_error", "Server error (5xx)"),
        ("error", "Other request error"),
    ]

    for status, description in statuses:
        print(f"   • {status}: {description}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test SentinelForge Feed Health Check API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default settings
  python scripts/test_feed_health.py
  
  # Test with custom API URL
  python scripts/test_feed_health.py --api-url http://localhost:5059
  
  # Test with authentication token
  python scripts/test_feed_health.py --token your_jwt_token
  
  # Show sample requests only
  python scripts/test_feed_health.py --samples-only
        """,
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:5059",
        help="API base URL (default: http://localhost:5059)",
    )
    parser.add_argument("--token", help="Authentication token (JWT)")
    parser.add_argument(
        "--samples-only",
        action="store_true",
        help="Show sample requests/responses only",
    )

    args = parser.parse_args()

    if args.samples_only:
        test_sample_requests()
    else:
        test_feed_health_api(args.api_url, args.token)
        test_sample_requests()


if __name__ == "__main__":
    main()
