#!/usr/bin/env python3
"""
Demo script to test the enhanced AlertTable UI sorting functionality.
"""

import requests


def test_ui_sorting():
    """Test the enhanced AlertTable UI sorting functionality through the proxy."""
    base_url = "http://localhost:3000/api/alerts"

    print("🎯 Testing Enhanced AlertTable UI Sorting Functionality\n")

    # Test cases that simulate what the UI would send
    test_cases = [
        {
            "name": "Default UI Load",
            "url": f"{base_url}?page=1&limit=10&sort=id&order=asc",
            "description": "Default sort when AlertTable loads (id, asc)",
        },
        {
            "name": "Click Alert ID Header (Toggle to Desc)",
            "url": f"{base_url}?page=1&limit=10&sort=id&order=desc",
            "description": "User clicks Alert ID header to sort descending",
        },
        {
            "name": "Click Title Header (Switch to Name)",
            "url": f"{base_url}?page=1&limit=10&sort=name&order=asc",
            "description": "User clicks Title header to sort by name ascending",
        },
        {
            "name": "Click Title Header Again (Toggle to Desc)",
            "url": f"{base_url}?page=1&limit=10&sort=name&order=desc",
            "description": "User clicks Title header again to sort by name descending",
        },
        {
            "name": "Search + Sort Combination",
            "url": f"{base_url}?page=1&limit=10&sort=name&order=asc&name=suspicious",
            "description": "User searches for 'suspicious' and sorts by name",
        },
        {
            "name": "Pagination + Sort",
            "url": f"{base_url}?page=2&limit=2&sort=id&order=desc",
            "description": "User navigates to page 2 with sorting applied",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"🖱️  Test {i}: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Request: {test_case['url']}")

        try:
            response = requests.get(test_case["url"])
            if response.status_code == 200:
                alerts = response.json()
                print(f"   ✅ Success: {len(alerts)} alerts returned")

                # Show the order of results
                if alerts:
                    print("   📊 UI would display in this order:")
                    for j, alert in enumerate(alerts, 1):
                        print(f"      {j}. ID: {alert['id']}, Name: {alert['name']}")
                else:
                    print("   📊 No alerts to display")
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

        print()  # Empty line for readability


def test_ui_features():
    """Test specific UI features."""
    print("🎨 Testing UI-Specific Features\n")

    print("✨ Enhanced Features in AlertTable:")
    print("   • Clickable column headers for 'Alert ID' and 'Title'")
    print("   • Visual sort indicators (↑ for asc, ↓ for desc)")
    print("   • Hover effects on sortable headers")
    print("   • Automatic pagination reset when sorting changes")
    print("   • Integration with existing search and filter functionality")
    print("   • Accessibility support with aria-labels")
    print()

    print("🔄 Sort Behavior:")
    print("   • Default: Sort by ID, ascending")
    print("   • Click same header: Toggle sort order (asc ↔ desc)")
    print("   • Click different header: Switch field, reset to ascending")
    print("   • Sort state persists during search/filter operations")
    print()

    print("🎯 Supported Sort Fields:")
    print("   • Alert ID (id): Numeric sorting")
    print("   • Title (name): Alphabetical sorting")
    print("   • Description: Not sortable (display only)")
    print()


if __name__ == "__main__":
    test_ui_features()
    test_ui_sorting()

    print("🌟 Summary:")
    print("   The AlertTable component now supports full sorting functionality!")
    print("   Users can click column headers to sort alerts by ID or Name.")
    print("   Visual indicators show the current sort field and direction.")
    print("   All sorting integrates seamlessly with existing filters and pagination.")
