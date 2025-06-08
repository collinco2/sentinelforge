#!/usr/bin/env python3
"""
Debug script to test IOC ingestion validation
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ingestion import FeedIngestionService, IOCValidator
import tempfile
import csv


def test_ioc_validation():
    """Test IOC validation directly."""
    print("🔍 Testing IOC Validation...")

    validator = IOCValidator()

    # Test cases
    test_iocs = [
        {
            "ioc_type": "domain",
            "ioc_value": "malicious-test1.com",
            "source_feed": "Test CSV Feed",
            "severity": "high",
            "confidence": "85",
            "score": "7.5",
            "tags": "malware,test",
        },
        {
            "ioc_type": "ip",
            "ioc_value": "192.168.100.1",
            "source_feed": "Test CSV Feed",
            "severity": "medium",
            "confidence": "70",
            "score": "5.0",
            "tags": "botnet",
        },
        {
            "ioc_type": "hash",
            "ioc_value": "d41d8cd98f00b204e9800998ecf8427e",
            "source_feed": "Test CSV Feed",
            "severity": "critical",
            "confidence": "95",
            "score": "9.0",
            "tags": "ransomware,critical",
        },
    ]

    for i, raw_ioc in enumerate(test_iocs):
        print(f"\n--- Test IOC {i + 1} ---")
        print(f"Raw IOC: {raw_ioc}")

        # Normalize
        try:
            normalized = validator.normalize_ioc(raw_ioc)
            print(f"✅ Normalized: {normalized}")
        except Exception as e:
            print(f"❌ Normalization failed: {e}")
            continue

        # Validate
        try:
            is_valid, errors = validator.validate_ioc(normalized)
            print(f"Valid: {is_valid}")
            if errors:
                print(f"Errors: {errors}")
        except Exception as e:
            print(f"❌ Validation failed: {e}")


def test_csv_parsing():
    """Test CSV parsing directly."""
    print("\n🔍 Testing CSV Parsing...")

    service = FeedIngestionService()

    # Create test CSV content
    csv_content = """ioc_type,ioc_value,source_feed,severity,confidence,score,tags
domain,malicious-test1.com,Test CSV Feed,high,85,7.5,"malware,test"
ip,192.168.100.1,Test CSV Feed,medium,70,5.0,botnet
hash,d41d8cd98f00b204e9800998ecf8427e,Test CSV Feed,critical,95,9.0,"ransomware,critical"
"""

    try:
        raw_iocs = service.parser.parse_csv(csv_content)
        print(f"✅ Parsed {len(raw_iocs)} IOCs from CSV")
        for i, ioc in enumerate(raw_iocs):
            print(f"  IOC {i + 1}: {ioc}")
    except Exception as e:
        print(f"❌ CSV parsing failed: {e}")


def test_full_import():
    """Test full import process."""
    print("\n🔍 Testing Full Import Process...")

    service = FeedIngestionService()

    # Create test CSV file
    csv_content = """ioc_type,ioc_value,source_feed,severity,confidence,score,tags
domain,debug-test1.com,Debug Test Feed,high,85,7.5,"malware,test"
ip,10.10.10.10,Debug Test Feed,medium,70,5.0,botnet
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_file = f.name

    try:
        result = service.import_from_file(
            file_path=temp_file,
            source_feed="Debug Test Feed",
            user_id=1,
            justification="Debug testing",
        )

        print(f"✅ Import result: {result}")

    except Exception as e:
        print(f"❌ Import failed: {e}")
    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    print("🧪 IOC Ingestion Debug Tests")
    print("=" * 50)

    test_ioc_validation()
    test_csv_parsing()
    test_full_import()

    print("\n✅ Debug tests completed")
