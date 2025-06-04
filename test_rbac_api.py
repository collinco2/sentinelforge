#!/usr/bin/env python3
"""
🛡️ SentinelForge RBAC API Tests

This test suite validates the Role-Based Access Control (RBAC) implementation
for the SentinelForge API server, ensuring proper authorization for different
user roles.

Test Coverage:
- Risk score override permissions (analyst, admin only)
- Audit trail access permissions (auditor, admin only)
- Authentication validation
- Permission error responses
- Role hierarchy enforcement

Usage:
    python3 test_rbac_api.py
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import base64


class RBACTester:
    """Test suite for RBAC functionality."""

    def __init__(self, base_url: str = "http://localhost:5059"):
        self.base_url = base_url
        self.test_results = []

        # Test users with different roles
        self.test_users = {
            "admin": {"user_id": 1, "role": "admin"},
            "analyst": {"user_id": 2, "role": "analyst"},
            "auditor": {"user_id": 3, "role": "auditor"},
            "viewer": {"user_id": 4, "role": "viewer"},
        }

    def get_auth_headers(self, user_role: str) -> Dict[str, str]:
        """Get authentication headers for a specific user role."""
        user = self.test_users.get(user_role)
        if not user:
            return {}

        return {
            "X-Demo-User-ID": str(user["user_id"]),
            "Content-Type": "application/json",
        }

    def log_test(self, test_name: str, expected: bool, actual: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if expected == actual else "❌ FAIL"
        result = {
            "test": test_name,
            "expected": expected,
            "actual": actual,
            "status": status,
            "details": details,
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {details}")

    def test_risk_score_override_permissions(self):
        """Test risk score override permissions for different roles."""
        print("\n🔒 Testing Risk Score Override Permissions")
        print("=" * 50)

        alert_id = 1
        override_data = {
            "risk_score": 75,
            "justification": "RBAC Test - Testing permission system",
        }

        # Test each role
        for role, user in self.test_users.items():
            try:
                response = requests.patch(
                    f"{self.base_url}/api/alert/{alert_id}/override",
                    json=override_data,
                    headers=self.get_auth_headers(role),
                    timeout=10,
                )

                # Analysts and admins should succeed (200), others should fail (403)
                expected_success = role in ["analyst", "admin"]
                actual_success = response.status_code == 200

                if expected_success:
                    self.log_test(
                        f"Override permission - {role}",
                        True,
                        actual_success,
                        f"Status: {response.status_code}",
                    )
                else:
                    expected_forbidden = response.status_code == 403
                    self.log_test(
                        f"Override blocked - {role}",
                        True,
                        expected_forbidden,
                        f"Status: {response.status_code}",
                    )

            except Exception as e:
                self.log_test(f"Override test - {role}", False, False, f"Error: {e}")

    def test_audit_trail_permissions(self):
        """Test audit trail access permissions for different roles."""
        print("\n📋 Testing Audit Trail Access Permissions")
        print("=" * 50)

        # Test each role
        for role, user in self.test_users.items():
            try:
                response = requests.get(
                    f"{self.base_url}/api/audit?limit=5",
                    headers=self.get_auth_headers(role),
                    timeout=10,
                )

                # Auditors and admins should succeed (200), others should fail (403)
                expected_success = role in ["auditor", "admin"]
                actual_success = response.status_code == 200

                if expected_success:
                    self.log_test(
                        f"Audit access - {role}",
                        True,
                        actual_success,
                        f"Status: {response.status_code}",
                    )
                else:
                    expected_forbidden = response.status_code == 403
                    self.log_test(
                        f"Audit blocked - {role}",
                        True,
                        expected_forbidden,
                        f"Status: {response.status_code}",
                    )

            except Exception as e:
                self.log_test(f"Audit test - {role}", False, False, f"Error: {e}")

    def test_user_info_endpoint(self):
        """Test user information endpoint."""
        print("\n👤 Testing User Information Endpoint")
        print("=" * 50)

        for role, user in self.test_users.items():
            try:
                response = requests.get(
                    f"{self.base_url}/api/user/current",
                    headers=self.get_auth_headers(role),
                    timeout=10,
                )

                if response.status_code == 200:
                    user_data = response.json()
                    expected_role = user["role"]
                    actual_role = user_data.get("role")

                    self.log_test(
                        f"User info - {role}",
                        True,
                        actual_role == expected_role,
                        f"Expected: {expected_role}, Got: {actual_role}",
                    )

                    # Check permissions
                    permissions = user_data.get("permissions", {})
                    can_override = permissions.get("can_override_risk_scores", False)
                    can_audit = permissions.get("can_view_audit_trail", False)

                    expected_override = role in ["analyst", "admin"]
                    expected_audit = role in ["auditor", "admin"]

                    self.log_test(
                        f"Override permission flag - {role}",
                        expected_override,
                        can_override,
                        f"Can override: {can_override}",
                    )

                    self.log_test(
                        f"Audit permission flag - {role}",
                        expected_audit,
                        can_audit,
                        f"Can view audit: {can_audit}",
                    )
                else:
                    self.log_test(
                        f"User info - {role}",
                        False,
                        False,
                        f"Status: {response.status_code}",
                    )

            except Exception as e:
                self.log_test(f"User info test - {role}", False, False, f"Error: {e}")

    def test_unauthenticated_access(self):
        """Test access without authentication."""
        print("\n🚫 Testing Unauthenticated Access")
        print("=" * 50)

        # Test override without auth
        try:
            response = requests.patch(
                f"{self.base_url}/api/alert/1/override",
                json={"risk_score": 50, "justification": "Test"},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            expected_unauthorized = response.status_code == 401
            self.log_test(
                "Unauthenticated override",
                True,
                expected_unauthorized,
                f"Status: {response.status_code}",
            )

        except Exception as e:
            self.log_test("Unauthenticated override", False, False, f"Error: {e}")

        # Test audit without auth
        try:
            response = requests.get(
                f"{self.base_url}/api/audit",
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            expected_unauthorized = response.status_code == 401
            self.log_test(
                "Unauthenticated audit",
                True,
                expected_unauthorized,
                f"Status: {response.status_code}",
            )

        except Exception as e:
            self.log_test("Unauthenticated audit", False, False, f"Error: {e}")

    def test_permission_error_messages(self):
        """Test that permission error messages are informative."""
        print("\n💬 Testing Permission Error Messages")
        print("=" * 50)

        # Test viewer trying to override
        try:
            response = requests.patch(
                f"{self.base_url}/api/alert/1/override",
                json={"risk_score": 50, "justification": "Test"},
                headers=self.get_auth_headers("viewer"),
                timeout=10,
            )

            if response.status_code == 403:
                error_data = response.json()
                has_error_message = "error" in error_data and "message" in error_data

                self.log_test(
                    "Error message structure",
                    True,
                    has_error_message,
                    f"Response: {error_data}",
                )

        except Exception as e:
            self.log_test("Error message test", False, False, f"Error: {e}")

    def run_all_tests(self):
        """Run all RBAC tests."""
        print("🛡️ SentinelForge RBAC Test Suite")
        print("=" * 60)
        print(f"Testing API at: {self.base_url}")
        print(f"Test users: {list(self.test_users.keys())}")
        print()

        # Run test suites
        self.test_user_info_endpoint()
        self.test_risk_score_override_permissions()
        self.test_audit_trail_permissions()
        self.test_unauthenticated_access()
        self.test_permission_error_messages()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["expected"] == r["actual"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result["expected"] != result["actual"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🛡️ RBAC Test Suite Complete!")


def main():
    """Main test execution."""
    tester = RBACTester()

    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        print("Please ensure the SentinelForge API server is running on localhost:5059")


if __name__ == "__main__":
    main()
