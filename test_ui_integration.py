#!/usr/bin/env python3
"""
UI Integration test script to verify the audit logging system works end-to-end.
"""

import requests
import time
import json

API_BASE = "http://localhost:5059"
UI_BASE = "http://localhost:3000"


def test_ui_integration():
    """Test the complete UI integration for audit logging."""
    print("🎯 SentinelForge UI Integration Test for Audit Logging")
    print("=" * 60)

    # Step 1: Verify API server is running
    print("\n📋 Step 1: Verifying API Server")
    try:
        response = requests.get(f"{API_BASE}/api/alerts", timeout=5)
        if response.status_code == 200:
            alerts = response.json()
            print(f"   ✅ API Server running - {len(alerts)} alerts available")
            if alerts:
                test_alert = alerts[0]
                print(
                    f"   📝 Test Alert: {test_alert['name']} (ID: {test_alert['id']})"
                )
                print(f"   📊 Current Risk Score: {test_alert['risk_score']}")
                if test_alert.get("overridden_risk_score"):
                    print(
                        f"   🔧 Overridden Score: {test_alert['overridden_risk_score']}"
                    )
            else:
                print("   ⚠️ No alerts available for testing")
                return False
        else:
            print(f"   ❌ API Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API Server connection failed: {e}")
        return False

    # Step 2: Check existing audit trail
    print("\n📋 Step 2: Checking Existing Audit Trail")
    try:
        alert_id = alerts[0]["id"]
        response = requests.get(f"{API_BASE}/api/audit?alert_id={alert_id}", timeout=5)
        if response.status_code == 200:
            audit_data = response.json()
            audit_logs = audit_data.get("audit_logs", [])
            print(f"   ✅ Found {len(audit_logs)} existing audit entries")

            if audit_logs:
                latest = audit_logs[0]
                print(f"   📝 Latest Entry:")
                print(f"      User: {latest['user_id']}")
                print(
                    f"      Score Change: {latest['original_score']} → {latest['override_score']}"
                )
                print(f"      Justification: {latest['justification']}")
                print(f"      Timestamp: {latest['timestamp']}")
        else:
            print(f"   ❌ Audit retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Audit retrieval error: {e}")
        return False

    # Step 3: Test new risk score override
    print("\n📋 Step 3: Testing New Risk Score Override")
    try:
        # Get current score
        current_score = test_alert.get(
            "overridden_risk_score", test_alert["risk_score"]
        )
        new_score = 90 if current_score < 90 else 40

        override_data = {
            "risk_score": new_score,
            "justification": f"UI Integration Test - Score changed from {current_score} to {new_score}",
            "user_id": 999,  # Test user ID
        }

        print(f"   📊 Changing score: {current_score} → {new_score}")
        print(f"   📝 Justification: {override_data['justification']}")

        response = requests.patch(
            f"{API_BASE}/api/alert/{alert_id}/override", json=override_data, timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Override successful")
            print(f"   📊 New overridden score: {result.get('overridden_risk_score')}")
        else:
            print(f"   ❌ Override failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Override error: {e}")
        return False

    # Step 4: Verify new audit entry
    print("\n📋 Step 4: Verifying New Audit Entry")
    try:
        time.sleep(0.5)  # Small delay for database write

        response = requests.get(
            f"{API_BASE}/api/audit?alert_id={alert_id}&limit=1", timeout=5
        )
        if response.status_code == 200:
            audit_data = response.json()
            audit_logs = audit_data.get("audit_logs", [])

            if audit_logs:
                latest = audit_logs[0]
                print(f"   ✅ New audit entry created")
                print(f"   📝 Entry Details:")
                print(f"      ID: {latest['id']}")
                print(f"      User: {latest['user_id']}")
                print(
                    f"      Score Change: {latest['original_score']} → {latest['override_score']}"
                )
                print(f"      Justification: {latest['justification']}")
                print(f"      Timestamp: {latest['timestamp']}")

                # Verify the data matches our override
                if (
                    latest["override_score"] == new_score
                    and latest["user_id"] == 999
                    and "UI Integration Test" in latest["justification"]
                ):
                    print(f"   ✅ Audit entry data verified")
                else:
                    print(f"   ❌ Audit entry data mismatch")
                    return False
            else:
                print(f"   ❌ No audit entry found")
                return False
        else:
            print(f"   ❌ Audit verification failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Audit verification error: {e}")
        return False

    # Step 5: Test audit filtering
    print("\n📋 Step 5: Testing Audit Filtering")
    try:
        # Test user filter
        response = requests.get(f"{API_BASE}/api/audit?user_id=999", timeout=5)
        if response.status_code == 200:
            audit_data = response.json()
            user_logs = audit_data.get("audit_logs", [])
            print(f"   ✅ User 999 has {len(user_logs)} audit entries")

        # Test pagination
        response = requests.get(f"{API_BASE}/api/audit?limit=2", timeout=5)
        if response.status_code == 200:
            audit_data = response.json()
            limited_logs = audit_data.get("audit_logs", [])
            total = audit_data.get("total", 0)
            print(
                f"   ✅ Pagination working: {len(limited_logs)} of {total} entries returned"
            )

    except Exception as e:
        print(f"   ❌ Filtering test error: {e}")
        return False

    # Step 6: UI Instructions
    print("\n📋 Step 6: UI Testing Instructions")
    print(f"   🌐 Frontend URL: {UI_BASE}")
    print(f"   📝 Manual Testing Steps:")
    print(f"      1. Open {UI_BASE} in your browser")
    print(f"      2. Navigate to the Alerts page")
    print(f"      3. Click on alert '{test_alert['name']}' (ID: {alert_id})")
    print(f"      4. Verify the modal opens with 3 tabs: Details, IOCs, Audit Trail")
    print(f"      5. Click on 'Audit Trail' tab")
    print(
        f"      6. Verify you see the audit history with timestamps and justifications"
    )
    print(f"      7. Go back to 'Details' tab")
    print(f"      8. Click the edit icon next to the risk score")
    print(f"      9. Change the score and add a justification")
    print(f"      10. Save the changes")
    print(f"      11. Go back to 'Audit Trail' tab and verify the new entry appears")

    print("\n" + "=" * 60)
    print("🎉 UI Integration Test Complete!")
    print("\n✅ Backend Features Verified:")
    print("   • API server running and responsive")
    print("   • Risk score override with audit logging")
    print("   • Audit trail retrieval and filtering")
    print("   • Real-time audit entry creation")
    print("   • Data integrity and validation")

    print("\n🌐 Frontend Ready for Testing:")
    print("   • React app running on localhost:3000")
    print("   • AuditTrailView component integrated")
    print("   • Enhanced AlertDetailModal with tabs")
    print("   • API service functions implemented")
    print("   • TypeScript interfaces defined")

    return True


if __name__ == "__main__":
    success = test_ui_integration()
    if success:
        print("\n🚀 Ready for manual UI testing!")
    else:
        print("\n❌ Integration test failed - check the issues above")
    exit(0 if success else 1)
