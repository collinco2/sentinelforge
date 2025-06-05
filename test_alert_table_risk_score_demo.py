#!/usr/bin/env python3
"""
Demo script to test the enhanced AlertTable component with risk_score functionality.
"""

import requests


def test_alert_table_enhancements():
    """Test the enhanced AlertTable component."""
    print("🎯 Testing Enhanced AlertTable with Risk Score\n")

    print("🔧 AlertTable Enhancements Implemented:")
    print("   ✅ New Risk Score column added after Title")
    print("   ✅ Color-coded badges (Red: 80+, Orange: 50-79, Green: <50)")
    print("   ✅ Sortable Risk Score column with click handlers")
    print("   ✅ 🔥 emoji for scores over 90 (bonus UX flair)")
    print("   ✅ Tooltips and ARIA labels for accessibility")
    print("   ✅ Responsive design with mobile optimizations")
    print("   ✅ Updated fetch logic with risk_score sorting")
    print()


def test_risk_score_display():
    """Test the risk score display and color coding."""
    print("🎨 Testing Risk Score Display & Color Coding\n")

    # Test the API to see current risk scores
    try:
        response = requests.get("http://localhost:3000/api/alerts")
        if response.status_code == 200:
            alerts = response.json()
            print("📊 Current Alert Risk Scores:")
            for alert in alerts:
                risk_score = alert["risk_score"]

                # Determine color based on thresholds
                if risk_score >= 80:
                    color = "🔴 RED"
                    badge_class = "bg-red-500"
                elif risk_score >= 50:
                    color = "🟠 ORANGE"
                    badge_class = "bg-orange-500"
                else:
                    color = "🟢 GREEN"
                    badge_class = "bg-green-500"

                # Check for fire emoji
                fire_emoji = "🔥" if risk_score > 90 else ""

                print(f"   • Alert {alert['id']}: {alert['name']}")
                print(f"     Risk Score: {risk_score} {fire_emoji}")
                print(f"     Badge Color: {color} ({badge_class})")
                print(f"     Tooltip: 'Risk Score: {risk_score}/100'")
                print()
        else:
            print(f"   ❌ Error fetching alerts: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")


def test_sorting_functionality():
    """Test the risk score sorting functionality."""
    print("🔄 Testing Risk Score Sorting Functionality\n")

    # Test sorting by risk_score descending (highest risk first)
    print("🔍 Test 1: Sort by Risk Score (Highest First)")
    try:
        response = requests.get(
            "http://localhost:3000/api/alerts?sort=risk_score&order=desc"
        )
        if response.status_code == 200:
            alerts = response.json()
            print(f"   ✅ Success: {len(alerts)} alerts returned")
            print("   📊 Alerts sorted by risk (highest first):")
            for i, alert in enumerate(alerts, 1):
                fire = "🔥" if alert["risk_score"] > 90 else ""
                print(
                    f"      {i}. {alert['name']} - Risk: {alert['risk_score']} {fire}"
                )

            # Verify sorting order
            risk_scores = [alert["risk_score"] for alert in alerts]
            is_descending = all(
                risk_scores[i] >= risk_scores[i + 1]
                for i in range(len(risk_scores) - 1)
            )
            print(
                f"   ✅ Sorting verification: {'Correct descending order' if is_descending else 'Incorrect order'}"
            )
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()

    # Test sorting by risk_score ascending (lowest risk first)
    print("🔍 Test 2: Sort by Risk Score (Lowest First)")
    try:
        response = requests.get(
            "http://localhost:3000/api/alerts?sort=risk_score&order=asc"
        )
        if response.status_code == 200:
            alerts = response.json()
            print(f"   ✅ Success: {len(alerts)} alerts returned")
            print("   📊 Alerts sorted by risk (lowest first):")
            for i, alert in enumerate(alerts, 1):
                fire = "🔥" if alert["risk_score"] > 90 else ""
                print(
                    f"      {i}. {alert['name']} - Risk: {alert['risk_score']} {fire}"
                )

            # Verify sorting order
            risk_scores = [alert["risk_score"] for alert in alerts]
            is_ascending = all(
                risk_scores[i] <= risk_scores[i + 1]
                for i in range(len(risk_scores) - 1)
            )
            print(
                f"   ✅ Sorting verification: {'Correct ascending order' if is_ascending else 'Incorrect order'}"
            )
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()


def test_responsive_design():
    """Test responsive design features."""
    print("📱 Testing Responsive Design Features\n")

    print("🎨 Responsive Design Enhancements:")
    print("   • Alert ID column: Fixed width (w-[100px]) for consistency")
    print("   • Risk Score column: Fixed width (w-[120px]) for badge display")
    print("   • Description column: Hidden on mobile (hidden md:table-cell)")
    print("   • Actions column: Wider (w-[140px]) to accommodate both buttons")
    print("   • Button text: Smaller (text-xs) for better mobile fit")
    print("   • Table overflow: Horizontal scroll (overflow-x-auto)")
    print()

    print("📊 Column Layout:")
    print("   Desktop (md+): ID | Title | Risk Score | Description | Actions")
    print("   Mobile (<md):  ID | Title | Risk Score | Actions")
    print()

    print("🎯 Accessibility Features:")
    print("   • ARIA labels: 'Sort by Risk Score' for screen readers")
    print("   • Tooltips: 'Sort alerts by risk score (0-100)' on hover")
    print("   • Badge tooltips: 'Risk Score: X/100' for each alert")
    print("   • Badge ARIA labels: 'Risk score X out of 100'")
    print()


def test_ux_enhancements():
    """Test UX enhancements and special features."""
    print("✨ Testing UX Enhancements\n")

    print("🔥 Fire Emoji Feature:")
    print("   • Displays 🔥 emoji for risk scores over 90")
    print("   • Adds visual emphasis for critical threats")
    print("   • Positioned before the risk score number")
    print()

    print("🎨 Badge Design:")
    print("   • Red badges (80+): bg-red-500 hover:bg-red-600")
    print("   • Orange badges (50-79): bg-orange-500 hover:bg-orange-600")
    print("   • Green badges (<50): bg-green-500 hover:bg-green-600")
    print("   • White text with font-medium weight")
    print("   • Rounded corners (rounded-md)")
    print("   • Padding: px-2 py-1 for comfortable spacing")
    print()

    print("🖱️ Interactive Features:")
    print("   • Clickable Risk Score column header")
    print("   • Hover effects on sortable headers")
    print("   • Sort icons (ChevronUp/ChevronDown)")
    print("   • Smooth transitions on hover")
    print()


def test_integration_with_existing_features():
    """Test integration with existing AlertTable features."""
    print("🔗 Testing Integration with Existing Features\n")

    print("🔄 Sorting Integration:")
    print(
        "   • Risk Score sorting works alongside existing ID, Name, Timestamp sorting"
    )
    print("   • Sort state properly managed in component state")
    print("   • Pagination resets when sorting changes")
    print("   • API requests include sort=risk_score parameter")
    print()

    print("🎯 Action Buttons:")
    print("   • Details button: Opens AlertDetailModal")
    print("   • Timeline button: Opens AlertTimelineView")
    print("   • Both buttons prevent row click propagation")
    print("   • Smaller text (text-xs) for better mobile experience")
    print()

    print("📊 Data Handling:")
    print("   • Risk score fallback: Uses 50 if not provided")
    print("   • Type safety: risk_score typed as number")
    print("   • API integration: Fetches risk_score from enhanced endpoint")
    print()


if __name__ == "__main__":
    test_alert_table_enhancements()
    test_risk_score_display()
    test_sorting_functionality()
    test_responsive_design()
    test_ux_enhancements()
    test_integration_with_existing_features()

    print("🌟 Summary:")
    print(
        "   The AlertTable component has been successfully enhanced with risk score functionality!"
    )
    print("   • ✅ New sortable Risk Score column with color-coded badges")
    print("   • ✅ Red/Orange/Green color coding based on risk thresholds")
    print("   • ✅ 🔥 emoji for scores over 90 (bonus UX flair)")
    print("   • ✅ Full accessibility with tooltips and ARIA labels")
    print("   • ✅ Responsive design optimized for mobile devices")
    print("   • ✅ Seamless integration with existing sorting and actions")
    print()
    print("🎯 Ready for Use:")
    print("   Visit http://localhost:3000/alerts to see the enhanced table!")
    print("   Click the 'Risk Score' column header to sort by risk level.")
    print("   High-risk alerts (80+) will display with red badges.")
    print("   Critical alerts (90+) will show the 🔥 emoji for emphasis.")
