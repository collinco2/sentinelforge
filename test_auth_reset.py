#!/usr/bin/env python3
"""
🔐 Password Reset Authentication Tests
Comprehensive test suite for password reset functionality in SentinelForge.
"""

import unittest
import sqlite3
import tempfile
import os
import time
import json
from unittest.mock import patch, MagicMock
from auth import (
    init_auth_tables,
    create_password_reset_token,
    validate_password_reset_token,
    use_password_reset_token,
    update_user_password,
    verify_password,
    hash_password,
    get_db_connection,
)
from email_service import (
    send_password_reset_email,
    send_password_reset_confirmation_email,
    test_email_configuration,
)


class TestPasswordResetAuth(unittest.TestCase):
    """Test password reset authentication functionality."""

    def setUp(self):
        """Set up test database and user."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Patch the database path in auth module
        self.db_patcher = patch("auth.get_db_connection")
        self.mock_get_db = self.db_patcher.start()

        # Create test database connection
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.mock_get_db.return_value = self.conn

        # Initialize auth tables
        init_auth_tables()

        # Create test user
        cursor = self.conn.cursor()
        password_hash = hash_password("testpassword123")
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("testuser", "test@example.com", password_hash, "analyst", True),
        )
        self.conn.commit()

        # Get test user ID
        cursor.execute("SELECT user_id FROM users WHERE username = ?", ("testuser",))
        self.test_user_id = cursor.fetchone()["user_id"]

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
        self.db_patcher.stop()

    def test_create_password_reset_token_valid_email(self):
        """Test creating password reset token for valid email."""
        token = create_password_reset_token("test@example.com", "127.0.0.1")

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)  # Should be a long secure token

    def test_create_password_reset_token_invalid_email(self):
        """Test creating password reset token for invalid email."""
        token = create_password_reset_token("nonexistent@example.com", "127.0.0.1")

        # Should return None for security (don't reveal if email exists)
        self.assertIsNone(token)

    def test_create_password_reset_token_inactive_user(self):
        """Test creating password reset token for inactive user."""
        # Create inactive user
        cursor = self.conn.cursor()
        password_hash = hash_password("testpassword123")
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("inactive", "inactive@example.com", password_hash, "viewer", False),
        )
        self.conn.commit()

        token = create_password_reset_token("inactive@example.com", "127.0.0.1")

        # Should return None for inactive users
        self.assertIsNone(token)

    def test_validate_password_reset_token_valid(self):
        """Test validating a valid password reset token."""
        token = create_password_reset_token("test@example.com", "127.0.0.1")
        self.assertIsNotNone(token)

        token_info = validate_password_reset_token(token)

        self.assertIsNotNone(token_info)
        self.assertEqual(token_info["email"], "test@example.com")
        self.assertEqual(token_info["username"], "testuser")
        self.assertEqual(token_info["user_id"], self.test_user_id)

    def test_validate_password_reset_token_invalid(self):
        """Test validating an invalid password reset token."""
        token_info = validate_password_reset_token("invalid_token")

        self.assertIsNone(token_info)

    def test_validate_password_reset_token_expired(self):
        """Test validating an expired password reset token."""
        # Create token
        token = create_password_reset_token("test@example.com", "127.0.0.1")
        self.assertIsNotNone(token)

        # Manually expire the token by updating the database
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE password_reset_tokens 
            SET expires_at = datetime('now', '-2 hours')
            WHERE token_id = ?
            """,
            (token,),
        )
        self.conn.commit()

        token_info = validate_password_reset_token(token)

        self.assertIsNone(token_info)

    def test_use_password_reset_token_valid(self):
        """Test using a valid password reset token."""
        token = create_password_reset_token("test@example.com", "127.0.0.1")
        self.assertIsNotNone(token)

        # Use the token
        result = use_password_reset_token(token, "127.0.0.1")

        self.assertTrue(result)

        # Token should no longer be valid
        token_info = validate_password_reset_token(token)
        self.assertIsNone(token_info)

    def test_use_password_reset_token_already_used(self):
        """Test using a password reset token that's already been used."""
        token = create_password_reset_token("test@example.com", "127.0.0.1")
        self.assertIsNotNone(token)

        # Use the token once
        result1 = use_password_reset_token(token, "127.0.0.1")
        self.assertTrue(result1)

        # Try to use it again
        result2 = use_password_reset_token(token, "127.0.0.1")
        self.assertFalse(result2)

    def test_update_user_password_valid(self):
        """Test updating user password with valid data."""
        new_password = "newpassword456"

        result = update_user_password(self.test_user_id, new_password)

        self.assertTrue(result)

        # Verify password was updated
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE user_id = ?", (self.test_user_id,)
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)

        # Verify new password works
        self.assertTrue(verify_password(new_password, row["password_hash"]))

        # Verify old password doesn't work
        self.assertFalse(verify_password("testpassword123", row["password_hash"]))

    def test_update_user_password_invalid_user(self):
        """Test updating password for non-existent user."""
        result = update_user_password(99999, "newpassword456")

        self.assertFalse(result)

    def test_password_reset_token_expiry_time(self):
        """Test that password reset tokens have correct expiry time."""
        token = create_password_reset_token("test@example.com", "127.0.0.1")
        self.assertIsNotNone(token)

        # Check token expiry in database
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT created_at, expires_at,
                   (julianday(expires_at) - julianday(created_at)) * 24 * 60 as minutes_diff
            FROM password_reset_tokens 
            WHERE token_id = ?
            """,
            (token,),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)

        # Should expire in approximately 60 minutes (1 hour)
        minutes_diff = row["minutes_diff"]
        self.assertAlmostEqual(minutes_diff, 60, delta=1)

    def test_password_reset_token_security(self):
        """Test password reset token security properties."""
        tokens = []

        # Generate multiple tokens
        for _ in range(10):
            token = create_password_reset_token("test@example.com", "127.0.0.1")
            self.assertIsNotNone(token)
            tokens.append(token)

        # All tokens should be unique
        self.assertEqual(len(tokens), len(set(tokens)))

        # All tokens should be sufficiently long
        for token in tokens:
            self.assertGreaterEqual(len(token), 32)


class TestPasswordResetEmail(unittest.TestCase):
    """Test password reset email functionality."""

    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key"})
    def test_email_configuration_valid(self):
        """Test email configuration validation."""
        result = test_email_configuration()
        self.assertTrue(result)

    def test_email_configuration_invalid(self):
        """Test email configuration validation without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = test_email_configuration()
            self.assertFalse(result)

    @patch("email_service.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key"})
    def test_send_password_reset_email_success(self, mock_sendgrid):
        """Test successful password reset email sending."""
        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sendgrid.return_value.send.return_value = mock_response

        result = send_password_reset_email(
            "test@example.com", "testuser", "test_token_123"
        )

        self.assertTrue(result)
        mock_sendgrid.assert_called_once()

    @patch("email_service.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key"})
    def test_send_password_reset_email_failure(self, mock_sendgrid):
        """Test failed password reset email sending."""
        # Mock SendGrid error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.body = "Bad Request"
        mock_sendgrid.return_value.send.return_value = mock_response

        result = send_password_reset_email(
            "test@example.com", "testuser", "test_token_123"
        )

        self.assertFalse(result)

    def test_send_password_reset_email_no_api_key(self):
        """Test password reset email sending without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = send_password_reset_email(
                "test@example.com", "testuser", "test_token_123"
            )

            self.assertFalse(result)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
