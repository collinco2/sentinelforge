#!/usr/bin/env python3
"""
Debug script to test the upload endpoint directly
"""

import requests
import tempfile
import csv
import json


def test_upload_endpoint():
    """Test the upload endpoint with a simple file."""
    print("🔍 Testing Upload Endpoint...")

    # Login first
    session = requests.Session()
    login_data = {"username": "admin", "password": "admin123"}

    response = session.post("http://localhost:5059/api/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False

    data = response.json()
    session_token = data.get("session_token")
    session.headers.update({"X-Session-Token": session_token})
    print("✅ Logged in successfully")

    # Create a simple test CSV
    csv_content = """ioc_type,ioc_value,source_feed,severity,confidence
domain,debug-upload-test.com,Debug Upload Test,high,85
ip,10.20.30.40,Debug Upload Test,medium,70
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_file = f.name

    try:
        # Test upload
        with open(temp_file, "rb") as f:
            files = {"file": ("debug_test.csv", f, "text/csv")}
            data = {
                "source_feed": "Debug Upload Test",
                "justification": "Testing upload endpoint",
            }

            print("📤 Uploading file...")
            response = session.post(
                "http://localhost:5059/api/feeds/upload", files=files, data=data
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content: {response.text}")

            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"  Imported: {result.get('imported_count', 0)}")
                print(f"  Skipped: {result.get('skipped_count', 0)}")
                print(f"  Errors: {result.get('error_count', 0)}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return False
    finally:
        import os

        os.unlink(temp_file)


if __name__ == "__main__":
    print("🧪 Upload Endpoint Debug Test")
    print("=" * 40)

    success = test_upload_endpoint()

    if success:
        print("\n✅ Upload endpoint working correctly")
    else:
        print("\n❌ Upload endpoint has issues")
