#!/usr/bin/env python3
"""
🧪 IOC Feed Ingestion Test Suite

This test suite validates the IOC feed ingestion functionality including:
- CSV feed parsing and import
- JSON feed parsing and import
- TXT feed parsing and import
- File validation and error handling
- Duplicate detection and handling
- Bulk import performance
- Import audit logging

Usage:
    python test_feed_ingest.py
"""

import requests
import json
import csv
import tempfile
import os
from datetime import datetime
from io import StringIO


class FeedIngestionTester:
    def __init__(self, base_url="http://localhost:5059"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_files = []

    def login_as_admin(self):
        """Login as admin user for testing."""
        login_data = {"username": "admin", "password": "admin123"}

        response = self.session.post(f"{self.base_url}/api/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            if session_token:
                # Set session token in headers for future requests
                self.session.headers.update({"X-Session-Token": session_token})
                print("✅ Logged in as admin")
                return True
            else:
                print("❌ No session token received")
                return False
        else:
            print(f"❌ Failed to login: {response.status_code}")
            return False

    def create_test_csv_feed(self):
        """Create a test CSV feed file."""
        csv_data = [
            [
                "ioc_type",
                "ioc_value",
                "source_feed",
                "severity",
                "confidence",
                "score",
                "tags",
            ],
            [
                "domain",
                "malicious-test1.com",
                "Test CSV Feed",
                "high",
                "85",
                "7.5",
                "malware,test",
            ],
            ["ip", "192.168.100.1", "Test CSV Feed", "medium", "70", "5.0", "botnet"],
            [
                "hash",
                "d41d8cd98f00b204e9800998ecf8427e",
                "Test CSV Feed",
                "critical",
                "95",
                "9.0",
                "ransomware,critical",
            ],
            [
                "url",
                "https://evil-test.com/payload",
                "Test CSV Feed",
                "high",
                "80",
                "7.0",
                "phishing",
            ],
            [
                "email",
                "attacker@evil-test.com",
                "Test CSV Feed",
                "medium",
                "60",
                "4.5",
                "spam",
            ],
        ]

        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        writer = csv.writer(temp_file)
        writer.writerows(csv_data)
        temp_file.close()

        self.test_files.append(temp_file.name)
        return temp_file.name

    def create_test_json_feed(self):
        """Create a test JSON feed file."""
        json_data = {
            "iocs": [
                {
                    "ioc_type": "domain",
                    "ioc_value": "malicious-test2.com",
                    "source_feed": "Test JSON Feed",
                    "severity": "high",
                    "confidence": 90,
                    "score": 8.0,
                    "tags": ["malware", "json-test"],
                },
                {
                    "ioc_type": "ip",
                    "ioc_value": "10.0.0.100",
                    "source_feed": "Test JSON Feed",
                    "severity": "critical",
                    "confidence": 95,
                    "score": 9.5,
                    "tags": ["c2", "critical"],
                },
                {
                    "type": "hash",  # Test field mapping
                    "value": "5d41402abc4b2a76b9719d911017c592",  # Test field mapping
                    "source_feed": "Test JSON Feed",
                    "severity": "medium",
                    "confidence": 75,
                    "score": 6.0,
                },
            ]
        }

        # Create temporary JSON file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(json_data, temp_file, indent=2)
        temp_file.close()

        self.test_files.append(temp_file.name)
        return temp_file.name

    def create_test_txt_feed(self):
        """Create a test TXT feed file."""
        txt_data = [
            "# Test TXT Feed - One IOC per line",
            "malicious-test3.com",
            "192.168.200.1",
            "https://phishing-test.com/login",
            "attacker2@evil-test.com",
            "e3b0c44298fc1c149afbf4c8996fb924",
            "",  # Empty line (should be ignored)
            "# Another comment (should be ignored)",
            "final-test.com",
        ]

        # Create temporary TXT file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        temp_file.write("\n".join(txt_data))
        temp_file.close()

        self.test_files.append(temp_file.name)
        return temp_file.name

    def create_invalid_csv_feed(self):
        """Create an invalid CSV feed for error testing."""
        csv_data = [
            ["ioc_type", "ioc_value", "source_feed"],
            ["invalid_type", "test.com", "Invalid Feed"],  # Invalid IOC type
            ["domain", "", "Invalid Feed"],  # Empty IOC value
            ["ip", "invalid.ip.address", "Invalid Feed"],  # Invalid IP format
        ]

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        writer = csv.writer(temp_file)
        writer.writerows(csv_data)
        temp_file.close()

        self.test_files.append(temp_file.name)
        return temp_file.name

    def test_csv_import(self):
        """Test CSV feed import."""
        print("\n🧪 Testing CSV Feed Import...")

        csv_file = self.create_test_csv_feed()

        with open(csv_file, "rb") as f:
            files = {"file": ("test_feed.csv", f, "text/csv")}
            data = {
                "source_feed": "Test CSV Import",
                "justification": "Testing CSV import functionality",
            }

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response.status_code == 200:
            result = response.json()
            imported = result.get("imported_count", 0)
            skipped = result.get("skipped_count", 0)
            errors = result.get("errors", [])

            print(f"  ✅ CSV import completed")
            print(f"    📥 Imported: {imported}")
            print(f"    ⏭️  Skipped: {skipped}")
            print(f"    ❌ Errors: {len(errors)}")

            if errors:
                print("    Error details:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      • {error}")

            return imported > 0
        else:
            print(f"  ❌ CSV import failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return False

    def test_json_import(self):
        """Test JSON feed import."""
        print("\n🧪 Testing JSON Feed Import...")

        json_file = self.create_test_json_feed()

        with open(json_file, "rb") as f:
            files = {"file": ("test_feed.json", f, "application/json")}
            data = {
                "source_feed": "Test JSON Import",
                "justification": "Testing JSON import functionality",
            }

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response.status_code == 200:
            result = response.json()
            imported = result.get("imported_count", 0)
            skipped = result.get("skipped_count", 0)
            errors = result.get("errors", [])

            print(f"  ✅ JSON import completed")
            print(f"    📥 Imported: {imported}")
            print(f"    ⏭️  Skipped: {skipped}")
            print(f"    ❌ Errors: {len(errors)}")

            return imported > 0
        else:
            print(f"  ❌ JSON import failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return False

    def test_txt_import(self):
        """Test TXT feed import."""
        print("\n🧪 Testing TXT Feed Import...")

        txt_file = self.create_test_txt_feed()

        with open(txt_file, "rb") as f:
            files = {"file": ("test_feed.txt", f, "text/plain")}
            data = {
                "source_feed": "Test TXT Import",
                "justification": "Testing TXT import functionality",
            }

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response.status_code == 200:
            result = response.json()
            imported = result.get("imported_count", 0)
            skipped = result.get("skipped_count", 0)
            errors = result.get("errors", [])

            print(f"  ✅ TXT import completed")
            print(f"    📥 Imported: {imported}")
            print(f"    ⏭️  Skipped: {skipped}")
            print(f"    ❌ Errors: {len(errors)}")

            return imported > 0
        else:
            print(f"  ❌ TXT import failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return False

    def test_duplicate_handling(self):
        """Test duplicate IOC handling during import."""
        print("\n🧪 Testing Duplicate Handling...")

        # Import the same CSV file twice
        csv_file = self.create_test_csv_feed()

        # First import
        with open(csv_file, "rb") as f:
            files = {"file": ("test_feed.csv", f, "text/csv")}
            data = {
                "source_feed": "Duplicate Test 1",
                "justification": "First import for duplicate testing",
            }

            response1 = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        # Second import (should detect duplicates)
        with open(csv_file, "rb") as f:
            files = {"file": ("test_feed.csv", f, "text/csv")}
            data = {
                "source_feed": "Duplicate Test 2",
                "justification": "Second import for duplicate testing",
            }

            response2 = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response1.status_code == 200 and response2.status_code == 200:
            result1 = response1.json()
            result2 = response2.json()

            imported1 = result1.get("imported_count", 0)
            imported2 = result2.get("imported_count", 0)
            skipped2 = result2.get("skipped_count", 0)

            print(f"  ✅ Duplicate handling test completed")
            print(f"    📥 First import: {imported1}")
            print(f"    📥 Second import: {imported2}")
            print(f"    ⏭️  Skipped duplicates: {skipped2}")

            if skipped2 > 0:
                print("    ✅ Duplicates properly detected and skipped")
                return True
            else:
                print("    ❌ Duplicates not properly handled")
                return False
        else:
            print("  ❌ Duplicate handling test failed")
            return False

    def test_invalid_file_handling(self):
        """Test handling of invalid files and data."""
        print("\n🧪 Testing Invalid File Handling...")

        # Test unsupported file type
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False)
        temp_file.write("<xml>Invalid format</xml>")
        temp_file.close()
        self.test_files.append(temp_file.name)

        with open(temp_file.name, "rb") as f:
            files = {"file": ("test.xml", f, "application/xml")}
            data = {"source_feed": "Invalid Test"}

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response.status_code == 400:
            print("  ✅ Unsupported file type properly rejected")
        else:
            print(f"  ❌ Unsupported file type not rejected: {response.status_code}")

        # Test invalid CSV data
        invalid_csv = self.create_invalid_csv_feed()

        with open(invalid_csv, "rb") as f:
            files = {"file": ("invalid.csv", f, "text/csv")}
            data = {
                "source_feed": "Invalid CSV Test",
                "justification": "Testing invalid data handling",
            }

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        if response.status_code == 200:
            result = response.json()
            errors = result.get("errors", [])

            if len(errors) > 0:
                print("  ✅ Invalid data properly handled with errors reported")
                print(f"    ❌ Errors reported: {len(errors)}")
            else:
                print("  ❌ Invalid data not properly validated")
        else:
            print(f"  ❌ Invalid CSV handling failed: {response.status_code}")

    def test_large_file_import(self):
        """Test importing a larger file for performance."""
        print("\n🧪 Testing Large File Import Performance...")

        # Create a larger CSV file
        large_csv_data = [
            ["ioc_type", "ioc_value", "source_feed", "severity", "confidence"]
        ]

        for i in range(100):  # 100 test IOCs
            large_csv_data.append(
                ["domain", f"large-test-{i:03d}.com", "Large Test Feed", "medium", "70"]
            )

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        writer = csv.writer(temp_file)
        writer.writerows(large_csv_data)
        temp_file.close()
        self.test_files.append(temp_file.name)

        start_time = datetime.now()

        with open(temp_file.name, "rb") as f:
            files = {"file": ("large_feed.csv", f, "text/csv")}
            data = {
                "source_feed": "Large Test Import",
                "justification": "Testing large file import performance",
            }

            response = self.session.post(
                f"{self.base_url}/api/iocs/import", files=files, data=data
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if response.status_code == 200:
            result = response.json()
            imported = result.get("imported_count", 0)

            print(f"  ✅ Large file import completed")
            print(f"    📥 Imported: {imported} IOCs")
            print(f"    ⏱️  Duration: {duration:.2f} seconds")
            print(f"    🚀 Rate: {imported / duration:.1f} IOCs/second")

            return True
        else:
            print(f"  ❌ Large file import failed: {response.status_code}")
            return False

    def cleanup_test_files(self):
        """Clean up temporary test files."""
        print("\n🧹 Cleaning up test files...")

        cleaned = 0
        for file_path in self.test_files:
            try:
                os.unlink(file_path)
                cleaned += 1
            except OSError:
                pass

        print(f"  ✅ Cleaned up {cleaned} test files")

    def run_all_tests(self):
        """Run the complete feed ingestion test suite."""
        print("🚀 Starting IOC Feed Ingestion Test Suite")
        print("=" * 50)

        # Login first
        if not self.login_as_admin():
            print("❌ Cannot proceed without authentication")
            return False

        try:
            # Run all tests
            tests = [
                self.test_csv_import,
                self.test_json_import,
                self.test_txt_import,
                self.test_duplicate_handling,
                self.test_invalid_file_handling,
                self.test_large_file_import,
            ]

            passed = 0
            for test in tests:
                if test():
                    passed += 1

            # Cleanup
            self.cleanup_test_files()

            print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")

            if passed == len(tests):
                print("✅ Feed Ingestion Test Suite Completed Successfully!")
                return True
            else:
                print("❌ Some tests failed. Please check the output above.")
                return False

        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            return False


def main():
    """Main test execution."""
    tester = FeedIngestionTester()

    print("🔍 Testing IOC Feed Ingestion functionality...")
    print(f"📡 API Base URL: {tester.base_url}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success = tester.run_all_tests()

    if success:
        print("\n🎉 All tests passed! Feed ingestion system is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the output above.")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
