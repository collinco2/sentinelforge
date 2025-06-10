#!/usr/bin/env python3
"""
Test script for SentinelForge Demo Feed Setup functionality.

Tests both the script-based and API endpoint approaches for setting up demo feeds.
"""

import requests
import json
import sys
import subprocess
from pathlib import Path


def test_api_endpoint():
    """Test the admin API endpoint for demo feed setup."""
    print("🧪 Testing Admin API Endpoint")
    print("=" * 40)

    # Test authentication first
    login_data = {
        "username": "admin",
        "password": "admin123",  # Default admin password
    }

    print("🔐 Authenticating as admin...")
    response = requests.post("http://localhost:5059/api/login", json=login_data)

    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    auth_data = response.json()
    session_token = auth_data.get("session_token")

    if not session_token:
        print("❌ No session token received")
        return False

    print("✅ Authentication successful")

    # Test endpoint without confirmation (should fail)
    print("\n📋 Testing endpoint without confirmation...")
    headers = {"X-Session-Token": session_token}
    response = requests.post(
        "http://localhost:5059/api/admin/setup-demo-feeds", headers=headers
    )

    if response.status_code != 400:
        print(f"❌ Expected 400 error, got {response.status_code}")
        return False

    print("✅ Correctly rejected request without confirmation")

    # Test endpoint with confirmation (feeds only)
    print("\n📋 Testing feed registration only...")
    response = requests.post(
        "http://localhost:5059/api/admin/setup-demo-feeds?confirm=true", headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Feed registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()
    print(f"✅ Registered {result.get('total_feeds', 0)} demo feeds")

    # Test endpoint with confirmation and data import
    print("\n📊 Testing feed registration with data import...")
    response = requests.post(
        "http://localhost:5059/api/admin/setup-demo-feeds?confirm=true&import_data=true",
        headers=headers,
    )

    if response.status_code != 200:
        print(f"❌ Feed registration with import failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()
    print(
        f"✅ Registered {result.get('total_feeds', 0)} feeds and imported {result.get('iocs_imported', 0)} IOCs"
    )

    # Verify feeds were created
    print("\n🔍 Verifying feeds were created...")
    response = requests.get("http://localhost:5059/api/feeds", headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch feeds: {response.status_code}")
        return False

    feeds_data = response.json()
    demo_feeds = [
        f
        for f in feeds_data.get("feeds", [])
        if "demo" in f.get("name", "").lower()
        or any(
            keyword in f.get("name", "").lower()
            for keyword in ["malware", "abuse", "ipsum", "mitre", "emerging"]
        )
    ]

    print(f"✅ Found {len(demo_feeds)} demo feeds in database")

    # Verify IOCs were imported
    if result.get("iocs_imported", 0) > 0:
        print("\n🔍 Verifying IOCs were imported...")
        response = requests.get(
            "http://localhost:5059/api/iocs?limit=50", headers=headers
        )

        if response.status_code != 200:
            print(f"❌ Failed to fetch IOCs: {response.status_code}")
            return False

        iocs_data = response.json()
        demo_iocs = [
            ioc
            for ioc in iocs_data.get("iocs", [])
            if any(
                keyword in ioc.get("source_feed", "").lower()
                for keyword in ["malware", "abuse", "ipsum", "mitre", "emerging"]
            )
        ]

        print(f"✅ Found {len(demo_iocs)} demo IOCs in database")

    return True


def test_script_approach():
    """Test the script-based approach for demo feed setup."""
    print("\n🧪 Testing Script Approach")
    print("=" * 40)

    script_path = Path("scripts/seed_feeds.py")

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    print("📋 Testing script with --confirm flag...")

    try:
        # Test script execution
        result = subprocess.run(
            [sys.executable, str(script_path), "--confirm"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"❌ Script failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        print("✅ Script executed successfully")
        print(f"Output: {result.stdout}")

        # Test script with data import
        print("\n📊 Testing script with data import...")
        result = subprocess.run(
            [sys.executable, str(script_path), "--confirm", "--import-data"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"❌ Script with import failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        print("✅ Script with data import executed successfully")

        return True

    except subprocess.TimeoutExpired:
        print("❌ Script execution timed out")
        return False
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        return False


def test_feed_formats():
    """Test that all demo feed formats are properly created."""
    print("\n🧪 Testing Feed Format Files")
    print("=" * 40)

    demo_dir = Path("feeds/demo")
    expected_files = [
        "demo_malwaredomainlist_domains.txt",
        "demo_abuse_ch_urlhaus_malware_urls.csv",
        "demo_ipsum_threat_intelligence.txt",
        "demo_mitre_att_ck_stix_feed.json",
        "demo_emerging_threats_compromised_ips.txt",
    ]

    all_files_exist = True

    for filename in expected_files:
        filepath = demo_dir / filename
        if filepath.exists():
            print(f"✅ {filename}")

            # Validate file content
            try:
                content = filepath.read_text()
                if len(content.strip()) > 0:
                    print(f"   📄 Content length: {len(content)} characters")
                else:
                    print(f"   ⚠️  File is empty")
                    all_files_exist = False
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
                all_files_exist = False
        else:
            print(f"❌ {filename} - NOT FOUND")
            all_files_exist = False

    return all_files_exist


def test_ingestion_formats():
    """Test that the ingestion system can handle all demo formats."""
    print("\n🧪 Testing Ingestion Format Support")
    print("=" * 40)

    try:
        from services.ingestion import FeedIngestionService

        # Test TXT format
        print("📄 Testing TXT format parsing...")
        txt_content = (
            "malicious-domain.com\nevil-site.net\n# comment line\nphishing.org"
        )
        txt_result = FeedIngestionService.parse_txt_feed(
            txt_content, {"delimiter": "\n", "comment_prefix": "#"}
        )
        print(f"   ✅ Parsed {len(txt_result)} items from TXT")

        # Test CSV format
        print("📊 Testing CSV format parsing...")
        csv_content = "url,threat,tags\nhttp://evil.com,malware,exe\nhttps://bad.net,phishing,banking"
        csv_result = FeedIngestionService.parse_csv_feed(
            csv_content, {"has_header": True, "delimiter": ","}
        )
        print(f"   ✅ Parsed {len(csv_result)} items from CSV")

        # Test JSON/STIX format
        print("🔗 Testing JSON/STIX format parsing...")
        stix_content = {
            "type": "bundle",
            "objects": [
                {
                    "type": "indicator",
                    "pattern": "[domain-name:value = 'evil.com']",
                    "labels": ["malicious-activity"],
                }
            ],
        }
        json_result = FeedIngestionService.parse_json_feed(
            json.dumps(stix_content), {"stix_version": "2.0", "bundle_key": "objects"}
        )
        print(f"   ✅ Parsed {len(json_result)} items from JSON/STIX")

        return True

    except ImportError:
        print("❌ FeedIngestionService not available")
        return False
    except Exception as e:
        print(f"❌ Ingestion testing failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 SentinelForge Demo Feed Setup Tests")
    print("=" * 50)

    # Check if API server is running
    try:
        response = requests.get("http://localhost:5059/api/session", timeout=5)
        if response.status_code != 200:
            print("❌ API server not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("❌ API server not running on localhost:5059")
        print("   Please start the API server first: python api_server.py")
        return

    print("✅ API server is running")

    # Run tests
    tests = [
        ("Feed Format Files", test_feed_formats),
        ("Ingestion Format Support", test_ingestion_formats),
        ("API Endpoint", test_api_endpoint),
        ("Script Approach", test_script_approach),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Demo feed setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    main()
