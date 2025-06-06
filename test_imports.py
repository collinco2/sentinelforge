#!/usr/bin/env python3
"""
Test script to verify import paths work correctly in CI environment.
"""

import sys
import os

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

# Test different import strategies
print("\n=== Testing Import Strategies ===")

# Strategy 1: Direct import
try:
    import sentinelforge

    print("✓ Direct import of sentinelforge successful")
    print("  sentinelforge location:", sentinelforge.__file__)
except ImportError as e:
    print("✗ Direct import failed:", e)

# Strategy 2: Import from nested directory
try:
    sys.path.insert(0, "sentinelforge")
    import sentinelforge as sf_nested

    print("✓ Nested import of sentinelforge successful")
    print("  sentinelforge location:", sf_nested.__file__)
except ImportError as e:
    print("✗ Nested import failed:", e)

# Strategy 3: Test specific modules
try:
    from sentinelforge.ml.scoring_model import extract_features

    print("✓ ML module import successful")
except ImportError as e:
    print("✗ ML module import failed:", e)
    try:
        sys.path.insert(0, "sentinelforge")
        from ml.scoring_model import extract_features

        print("✓ ML module import successful (nested path)")
    except ImportError as e2:
        print("✗ ML module import failed (nested path):", e2)

try:
    from sentinelforge.notifications.slack_notifier import send_high_severity_alert

    print("✓ Notifications module import successful")
except ImportError as e:
    print("✗ Notifications module import failed:", e)
    try:
        sys.path.insert(0, "sentinelforge")
        from notifications.slack_notifier import send_high_severity_alert

        print("✓ Notifications module import successful (nested path)")
    except ImportError as e2:
        print("✗ Notifications module import failed (nested path):", e2)

print("\n=== Directory Structure ===")
print("Root directory contents:")
for item in sorted(os.listdir(".")):
    if not item.startswith("."):
        print(f"  {item}")

if os.path.exists("sentinelforge"):
    print("\nsentinelforge directory contents:")
    for item in sorted(os.listdir("sentinelforge")):
        if not item.startswith("."):
            print(f"  {item}")
