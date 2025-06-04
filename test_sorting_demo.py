#!/usr/bin/env python3
"""
Demo script to test the enhanced /api/alerts sorting functionality.
"""

import requests


def test_alerts_sorting():
    """Test the enhanced alerts API with sorting functionality."""
    base_url = "http://localhost:5059/api/alerts"

    print("🔍 Testing Enhanced /api/alerts Sorting Functionality\n")

    # Test cases
    test_cases = [
        {
            "name": "Default (no parameters)",
            "url": base_url,
            "description": "Should default to sort=id, order=asc",
        },
        {
            "name": "Sort by ID, Ascending",
            "url": f"{base_url}?sort=id&order=asc",
            "description": "Explicit sort by ID ascending",
        },
        {
            "name": "Sort by ID, Descending",
            "url": f"{base_url}?sort=id&order=desc",
            "description": "Sort by ID descending (newest first)",
        },
        {
            "name": "Sort by Name, Ascending",
            "url": f"{base_url}?sort=name&order=asc",
            "description": "Sort alphabetically by alert name",
        },
        {
            "name": "Sort by Name, Descending",
            "url": f"{base_url}?sort=name&order=desc",
            "description": "Sort reverse alphabetically by alert name",
        },
        {
            "name": "Sort by Timestamp, Descending",
            "url": f"{base_url}?sort=timestamp&order=desc",
            "description": "Sort by timestamp (most recent first)",
        },
        {
            "name": "Sort by Timestamp, Ascending",
            "url": f"{base_url}?sort=timestamp&order=asc",
            "description": "Sort by timestamp (oldest first)",
        },
        {
            "name": "Invalid Sort Field",
            "url": f"{base_url}?sort=invalid_field&order=desc",
            "description": "Should fallback to default sort=id",
        },
        {
            "name": "Invalid Sort Order",
            "url": f"{base_url}?sort=name&order=invalid_order",
            "description": "Should fallback to default order=asc",
        },
        {
            "name": "Combined with Filtering",
            "url": f"{base_url}?name=suspicious&sort=name&order=desc",
            "description": "Filter by name + sort by name descending",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"📋 Test {i}: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   URL: {test_case['url']}")

        try:
            response = requests.get(test_case["url"])
            if response.status_code == 200:
                alerts = response.json()
                print(f"   ✅ Success: {len(alerts)} alerts returned")

                # Show the order of results
                if alerts:
                    print("   📊 Results order:")
                    for j, alert in enumerate(alerts, 1):
                        print(f"      {j}. ID: {alert['id']}, Name: {alert['name']}")
                else:
                    print("   📊 No alerts returned")
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

        print()  # Empty line for readability


if __name__ == "__main__":
    test_alerts_sorting()
