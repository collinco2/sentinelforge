#!/usr/bin/env python3
"""
Unit tests for the Alert IOCs endpoint in the API server.
"""
import json
import unittest
import sys
import os

# Add the parent directory to sys.path to import api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import api_server
from api_server import app

class TestApiAlertIocsEndpoint(unittest.TestCase):
    """Tests for the Alert IOCs endpoint."""

    def setUp(self):
        """Set up the test client and mock data."""
        self.app = app.test_client()
        
        # Mock IOC data
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
            {
                "id": 3,
                "ioc_type": "url",
                "ioc_value": "https://malicious-site.com/download.exe",
                "value": "https://malicious-site.com/download.exe",
                "score": 8.5,
            }
        ]
        
        # Mock alert data
        api_server.ALERTS = [
            {
                "id": "AL1",
                "name": "Suspicious Network Connection",
                "timestamp": 1651234567,
                "formatted_time": "2022-04-29 12:34:56",
                "threat_type": "Command and Control",
                "severity": "High",
                "confidence": 85,
                "description": "Alert triggered by detection of domain example.com in network traffic.",
                "ioc_values": ["example.com"],
                "related_iocs": ["example.com"],
                "source": "SIEM"
            },
            {
                "id": "AL2",
                "name": "Multiple IOC Detection",
                "timestamp": 1667890123,
                "formatted_time": "2022-11-08 15:42:03",
                "threat_type": "Malware",
                "severity": "Critical",
                "confidence": 92,
                "description": "Multiple IOCs detected: domain example.com, IP 1.1.1.1, and URL https://malicious-site.com/download.exe",
                "ioc_values": ["example.com", "1.1.1.1", "https://malicious-site.com/download.exe"],
                "related_iocs": ["example.com", "1.1.1.1", "https://malicious-site.com/download.exe"],
                "source": "EDR"
            },
            {
                "id": "AL3",
                "name": "Unlisted IOC Detection",
                "timestamp": 1662345678,
                "formatted_time": "2022-09-05 09:14:38",
                "threat_type": "Data Exfiltration",
                "severity": "Medium",
                "confidence": 70,
                "description": "Alert triggered by detection of unknown domain new-malicious.com in network traffic.",
                "ioc_values": [],
                "related_iocs": [],
                "source": "Firewall"
            }
        ]

    def test_get_alert_iocs_success(self):
        """Test successful retrieval of IOCs for an alert."""
        # Test for alert with multiple known IOCs
        response = self.app.get('/api/alert/AL2/iocs')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['alert_id'], 'AL2')
        
        # The implementation may find additional IOCs from the description text
        # We're only concerned that our explicitly listed IOCs are included
        self.assertGreaterEqual(data['total_iocs'], 3)
        self.assertGreaterEqual(len(data['iocs']), 3)
        
        # Verify that all expected IOCs are present
        ioc_values = [ioc.get('value') for ioc in data['iocs']]
        self.assertIn('example.com', ioc_values)
        self.assertIn('1.1.1.1', ioc_values)
        self.assertIn('https://malicious-site.com/download.exe', ioc_values)

    def test_get_alert_iocs_inferred(self):
        """Test that IOCs are inferred from description when not explicitly listed."""
        # Test for alert with an unknown IOC mentioned in the description
        response = self.app.get('/api/alert/AL3/iocs')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['alert_id'], 'AL3')
        
        # There should be at least one IOC (new-malicious.com) extracted from the description
        self.assertGreater(data['total_iocs'], 0)
        
        # At least one of the IOCs should be "new-malicious.com"
        ioc_values = [ioc.get('value') for ioc in data['iocs']]
        self.assertIn('new-malicious.com', ioc_values)
        
        # The inferred IOC should be flagged as such
        inferred_ioc = next((ioc for ioc in data['iocs'] if ioc.get('value') == 'new-malicious.com'), None)
        self.assertIsNotNone(inferred_ioc)
        self.assertTrue(inferred_ioc.get('inferred', False))
        self.assertEqual(inferred_ioc.get('ioc_type'), 'domain')

    def test_get_alert_iocs_not_found(self):
        """Test 404 response when alert is not found."""
        response = self.app.get('/api/alert/nonexistent-alert-id/iocs')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main() 