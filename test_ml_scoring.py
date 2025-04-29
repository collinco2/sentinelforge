#!/usr/bin/env python3

import logging
from sentinelforge.ml.scoring_model import extract_features, predict_score
from sentinelforge.scoring import score_ioc, categorize
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("test_ml_scoring")

# Test data for various IOC types
test_iocs = [
    {
        "type": "ip",
        "value": "1.1.1.1",
        "feeds": ["dummy"],
        "enrichment": {
            "country": "United States",
            "asn": "13335",
            "org": "CLOUDFLARENET",
        },
        "summary": "Cloudflare DNS resolver",
    },
    {
        "type": "ip",
        "value": "185.159.128.61",
        "feeds": ["abusech"],
        "enrichment": {"country": "Russia", "asn": "58271"},
        "summary": "Malicious IP associated with malware distribution",
    },
    {
        "type": "domain",
        "value": "example.com",
        "feeds": ["dummy"],
        "enrichment": {"registrar": "ICANN", "creation_date": "1995-08-14"},
        "summary": "Example domain for documentation",
    },
    {
        "type": "domain",
        "value": "malicious-payload.xyz",
        "feeds": ["urlhaus", "abusech"],
        "enrichment": {"registrar": "NameCheap", "creation_date": "2023-01-15"},
        "summary": "Domain hosting malware payloads",
    },
    {
        "type": "url",
        "value": "https://example.com/about.html",
        "feeds": ["dummy"],
        "enrichment": {},
        "summary": "Example URL",
    },
    {
        "type": "url",
        "value": "https://malicious-payload.xyz/download.php?id=1234&payload=malware.exe",
        "feeds": ["urlhaus", "abusech"],
        "enrichment": {},
        "summary": "URL leading to malware download",
    },
    {
        "type": "hash",
        "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "feeds": ["dummy"],
        "enrichment": {},
        "summary": "SHA-256 hash of an empty file",
    },
    {
        "type": "hash",
        "value": "f5bc7fcc7f5b213e8a75b03353c1242c89829747398e9ba651a9d0e32d92321d",
        "feeds": ["abusech"],
        "enrichment": {},
        "summary": "SHA-256 hash of malware sample",
    },
]


def test_feature_extraction():
    """Test feature extraction for different IOC types."""
    print("\n=== Testing Feature Extraction ===")

    for ioc in test_iocs:
        print(f"\nExtracting features for {ioc['type']}: {ioc['value']}")
        features = extract_features(
            ioc_type=ioc["type"],
            source_feeds=ioc["feeds"],
            ioc_value=ioc["value"],
            enrichment_data=ioc["enrichment"],
            summary=ioc["summary"],
        )

        # Print key features based on IOC type
        type_feature = f"type_{ioc['type']}"
        print(f"  - {type_feature}: {features.get(type_feature)}")
        print(f"  - feed_count: {features.get('feed_count')}")

        if ioc["type"] == "ip":
            print(f"  - has_country: {features.get('has_country')}")
            print(f"  - country_high_risk: {features.get('country_high_risk')}")
        elif ioc["type"] == "domain":
            print(f"  - has_registrar: {features.get('has_registrar')}")
            print(f"  - has_creation_date: {features.get('has_creation_date')}")
        elif ioc["type"] == "url":
            print(f"  - url_length: {features.get('url_length')}")
            print(f"  - dot_count: {features.get('dot_count')}")
        elif ioc["type"] == "hash":
            print(f"  - hash_length: {features.get('hash_length')}")


def test_ml_prediction():
    """Test ML prediction directly with features."""
    print("\n=== Testing ML Prediction ===")

    results = []
    for ioc in test_iocs:
        features = extract_features(
            ioc_type=ioc["type"],
            source_feeds=ioc["feeds"],
            ioc_value=ioc["value"],
            enrichment_data=ioc["enrichment"],
            summary=ioc["summary"],
        )

        ml_score = predict_score(features)

        results.append(
            {
                "Type": ioc["type"],
                "Value": ioc["value"],
                "Feeds": ", ".join(ioc["feeds"]),
                "ML Score": f"{ml_score:.4f}",
            }
        )

    # Create a DataFrame for cleaner output
    df = pd.DataFrame(results)
    print(df)


def test_integrated_scoring():
    """Test integrated scoring (rules + ML)."""
    print("\n=== Testing Integrated Scoring ===")

    results = []
    for ioc in test_iocs:
        # Unpack the tuple returned by score_ioc
        final_score, explanation = score_ioc(
            ioc_value=ioc["value"],
            ioc_type=ioc["type"],
            source_feeds=ioc["feeds"],
            enrichment_data=ioc["enrichment"],
            summary=ioc["summary"],
        )

        category = categorize(final_score)

        results.append(
            {
                "Type": ioc["type"],
                "Value": ioc["value"],
                "Feeds": ", ".join(ioc["feeds"]),
                "Final Score": final_score,
                "Category": category,
            }
        )

    # Create a DataFrame for cleaner output
    df = pd.DataFrame(results)
    print(df)


if __name__ == "__main__":
    print("ML Scoring Test Script")
    print("=====================")

    test_feature_extraction()
    test_ml_prediction()
    test_integrated_scoring()

    print("\nTest completed successfully!")
