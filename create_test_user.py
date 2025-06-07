#!/usr/bin/env python3
"""
🔧 Create Test User Script

This script creates a test admin user for testing the IOC CRUD functionality.
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime


def hash_password(password, salt=None):
    """Hash a password with salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt
    password_salt = f"{password}{salt}"
    
    # Hash with SHA-256
    hashed = hashlib.sha256(password_salt.encode()).hexdigest()
    
    return hashed, salt


def create_test_user():
    """Create a test admin user."""
    # Database connection
    db_path = "ioc_store.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users'
    """)
    
    if not cursor.fetchone():
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    # Check if admin user already exists
    cursor.execute("SELECT user_id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        print("Admin user already exists")
        conn.close()
        return
    
    # Create admin user
    username = "admin"
    email = "admin@sentinelforge.local"
    password = "admin123"
    role = "admin"
    
    # Hash password
    password_hash, salt = hash_password(password)
    
    # Insert user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, salt, role, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (username, email, password_hash, salt, role))
    
    user_id = cursor.lastrowid
    
    # Create sessions table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created admin user:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Role: {role}")
    print(f"   User ID: {user_id}")


if __name__ == "__main__":
    create_test_user()
