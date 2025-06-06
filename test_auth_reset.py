#!/usr/bin/env python3
"""
🔐 Password Reset Authentication Tests
Basic test suite for password reset functionality in SentinelForge.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestPasswordResetBasic(unittest.TestCase):
    """Basic tests for password reset functionality."""

    def test_imports_available(self):
        """Test that required modules can be imported."""
        try:
            import auth

            self.assertTrue(hasattr(auth, "hash_password"))
            self.assertTrue(hasattr(auth, "verify_password"))
        except ImportError:
            self.skipTest("Auth module not available")

    def test_password_hashing(self):
        """Test password hashing functionality."""
        try:
            from auth import hash_password, verify_password

            password = "testpassword123"
            hashed = hash_password(password)

            # Verify hash format
            self.assertIsInstance(hashed, str)
            self.assertIn(":", hashed)  # Should contain salt separator

            # Verify password verification works
            self.assertTrue(verify_password(password, hashed))
            self.assertFalse(verify_password("wrongpassword", hashed))

        except ImportError:
            self.skipTest("Auth module not available")

    def test_email_service_import(self):
        """Test that email service can be imported."""
        try:
            import email_service

            self.assertTrue(hasattr(email_service, "send_password_reset_email"))
            self.assertTrue(hasattr(email_service, "test_email_configuration"))
        except ImportError:
            self.skipTest("Email service module not available")


class TestPasswordResetEmail(unittest.TestCase):
    """Test password reset email functionality."""

    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key"})
    def test_email_configuration_valid(self):
        """Test email configuration validation."""
        try:
            from email_service import test_email_configuration

            result = test_email_configuration()
            self.assertTrue(result)
        except ImportError:
            self.skipTest("Email service module not available")

    def test_email_configuration_invalid(self):
        """Test email configuration validation without API key."""
        try:
            from email_service import test_email_configuration

            with patch.dict(os.environ, {}, clear=True):
                result = test_email_configuration()
                self.assertFalse(result)
        except ImportError:
            self.skipTest("Email service module not available")

    @patch("email_service.SendGridAPIClient")
    @patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key"})
    def test_send_password_reset_email_success(self, mock_sendgrid):
        """Test successful password reset email sending."""
        try:
            from email_service import send_password_reset_email

            # Mock SendGrid response
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_sendgrid.return_value.send.return_value = mock_response

            result = send_password_reset_email(
                "test@example.com", "testuser", "test_token_123"
            )

            self.assertTrue(result)
            mock_sendgrid.assert_called_once()
        except ImportError:
            self.skipTest("Email service module not available")

    def test_send_password_reset_email_no_api_key(self):
        """Test password reset email sending without API key."""
        try:
            from email_service import send_password_reset_email

            with patch.dict(os.environ, {}, clear=True):
                result = send_password_reset_email(
                    "test@example.com", "testuser", "test_token_123"
                )
                self.assertFalse(result)
        except ImportError:
            self.skipTest("Email service module not available")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
