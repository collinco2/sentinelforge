#!/usr/bin/env python3
"""
Test script for enhanced Slack notifications with explainability.

This script simulates a high-severity IOC detection and sends a notification
with detailed explanations using the enhanced SHAP explainer implementation.
"""

import logging
import sys
from typing import Dict, Any, Tuple, Optional, Union, List
import argparse
import datetime
import traceback
import re
import json
import signal
import time
from functools import lru_cache

# Import necessary modules
from sentinelforge.settings import settings
from sentinelforge.scoring import score_ioc
from sentinelforge.notifications.slack_notifier import send_high_severity_alert
from sentinelforge.enrichment.whois_geoip import WhoisGeoIPEnricher

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set a timeout for potentially slow operations
OPERATION_TIMEOUT = 30  # seconds

# Define valid IOC types and patterns for validation
VALID_IOC_TYPES = {"ip", "domain", "url", "hash", "email"}
IOC_PATTERNS = {
    "ip": re.compile(r"^(\d{1,3}\.){3}\d{1,3}$"),
    "domain": re.compile(
        r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    ),
    "url": re.compile(r"^https?://"),
    "hash": re.compile(r"^[a-fA-F0-9]{32,64}$"),
    "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
}

# Cache for enrichment data and explanations
enrichment_cache = {}
explanation_cache = {}


def timeout_handler(signum, frame):
    """Handle timeout for long-running operations."""
    raise TimeoutError("Operation timed out")


def validate_ioc(ioc_type: str, ioc_value: str) -> Tuple[bool, str]:
    """
    Validate IOC type and value for format and security issues.

    Args:
        ioc_type: The type of indicator
        ioc_value: The indicator value

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check IOC type
    if ioc_type not in VALID_IOC_TYPES:
        return (
            False,
            f"Invalid IOC type: {ioc_type}. Must be one of: {', '.join(VALID_IOC_TYPES)}",
        )

    # Check if IOC value is empty
    if not ioc_value or not ioc_value.strip():
        return False, "IOC value cannot be empty"

    # Check length - prevent excessive values that could cause memory issues
    if len(ioc_value) > 2048:
        return (
            False,
            f"IOC value too long ({len(ioc_value)} chars). Maximum is 2048 characters.",
        )

    # Check pattern based on type
    if ioc_type in IOC_PATTERNS and not IOC_PATTERNS[ioc_type].search(ioc_value):
        return False, f"IOC value doesn't match expected pattern for type '{ioc_type}'"

    # Check for potentially harmful characters
    if re.search(r'[<>"\'%;)(&+]', ioc_value):
        return False, "IOC value contains potentially harmful characters"

    return True, ""


@lru_cache(maxsize=128)
def get_test_enrichment_data(ioc_type: str, ioc_value: str) -> Dict[str, Any]:
    """
    Get enrichment data for a test IOC, either from the enricher or mock data.
    Results are cached to improve performance for repeated calls.
    """
    # Check cache first (belt and suspenders with lru_cache)
    cache_key = f"{ioc_type}:{ioc_value}"
    if cache_key in enrichment_cache:
        logger.debug(f"Using cached enrichment data for {cache_key}")
        return enrichment_cache[cache_key]

    try:
        # Set timeout for enrichment operations
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(OPERATION_TIMEOUT)

        if settings.geoip_db_path:
            enricher = WhoisGeoIPEnricher(str(settings.geoip_db_path))
            result = dict(enricher.enrich({"type": ioc_type, "value": ioc_value}) or {})

            # Reset alarm
            signal.alarm(0)

            if result:
                # Store in cache
                enrichment_cache[cache_key] = result
                return result
        else:
            logger.warning("GeoIP database not configured, using mock data")
    except TimeoutError:
        logger.error(f"Enrichment operation timed out for {ioc_type}:{ioc_value}")
        signal.alarm(0)  # Reset alarm
    except Exception as e:
        logger.error(f"Error initializing or using enricher: {e}")
        signal.alarm(0)  # Reset alarm

    # Return mock data if enrichment fails or is not available
    mock_data = {}

    if ioc_type == "ip":
        mock_data = {
            "country": "United States",
            "city": "Mountain View",
            "organization": "Google LLC",
            "asn": "AS15169",
        }
    elif ioc_type == "domain":
        mock_data = {
            "registrar": "NameCheap, Inc.",
            "creation_date": datetime.datetime(2020, 3, 15),
            "expiration_date": datetime.datetime(2025, 3, 15),
            "country": "United States",
        }
    elif ioc_type == "url":
        mock_data = {
            "domain": "example.com",
            "path": "/malware",
            "query_params": "id=12345",
        }
    elif ioc_type == "hash":
        mock_data = {"algorithm": "SHA-256", "file_type": "PE Executable"}

    # Store in cache
    enrichment_cache[cache_key] = mock_data
    return mock_data


def generate_explanation(
    score: int, ioc_type: str, enrichment_data: Dict[str, Any]
) -> str:
    """Generate a simplified explanation text based on score and enrichment data."""
    # Create a safer copy of enrichment data to avoid potential memory issues
    safe_enrichment = {}

    # Process datetime objects to strings and limit data size
    for key, value in enrichment_data.items():
        if isinstance(value, datetime.datetime):
            safe_enrichment[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, (str, int, float, bool)) and len(str(value)) < 1000:
            safe_enrichment[key] = value
        elif isinstance(value, (list, dict)):
            # For complex objects, convert to string but limit size
            str_val = str(value)
            if len(str_val) > 1000:
                str_val = str_val[:997] + "..."
            safe_enrichment[key] = str_val

    explanation = f"The indicator received a severity score of {score}.\n\n"

    if score >= 75:
        explanation += "HIGH SEVERITY: This indicator shows strong evidence of malicious behavior.\n"
    elif score >= 50:
        explanation += (
            "MEDIUM SEVERITY: This indicator shows some suspicious characteristics.\n"
        )
    else:
        explanation += "LOW SEVERITY: This indicator shows limited evidence of malicious behavior.\n"

    # Add enrichment data to explanation
    explanation += "\nIndicator details:\n"
    for key, value in safe_enrichment.items():
        explanation += f"- {key}: {value}\n"

    # Add contextual insights based on IOC type
    explanation += "\nContextual insights:\n"
    if ioc_type == "domain":
        if "creation_date" in safe_enrichment and "expiration_date" in safe_enrichment:
            try:
                creation = datetime.datetime.strptime(
                    safe_enrichment["creation_date"], "%Y-%m-%d %H:%M:%S"
                )
                now = datetime.datetime.now()
                age_days = (now - creation).days
                if age_days < 30:
                    explanation += (
                        f"- Recently registered domain ({age_days} days old)\n"
                    )
                else:
                    explanation += f"- Domain age: {age_days} days\n"
            except Exception:
                pass
    elif ioc_type == "ip":
        if "country" in safe_enrichment:
            explanation += f"- Geolocation: {safe_enrichment['country']}\n"

    return explanation


def test_explanation(
    ioc_value: str,
    ioc_type: str,
    source_feeds: List[str],
    score_override: Optional[int] = None,
) -> Tuple[int, str]:
    """Test the enhanced explanation generation for an IOC."""
    start_time = time.time()

    try:
        # Validate inputs first
        is_valid, error_message = validate_ioc(ioc_type, ioc_value)
        if not is_valid:
            logger.error(f"Invalid IOC: {error_message}")
            return 0, f"Error: {error_message}"

        logger.info(f"Testing explanation for {ioc_type}:{ioc_value}")

        # Check cache for existing explanation
        cache_key = (
            f"{ioc_type}:{ioc_value}:{'-'.join(sorted(source_feeds))}:{score_override}"
        )
        if cache_key in explanation_cache:
            logger.info(f"Using cached explanation for {ioc_type}:{ioc_value}")
            cached_result = explanation_cache[cache_key]
            return cached_result[0], cached_result[1]

        # Set timeout for potentially slow operations
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(OPERATION_TIMEOUT)

        # Get enrichment data
        enrichment_data = get_test_enrichment_data(ioc_type, ioc_value)
        logger.info(f"Enrichment data: {enrichment_data}")

        # Get score using the scoring module
        try:
            score, _ = score_ioc(ioc_value, ioc_type, source_feeds)
        except Exception as scoring_error:
            logger.error(f"Error in scoring: {str(scoring_error)}")
            score = 0

        # Reset timeout alarm
        signal.alarm(0)

        # Override score if requested (for testing high severity notifications)
        if score_override is not None:
            score = score_override

        # Generate explanation text
        text_explanation = generate_explanation(score, ioc_type, enrichment_data)

        # Print explanation details
        logger.info(f"Score: {score}")
        logger.info(f"Explanation:\n{text_explanation}")

        # Check if we should send a Slack notification (for scores over 75 or with override)
        if score >= 75 or score_override is not None:
            logger.info("Sending Slack notification for high-severity IOC")

            # Create a dashboard link (example URL)
            dashboard_url = f"http://localhost:5050/ioc/{ioc_type}/{ioc_value}"

            # Send the notification with timeout
            try:
                signal.alarm(OPERATION_TIMEOUT)
                send_high_severity_alert(
                    ioc_value=ioc_value,
                    ioc_type=ioc_type,
                    score=score,
                    link=dashboard_url,
                    explanation=text_explanation,
                )
                signal.alarm(0)
                logger.info("Slack notification sent")
            except TimeoutError:
                signal.alarm(0)
                logger.error("Slack notification timed out")
            except Exception as e:
                signal.alarm(0)
                logger.error(f"Failed to send Slack notification: {e}")
        else:
            logger.info(f"Score {score} below threshold, not sending notification")

        # Cache the result
        explanation_cache[cache_key] = (score, text_explanation)

        # Log performance metrics
        execution_time = time.time() - start_time
        logger.info(f"Explanation generation completed in {execution_time:.2f} seconds")

        return score, text_explanation
    except TimeoutError:
        signal.alarm(0)  # Reset alarm
        logger.error(f"Operation timed out for {ioc_type}:{ioc_value}")
        return 0, "Error: Operation timed out"
    except Exception as e:
        signal.alarm(0)  # Reset alarm
        logger.error(f"Error in test_explanation: {traceback.format_exc()}")
        return 0, f"Error: {str(e)}"


def batch_test(
    ioc_list: List[Dict[str, Union[str, List[str], int]]],
    output_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Test multiple IOCs in batch mode.

    Args:
        ioc_list: List of dictionaries with ioc_value, ioc_type, source_feeds, and optional score_override
        output_file: Optional file path to save results as JSON

    Returns:
        List of result dictionaries
    """
    results = []

    for i, ioc_data in enumerate(ioc_list):
        logger.info(f"Processing batch item {i + 1}/{len(ioc_list)}")

        try:
            # Extract parameters from the dictionary
            ioc_value = ioc_data.get("ioc_value", "")
            ioc_type = ioc_data.get("ioc_type", "")
            source_feeds = ioc_data.get("source_feeds", [])
            score_override = ioc_data.get("score_override")

            # Test the IOC
            score, explanation = test_explanation(
                ioc_value, ioc_type, source_feeds, score_override
            )

            # Add result
            result = {
                "ioc_value": ioc_value,
                "ioc_type": ioc_type,
                "source_feeds": source_feeds,
                "score": score,
                "explanation": explanation,
                "timestamp": datetime.datetime.now().isoformat(),
            }
            results.append(result)

        except Exception as e:
            logger.error(f"Error processing batch item: {e}")
            results.append(
                {"ioc_value": ioc_data.get("ioc_value", "unknown"), "error": str(e)}
            )

    # Save to file if requested
    if output_file:
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Batch results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save batch results: {e}")

    return results


def main():
    """Main function to run the test script."""
    try:
        # Declare global variables first
        global OPERATION_TIMEOUT

        parser = argparse.ArgumentParser(description="Test enhanced IOC explanations")
        parser.add_argument("--ioc", help="IOC value to test", default="example.com")
        parser.add_argument(
            "--type", help="IOC type", default="domain", choices=list(VALID_IOC_TYPES)
        )
        parser.add_argument(
            "--feeds", help="Source feeds (comma-separated)", default="urlhaus,abusech"
        )
        parser.add_argument("--score", help="Override score for testing", type=int)
        parser.add_argument(
            "--batch", help="Path to JSON file with batch of IOCs to test"
        )
        parser.add_argument("--output", help="Path to save results (for batch mode)")
        parser.add_argument(
            "--timeout",
            help="Operation timeout in seconds",
            type=int,
            default=OPERATION_TIMEOUT,
        )
        parser.add_argument("--debug", help="Enable debug logging", action="store_true")
        args = parser.parse_args()

        # Set custom timeout if specified
        OPERATION_TIMEOUT = args.timeout

        # Set debug logging if requested
        if args.debug:
            logger.setLevel(logging.DEBUG)
            # Set root logger to debug as well
            logging.getLogger().setLevel(logging.DEBUG)

        # Check for batch mode
        if args.batch:
            try:
                with open(args.batch, "r") as f:
                    ioc_list = json.load(f)
                batch_test(ioc_list, args.output)
            except Exception as e:
                logger.error(f"Failed to process batch file: {e}")
                return 1
        else:
            # Split feeds by comma
            feeds = [f.strip() for f in args.feeds.split(",")]

            # Run the test
            test_explanation(args.ioc, args.type, feeds, args.score)

        return 0
    except Exception:
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
