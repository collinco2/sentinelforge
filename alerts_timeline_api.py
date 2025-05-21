#!/usr/bin/env python3
"""
Alerts Timeline API Server

This script starts a Flask API server that provides alerts timeline data
for the SentinelForge threat intelligence platform.

Usage:
    python alerts_timeline_api.py [--port PORT]

Options:
    --port PORT   Port to run the API server on (default: 5101)

Example:
    python alerts_timeline_api.py --port 5101
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import json
import os
import random
import time
import argparse

app = Flask(__name__)
CORS(app)

# Sample alerts data (will be populated on startup)
ALERTS = []


def generate_sample_alerts(num_alerts=200):
    """Generate sample alert data for testing the timeline endpoint."""
    alerts = []

    # Define possible severity levels
    severities = ["Low", "Medium", "High", "Critical"]

    # Generate alerts over the past 30 days
    now = time.time()

    # Create a realistic distribution with more alerts on certain days
    for i in range(num_alerts):
        # Generate a timestamp within the last 30 days
        # Use a distribution that makes some days have more alerts
        if random.random() < 0.3:  # 30% of alerts in the last 5 days
            days_ago = random.uniform(0, 5)
        elif random.random() < 0.6:  # 30% of alerts in the last 5-15 days
            days_ago = random.uniform(5, 15)
        else:  # 40% of alerts in the last 15-30 days
            days_ago = random.uniform(15, 30)

        timestamp = now - (days_ago * 24 * 60 * 60)
        formatted_time = datetime.datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Create more high/critical alerts on certain days for interesting patterns
        day_of_month = datetime.datetime.fromtimestamp(timestamp).day
        if day_of_month % 7 == 0:  # Create a weekly pattern
            severity = random.choice(["High", "Critical", "Critical"])
        elif day_of_month % 3 == 0:  # Another pattern every 3 days
            severity = random.choice(["High", "Medium", "Critical"])
        else:
            severity = random.choice(severities)

        alerts.append(
            {
                "id": f"AL{int(timestamp)}{random.randint(1000, 9999)}",
                "timestamp": timestamp,
                "formatted_time": formatted_time,
                "severity": severity,
            }
        )

    return alerts


@app.route("/api/alerts/timeline", methods=["GET"])
def get_alerts_timeline():
    """
    Get a timeline of alerts grouped by day or hour with severity breakdown.

    Query Parameters:
        start_date (float): Filter alerts after this timestamp (Unix timestamp)
        end_date (float): Filter alerts before this timestamp (Unix timestamp)
        group_by (str): Group by 'day' (default) or 'hour'

    Returns:
        JSON response with alerts grouped by date, including total count and severity breakdown.
    """
    print("[Timeline API] Received request for alerts timeline")

    # Parse query parameters
    start_date = request.args.get("start_date", None, type=float)
    end_date = request.args.get("end_date", None, type=float)
    group_by = request.args.get("group_by", "day")

    print(
        f"[Timeline API] Parameters: start_date={start_date}, end_date={end_date}, group_by={group_by}"
    )

    # Validate group_by parameter
    if group_by not in ["day", "hour"]:
        return jsonify(
            {
                "error": f"Invalid group_by parameter: {group_by}. Must be 'day' or 'hour'."
            }
        ), 400

    # Apply date filters
    filtered_alerts = ALERTS

    if start_date:
        filtered_alerts = [
            a for a in filtered_alerts if a.get("timestamp", 0) >= start_date
        ]

    if end_date:
        filtered_alerts = [
            a for a in filtered_alerts if a.get("timestamp", 0) <= end_date
        ]

    print(f"[Timeline API] Filtered to {len(filtered_alerts)} alerts")

    # Group alerts by date
    timeline = {}

    for alert in filtered_alerts:
        timestamp = alert.get("timestamp", 0)
        if timestamp == 0:
            continue

        # Convert timestamp to datetime
        dt = datetime.datetime.fromtimestamp(timestamp)

        # Format the date string according to grouping
        if group_by == "hour":
            # Format: YYYY-MM-DD HH:00:00
            date_key = dt.strftime("%Y-%m-%d %H:00:00")
        else:
            # Format: YYYY-MM-DD
            date_key = dt.strftime("%Y-%m-%d")

        # Initialize entry if it doesn't exist
        if date_key not in timeline:
            timeline[date_key] = {
                "date": date_key,
                "timestamp": int(timestamp)
                if group_by == "hour"
                else int(datetime.datetime(dt.year, dt.month, dt.day).timestamp()),
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            }

        # Increment counters
        timeline[date_key]["total"] += 1

        # Increment severity counter
        severity = alert.get("severity", "").lower()
        if severity in ["critical", "high", "medium", "low"]:
            timeline[date_key][severity] += 1

    # Convert dictionary to list and sort by date
    timeline_list = list(timeline.values())
    timeline_list.sort(key=lambda x: x["timestamp"])

    print(f"[Timeline API] Returning {len(timeline_list)} timeline entries")

    return jsonify(timeline_list)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the Alerts Timeline API server")
    parser.add_argument(
        "--port",
        type=int,
        default=5101,
        help="Port to run the API server on (default: 5101)",
    )
    args = parser.parse_args()

    # Generate sample alerts data
    ALERTS = generate_sample_alerts(200)
    print(f"Generated {len(ALERTS)} sample alerts for testing")

    # Start the server
    print(f"Starting Timeline API server on port {args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=True)
