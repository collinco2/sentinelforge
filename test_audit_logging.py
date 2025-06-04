#!/usr/bin/env python3
"""
Test script for audit logging functionality.
"""

import requests
import json
import sqlite3
import os

API_BASE = "http://localhost:5059"
DB_PATH = "/Users/Collins/sentinelforge/ioc_store.db"


def test_audit_logging():
    """Test the complete audit logging functionality."""
    print("🔍 Testing Audit Logging System\n")

    # First, ensure the audit_logs table exists
    if not create_audit_table():
        print("❌ Failed to create audit_logs table")
        return False

    # Test 1: Create a risk score override
    print("1. Testing risk score override with audit logging...")

    # Get an existing alert first
    try:
        response = requests.get(f"{API_BASE}/api/alerts")
        if response.status_code != 200:
            print(f"❌ Failed to get alerts: {response.status_code}")
            return False

        alerts = response.json()
        if not alerts:
            print("❌ No alerts found to test with")
            return False

        alert_id = alerts[0]["id"]
        original_score = alerts[0].get("risk_score", 50)
        print(f"   Using alert ID: {alert_id}, original score: {original_score}")

    except Exception as e:
        print(f"❌ Error getting alerts: {e}")
        return False

    # Test override with justification
    override_data = {
        "risk_score": 85,
        "justification": "Test override for audit logging verification",
        "user_id": 1,
    }

    try:
        response = requests.patch(
            f"{API_BASE}/api/alert/{alert_id}/override",
            headers={"Content-Type": "application/json"},
            json=override_data,
        )

        if response.status_code != 200:
            print(f"❌ Failed to override risk score: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        print("✅ Risk score override successful")

    except Exception as e:
        print(f"❌ Error overriding risk score: {e}")
        return False

    # Test 2: Verify audit log was created
    print("\n2. Verifying audit log entry...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM audit_logs 
            WHERE alert_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """,
            (alert_id,),
        )

        audit_entry = cursor.fetchone()
        conn.close()

        if not audit_entry:
            print("❌ No audit log entry found")
            return False

        print("✅ Audit log entry found:")
        print(f"   Alert ID: {audit_entry[1]}")
        print(f"   User ID: {audit_entry[2]}")
        print(f"   Original Score: {audit_entry[3]}")
        print(f"   Override Score: {audit_entry[4]}")
        print(f"   Justification: {audit_entry[5]}")
        print(f"   Timestamp: {audit_entry[6]}")

    except Exception as e:
        print(f"❌ Error checking audit log: {e}")
        return False

    # Test 3: Test audit API endpoint
    print("\n3. Testing audit API endpoint...")

    try:
        response = requests.get(f"{API_BASE}/api/audit?alert_id={alert_id}")

        if response.status_code != 200:
            print(f"❌ Failed to get audit logs: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        audit_data = response.json()

        if not audit_data.get("audit_logs"):
            print("❌ No audit logs returned from API")
            return False

        print("✅ Audit API endpoint working:")
        print(f"   Total logs: {audit_data['total']}")
        print(f"   Logs returned: {len(audit_data['audit_logs'])}")

        # Show the latest log
        latest_log = audit_data["audit_logs"][0]
        print(
            f"   Latest log: {latest_log['original_score']} → {latest_log['override_score']}"
        )
        print(f"   Justification: {latest_log['justification']}")

    except Exception as e:
        print(f"❌ Error testing audit API: {e}")
        return False

    # Test 4: Test filtering
    print("\n4. Testing audit API filtering...")

    try:
        # Test user_id filter
        response = requests.get(f"{API_BASE}/api/audit?user_id=1")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User filter working: {len(data['audit_logs'])} logs for user 1")
        else:
            print(f"⚠️ User filter test failed: {response.status_code}")

        # Test limit
        response = requests.get(f"{API_BASE}/api/audit?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Limit filter working: {len(data['audit_logs'])} logs (limit 5)")
        else:
            print(f"⚠️ Limit filter test failed: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Error testing filters: {e}")

    print("\n🎯 Audit logging system test completed successfully!")
    return True


def create_audit_table():
    """Create audit_logs table if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if audit_logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if cursor.fetchone():
            print("✅ audit_logs table already exists")
            conn.close()
            return True

        # Create audit_logs table
        print("📝 Creating audit_logs table...")
        cursor.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                original_score INTEGER NOT NULL,
                override_score INTEGER NOT NULL,
                justification TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts (id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_audit_logs_alert_id ON audit_logs(alert_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp)")

        conn.commit()
        conn.close()
        print("✅ audit_logs table created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating audit table: {e}")
        return False


if __name__ == "__main__":
    test_audit_logging()
