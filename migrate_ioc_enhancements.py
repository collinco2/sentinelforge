#!/usr/bin/env python3
"""
🔄 IOC Enhancement Migration Script

This script migrates the existing IOC database schema to support the new
IOC management features including enhanced fields and audit logging.

Features added:
- Enhanced IOC fields (severity, tags, confidence, created_by, etc.)
- IOC audit logging table
- Soft delete functionality
- User tracking for IOC operations

Usage:
    python migrate_ioc_enhancements.py
"""

import sqlite3
import os
import datetime
import json
from pathlib import Path


def get_db_path():
    """Get the database path."""
    # Try multiple possible locations
    possible_paths = [
        "ioc_store.db",
        "sentinelforge.db",
        "/Users/Collins/sentinelforge/ioc_store.db",
        "/Users/Collins/sentinelforge/sentinelforge.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Default to the first path if none exist
    return possible_paths[0]


def backup_database(db_path):
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        return None


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_ioc_table(cursor):
    """Migrate the IOC table to add new fields."""
    print("🔄 Migrating IOC table...")
    
    # Check which columns need to be added
    new_columns = [
        ("severity", "TEXT DEFAULT 'medium'"),
        ("tags", "TEXT"),  # JSON array
        ("confidence", "INTEGER DEFAULT 50"),
        ("created_by", "INTEGER"),
        ("updated_by", "INTEGER"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
        ("is_active", "BOOLEAN DEFAULT 1")
    ]
    
    for column_name, column_def in new_columns:
        if not check_column_exists(cursor, "iocs", column_name):
            try:
                cursor.execute(f"ALTER TABLE iocs ADD COLUMN {column_name} {column_def}")
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.Error as e:
                print(f"  ⚠️  Error adding column {column_name}: {e}")
        else:
            print(f"  ℹ️  Column {column_name} already exists")


def create_ioc_audit_table(cursor):
    """Create the IOC audit log table."""
    print("🔄 Creating IOC audit log table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ioc_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ioc_type TEXT NOT NULL,
            ioc_value TEXT NOT NULL,
            action TEXT NOT NULL,  -- CREATE, UPDATE, DELETE, IMPORT
            user_id INTEGER NOT NULL,
            changes TEXT,  -- JSON of what changed
            justification TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_ip TEXT,
            user_agent TEXT
        )
    """)
    print("  ✅ IOC audit log table created")


def populate_default_values(cursor):
    """Populate default values for existing IOCs."""
    print("🔄 Populating default values for existing IOCs...")
    
    now = datetime.datetime.utcnow().isoformat()
    
    # Update existing IOCs with default values where NULL
    updates = [
        ("severity", "'medium'", "severity IS NULL"),
        ("confidence", "50", "confidence IS NULL"),
        ("created_at", f"'{now}'", "created_at IS NULL"),
        ("updated_at", f"'{now}'", "updated_at IS NULL"),
        ("is_active", "1", "is_active IS NULL"),
        ("tags", "'[]'", "tags IS NULL")
    ]
    
    for column, default_value, condition in updates:
        try:
            cursor.execute(f"UPDATE iocs SET {column} = {default_value} WHERE {condition}")
            affected = cursor.rowcount
            if affected > 0:
                print(f"  ✅ Updated {affected} rows for {column}")
        except sqlite3.Error as e:
            print(f"  ⚠️  Error updating {column}: {e}")


def create_indexes(cursor):
    """Create indexes for better performance."""
    print("🔄 Creating performance indexes...")
    
    indexes = [
        ("idx_iocs_active", "iocs", "is_active"),
        ("idx_iocs_created_at", "iocs", "created_at"),
        ("idx_iocs_severity", "iocs", "severity"),
        ("idx_ioc_audit_timestamp", "ioc_audit_logs", "timestamp"),
        ("idx_ioc_audit_action", "ioc_audit_logs", "action"),
        ("idx_ioc_audit_user", "ioc_audit_logs", "user_id")
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
            print(f"  ✅ Created index: {index_name}")
        except sqlite3.Error as e:
            print(f"  ⚠️  Error creating index {index_name}: {e}")


def verify_migration(cursor):
    """Verify the migration was successful."""
    print("🔍 Verifying migration...")
    
    # Check IOC table structure
    cursor.execute("PRAGMA table_info(iocs)")
    ioc_columns = [row[1] for row in cursor.fetchall()]
    
    required_columns = ["severity", "tags", "confidence", "created_by", "updated_by", 
                       "created_at", "updated_at", "is_active"]
    
    missing_columns = [col for col in required_columns if col not in ioc_columns]
    if missing_columns:
        print(f"  ❌ Missing IOC columns: {missing_columns}")
        return False
    else:
        print("  ✅ All IOC columns present")
    
    # Check audit table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ioc_audit_logs'")
    if not cursor.fetchone():
        print("  ❌ IOC audit log table not found")
        return False
    else:
        print("  ✅ IOC audit log table exists")
    
    # Check data integrity
    cursor.execute("SELECT COUNT(*) FROM iocs WHERE is_active IS NULL")
    null_active = cursor.fetchone()[0]
    if null_active > 0:
        print(f"  ⚠️  {null_active} IOCs have NULL is_active values")
    else:
        print("  ✅ All IOCs have valid is_active values")
    
    return True


def main():
    """Main migration function."""
    print("🚀 Starting IOC Enhancement Migration")
    print("=" * 50)
    
    # Get database path
    db_path = get_db_path()
    print(f"📁 Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Creating new database...")
    
    # Create backup
    backup_path = backup_database(db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Run migrations
        migrate_ioc_table(cursor)
        create_ioc_audit_table(cursor)
        populate_default_values(cursor)
        create_indexes(cursor)
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        if verify_migration(cursor):
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration verification failed!")
            return False
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM iocs")
        ioc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ioc_audit_logs")
        audit_count = cursor.fetchone()[0]
        
        print(f"\n📊 Migration Summary:")
        print(f"  • Total IOCs: {ioc_count}")
        print(f"  • Audit log entries: {audit_count}")
        print(f"  • Backup created: {backup_path or 'No backup created'}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"💡 You can restore from backup: {backup_path}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
