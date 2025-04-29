#!/usr/bin/env python3
"""
Command-line tool to score an IOC and provide explanations using SHAP.
"""

import argparse
import json
from typing import Dict, Any, Optional

from sentinelforge.scoring import score_ioc_with_explanation


def parse_enrichment_data(data_str: Optional[str]) -> Dict[str, Any]:
    """Parse enrichment data from string to dictionary."""
    if not data_str:
        return {}

    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse enrichment data: {data_str}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Score an IOC and explain the result using SHAP"
    )

    parser.add_argument("value", help="The IOC value (e.g., domain, IP, URL, hash)")
    parser.add_argument(
        "type", choices=["ip", "domain", "url", "hash"], help="Type of IOC"
    )
    parser.add_argument(
        "--feeds",
        "-f",
        nargs="+",
        default=["dummy"],
        help="Source feeds (space separated)",
    )
    parser.add_argument("--enrichment", "-e", help="Enrichment data as JSON string")
    parser.add_argument("--summary", "-s", default="", help="Optional IOC summary")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output"
    )

    args = parser.parse_args()

    # Parse enrichment data
    enrichment_data = parse_enrichment_data(args.enrichment)

    # Score the IOC with explanation
    score, explanation_text, explanation_data = score_ioc_with_explanation(
        ioc_value=args.value,
        ioc_type=args.type,
        source_feeds=args.feeds,
        enrichment_data=enrichment_data,
        summary=args.summary,
    )

    # Print results
    print("\n===== IOC Scoring Result =====")
    print(f"IOC: {args.value} ({args.type})")
    print(f"Source Feeds: {', '.join(args.feeds)}")
    if args.summary:
        print(f"Summary: {args.summary}")
    print(f"\nFinal Score: {score}")

    # Print explanation
    print("\n===== Explanation =====")
    print(explanation_text)

    # Show plot path if available
    if explanation_data and "plot_path" in explanation_data:
        print(f"\nSHAP visualization saved to: {explanation_data['plot_path']}")

    # Print verbose data if requested
    if args.verbose and explanation_data:
        print("\n===== Detailed Explanation Data =====")

        if "rule_explanation" in explanation_data:
            print("\nRule-based scoring:")
            for rule in explanation_data["rule_explanation"]:
                print(f"  - {rule}")

        if "top_features" in explanation_data:
            print("\nTop 5 influential features:")
            for name, value in explanation_data["top_features"]:
                print(f"  - {name}: {value:.4f}")

        if "base_value" in explanation_data:
            print(f"\nModel base value: {explanation_data['base_value']:.4f}")


if __name__ == "__main__":
    main()
