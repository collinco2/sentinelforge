#!/usr/bin/env python3
"""Fix admin password to use correct hashing method"""

import sqlite3
import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def fix_admin_password():
    """Update admin password with correct hash."""
    db_path = "ioc_store.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create correct password hash
    password = "admin123"
    correct_hash = hash_password(password)

    # Update admin user
    cursor.execute(
        """
        UPDATE users 
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
        WHERE username = 'admin'
    """,
        (correct_hash,),
    )

    if cursor.rowcount > 0:
        print(f"✅ Updated admin password hash: {correct_hash}")
        conn.commit()
    else:
        print("❌ Admin user not found")

    conn.close()


if __name__ == "__main__":
    fix_admin_password()
