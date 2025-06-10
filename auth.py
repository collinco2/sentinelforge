#!/usr/bin/env python3
"""
🛡️ SentinelForge Authentication and Role-Based Access Control (RBAC)

This module provides authentication and authorization functionality for SentinelForge,
implementing role-based access control to secure sensitive operations.

Roles:
- viewer: Can view alerts and IOCs (read-only)
- analyst: Can view and override alert risk scores
- auditor: Can view audit trails and all data (read-only)
- admin: Full access to all features

Usage:
    from auth import require_role, get_current_user, UserRole

    @require_role([UserRole.ANALYST, UserRole.ADMIN])
    def override_risk_score():
        # Only analysts and admins can access this
        pass
"""

import sqlite3
import hashlib
import secrets
import time
import json
import datetime
from enum import Enum
from functools import wraps
from typing import List, Optional, Dict, Any
from flask import request, jsonify, g


class UserRole(Enum):
    """User roles with hierarchical permissions."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    ADMIN = "admin"


class User:
    """User model with role-based permissions."""

    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        role: UserRole,
        is_active: bool = True,
        created_at: str = None,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active
        self.created_at = created_at

    def has_permission(self, required_roles: List[UserRole]) -> bool:
        """Check if user has any of the required roles."""
        return self.is_active and self.role in required_roles

    def can_override_risk_scores(self) -> bool:
        """Check if user can override alert risk scores."""
        return self.has_permission([UserRole.ANALYST, UserRole.ADMIN])

    def can_view_audit_trail(self) -> bool:
        """Check if user can view audit trail."""
        return self.has_permission([UserRole.AUDITOR, UserRole.ADMIN])

    def can_manage_user_roles(self) -> bool:
        """Check if user can manage other users' roles."""
        return self.has_permission([UserRole.ADMIN])

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "permissions": {
                "can_override_risk_scores": self.can_override_risk_scores(),
                "can_view_audit_trail": self.can_view_audit_trail(),
                "can_manage_user_roles": self.can_manage_user_roles(),
            },
        }


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permissions."""

    pass


def get_db_connection():
    """Get database connection for auth operations."""
    try:
        conn = sqlite3.connect("/Users/Collins/sentinelforge/ioc_store.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Auth database connection error: {e}")
        return None


def init_auth_tables():
    """Initialize authentication tables in database."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sessions table for token management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Create password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT 0,
                used_at TIMESTAMP NULL,
                ip_address TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        conn.commit()

        # Create default users if they don't exist
        create_default_users(cursor)
        conn.commit()

        conn.close()
        return True

    except Exception as e:
        print(f"Error initializing auth tables: {e}")
        conn.close()
        return False


def create_default_users(cursor):
    """Create default users for demonstration."""
    default_users = [
        ("admin", "admin@sentinelforge.com", "admin123", UserRole.ADMIN.value),
        (
            "analyst1",
            "analyst1@sentinelforge.com",
            "analyst123",
            UserRole.ANALYST.value,
        ),
        (
            "auditor1",
            "auditor1@sentinelforge.com",
            "auditor123",
            UserRole.AUDITOR.value,
        ),
        ("viewer1", "viewer1@sentinelforge.com", "viewer123", UserRole.VIEWER.value),
    ]

    for username, email, password, role in default_users:
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            continue

        # Hash password
        password_hash = hash_password(password)

        # Insert user
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """,
            (username, email, password_hash, role),
        )

        print(f"Created default user: {username} ({role})")


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        salt, hash_value = password_hash.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    except ValueError:
        return False


def update_user_password(user_id: int, new_password: str) -> bool:
    """Update user's password with new hash."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        password_hash = hash_password(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND is_active = 1
            """,
            (password_hash, user_id),
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    except Exception as e:
        print(f"Error updating user password: {e}")
        conn.close()
        return False


def create_password_reset_token(email: str, ip_address: str = None) -> Optional[str]:
    """Create a password reset token for the given email."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # First, check if user exists and is active
        cursor.execute(
            "SELECT user_id FROM users WHERE email = ? AND is_active = 1", (email,)
        )

        user_row = cursor.fetchone()
        if not user_row:
            # Don't reveal if email exists or not for security
            conn.close()
            return None

        user_id = user_row["user_id"]

        # Generate secure token
        token_id = secrets.token_urlsafe(32)
        expires_at = time.time() + (60 * 60)  # 1 hour expiry

        # Insert reset token
        cursor.execute(
            """
            INSERT INTO password_reset_tokens
            (token_id, user_id, email, expires_at, ip_address)
            VALUES (?, ?, ?, datetime(?, 'unixepoch'), ?)
            """,
            (token_id, user_id, email, expires_at, ip_address),
        )

        conn.commit()
        conn.close()
        return token_id

    except Exception as e:
        print(f"Error creating password reset token: {e}")
        conn.close()
        return None


def validate_password_reset_token(token_id: str) -> Optional[Dict[str, Any]]:
    """Validate password reset token and return user info if valid."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT prt.user_id, prt.email, prt.created_at, prt.expires_at,
                   u.username, u.is_active
            FROM password_reset_tokens prt
            JOIN users u ON prt.user_id = u.user_id
            WHERE prt.token_id = ?
            AND prt.is_used = 0
            AND prt.expires_at > datetime('now')
            AND u.is_active = 1
            """,
            (token_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row["user_id"],
                "email": row["email"],
                "username": row["username"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }
        return None

    except Exception as e:
        print(f"Error validating password reset token: {e}")
        conn.close()
        return None


def use_password_reset_token(token_id: str, ip_address: str = None) -> bool:
    """Mark password reset token as used."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET is_used = 1, used_at = CURRENT_TIMESTAMP, ip_address = ?
            WHERE token_id = ? AND is_used = 0
            """,
            (ip_address, token_id),
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    except Exception as e:
        print(f"Error marking password reset token as used: {e}")
        conn.close()
        return False


def create_session(user_id: int) -> str:
    """Create a new session for user."""
    session_id = secrets.token_urlsafe(32)
    expires_at = time.time() + (24 * 60 * 60)  # 24 hours

    conn = get_db_connection()
    if not conn:
        raise AuthenticationError("Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (session_id, user_id, expires_at)
            VALUES (?, ?, datetime(?, 'unixepoch'))
        """,
            (session_id, user_id, expires_at),
        )
        conn.commit()
        conn.close()
        return session_id
    except Exception as e:
        conn.close()
        raise AuthenticationError(f"Failed to create session: {e}")


def get_user_by_session(session_id: str) -> Optional[User]:
    """Get user by session ID."""
    if not session_id:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.user_id, u.username, u.email, u.role, u.is_active, u.created_at
            FROM users u
            JOIN user_sessions s ON u.user_id = s.user_id
            WHERE s.session_id = ? 
            AND s.is_active = 1 
            AND s.expires_at > datetime('now')
            AND u.is_active = 1
        """,
            (session_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return User(
                user_id=row["user_id"],
                username=row["username"],
                email=row["email"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )
        return None

    except Exception as e:
        print(f"Error getting user by session: {e}")
        conn.close()
        return None


def invalidate_session(session_id: str) -> bool:
    """Invalidate a session by marking it as expired."""
    if not session_id:
        return False

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sessions
            SET expires_at = ?
            WHERE session_id = ?
        """,
            (time.time() - 1, session_id),  # Set expiry to past time
        )

        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    except Exception as e:
        print(f"Error invalidating session: {e}")
        conn.close()
        return False


def get_user_by_credentials(username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, password_hash, role, is_active, created_at
            FROM users
            WHERE username = ? AND is_active = 1
        """,
            (username,),
        )

        row = cursor.fetchone()
        conn.close()

        if row and verify_password(password, row["password_hash"]):
            return User(
                user_id=row["user_id"],
                username=row["username"],
                email=row["email"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )
        return None

    except Exception as e:
        print(f"Error authenticating user: {e}")
        conn.close()
        return None


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256 with salt."""
    # Use a consistent salt for API keys (in production, use environment variable)
    salt = "sentinelforge_api_key_salt_2024"
    return hashlib.sha256((api_key + salt).encode()).hexdigest()


def get_user_by_api_key(api_key: str) -> Optional[User]:
    """Get user by API key."""
    if not api_key:
        return None

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Look up the API key and get user info
        cursor.execute("""
            SELECT uak.*, u.username, u.email, u.role, u.is_active as user_active, u.created_at
            FROM user_api_keys uak
            JOIN users u ON uak.user_id = u.user_id
            WHERE uak.key_hash = ? AND uak.is_active = 1
        """, (key_hash,))

        key_record = cursor.fetchone()

        if not key_record:
            conn.close()
            return None

        # Check if user is active
        if not key_record['user_active']:
            conn.close()
            return None

        # Check if key is expired
        if key_record['expires_at']:
            try:
                expires_at = datetime.datetime.fromisoformat(key_record['expires_at'])
                if datetime.datetime.now() > expires_at:
                    conn.close()
                    return None
            except:
                pass  # If parsing fails, assume no expiration

        # Update last_used timestamp
        try:
            cursor.execute("""
                UPDATE user_api_keys
                SET last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (key_record['id'],))
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not update last_used timestamp: {e}")

        conn.close()

        # Create User object
        user = User(
            user_id=key_record['user_id'],
            username=key_record['username'],
            email=key_record['email'],
            role=UserRole(key_record['role']),
            is_active=bool(key_record['user_active']),
            created_at=key_record['created_at']
        )

        # Add API key specific attributes
        user.api_key_id = key_record['id']
        user.api_key_name = key_record['name']
        user.access_scope = json.loads(key_record['access_scope']) if key_record['access_scope'] else ['read']
        user.auth_method = 'api_key'

        return user

    except Exception as e:
        print(f"Error getting user by API key: {e}")
        conn.close()
        return None


def get_current_user() -> Optional[User]:
    """Get current user from request context."""
    # Try API key from header first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = get_user_by_api_key(api_key)
        if user:
            return user

    # Try session token from header
    session_token = request.headers.get("X-Session-Token")
    if session_token:
        user = get_user_by_session(session_token)
        if user:
            user.auth_method = 'session'
            return user

    # Try basic auth for demo purposes
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64

        try:
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
            user = get_user_by_credentials(username, password)
            if user:
                user.auth_method = 'basic'
            return user
        except Exception:
            pass

    # Default demo user for testing (remove in production)
    demo_user_id = request.headers.get("X-Demo-User-ID")
    if demo_user_id:
        user = get_demo_user(int(demo_user_id))
        if user:
            user.auth_method = 'demo'
        return user

    return None


def get_demo_user(user_id: int) -> Optional[User]:
    """Get demo user for testing purposes."""
    demo_users = {
        1: User(1, "admin", "admin@demo.com", UserRole.ADMIN),
        2: User(2, "analyst", "analyst@demo.com", UserRole.ANALYST),
        3: User(3, "auditor", "auditor@demo.com", UserRole.AUDITOR),
        4: User(4, "viewer", "viewer@demo.com", UserRole.VIEWER),
    }
    return demo_users.get(user_id)


def require_role(required_roles: List[UserRole]):
    """Decorator to require specific roles for endpoint access."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify(
                    {
                        "error": "Authentication required",
                        "message": "Please provide valid credentials",
                    }
                ), 401

            if not user.has_permission(required_roles):
                return jsonify(
                    {
                        "error": "Insufficient permissions",
                        "message": f"This action requires one of the following roles: {[r.value for r in required_roles]}",
                        "user_role": user.role.value,
                    }
                ), 403

            # Store user in request context
            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_authentication():
    """Decorator to require authentication (any valid user)."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify(
                    {
                        "error": "Authentication required",
                        "message": "Please provide valid credentials",
                    }
                ), 401

            # Store user in request context
            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Initialize auth tables on module import
init_auth_tables()
