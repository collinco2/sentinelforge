#!/usr/bin/env python3
"""
Unit tests for the IOC-to-alerts endpoint in the API server.
"""

import json
import unittest
import sys
import os

# Add the parent directory to sys.path to import api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import api_server
from api_server import app


class TestApiAlertsEndpoint(unittest.TestCase):
    """Tests for the IOC-to-alerts endpoint."""

    def setUp(self):
        """Set up the test client and mock data."""
        self.app = app.test_client()

        # Mock IOC and alert data
        api_server.IOCS = [
            {
                "id": 1,
                "ioc_type": "domain",
                "ioc_value": "example.com",
                "value": "example.com",
                "score": 9.0,
            },
            {
                "id": 2,
                "ioc_type": "ip",
                "ioc_value": "1.1.1.1",
                "value": "1.1.1.1",
                "score": 7.2,
            },
        ]

        # Mock alert data with timestamps for sorting test
        api_server.ALERTS = [
            {
                "id": "AL1",
                "name": "Suspicious Network Connection",
                "timestamp": 1651234567,  # Older timestamp
                "formatted_time": "2022-04-29 12:34:56",
                "threat_type": "Command and Control",
                "severity": "High",
                "confidence": 85,
                "description": "Alert triggered by detection of domain example.com in network traffic.",
                "ioc_values": ["example.com"],
                "related_iocs": ["example.com"],
                "source": "SIEM",
            },
            {
                "id": "AL2",
                "name": "Malware Detection",
                "timestamp": 1667890123,  # Newer timestamp
                "formatted_time": "2022-11-08 15:42:03",
                "threat_type": "Malware",
                "severity": "Critical",
                "confidence": 92,
                "description": "Alert triggered by detection of domain example.com in network traffic.",
                "ioc_values": ["example.com"],
                "related_iocs": ["example.com"],
                "source": "EDR",
            },
            {
                "id": "AL3",
                "name": "Potential Data Exfiltration",
                "timestamp": 1662345678,  # Middle timestamp
                "formatted_time": "2022-09-05 09:14:38",
                "threat_type": "Data Exfiltration",
                "severity": "Medium",
                "confidence": 70,
                "description": "Alert triggered by detection of ip 1.1.1.1 in network traffic.",
                "ioc_values": ["1.1.1.1"],
                "related_iocs": ["1.1.1.1"],
                "source": "Firewall",
            },
        ]

    def test_get_ioc_alerts_success(self):
        """Test successful retrieval of alerts for an IOC."""
        # Test for example.com which should have 2 alerts
        response = self.app.get("/api/ioc/example.com/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ioc_value"], "example.com")
        self.assertEqual(data["total_alerts"], 2)
        self.assertEqual(len(data["alerts"]), 2)

        # Verify alerts are sorted by timestamp in reverse chronological order (newest first)
        self.assertEqual(data["alerts"][0]["id"], "AL2")
        self.assertEqual(data["alerts"][1]["id"], "AL1")

    def test_get_ioc_alerts_case_insensitive(self):
        """Test that IOC matching is case-insensitive."""
        # Test with uppercase version of the IOC
        response = self.app.get("/api/ioc/EXAMPLE.COM/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_alerts"], 2)

    def test_get_ioc_alerts_not_found(self):
        """Test 404 response when IOC is not found."""
        response = self.app.get("/api/ioc/nonexistent-ioc.com/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "IOC not found")

    def test_get_ioc_alerts_empty_results(self):
        """Test successful response with empty results when no alerts are found."""
        # Add a new IOC with no alerts
        api_server.IOCS.append(
            {
                "id": 3,
                "ioc_type": "hash",
                "ioc_value": "deadbeef",
                "value": "deadbeef",
                "score": 5.0,
            }
        )

        # Use a unique value that won't match any generated alerts
        unique_ioc_value = "deadbeef12345unique"
        api_server.IOCS.append(
            {
                "id": 4,
                "ioc_type": "hash",
                "ioc_value": unique_ioc_value,
                "value": unique_ioc_value,
                "score": 5.0,
            }
        )

        # Patch the get_ioc_by_value function to return our test IOC
        original_get_ioc = api_server.get_ioc_by_value

        def mock_get_ioc_by_value(value):
            if value == unique_ioc_value:
                return {"id": 4, "ioc_type": "hash", "value": unique_ioc_value}
            return original_get_ioc(value)

        api_server.get_ioc_by_value = mock_get_ioc_by_value

        # Clear ALERTS list and define only one unrelated alert
        api_server.ALERTS = [
            {
                "id": "AL4",
                "name": "Unrelated Alert",
                "timestamp": 1667890123,
                "formatted_time": "2022-11-08 15:42:03",
                "threat_type": "Malware",
                "severity": "Low",
                "confidence": 30,
                "description": "This alert is not related to deadbeef12345unique.",
                "ioc_values": ["unrelated.com"],
                "related_iocs": ["unrelated.com"],
                "source": "User Report",
            }
        ]

        response = self.app.get(f"/api/ioc/{unique_ioc_value}/alerts")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ioc_value"], unique_ioc_value)
        self.assertEqual(data["total_alerts"], 0)
        self.assertEqual(data["alerts"], [])

        # Restore original function
        api_server.get_ioc_by_value = original_get_ioc

    def test_generate_mock_alerts(self):
        """Test that the generate_mock_alerts function creates alerts."""
        # Clear existing alerts
        api_server.ALERTS = []

        # Call the function
        api_server.generate_mock_alerts()

        # Check that alerts were generated
        self.assertGreater(len(api_server.ALERTS), 0)

        # Check that each alert has all required fields
        required_fields = [
            "id",
            "name",
            "timestamp",
            "formatted_time",
            "threat_type",
            "severity",
            "confidence",
            "description",
            "ioc_values",
            "source",
        ]

        for alert in api_server.ALERTS:
            for field in required_fields:
                self.assertIn(field, alert)


if __name__ == "__main__":
    unittest.main()
