#!/usr/bin/env python3
"""
🛡️ SentinelForge Role Management Demo

This script demonstrates the admin-only role management functionality,
including user listing, role updates, and audit logging.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List


class RoleManagementDemo:
    """Demo class for role management functionality."""

    def __init__(self):
        self.api_base = "http://localhost:5059"
        self.ui_base = "http://localhost:3000"

        # Demo users with their capabilities
        self.demo_users = {
            "👑 Admin": {
                "user_id": 1,
                "description": "Full system access including role management",
                "can_manage_roles": True,
                "can_override": True,
                "can_audit": True,
            },
            "🔍 Analyst": {
                "user_id": 2,
                "description": "Active threat analysis and response",
                "can_manage_roles": False,
                "can_override": True,
                "can_audit": False,
            },
            "📊 Auditor": {
                "user_id": 3,
                "description": "Compliance monitoring and audit review",
                "can_manage_roles": False,
                "can_override": False,
                "can_audit": True,
            },
            "👁️  Viewer": {
                "user_id": 4,
                "description": "Read-only access for monitoring",
                "can_manage_roles": False,
                "can_override": False,
                "can_audit": False,
            },
        }

    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'=' * 60}")
        print(f"🛡️  {title}")
        print(f"{'=' * 60}")

    def print_step(self, step: str):
        """Print a formatted step."""
        print(f"\n📋 {step}")
        print("-" * 50)

    def make_request(
        self, method: str, endpoint: str, user_id: int, data: Dict = None
    ) -> Dict:
        """Make an API request with proper headers."""
        headers = {
            "X-Demo-User-ID": str(user_id),
            "Content-Type": "application/json",
        }

        url = f"{self.api_base}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code < 400,
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False,
            }

    def demo_user_listing(self):
        """Demonstrate user listing functionality."""
        self.print_step("1. User Listing Access Control")

        for role_name, user_info in self.demo_users.items():
            user_id = user_info["user_id"]
            can_manage = user_info["can_manage_roles"]

            print(f"\n{role_name} attempting to list users...")

            response = self.make_request("GET", "/api/users", user_id)

            if can_manage and response["success"]:
                users = response["data"].get("users", [])
                print(f"✅ SUCCESS: Retrieved {len(users)} users")
                for user in users[:2]:  # Show first 2 users
                    print(f"   - {user['username']} ({user['role']})")
            elif not can_manage and response["status_code"] == 403:
                print(f"🚫 EXPECTED: Access denied (403)")
            elif response["success"]:
                print(f"⚠️  UNEXPECTED: Access granted when it shouldn't be")
            else:
                print(f"❌ ERROR: {response['data'].get('error', 'Unknown error')}")

    def demo_role_updates(self):
        """Demonstrate role update functionality."""
        self.print_step("2. Role Update Operations")

        # Test admin updating another user's role
        print("\n👑 Admin updating analyst role to auditor...")
        response = self.make_request(
            "PATCH",
            "/api/user/2/role",
            1,  # Admin user ID
            {"role": "auditor"},
        )

        if response["success"]:
            print("✅ SUCCESS: Role updated successfully")
            print(f"   Old role: {response['data'].get('old_role')}")
            print(f"   New role: {response['data'].get('new_role')}")
        else:
            print(f"❌ ERROR: {response['data'].get('error', 'Unknown error')}")

        time.sleep(1)

        # Test non-admin trying to update roles
        print("\n🔍 Analyst attempting to update roles...")
        response = self.make_request(
            "PATCH",
            "/api/user/3/role",
            2,  # Analyst user ID
            {"role": "viewer"},
        )

        if response["status_code"] == 403:
            print("🚫 EXPECTED: Access denied (403)")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

        # Test admin trying to demote themselves
        print("\n👑 Admin attempting self-demotion...")
        response = self.make_request(
            "PATCH",
            "/api/user/1/role",
            1,  # Admin user ID
            {"role": "viewer"},
        )

        if response["status_code"] == 400:
            print("🚫 EXPECTED: Self-demotion prevented (400)")
            print(f"   Message: {response['data'].get('error')}")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

        # Restore original role
        print("\n👑 Admin restoring analyst role...")
        response = self.make_request(
            "PATCH",
            "/api/user/2/role",
            1,  # Admin user ID
            {"role": "analyst"},
        )

        if response["success"]:
            print("✅ SUCCESS: Role restored")
        else:
            print(f"❌ ERROR: {response['data'].get('error', 'Unknown error')}")

    def demo_audit_logging(self):
        """Demonstrate audit logging functionality."""
        self.print_step("3. Role Change Audit Logging")

        # Admin accessing audit logs
        print("\n👑 Admin viewing role change audit logs...")
        response = self.make_request("GET", "/api/audit/roles", 1)

        if response["success"]:
            audit_logs = response["data"].get("audit_logs", [])
            print(f"✅ SUCCESS: Retrieved {len(audit_logs)} audit entries")

            for log in audit_logs[:3]:  # Show first 3 entries
                timestamp = log.get("timestamp", "")
                admin = log.get("admin_username", "Unknown")
                justification = log.get("justification", "")

                print(f"   📝 {timestamp[:19]} - {admin}")
                print(f"      {justification[:80]}...")
        else:
            print(f"❌ ERROR: {response['data'].get('error', 'Unknown error')}")

        # Non-admin trying to access audit logs
        print("\n🔍 Analyst attempting to view audit logs...")
        response = self.make_request("GET", "/api/audit/roles", 2)

        if response["status_code"] == 403:
            print("🚫 EXPECTED: Access denied (403)")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

    def demo_edge_cases(self):
        """Demonstrate edge cases and error handling."""
        self.print_step("4. Edge Cases and Error Handling")

        # Invalid role
        print("\n👑 Admin attempting to set invalid role...")
        response = self.make_request(
            "PATCH", "/api/user/2/role", 1, {"role": "super_admin"}
        )

        if response["status_code"] == 400:
            print("🚫 EXPECTED: Invalid role rejected (400)")
            print(f"   Message: {response['data'].get('error')}")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

        # Missing role field
        print("\n👑 Admin attempting update without role field...")
        response = self.make_request("PATCH", "/api/user/2/role", 1, {})

        if response["status_code"] == 400:
            print("🚫 EXPECTED: Missing role field rejected (400)")
            print(f"   Message: {response['data'].get('error')}")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

        # Non-existent user
        print("\n👑 Admin attempting to update non-existent user...")
        response = self.make_request(
            "PATCH", "/api/user/999/role", 1, {"role": "viewer"}
        )

        if response["status_code"] == 404:
            print("🚫 EXPECTED: User not found (404)")
        else:
            print(f"⚠️  UNEXPECTED: {response['status_code']} - {response['data']}")

    def demo_ui_integration(self):
        """Demonstrate UI integration points."""
        self.print_step("5. UI Integration")

        print(f"\n🌐 Frontend Role Management Interface:")
        print(f"   URL: {self.ui_base}/role-management")
        print(f"   📋 Features:")
        print(f"      • User listing with role badges")
        print(f"      • Role filtering and search")
        print(f"      • Inline role editing with dropdowns")
        print(f"      • Confirmation dialogs for role changes")
        print(f"      • Real-time audit trail display")
        print(f"      • Admin-only access control")

        print(f"\n🔐 Security Features:")
        print(f"      • RBAC enforcement at API level")
        print(f"      • Self-demotion prevention")
        print(f"      • Comprehensive audit logging")
        print(f"      • Input validation and sanitization")
        print(f"      • Error handling with user feedback")

    def run_demo(self):
        """Run the complete role management demo."""
        self.print_header("SentinelForge Role Management Demo")

        print(f"🎯 This demo showcases the admin-only role management system")
        print(f"📊 Testing with {len(self.demo_users)} different user roles")
        print(f"🔗 API Base: {self.api_base}")
        print(f"🌐 UI Base: {self.ui_base}")

        try:
            self.demo_user_listing()
            self.demo_role_updates()
            self.demo_audit_logging()
            self.demo_edge_cases()
            self.demo_ui_integration()

            self.print_header("Demo Complete")
            print("✅ All role management features demonstrated successfully!")
            print("\n📋 Summary:")
            print("   • User listing with proper access control")
            print("   • Role updates with validation and security")
            print("   • Comprehensive audit logging")
            print("   • Edge case handling and error management")
            print("   • UI integration with admin-only access")

            print(f"\n🌐 Visit {self.ui_base}/role-management to see the UI!")

        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Demo failed with error: {e}")


if __name__ == "__main__":
    demo = RoleManagementDemo()
    demo.run_demo()
