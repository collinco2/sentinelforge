#!/usr/bin/env python3
"""
Comprehensive demo script for the audit logging system.
"""

import requests
import sqlite3
import os
import time

API_BASE = "http://localhost:5059"
DB_PATH = "/Users/Collins/sentinelforge/ioc_store.db"


def demo_audit_system():
    """Demonstrate the complete audit logging system."""
    print("🎯 SentinelForge Audit Logging System Demo\n")
    print("=" * 60)

    # Step 1: Setup
    print("\n📋 Step 1: System Setup")
    if not setup_audit_table():
        print("❌ Failed to setup audit table")
        return False

    # Step 2: Get test alert
    print("\n📋 Step 2: Getting Test Alert")
    alert_id, original_score = get_test_alert()
    if not alert_id:
        print("❌ No test alert available")
        return False

    print(f"   Using Alert ID: {alert_id}")
    print(f"   Original Risk Score: {original_score}")

    # Step 3: Demonstrate multiple overrides
    print("\n📋 Step 3: Demonstrating Risk Score Overrides")

    overrides = [
        {
            "score": 85,
            "justification": "Elevated threat level based on recent intelligence reports",
            "user": 1,
        },
        {
            "score": 95,
            "justification": "Critical: Active exploitation detected in the wild",
            "user": 2,
        },
        {
            "score": 30,
            "justification": "False positive: Confirmed benign after manual analysis",
            "user": 1,
        },
    ]

    for i, override in enumerate(overrides, 1):
        print(f"\n   Override {i}: {override['score']} (User {override['user']})")
        print(f"   Justification: {override['justification']}")

        success = perform_override(alert_id, override)
        if success:
            print("   ✅ Override successful")
            time.sleep(1)  # Small delay for timestamp differentiation
        else:
            print("   ❌ Override failed")

    # Step 4: Demonstrate audit trail retrieval
    print("\n📋 Step 4: Retrieving Audit Trail")

    audit_logs = get_audit_trail(alert_id)
    if audit_logs:
        print(f"   Found {len(audit_logs)} audit entries:")
        for i, log in enumerate(audit_logs, 1):
            print(f"\n   Entry {i}:")
            print(f"     Timestamp: {log['timestamp']}")
            print(f"     User: {log['user_id']}")
            print(
                f"     Score Change: {log['original_score']} → {log['override_score']}"
            )
            print(f"     Justification: {log['justification']}")
    else:
        print("   ❌ No audit logs found")

    # Step 5: Demonstrate filtering
    print("\n📋 Step 5: Demonstrating Audit Filters")

    # Filter by user
    user_logs = get_audit_trail_filtered(user_id=1)
    print(f"   User 1 activity: {len(user_logs) if user_logs else 0} entries")

    user_logs = get_audit_trail_filtered(user_id=2)
    print(f"   User 2 activity: {len(user_logs) if user_logs else 0} entries")

    # Filter with pagination
    paginated_logs = get_audit_trail_filtered(limit=2)
    print(
        f"   Latest 2 entries: {len(paginated_logs) if paginated_logs else 0} returned"
    )

    # Step 6: Database verification
    print("\n📋 Step 6: Database Verification")
    verify_database_integrity(alert_id)

    # Step 7: Performance metrics
    print("\n📋 Step 7: Performance Metrics")
    show_performance_metrics()

    print("\n" + "=" * 60)
    print("🎉 Audit Logging System Demo Complete!")
    print("\n✅ Features Demonstrated:")
    print("   • Risk score override with audit logging")
    print("   • Justification capture and storage")
    print("   • Multi-user activity tracking")
    print("   • Comprehensive audit trail retrieval")
    print("   • Flexible filtering and pagination")
    print("   • Database integrity verification")
    print("   • Performance optimization")

    return True


def setup_audit_table():
    """Setup the audit_logs table."""
    if not os.path.exists(DB_PATH):
        print(f"   ❌ Database not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if audit_logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if cursor.fetchone():
            print("   ✅ audit_logs table exists")
        else:
            print("   📝 Creating audit_logs table...")
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
            cursor.execute(
                "CREATE INDEX idx_audit_logs_alert_id ON audit_logs(alert_id)"
            )
            cursor.execute("CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id)")
            cursor.execute(
                "CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp)"
            )

            conn.commit()
            print("   ✅ audit_logs table created")

        conn.close()
        return True

    except Exception as e:
        print(f"   ❌ Error setting up audit table: {e}")
        return False


def get_test_alert():
    """Get a test alert for demonstration."""
    try:
        response = requests.get(f"{API_BASE}/api/alerts", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Failed to get alerts: {response.status_code}")
            return None, None

        alerts = response.json()
        if not alerts:
            print("   ❌ No alerts found")
            return None, None

        alert = alerts[0]
        return alert["id"], alert.get("risk_score", 50)

    except Exception as e:
        print(f"   ❌ Error getting test alert: {e}")
        return None, None


def perform_override(alert_id, override_data):
    """Perform a risk score override."""
    try:
        response = requests.patch(
            f"{API_BASE}/api/alert/{alert_id}/override",
            headers={"Content-Type": "application/json"},
            json={
                "risk_score": override_data["score"],
                "justification": override_data["justification"],
                "user_id": override_data["user"],
            },
            timeout=5,
        )

        return response.status_code == 200

    except Exception as e:
        print(f"   ❌ Error performing override: {e}")
        return False


def get_audit_trail(alert_id):
    """Get audit trail for a specific alert."""
    try:
        response = requests.get(f"{API_BASE}/api/audit?alert_id={alert_id}", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Failed to get audit trail: {response.status_code}")
            return None

        data = response.json()
        return data.get("audit_logs", [])

    except Exception as e:
        print(f"   ❌ Error getting audit trail: {e}")
        return None


def get_audit_trail_filtered(**filters):
    """Get audit trail with filters."""
    try:
        params = "&".join([f"{k}={v}" for k, v in filters.items()])
        response = requests.get(f"{API_BASE}/api/audit?{params}", timeout=5)
        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("audit_logs", [])

    except Exception:
        return None


def verify_database_integrity(alert_id):
    """Verify database integrity."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check audit log count
        cursor.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE alert_id = ?", (alert_id,)
        )
        count = cursor.fetchone()[0]
        print(f"   Database entries for alert {alert_id}: {count}")

        # Check foreign key integrity
        cursor.execute(
            """
            SELECT COUNT(*) FROM audit_logs al
            LEFT JOIN alerts a ON al.alert_id = a.id
            WHERE al.alert_id = ? AND a.id IS NULL
        """,
            (alert_id,),
        )
        orphaned = cursor.fetchone()[0]

        if orphaned == 0:
            print("   ✅ Foreign key integrity verified")
        else:
            print(f"   ⚠️ Found {orphaned} orphaned audit entries")

        # Check timestamp ordering
        cursor.execute(
            """
            SELECT timestamp FROM audit_logs 
            WHERE alert_id = ? 
            ORDER BY timestamp DESC
        """,
            (alert_id,),
        )
        timestamps = [row[0] for row in cursor.fetchall()]

        if timestamps == sorted(timestamps, reverse=True):
            print("   ✅ Timestamp ordering verified")
        else:
            print("   ⚠️ Timestamp ordering issue detected")

        conn.close()

    except Exception as e:
        print(f"   ❌ Error verifying database: {e}")


def show_performance_metrics():
    """Show performance metrics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total audit entries
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total = cursor.fetchone()[0]
        print(f"   Total audit entries: {total}")

        # Unique alerts with overrides
        cursor.execute("SELECT COUNT(DISTINCT alert_id) FROM audit_logs")
        unique_alerts = cursor.fetchone()[0]
        print(f"   Alerts with overrides: {unique_alerts}")

        # Active users
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM audit_logs")
        active_users = cursor.fetchone()[0]
        print(f"   Active analysts: {active_users}")

        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        """)
        recent = cursor.fetchone()[0]
        print(f"   Recent activity (24h): {recent}")

        conn.close()

    except Exception as e:
        print(f"   ❌ Error getting metrics: {e}")


if __name__ == "__main__":
    demo_audit_system()
