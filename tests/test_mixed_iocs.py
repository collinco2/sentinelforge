#!/usr/bin/env python3
"""
Test script for the Alert IOCs endpoint with a complex alert.
"""
import json
import sys
import os

# Add the parent directory to sys.path to import api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import api_server
from api_server import app

def test_mixed_iocs():
    """Test our alert/iocs endpoint with an alert containing multiple mentioned IOCs using the test client."""
    
    # Create a Flask test client
    client = app.test_client()
    
    # Create a special test alert with various IOCs mentioned in the description
    test_alert = {
        "id": "AL_TEST_MIXED",
        "name": "Complex Alert with Multiple IOCs",
        "timestamp": 1678901234,
        "formatted_time": "2023-03-15 12:34:56",
        "threat_type": "APT Activity",
        "severity": "Critical",
        "confidence": 95,
        "description": "This alert contains multiple IOCs. Domain: evil-domain.com and another-domain.org, " +
                       "IP: 192.168.1.1 and 10.0.0.1, " +
                       "URL: https://malicious-site.com/script.php?param=value, " +
                       "Hash: 5f4dcc3b5aa765d61d8327deb882cf99 (MD5) and " +
                       "e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4 (SHA1)",
        "ioc_values": ["evil-domain.com", "192.168.1.1"],  # Only explicitly list some IOCs
        "related_iocs": ["evil-domain.com", "192.168.1.1"],
        "source": "SOC Analyst"
    }
    
    # Add the test alert to the ALERTS list
    api_server.ALERTS.append(test_alert)
    
    # Make a request to our endpoint using the test client
    response = client.get("/api/alert/AL_TEST_MIXED/iocs")
    
    if response.status_code == 200:
        data = json.loads(response.data)
        print("SUCCESS! Response from API:")
        print(json.dumps(data, indent=2))
        
        print(f"\nTotal IOCs found: {data.get('total_iocs', 0)}")
        
        # Print all the IOC values
        print("\nIOCs extracted:")
        for i, ioc in enumerate(data.get('iocs', [])):
            print(f"{i+1}. {ioc.get('value')} ({ioc.get('ioc_type')}) - Inferred: {ioc.get('inferred', False)}")
        
        # Return the values for verification
        return data.get('iocs', [])
    else:
        print(f"ERROR! Status code: {response.status_code}")
        print(response.data.decode())
        return []

if __name__ == "__main__":
    test_mixed_iocs() 