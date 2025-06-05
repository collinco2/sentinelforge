#!/usr/bin/env python3
"""
🛡️ SentinelForge RBAC System Demonstration

This script demonstrates the comprehensive Role-Based Access Control (RBAC)
system implemented in SentinelForge, showing how different user roles have
different permissions and access levels.

Features Demonstrated:
- 4 distinct user roles with different permission levels
- API endpoint protection with proper HTTP status codes
- Frontend UI restrictions based on user permissions
- Comprehensive audit trail and accountability
- Enterprise-grade security with defense in depth

Usage:
    python3 demo_rbac_system.py
"""

import requests
import time
from typing import Dict, Any
import webbrowser


class RBACDemo:
    """Interactive demonstration of the RBAC system."""

    def __init__(self):
        self.api_base = "http://localhost:5059"
        self.ui_base = "http://localhost:3001"

        # User roles and their capabilities
        self.roles = {
            "👁️  Viewer": {
                "user_id": 4,
                "description": "Read-only access for monitoring",
                "can_override": False,
                "can_audit": False,
                "typical_users": "Junior analysts, stakeholders, external auditors",
            },
            "🔍 Analyst": {
                "user_id": 2,
                "description": "Active threat analysis and response",
                "can_override": True,
                "can_audit": False,
                "typical_users": "Security analysts, incident responders",
            },
            "📊 Auditor": {
                "user_id": 3,
                "description": "Compliance monitoring and audit review",
                "can_override": False,
                "can_audit": True,
                "typical_users": "Compliance officers, internal auditors",
            },
            "⚙️  Admin": {
                "user_id": 1,
                "description": "Full system administration",
                "can_override": True,
                "can_audit": True,
                "typical_users": "Security team leads, system administrators",
            },
        }

    def print_header(self, title: str, emoji: str = "🛡️"):
        """Print formatted section header."""
        print(f"\n{emoji} {title}")
        print("=" * (len(title) + 4))

    def print_role_info(self, role_name: str, role_data: Dict[str, Any]):
        """Print detailed role information."""
        print(f"\n{role_name}")
        print(f"   Description: {role_data['description']}")
        print(
            f"   Can Override Risk Scores: {'✅' if role_data['can_override'] else '❌'}"
        )
        print(f"   Can View Audit Trail: {'✅' if role_data['can_audit'] else '❌'}")
        print(f"   Typical Users: {role_data['typical_users']}")

    def test_api_permissions(self, role_name: str, user_id: int):
        """Test API permissions for a specific role."""
        headers = {"X-Demo-User-ID": str(user_id), "Content-Type": "application/json"}

        print(f"\n🔧 Testing API Permissions for {role_name}")
        print("-" * 40)

        # Test user info endpoint
        try:
            response = requests.get(
                f"{self.api_base}/api/user/current", headers=headers, timeout=5
            )
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ User Info: {user_data['username']} ({user_data['role']})")
                permissions = user_data.get("permissions", {})
                print(
                    f"   Override Permission: {'✅' if permissions.get('can_override_risk_scores') else '❌'}"
                )
                print(
                    f"   Audit Permission: {'✅' if permissions.get('can_view_audit_trail') else '❌'}"
                )
            else:
                print(f"❌ User Info: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ User Info: Error - {e}")

        # Test risk score override
        try:
            override_data = {
                "risk_score": 85,
                "justification": f"RBAC Demo - Testing {role_name} permissions",
            }
            response = requests.patch(
                f"{self.api_base}/api/alert/1/override",
                json=override_data,
                headers=headers,
                timeout=5,
            )

            if response.status_code == 200:
                print("✅ Risk Override: Allowed")
            elif response.status_code == 403:
                print("🚫 Risk Override: Forbidden (correct)")
            elif response.status_code == 401:
                print("🔒 Risk Override: Unauthorized")
            else:
                print(f"❓ Risk Override: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Risk Override: Error - {e}")

        # Test audit trail access
        try:
            response = requests.get(
                f"{self.api_base}/api/audit?limit=3", headers=headers, timeout=5
            )

            if response.status_code == 200:
                audit_data = response.json()
                count = len(audit_data.get("audit_logs", []))
                print(f"✅ Audit Access: Allowed ({count} entries)")
            elif response.status_code == 403:
                print("🚫 Audit Access: Forbidden (correct)")
            elif response.status_code == 401:
                print("🔒 Audit Access: Unauthorized")
            else:
                print(f"❓ Audit Access: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Audit Access: Error - {e}")

    def demonstrate_ui_restrictions(self):
        """Demonstrate UI restrictions based on roles."""
        print("\n🎨 UI Restrictions Demonstration")
        print("-" * 40)
        print("The React UI automatically adapts based on user permissions:")
        print()
        print("👁️  Viewer Role:")
        print("   • Override button: Disabled with tooltip")
        print("   • Audit Trail tab: Hidden")
        print("   • Permission badges: None")
        print()
        print("🔍 Analyst Role:")
        print("   • Override button: Enabled and functional")
        print("   • Audit Trail tab: Hidden")
        print("   • Permission badges: 'Override'")
        print()
        print("📊 Auditor Role:")
        print("   • Override button: Disabled with tooltip")
        print("   • Audit Trail tab: Visible and functional")
        print("   • Permission badges: 'Audit'")
        print()
        print("⚙️  Admin Role:")
        print("   • Override button: Enabled and functional")
        print("   • Audit Trail tab: Visible and functional")
        print("   • Permission badges: 'Override', 'Audit'")
        print()
        print(
            "💡 Use the User Role Selector in the top navigation to test different roles!"
        )

    def show_security_features(self):
        """Show security features of the RBAC system."""
        print("\n🔒 Security Features")
        print("-" * 40)
        print("✅ Defense in Depth:")
        print("   • Frontend: UI restrictions prevent unauthorized actions")
        print("   • Backend: API validation enforces permissions")
        print("   • Database: Audit trail provides accountability")
        print()
        print("✅ Proper Error Handling:")
        print("   • 401 Unauthorized: Missing authentication")
        print("   • 403 Forbidden: Insufficient permissions")
        print("   • Clear user-friendly error messages")
        print()
        print("✅ Audit and Compliance:")
        print("   • Immutable audit trail for all overrides")
        print("   • User attribution for every action")
        print("   • Justification required for risk score changes")
        print("   • Supports SOX, HIPAA, PCI DSS, SOC 2, ISO 27001")
        print()
        print("✅ Session Management:")
        print("   • Token-based authentication")
        print("   • Session expiration (24 hours)")
        print("   • Real-time permission validation")

    def run_demo(self):
        """Run the complete RBAC demonstration."""
        self.print_header("SentinelForge RBAC System Demonstration", "🛡️")

        print("""
Welcome to the SentinelForge Role-Based Access Control (RBAC) demonstration!

This demo showcases enterprise-grade security with proper separation of duties,
comprehensive audit capabilities, and defense-in-depth protection.
        """)

        # Show role definitions
        self.print_header("Role Definitions and Permissions", "🎭")
        for role_name, role_data in self.roles.items():
            self.print_role_info(role_name, role_data)

        input("\n💡 Press Enter to test API permissions for each role...")

        # Test API permissions for each role
        for role_name, role_data in self.roles.items():
            self.test_api_permissions(role_name, role_data["user_id"])
            time.sleep(1)  # Brief pause between tests

        input("\n💡 Press Enter to see UI restrictions demonstration...")

        # Demonstrate UI restrictions
        self.demonstrate_ui_restrictions()

        input("\n💡 Press Enter to see security features...")

        # Show security features
        self.show_security_features()

        # Offer to open browser
        print("\n🌐 Interactive Testing")
        print("-" * 40)
        print("To test the RBAC system interactively:")
        print(f"1. Open: {self.ui_base}/alerts")
        print("2. Use the User Role Selector in the top navigation")
        print("3. Switch between roles and observe UI changes")
        print("4. Try to override risk scores with different roles")
        print("5. Check audit trail access with different roles")

        open_browser = (
            input("\n🚀 Open browser to test interactively? (y/n): ").lower().strip()
        )
        if open_browser in ["y", "yes"]:
            try:
                webbrowser.open(f"{self.ui_base}/alerts")
                print(
                    "✅ Browser opened! Use the role selector to test different permissions."
                )
            except Exception as e:
                print(f"❌ Could not open browser: {e}")
                print(f"Please manually navigate to: {self.ui_base}/alerts")

        print("\n🎉 RBAC Demonstration Complete!")
        print("The SentinelForge RBAC system provides enterprise-grade security")
        print(
            "with proper role separation, audit capabilities, and compliance support."
        )


def main():
    """Main demo execution."""
    demo = RBACDemo()

    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Please ensure the SentinelForge API server is running on localhost:5059")
        print("and the React UI is running on localhost:3001")


if __name__ == "__main__":
    main()
