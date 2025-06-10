#!/usr/bin/env python3
"""
Emergency Database Schema Fix
Fixes critical database schema issues causing authentication failures
"""

import sqlite3
import os
import sys
from datetime import datetime


def fix_database_schema():
    """Fix all database schema issues immediately."""
    db_path = "/Users/Collins/sentinelforge/ioc_store.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False

    print("🔧 Fixing database schema issues...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Check and fix user_sessions table
        print("📋 Checking user_sessions table...")
        cursor.execute("PRAGMA table_info(user_sessions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "last_activity" not in columns:
            print("➕ Adding missing last_activity column...")
            cursor.execute(
                "ALTER TABLE user_sessions ADD COLUMN last_activity TIMESTAMP"
            )
            # Update existing rows with current timestamp
            cursor.execute(
                "UPDATE user_sessions SET last_activity = created_at WHERE last_activity IS NULL"
            )

        # 2. Create sessions table alias if missing
        print("📋 Checking sessions table...")
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        if not cursor.fetchone():
            print("➕ Creating sessions table alias...")
            cursor.execute("""
                CREATE TABLE sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

        # 3. Sync data between user_sessions and sessions
        print("🔄 Syncing session data...")
        cursor.execute("DELETE FROM sessions")  # Clear old data
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, created_at, expires_at, last_activity, is_active)
            SELECT session_id, user_id, created_at, expires_at, 
                   COALESCE(last_activity, created_at) as last_activity, is_active
            FROM user_sessions
        """)

        # 4. Clean up expired sessions
        print("🧹 Cleaning expired sessions...")
        cursor.execute("DELETE FROM user_sessions WHERE expires_at < datetime('now')")
        cursor.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")

        # 5. Verify auth tables exist
        print("📋 Verifying auth tables...")
        required_tables = ["users", "user_sessions", "sessions"]
        for table in required_tables:
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            if cursor.fetchone():
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Table {table} missing!")
                return False

        # 6. Verify admin user exists
        print("👤 Checking admin user...")
        cursor.execute("SELECT user_id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"✅ Admin user exists: ID {admin_user[0]}")
        else:
            print("❌ Admin user missing!")
            return False

        conn.commit()
        conn.close()

        print("✅ Database schema fixed successfully!")
        return True

    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False


def test_authentication():
    """Test authentication after fix."""
    print("\n🧪 Testing authentication...")

    try:
        import requests

        # Test session endpoint
        response = requests.get("http://localhost:5059/api/session", timeout=5)
        if response.status_code == 200:
            print("✅ Session endpoint working")
        else:
            print(f"⚠️  Session endpoint returned: {response.status_code}")

        # Test login
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(
            "http://localhost:5059/api/login", json=login_data, timeout=5
        )
        if response.status_code == 200:
            print("✅ Login endpoint working")
            data = response.json()
            if "session_token" in data:
                print("✅ Session token generated")
                return True
            else:
                print("⚠️  No session token in response")
        else:
            print(f"❌ Login failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")

    return False


def main():
    """Main execution."""
    print("=" * 60)
    print("🚨 EMERGENCY DATABASE SCHEMA FIX")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fix database schema
    if not fix_database_schema():
        print("❌ Schema fix failed!")
        sys.exit(1)

    # Test authentication
    if test_authentication():
        print("\n🎉 Authentication is working!")
    else:
        print("\n⚠️  Authentication test failed - may need server restart")

    print("\n" + "=" * 60)
    print("✅ Emergency fix completed!")
    print("🔄 Restart servers to apply changes")
    print("=" * 60)


if __name__ == "__main__":
    main()
