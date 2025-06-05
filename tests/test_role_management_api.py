#!/usr/bin/env python3
"""
🛡️ Role Management API Tests

Test suite for the admin-only role management functionality in SentinelForge.
Tests user listing, role updates, and audit logging.
"""

import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_server import app


class TestRoleManagementAPI:
    """Test class for role management API endpoints."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.client = app.test_client()
        self.admin_headers = {"X-Demo-User-ID": "1"}  # Admin user
        self.analyst_headers = {"X-Demo-User-ID": "2"}  # Analyst user
        self.viewer_headers = {"X-Demo-User-ID": "4"}  # Viewer user

    def test_get_users_admin_access(self):
        """Test that admin can access user list."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock user data
            mock_cursor.fetchall.return_value = [
                {
                    "user_id": 1,
                    "username": "admin",
                    "email": "admin@test.com",
                    "role": "admin",
                    "is_active": 1,
                    "created_at": "2023-12-21 10:00:00",
                    "updated_at": "2023-12-21 10:00:00",
                },
                {
                    "user_id": 2,
                    "username": "analyst1",
                    "email": "analyst1@test.com",
                    "role": "analyst",
                    "is_active": 1,
                    "created_at": "2023-12-21 11:00:00",
                    "updated_at": "2023-12-21 11:00:00",
                },
            ]

            response = self.client.get("/api/users", headers=self.admin_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "users" in data
            assert "total" in data
            assert len(data["users"]) == 2
            assert data["users"][0]["username"] == "admin"
            assert data["users"][1]["username"] == "analyst1"

    def test_get_users_non_admin_denied(self):
        """Test that non-admin users cannot access user list."""
        response = self.client.get("/api/users", headers=self.analyst_headers)
        assert response.status_code == 403

        response = self.client.get("/api/users", headers=self.viewer_headers)
        assert response.status_code == 403

    def test_update_user_role_admin_access(self):
        """Test that admin can update user roles."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock existing user data
            mock_cursor.fetchone.side_effect = [
                # First call - get current user data
                {
                    "user_id": 2,
                    "username": "analyst1",
                    "email": "analyst1@test.com",
                    "role": "analyst",
                    "is_active": 1,
                    "created_at": "2023-12-21 11:00:00",
                },
                # Second call - get updated user data
                {
                    "user_id": 2,
                    "username": "analyst1",
                    "email": "analyst1@test.com",
                    "role": "auditor",
                    "is_active": 1,
                    "created_at": "2023-12-21 11:00:00",
                    "updated_at": "2023-12-21 15:00:00",
                },
            ]

            response = self.client.patch(
                "/api/user/2/role",
                headers={**self.admin_headers, "Content-Type": "application/json"},
                data=json.dumps({"role": "auditor"}),
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "User role updated successfully"
            assert data["old_role"] == "analyst"
            assert data["new_role"] == "auditor"
            assert data["user"]["role"] == "auditor"

    def test_update_user_role_non_admin_denied(self):
        """Test that non-admin users cannot update roles."""
        response = self.client.patch(
            "/api/user/2/role",
            headers={**self.analyst_headers, "Content-Type": "application/json"},
            data=json.dumps({"role": "auditor"}),
        )
        assert response.status_code == 403

    def test_update_user_role_invalid_role(self):
        """Test that invalid roles are rejected."""
        response = self.client.patch(
            "/api/user/2/role",
            headers={**self.admin_headers, "Content-Type": "application/json"},
            data=json.dumps({"role": "invalid_role"}),
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid role" in data["error"]

    def test_update_user_role_missing_role_field(self):
        """Test that missing role field is rejected."""
        # Test with empty JSON object
        response = self.client.patch(
            "/api/user/2/role",
            headers={**self.admin_headers, "Content-Type": "application/json"},
            data='{"other_field": "value"}',  # JSON with other field but no role
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"] == "role field is required"

    def test_update_user_role_self_demotion_denied(self):
        """Test that admin cannot demote themselves."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock current user data (admin trying to demote themselves)
            mock_cursor.fetchone.return_value = {
                "user_id": 1,
                "username": "admin",
                "email": "admin@test.com",
                "role": "admin",
                "is_active": 1,
                "created_at": "2023-12-21 10:00:00",
            }

            response = self.client.patch(
                "/api/user/1/role",  # Admin user ID
                headers={**self.admin_headers, "Content-Type": "application/json"},
                data=json.dumps({"role": "viewer"}),
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Cannot demote yourself" in data["error"]

    def test_update_user_role_user_not_found(self):
        """Test that updating non-existent user returns 404."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock user not found
            mock_cursor.fetchone.return_value = None

            response = self.client.patch(
                "/api/user/999/role",
                headers={**self.admin_headers, "Content-Type": "application/json"},
                data=json.dumps({"role": "viewer"}),
            )

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["error"] == "User not found"

    def test_get_role_change_audit_logs_admin_access(self):
        """Test that admin can access role change audit logs."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock audit log data
            mock_cursor.fetchall.return_value = [
                {
                    "id": 1,
                    "alert_id": -2,
                    "user_id": 1,
                    "original_score": 0,
                    "override_score": 0,
                    "justification": "ROLE_CHANGE: User 'analyst1' (ID: 2) role changed from 'viewer' to 'analyst' by admin 'admin' (ID: 1)",
                    "timestamp": "2023-12-21 13:00:00",
                    "admin_username": "admin",
                }
            ]

            # Mock count query
            mock_cursor.fetchone.return_value = {"total": 1}

            response = self.client.get("/api/audit/roles", headers=self.admin_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "audit_logs" in data
            assert "total" in data
            assert len(data["audit_logs"]) == 1
            assert data["audit_logs"][0]["action"] == "role_change"
            assert data["audit_logs"][0]["admin_username"] == "admin"

    def test_get_role_change_audit_logs_non_admin_denied(self):
        """Test that non-admin users cannot access role change audit logs."""
        response = self.client.get("/api/audit/roles", headers=self.analyst_headers)
        assert response.status_code == 403

        response = self.client.get("/api/audit/roles", headers=self.viewer_headers)
        assert response.status_code == 403

    def test_role_change_creates_audit_log(self):
        """Test that role changes create audit log entries."""
        with patch("api_server.get_db_connection") as mock_db:
            # Mock database response
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock existing user data
            mock_cursor.fetchone.side_effect = [
                # First call - get current user data
                {
                    "user_id": 2,
                    "username": "analyst1",
                    "email": "analyst1@test.com",
                    "role": "analyst",
                    "is_active": 1,
                    "created_at": "2023-12-21 11:00:00",
                },
                # Second call - get updated user data
                {
                    "user_id": 2,
                    "username": "analyst1",
                    "email": "analyst1@test.com",
                    "role": "auditor",
                    "is_active": 1,
                    "created_at": "2023-12-21 11:00:00",
                    "updated_at": "2023-12-21 15:00:00",
                },
            ]

            response = self.client.patch(
                "/api/user/2/role",
                headers={**self.admin_headers, "Content-Type": "application/json"},
                data=json.dumps({"role": "auditor"}),
            )

            assert response.status_code == 200

            # Verify that audit log was created
            audit_calls = [
                call
                for call in mock_cursor.execute.call_args_list
                if "INSERT INTO audit_logs" in str(call)
            ]
            assert len(audit_calls) > 0

            # Check audit log content
            audit_call = audit_calls[0]
            assert "ROLE_CHANGE" in str(audit_call)
            assert "analyst1" in str(audit_call)
            assert "analyst" in str(audit_call)
            assert "auditor" in str(audit_call)


def run_tests():
    """Run all role management API tests."""
    import pytest

    print("🧪 Running Role Management API Tests...")

    # Run the tests
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("✅ All role management API tests passed!")
    else:
        print("❌ Some tests failed!")

    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
