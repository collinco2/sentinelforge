#!/usr/bin/env python3
"""
🧪 SentinelForge API Key System Test Suite

This script tests the complete API key management functionality including:
- User authentication via session tokens
- API key creation with various options
- API key listing and management
- API key rotation (regeneration)
- API key revocation (deletion)
- API key authentication for accessing protected endpoints

Usage:
    python3 test_api_key_system.py
"""

import requests
import json
import time
import sqlite3
from datetime import datetime


class SentinelForgeAPITester:
    def __init__(self, base_url="http://localhost:5059"):
        self.base_url = base_url
        self.session_token = None
        self.api_key = None
        
    def setup_test_session(self):
        """Create a test session directly in the database."""
        print("🔧 Setting up test session...")
        
        # Create a test session in the database
        conn = sqlite3.connect("ioc_store.db")
        cursor = conn.cursor()
        
        # Create session for admin user (user_id = 1)
        session_id = "test_session_" + str(int(time.time()))
        cursor.execute("""
            INSERT INTO user_sessions (session_id, user_id, expires_at) 
            VALUES (?, 1, datetime('now', '+1 day'))
        """, (session_id,))
        
        conn.commit()
        conn.close()
        
        self.session_token = session_id
        print(f"✅ Created test session: {session_id}")
        
    def test_list_empty_keys(self):
        """Test listing API keys when none exist."""
        print("\n📋 Testing: List empty API keys")
        
        response = requests.get(
            f"{self.base_url}/api/user/api-keys",
            headers={"X-Session-Token": self.session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["api_keys"] == []:
                print("✅ Empty API key list returned correctly")
                return True
            else:
                print(f"❌ Expected empty list, got: {data}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
    
    def test_create_api_key(self):
        """Test creating a new API key."""
        print("\n🔑 Testing: Create API key")
        
        payload = {
            "name": "Test API Key",
            "description": "Test key for automated testing",
            "access_scope": ["read", "write"],
            "rate_limit_tier": "standard"
        }
        
        response = requests.post(
            f"{self.base_url}/api/user/api-keys",
            headers={
                "Content-Type": "application/json",
                "X-Session-Token": self.session_token
            },
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            self.api_key = data["api_key"]
            self.key_id = data["key_id"]
            print(f"✅ API key created successfully")
            print(f"   Key ID: {data['key_id']}")
            print(f"   Preview: {data['key_preview']}")
            print(f"   Full key: {data['api_key'][:20]}...")
            return True
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
    
    def test_list_api_keys(self):
        """Test listing API keys after creation."""
        print("\n📋 Testing: List API keys")
        
        response = requests.get(
            f"{self.base_url}/api/user/api-keys",
            headers={"X-Session-Token": self.session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            if len(data["api_keys"]) == 1:
                key = data["api_keys"][0]
                print("✅ API key listed correctly")
                print(f"   Name: {key['name']}")
                print(f"   Preview: {key['key_preview']}")
                print(f"   Access Scope: {key['access_scope']}")
                print(f"   Created: {key['created_at']}")
                return True
            else:
                print(f"❌ Expected 1 key, got {len(data['api_keys'])}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
    
    def test_api_key_authentication(self):
        """Test using API key for authentication."""
        print("\n🔐 Testing: API key authentication")
        
        response = requests.get(
            f"{self.base_url}/api/user/api-keys",
            headers={"X-API-Key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API key authentication successful")
            
            # Check if last_used was updated
            key = data["api_keys"][0]
            if key["last_used"]:
                print(f"   Last used timestamp updated: {key['last_used']}")
            return True
        else:
            print(f"❌ API key authentication failed: {response.status_code} - {response.text}")
            return False
    
    def test_rotate_api_key(self):
        """Test rotating (regenerating) an API key."""
        print("\n🔄 Testing: API key rotation")
        
        old_key = self.api_key
        
        response = requests.post(
            f"{self.base_url}/api/user/api-keys/{self.key_id}/rotate",
            headers={"X-API-Key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.api_key = data["api_key"]
            print("✅ API key rotated successfully")
            print(f"   New preview: {data['key_preview']}")
            print(f"   New key: {data['api_key'][:20]}...")
            
            # Test that old key no longer works
            old_response = requests.get(
                f"{self.base_url}/api/user/api-keys",
                headers={"X-API-Key": old_key}
            )
            
            if old_response.status_code == 401:
                print("✅ Old API key correctly invalidated")
                
                # Test that new key works
                new_response = requests.get(
                    f"{self.base_url}/api/user/api-keys",
                    headers={"X-API-Key": self.api_key}
                )
                
                if new_response.status_code == 200:
                    print("✅ New API key works correctly")
                    return True
                else:
                    print("❌ New API key doesn't work")
                    return False
            else:
                print("❌ Old API key still works (should be invalid)")
                return False
        else:
            print(f"❌ Rotation failed: {response.status_code} - {response.text}")
            return False
    
    def test_revoke_api_key(self):
        """Test revoking (deleting) an API key."""
        print("\n🗑️  Testing: API key revocation")
        
        response = requests.delete(
            f"{self.base_url}/api/user/api-keys/{self.key_id}",
            headers={"X-API-Key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API key revoked successfully")
            
            # Test that revoked key no longer works
            test_response = requests.get(
                f"{self.base_url}/api/user/api-keys",
                headers={"X-API-Key": self.api_key}
            )
            
            if test_response.status_code == 401:
                print("✅ Revoked API key correctly invalidated")
                
                # Test that key list is empty again
                list_response = requests.get(
                    f"{self.base_url}/api/user/api-keys",
                    headers={"X-Session-Token": self.session_token}
                )
                
                if list_response.status_code == 200:
                    data = list_response.json()
                    if data["api_keys"] == []:
                        print("✅ API key list is empty after revocation")
                        return True
                    else:
                        print("❌ API key still appears in list")
                        return False
                else:
                    print("❌ Failed to list keys after revocation")
                    return False
            else:
                print("❌ Revoked API key still works")
                return False
        else:
            print(f"❌ Revocation failed: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 Starting SentinelForge API Key System Tests")
        print("=" * 60)
        
        tests = [
            ("Setup Test Session", self.setup_test_session),
            ("List Empty Keys", self.test_list_empty_keys),
            ("Create API Key", self.test_create_api_key),
            ("List API Keys", self.test_list_api_keys),
            ("API Key Authentication", self.test_api_key_authentication),
            ("Rotate API Key", self.test_rotate_api_key),
            ("Revoke API Key", self.test_revoke_api_key),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API key system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total


if __name__ == "__main__":
    tester = SentinelForgeAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
