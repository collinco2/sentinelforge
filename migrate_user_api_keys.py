#!/usr/bin/env python3
"""
Database migration script to add user_api_keys table for SentinelForge.

This script creates the user_api_keys table to support per-user API key management.
"""

import sqlite3
import os
import sys
from datetime import datetime


def get_db_path():
    """Get the database path."""
    return "/Users/Collins/sentinelforge/ioc_store.db"


def create_user_api_keys_table():
    """Create the user_api_keys table."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_api_keys'
        """)
        
        if cursor.fetchone():
            print("✅ user_api_keys table already exists")
            conn.close()
            return True
        
        # Create the user_api_keys table
        cursor.execute("""
            CREATE TABLE user_api_keys (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                key_preview TEXT NOT NULL,
                access_scope TEXT NOT NULL DEFAULT '["read"]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                ip_restrictions TEXT,
                rate_limit_tier TEXT DEFAULT 'standard',
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX idx_user_api_keys_user_id ON user_api_keys(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_user_api_keys_key_hash ON user_api_keys(key_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_user_api_keys_active ON user_api_keys(is_active)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully created user_api_keys table with indexes")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user_api_keys table: {e}")
        return False


def verify_table_structure():
    """Verify the table was created correctly."""
    db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(user_api_keys)")
        columns = cursor.fetchall()
        
        print("\n📋 Table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Get indexes
        cursor.execute("PRAGMA index_list(user_api_keys)")
        indexes = cursor.fetchall()
        
        print("\n📊 Indexes:")
        for idx in indexes:
            print(f"  - {idx[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return False


def main():
    """Main migration function."""
    print("🔄 Starting user_api_keys table migration...")
    
    # Create the table
    if not create_user_api_keys_table():
        sys.exit(1)
    
    # Verify the table structure
    if not verify_table_structure():
        sys.exit(1)
    
    print("\n✅ Migration completed successfully!")
    print("🔑 User API key management is now ready for use.")


if __name__ == "__main__":
    main()
