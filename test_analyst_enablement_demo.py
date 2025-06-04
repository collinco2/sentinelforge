#!/usr/bin/env python3
"""
🛡️ SentinelForge Analyst Enablement Demo

This interactive demo showcases the analyst onboarding workflow for risk score
overrides and audit trail features, demonstrating best practices and proper
justification techniques.

Usage:
    python3 test_analyst_enablement_demo.py

Features Demonstrated:
- Risk score override workflow with proper justification
- Audit trail review and interpretation
- Best practices for analyst decision-making
- Compliance and accountability features
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:5059"
DEMO_USER_ID = 3001  # Demo analyst user


class AnalystEnablementDemo:
    """Interactive demo for analyst onboarding and enablement."""

    def __init__(self):
        self.session = requests.Session()
        self.demo_scenarios = [
            {
                "alert_id": 1,
                "scenario": "False Positive - Legitimate Admin Activity",
                "original_score": 75,
                "new_score": 25,
                "justification": "FALSE_POSITIVE: Legitimate admin activity - PowerShell execution by john.admin@company.com for approved maintenance task per ticket INC-12345. Verified in change management system and authorized by IT Operations.",
                "learning_points": [
                    "Always reference specific evidence (ticket numbers, user accounts)",
                    "Include verification steps taken",
                    "Use structured justification format",
                ],
            },
            {
                "alert_id": 2,
                "scenario": "Escalation - Critical Asset Involvement",
                "original_score": 60,
                "new_score": 85,
                "justification": "ESCALATION: Critical asset targeted - Domain controller DC01 involved in suspicious authentication attempts. Escalating per security playbook SEC-PB-001 for critical infrastructure protection.",
                "learning_points": [
                    "Business context affects risk assessment",
                    "Reference security playbooks and procedures",
                    "Critical assets warrant higher attention",
                ],
            },
            {
                "alert_id": 3,
                "scenario": "Threat Intelligence Correlation",
                "original_score": 45,
                "new_score": 90,
                "justification": "THREAT_INTEL: IOC correlation confirmed - File hash matches known Emotet variant per VirusTotal analysis (family confidence 95%). Additional context from CISA alert AA23-347A indicates active campaign targeting financial sector.",
                "learning_points": [
                    "External threat intelligence enhances analysis",
                    "Include confidence levels and sources",
                    "Correlate with industry-specific threats",
                ],
            },
        ]

    def print_header(self, title: str, emoji: str = "🎯"):
        """Print formatted section header."""
        print(f"\n{emoji} {title}")
        print("=" * (len(title) + 4))

    def print_step(self, step: int, description: str):
        """Print formatted step."""
        print(f"\n{step}️⃣  {description}")
        print("-" * (len(description) + 6))

    def wait_for_user(self, message: str = "Press Enter to continue..."):
        """Wait for user input to proceed."""
        input(f"\n💡 {message}")

    def get_alert_details(self, alert_id: int) -> Optional[Dict]:
        """Fetch alert details from API."""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/alert/{alert_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to fetch alert {alert_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error fetching alert: {e}")
            return None

    def override_risk_score(
        self, alert_id: int, new_score: int, justification: str
    ) -> bool:
        """Perform risk score override."""
        try:
            payload = {
                "risk_score": new_score,
                "justification": justification,
                "user_id": DEMO_USER_ID,
            }

            response = self.session.patch(
                f"{API_BASE_URL}/api/alert/{alert_id}/override",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Override successful!")
                print(f"   Alert ID: {result.get('id')}")
                print(f"   New Risk Score: {result.get('overridden_risk_score')}")
                print(f"   Previous Score: {result.get('risk_score')}")
                return True
            else:
                print(f"❌ Override failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error during override: {e}")
            return False

    def get_audit_trail(self, alert_id: int) -> List[Dict]:
        """Fetch audit trail for alert."""
        try:
            response = self.session.get(
                f"{API_BASE_URL}/api/audit?alert_id={alert_id}&limit=10"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("audit_logs", [])
            else:
                print(f"❌ Failed to fetch audit trail: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching audit trail: {e}")
            return []

    def display_audit_entry(self, entry: Dict):
        """Display formatted audit entry."""
        timestamp = entry.get("timestamp", "Unknown")
        user_id = entry.get("user_id", "Unknown")
        original = entry.get("original_score", "N/A")
        override = entry.get("override_score", "N/A")
        justification = entry.get("justification", "No justification provided")

        print(f"📋 Audit Entry #{entry.get('id', 'Unknown')}")
        print(f"   ⏰ Timestamp: {timestamp}")
        print(f"   👤 Analyst: User {user_id}")
        print(f"   📊 Score Change: {original} → {override}")
        print(f"   📝 Justification: {justification}")

    def demonstrate_scenario(self, scenario: Dict):
        """Demonstrate a complete override scenario."""
        alert_id = scenario["alert_id"]
        scenario_name = scenario["scenario"]
        new_score = scenario["new_score"]
        justification = scenario["justification"]
        learning_points = scenario["learning_points"]

        self.print_step(1, f"Scenario: {scenario_name}")

        # Fetch current alert details
        print("🔍 Fetching alert details...")
        alert = self.get_alert_details(alert_id)
        if not alert:
            print("❌ Could not fetch alert details. Skipping scenario.")
            return

        current_score = alert.get("overridden_risk_score") or alert.get(
            "risk_score", "Unknown"
        )
        print(f"📊 Current Risk Score: {current_score}")
        print(f"🎯 Proposed New Score: {new_score}")
        print(f"📝 Justification Strategy: {scenario_name}")

        self.wait_for_user("Ready to see the justification? Press Enter...")

        # Show justification
        print(f"\n📝 Analyst Justification:")
        print(f'   "{justification}"')

        self.wait_for_user("Ready to perform the override? Press Enter...")

        # Perform override
        self.print_step(2, "Performing Risk Score Override")
        success = self.override_risk_score(alert_id, new_score, justification)

        if success:
            # Show audit trail
            self.print_step(3, "Reviewing Audit Trail")
            print("🔍 Fetching updated audit trail...")
            time.sleep(1)  # Brief pause for dramatic effect

            audit_logs = self.get_audit_trail(alert_id)
            if audit_logs:
                print(f"\n📋 Latest Audit Entries for Alert {alert_id}:")
                for i, entry in enumerate(audit_logs[:3]):  # Show last 3 entries
                    print(f"\n{i + 1}. ", end="")
                    self.display_audit_entry(entry)

            # Show learning points
            self.print_step(4, "Key Learning Points")
            for i, point in enumerate(learning_points, 1):
                print(f"   {i}. {point}")

        self.wait_for_user("Scenario complete! Press Enter for next scenario...")

    def run_demo(self):
        """Run the complete analyst enablement demo."""
        self.print_header("SentinelForge Analyst Enablement Demo", "🛡️")

        print("""
Welcome to the SentinelForge Analyst Enablement Demo!

This interactive demonstration will guide you through:
✅ Proper risk score override techniques
✅ Writing effective justifications
✅ Understanding audit trail entries
✅ Best practices for analyst decision-making
✅ Compliance and accountability features

The demo uses real API calls to demonstrate actual functionality.
        """)

        self.wait_for_user("Ready to begin? Press Enter to start...")

        # Introduction to audit trail
        self.print_header("Understanding the Audit Trail", "📋")
        print("""
The audit trail is an immutable record of all risk score overrides:

🔒 Immutable: Entries cannot be modified or deleted
👤 Attributed: Every change tracked to specific analyst
⏰ Timestamped: UTC timestamps for global consistency
📝 Justified: Required reasoning for every override
🏛️ Compliant: Supports SOX, HIPAA, PCI DSS, SOC 2, ISO 27001
        """)

        self.wait_for_user("Ready to see scenarios? Press Enter...")

        # Run through scenarios
        for i, scenario in enumerate(self.demo_scenarios, 1):
            self.print_header(f"Scenario {i}: {scenario['scenario']}", "🎭")
            self.demonstrate_scenario(scenario)

        # Conclusion
        self.print_header("Demo Complete - Key Takeaways", "🎓")
        print("""
🎯 Key Takeaways for Analysts:

1. 📝 Always provide detailed, technical justifications
2. 🔍 Reference specific evidence and sources
3. 📋 Review audit trail before making overrides
4. 🏛️ Remember that all actions are logged for compliance
5. 🚀 Use structured justification formats for consistency

📚 Next Steps:
- Review the Analyst Guide: docs/ANALYST_GUIDE.md
- Practice with real alerts in your environment
- Escalate uncertain cases to senior analysts
- Contribute to team knowledge sharing

🛡️ Remember: The audit trail supports both accountability 
   and learning - use it to improve your analysis skills!
        """)

        print("\n🎉 Thank you for completing the Analyst Enablement Demo!")
        print("💡 For questions or support, contact your SOC team lead.")


def main():
    """Main demo execution."""
    demo = AnalystEnablementDemo()

    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print(
            "Please check that the SentinelForge API server is running on localhost:5059"
        )


if __name__ == "__main__":
    main()
