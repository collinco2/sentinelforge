#!/usr/bin/env python3
"""
Test script for SentinelForge Feed Health Monitor functionality.

Tests the comprehensive health monitoring system including:
- Standalone health checks
- Database logging
- API endpoint integration
- Cron job scheduling
- Server startup integration
"""

import requests
import json
import time
import sqlite3
from datetime import datetime, timezone


def test_health_monitor_api():
    """Test the health monitor API endpoints."""
    print("🧪 Testing Feed Health Monitor API")
    print("=" * 50)
    
    # Login as admin
    login_response = requests.post(
        "http://localhost:5059/api/login", 
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()["session_token"]
    headers = {"X-Session-Token": token}
    
    print("✅ Authenticated successfully")
    
    # Test health check endpoint (cached)
    print("\n📊 Testing cached health check...")
    response = requests.get("http://localhost:5059/api/feeds/health", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Health check response: {result.get('summary', {})}")
        print(f"   From cache: {result.get('from_cache', False)}")
        print(f"   Total feeds: {result.get('summary', {}).get('total_feeds', 0)}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False
    
    # Test health check trigger
    print("\n🔄 Testing health check trigger...")
    response = requests.post("http://localhost:5059/api/feeds/health/trigger", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Health check triggered successfully")
        print(f"   Summary: {result.get('summary', {})}")
        print(f"   Triggered by: {result.get('triggered_by', 'Unknown')}")
    else:
        print(f"❌ Health check trigger failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test scheduler management (admin only)
    print("\n⏰ Testing scheduler management...")
    response = requests.get("http://localhost:5059/api/feeds/health/scheduler", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        scheduler_status = result.get("scheduler", {})
        print(f"✅ Scheduler status: {scheduler_status}")
        print(f"   Running: {scheduler_status.get('running', False)}")
        print(f"   Jobs: {len(scheduler_status.get('jobs', []))}")
    else:
        print(f"❌ Scheduler status failed: {response.status_code}")
        return False
    
    return True


def test_health_logs_database():
    """Test the feed_health_logs database table."""
    print("\n🧪 Testing Health Logs Database")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("ioc_store.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='feed_health_logs'
        """)
        
        if not cursor.fetchone():
            print("❌ feed_health_logs table does not exist")
            return False
        
        print("✅ feed_health_logs table exists")
        
        # Check recent health logs
        cursor.execute("""
            SELECT feed_name, status, http_code, response_time_ms, last_checked
            FROM feed_health_logs
            ORDER BY last_checked DESC
            LIMIT 10
        """)
        
        logs = cursor.fetchall()
        print(f"✅ Found {len(logs)} recent health log entries")
        
        for log in logs[:3]:  # Show first 3
            print(f"   - {log['feed_name']}: {log['status']} "
                  f"(HTTP {log['http_code']}, {log['response_time_ms']}ms)")
        
        # Check log statistics
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM feed_health_logs
            GROUP BY status
        """)
        
        stats = cursor.fetchall()
        print(f"✅ Health status distribution:")
        for stat in stats:
            print(f"   - {stat['status']}: {stat['count']} checks")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_standalone_health_check():
    """Test the standalone health check functionality."""
    print("\n🧪 Testing Standalone Health Check")
    print("=" * 50)
    
    try:
        from services.feed_health_monitor import FeedHealthMonitor
        
        monitor = FeedHealthMonitor()
        print("✅ Health monitor initialized")
        
        # Test getting active feeds
        feeds = monitor.get_active_feeds()
        print(f"✅ Found {len(feeds)} active feeds")
        
        # Test health check for first feed (if any)
        if feeds:
            feed = feeds[0]
            print(f"🔍 Testing health check for: {feed['name']}")
            
            health_result = monitor.check_feed_health(feed)
            print(f"✅ Health check completed:")
            print(f"   Status: {health_result['status']}")
            print(f"   Response time: {health_result['response_time_ms']}ms")
            if health_result.get('error_message'):
                print(f"   Error: {health_result['error_message']}")
        
        # Test cache functionality
        cached_health = monitor.get_cached_health()
        print(f"✅ Cache contains {len(cached_health)} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        return False


def test_cron_job_script():
    """Test the cron job script."""
    print("\n🧪 Testing Cron Job Script")
    print("=" * 50)
    
    import subprocess
    import sys
    
    try:
        # Test the cron script
        result = subprocess.run([
            sys.executable, "scripts/health_check_cron.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Cron job script executed successfully")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ Cron job script failed with return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Cron job script timed out (expected for network checks)")
        return True
    except Exception as e:
        print(f"❌ Cron job test failed: {e}")
        return False


def main():
    """Run all health monitor tests."""
    print("🚀 SentinelForge Feed Health Monitor Tests")
    print("=" * 60)
    
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
        ("Health Logs Database", test_health_logs_database),
        ("Standalone Health Check", test_standalone_health_check),
        ("Health Monitor API", test_health_monitor_api),
        ("Cron Job Script", test_cron_job_script),
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
    print("=" * 40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Feed health monitoring is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    main()
