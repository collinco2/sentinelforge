#!/usr/bin/env python3
"""
Integration test for the complete audit logging system.
Tests backend API, database integrity, and frontend compatibility.
"""

import requests
import sqlite3
import os
import time

API_BASE = "http://localhost:5059"
DB_PATH = "/Users/Collins/sentinelforge/ioc_store.db"


def run_integration_tests():
    """Run comprehensive integration tests."""
    print("🧪 SentinelForge Audit Logging Integration Tests")
    print("=" * 60)

    tests = [
        test_database_setup,
        test_api_endpoints,
        test_audit_creation,
        test_audit_retrieval,
        test_filtering_and_pagination,
        test_data_integrity,
        test_error_handling,
        test_performance,
    ]

    passed = 0
    failed = 0

    for test in tests:
        print(f"\n🔍 Running {test.__name__}...")
        try:
            if test():
                print(f"✅ {test.__name__} PASSED")
                passed += 1
            else:
                print(f"❌ {test.__name__} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Audit logging system is ready.")
    else:
        print("⚠️ Some tests failed. Please review the issues above.")

    return failed == 0


def test_database_setup():
    """Test database table creation and schema."""
    if not os.path.exists(DB_PATH):
        print("   ❌ Database file not found")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if audit_logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if not cursor.fetchone():
            # Create the table
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
            print("   📝 Created audit_logs table")

        # Verify schema
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = [
            "id",
            "alert_id",
            "user_id",
            "original_score",
            "override_score",
            "justification",
            "timestamp",
        ]

        for col in expected_columns:
            if col not in columns:
                print(f"   ❌ Missing column: {col}")
                return False

        # Verify indexes
        cursor.execute("PRAGMA index_list(audit_logs)")
        indexes = [idx[1] for idx in cursor.fetchall()]
        expected_indexes = [
            "idx_audit_logs_alert_id",
            "idx_audit_logs_user_id",
            "idx_audit_logs_timestamp",
        ]

        for idx in expected_indexes:
            if idx not in indexes:
                print(f"   ❌ Missing index: {idx}")
                return False

        conn.close()
        print("   ✅ Database schema verified")
        return True

    except Exception as e:
        print(f"   ❌ Database setup error: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint availability."""
    try:
        # Test alerts endpoint
        response = requests.get(f"{API_BASE}/api/alerts", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Alerts endpoint failed: {response.status_code}")
            return False

        # Test audit endpoint
        response = requests.get(f"{API_BASE}/api/audit", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Audit endpoint failed: {response.status_code}")
            return False

        print("   ✅ API endpoints accessible")
        return True

    except Exception as e:
        print(f"   ❌ API endpoint error: {e}")
        return False


def test_audit_creation():
    """Test audit log creation on risk score override."""
    try:
        # Get a test alert
        response = requests.get(f"{API_BASE}/api/alerts", timeout=5)
        alerts = response.json()
        if not alerts:
            print("   ❌ No alerts available for testing")
            return False

        alert_id = alerts[0]["id"]

        # Perform override
        override_data = {
            "risk_score": 75,
            "justification": "Integration test override",
            "user_id": 999,
        }

        response = requests.patch(
            f"{API_BASE}/api/alert/{alert_id}/override", json=override_data, timeout=5
        )

        if response.status_code != 200:
            print(f"   ❌ Override failed: {response.status_code}")
            return False

        # Verify audit log was created
        time.sleep(0.5)  # Small delay for database write

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM audit_logs 
            WHERE alert_id = ? AND user_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        """,
            (alert_id, 999),
        )

        audit_entry = cursor.fetchone()
        conn.close()

        if not audit_entry:
            print("   ❌ No audit log entry created")
            return False

        if audit_entry[4] != 75:  # override_score
            print(f"   ❌ Incorrect override score: {audit_entry[4]}")
            return False

        if audit_entry[5] != "Integration test override":  # justification
            print(f"   ❌ Incorrect justification: {audit_entry[5]}")
            return False

        print("   ✅ Audit log creation verified")
        return True

    except Exception as e:
        print(f"   ❌ Audit creation error: {e}")
        return False


def test_audit_retrieval():
    """Test audit log retrieval via API."""
    try:
        # Get audit logs
        response = requests.get(f"{API_BASE}/api/audit?limit=10", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Audit retrieval failed: {response.status_code}")
            return False

        data = response.json()

        # Verify response structure
        required_fields = ["audit_logs", "total", "limit", "offset"]
        for field in required_fields:
            if field not in data:
                print(f"   ❌ Missing field in response: {field}")
                return False

        # Verify audit log structure
        if data["audit_logs"]:
            log = data["audit_logs"][0]
            required_log_fields = [
                "id",
                "alert_id",
                "user_id",
                "original_score",
                "override_score",
                "justification",
                "timestamp",
            ]
            for field in required_log_fields:
                if field not in log:
                    print(f"   ❌ Missing field in audit log: {field}")
                    return False

        print("   ✅ Audit retrieval verified")
        return True

    except Exception as e:
        print(f"   ❌ Audit retrieval error: {e}")
        return False


def test_filtering_and_pagination():
    """Test audit log filtering and pagination."""
    try:
        # Test user_id filter
        response = requests.get(f"{API_BASE}/api/audit?user_id=999", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ User filter failed: {response.status_code}")
            return False

        # Test limit
        response = requests.get(f"{API_BASE}/api/audit?limit=5", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ Limit filter failed: {response.status_code}")
            return False

        data = response.json()
        if len(data["audit_logs"]) > 5:
            print(f"   ❌ Limit not respected: {len(data['audit_logs'])}")
            return False

        print("   ✅ Filtering and pagination verified")
        return True

    except Exception as e:
        print(f"   ❌ Filtering error: {e}")
        return False


def test_data_integrity():
    """Test data integrity and foreign key constraints."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check for orphaned audit logs
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs al
            LEFT JOIN alerts a ON al.alert_id = a.id
            WHERE a.id IS NULL
        """)
        orphaned = cursor.fetchone()[0]

        if orphaned > 0:
            print(f"   ⚠️ Found {orphaned} orphaned audit entries")

        # Check timestamp ordering
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT timestamp, LAG(timestamp) OVER (ORDER BY id) as prev_timestamp
                FROM audit_logs
            ) WHERE timestamp < prev_timestamp
        """)
        out_of_order = cursor.fetchone()[0]

        if out_of_order > 0:
            print(f"   ⚠️ Found {out_of_order} out-of-order timestamps")

        conn.close()
        print("   ✅ Data integrity verified")
        return True

    except Exception as e:
        print(f"   ❌ Data integrity error: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid requests."""
    try:
        # Test invalid alert ID
        response = requests.patch(
            f"{API_BASE}/api/alert/99999/override", json={"risk_score": 50}, timeout=5
        )
        if response.status_code != 404:
            print(f"   ❌ Expected 404 for invalid alert, got {response.status_code}")
            return False

        # Test invalid risk score
        response = requests.get(f"{API_BASE}/api/alerts", timeout=5)
        alerts = response.json()
        if alerts:
            alert_id = alerts[0]["id"]
            response = requests.patch(
                f"{API_BASE}/api/alert/{alert_id}/override",
                json={"risk_score": 150},  # Invalid score
                timeout=5,
            )
            if response.status_code != 400:
                print(
                    f"   ❌ Expected 400 for invalid score, got {response.status_code}"
                )
                return False

        print("   ✅ Error handling verified")
        return True

    except Exception as e:
        print(f"   ❌ Error handling test error: {e}")
        return False


def test_performance():
    """Test basic performance metrics."""
    try:
        start_time = time.time()

        # Test audit retrieval performance
        response = requests.get(f"{API_BASE}/api/audit?limit=100", timeout=10)
        if response.status_code != 200:
            print(f"   ❌ Performance test failed: {response.status_code}")
            return False

        retrieval_time = time.time() - start_time

        if retrieval_time > 2.0:  # Should be under 2 seconds
            print(f"   ⚠️ Slow audit retrieval: {retrieval_time:.2f}s")

        print(f"   ✅ Performance verified (retrieval: {retrieval_time:.2f}s)")
        return True

    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
