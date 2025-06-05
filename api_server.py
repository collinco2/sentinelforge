#!/usr/bin/env python3
from flask import Flask, jsonify, request, redirect, url_for, Blueprint, g
from flask_cors import CORS
import os
import sqlite3
import time
import re
import random
import datetime
from auth import require_role, require_authentication, UserRole

app = Flask(__name__)
# Enable CORS for all routes and all origins
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "OPTIONS"],
        }
    },
)

# Define global IOCS list to store IOC data
IOCS = []

# Define global ALERTS list to store Alert data
ALERTS = []

# Create a Blueprint for IOC-related routes
ioc_bp = Blueprint("ioc", __name__)


def infer_ioc_type(ioc_value):
    """Infer the IOC type based on pattern."""
    if not isinstance(ioc_value, str):
        return "unknown"

    if re.match(r"^https?://", ioc_value):
        return "url"
    elif re.match(r"^[a-fA-F0-9]{32,64}$", ioc_value):
        return "hash"
    elif re.match(
        r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$",
        ioc_value,
    ):
        return "domain"
    elif re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ioc_value):
        return "ip"
    elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", ioc_value):
        return "email"
    else:
        return "unknown"


def get_db_connection():
    """Get a database connection with proper row factory."""
    db_path = "/Users/Collins/sentinelforge/ioc_store.db"
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")

    try:
        conn = sqlite3.connect(db_path)

        # Custom row factory to avoid "tuple indices must be integers or slices, not str" error
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                if col[0]:  # Ensure column name exists
                    d[col[0]] = row[idx]
                    # For the 'ioc_value' field, also create a 'value' alias
                    if col[0] == "ioc_value":
                        d["value"] = row[idx]
            return d

        conn.row_factory = dict_factory
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@ioc_bp.route("/api/stats")
def get_stats():
    """Get statistics about IOCs."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Total IOCs
            cursor.execute("SELECT COUNT(*) as count FROM iocs")
            result = cursor.fetchone()
            total_iocs = result["count"] if result and "count" in result else 0

            # High risk IOCs (score > 7.5)
            cursor.execute("SELECT COUNT(*) as count FROM iocs WHERE score > 7.5")
            result = cursor.fetchone()
            high_risk = result["count"] if result and "count" in result else 0

            # New IOCs (last 7 days)
            one_week_ago = time.time() - (7 * 24 * 60 * 60)
            cursor.execute(
                "SELECT COUNT(*) as count FROM iocs WHERE first_seen_timestamp > ?",
                (one_week_ago,),
            )
            result = cursor.fetchone()
            new_iocs = result["count"] if result and "count" in result else 0

            # Avg score
            cursor.execute("SELECT AVG(score) as avg_score FROM iocs")
            result = cursor.fetchone()
            avg_score = result["avg_score"] if result and "avg_score" in result else 0

            # Type distribution
            cursor.execute(
                "SELECT ioc_type, COUNT(*) as count FROM iocs GROUP BY ioc_type"
            )
            type_dist = {}
            for row in cursor.fetchall():
                if "ioc_type" in row and "count" in row:
                    type_dist[row["ioc_type"]] = row["count"]

            # Category distribution
            cursor.execute("""
                SELECT
                    CASE
                        WHEN score > 7.5 THEN 'high'
                        WHEN score > 5 THEN 'medium'
                        ELSE 'low'
                    END as category,
                    COUNT(*) as count
                FROM iocs
                GROUP BY category
            """)
            category_dist = {}
            for row in cursor.fetchall():
                if "category" in row and "count" in row:
                    category_dist[row["category"]] = row["count"]

            conn.close()

            return jsonify(
                {
                    "total_iocs": total_iocs,
                    "high_risk_iocs": high_risk,
                    "new_iocs": new_iocs,
                    "avg_score": avg_score,
                    "type_distribution": type_dist,
                    "category_distribution": category_dist,
                }
            )
    except Exception as e:
        print(f"Error getting stats: {e}")

    # Return fallback stats if database access fails
    print("Returning fallback stats")
    return jsonify(
        {
            "total_iocs": 1968,
            "high_risk_iocs": 124,
            "new_iocs": 47,
            "avg_score": 7.4,
            "type_distribution": {"ip": 843, "domain": 562, "url": 425, "hash": 138},
            "category_distribution": {"high": 124, "medium": 764, "low": 1080},
        }
    )


@ioc_bp.route("/api/iocs")
def get_iocs():
    """Get a list of IOCs."""
    # Parse query parameters
    limit = request.args.get("limit", 10, type=int)
    offset = request.args.get("offset", 0, type=int)
    min_score = request.args.get("min_score", 0, type=float)
    max_score = request.args.get("max_score", 10, type=float)
    ioc_type = request.args.get("ioc_type", None)
    search = request.args.get("search", None)

    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Build query with parameters
            query = "SELECT * FROM iocs WHERE score BETWEEN ? AND ?"
            params = [min_score, max_score]

            if ioc_type:
                query += " AND ioc_type = ?"
                params.append(ioc_type)

            if search:
                query += " AND (ioc_value LIKE ? OR tags LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])

            # Add ordering and pagination
            query += " ORDER BY score DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # Execute query and fetch results
            cursor.execute(query, params)
            iocs = []
            for row in cursor.fetchall():
                ioc = dict(row)

                # Add ML fields
                ioc["threat_class"] = get_ml_threat_class(
                    ioc.get("ioc_value", ""), ioc.get("ioc_type", "unknown")
                )
                ioc["malicious_probability"] = get_ml_probability(ioc.get("score", 0))
                ioc["feature_importance"] = get_feature_importance(
                    ioc.get("ioc_type", "unknown")
                )
                ioc["similar_known_threats"] = get_similar_threats(
                    ioc.get("ioc_type", "unknown")
                )
                ioc["attack_techniques"] = get_attack_techniques(
                    ioc.get("ioc_type", "unknown")
                )

                iocs.append(ioc)

            # Get total count for pagination
            cursor.execute(
                "SELECT COUNT(*) as count FROM iocs WHERE score BETWEEN ? AND ?",
                [min_score, max_score],
            )
            result = cursor.fetchone()
            total = result.get("count", 0) if result else 0

            conn.close()

            # Update the global IOCS list with the fetched data
            IOCS.clear()
            IOCS.extend(iocs)

            return jsonify({"iocs": iocs, "total": total})
    except Exception as e:
        print(f"Database connection error: {e}")

    # Return fallback IOC list if database access fails
    print("Returning fallback IOCs")
    fallback_iocs = [
        # DOMAINS
        {
            "id": 1,
            "ioc_type": "domain",
            "ioc_value": "example.com",
            "value": "example.com",
            "score": 9.0,
            "category": "high",
            "first_seen": "2023-05-15 12:34:56",
            "last_seen": "2023-06-15 10:22:43",
            "source_feed": "dummy",
        },
        {
            "id": 2,
            "ioc_type": "domain",
            "ioc_value": "malicious-domain.com",
            "value": "malicious-domain.com",
            "score": 8.5,
            "category": "high",
            "first_seen": "2023-06-01 10:15:22",
            "last_seen": "2023-06-20 14:27:33",
            "source_feed": "AlienVault",
        },
        {
            "id": 3,
            "ioc_type": "domain",
            "ioc_value": "suspicious-domain.org",
            "value": "suspicious-domain.org",
            "score": 6.2,
            "category": "medium",
            "first_seen": "2023-05-10 08:25:14",
            "last_seen": "2023-06-12 17:38:29",
            "source_feed": "IBM X-Force",
        },
        {
            "id": 4,
            "ioc_type": "domain",
            "ioc_value": "fake-login.net",
            "value": "fake-login.net",
            "score": 7.8,
            "category": "high",
            "first_seen": "2023-05-18 11:42:16",
            "last_seen": "2023-06-17 19:33:28",
            "source_feed": "Mandiant",
        },
        {
            "id": 5,
            "ioc_type": "domain",
            "ioc_value": "credential-harvester.com",
            "value": "credential-harvester.com",
            "score": 9.1,
            "category": "critical",
            "first_seen": "2023-06-07 12:48:36",
            "last_seen": "2023-06-22 13:57:22",
            "source_feed": "AlienVault",
        },
        # IPs
        {
            "id": 6,
            "ioc_type": "ip",
            "ioc_value": "1.1.1.1",
            "value": "1.1.1.1",
            "score": 7.2,
            "category": "medium",
            "first_seen": "2023-05-14 08:22:33",
            "last_seen": "2023-06-14 15:44:12",
            "source_feed": "test_feed",
        },
        {
            "id": 7,
            "ioc_type": "ip",
            "ioc_value": "192.168.1.10",
            "value": "192.168.1.10",
            "score": 6.8,
            "category": "medium",
            "first_seen": "2023-05-25 09:30:11",
            "last_seen": "2023-06-18 16:42:53",
            "source_feed": "Recorded Future",
        },
        {
            "id": 8,
            "ioc_type": "ip",
            "ioc_value": "10.0.0.1",
            "value": "10.0.0.1",
            "score": 5.4,
            "category": "medium",
            "first_seen": "2023-05-20 16:28:42",
            "last_seen": "2023-06-15 08:49:37",
            "source_feed": "Crowdstrike",
        },
        {
            "id": 9,
            "ioc_type": "ip",
            "ioc_value": "172.16.254.1",
            "value": "172.16.254.1",
            "score": 4.8,
            "category": "low",
            "first_seen": "2023-05-12 14:56:32",
            "last_seen": "2023-06-10 11:28:47",
            "source_feed": "ThreatConnect",
        },
        {
            "id": 10,
            "ioc_type": "ip",
            "ioc_value": "192.0.2.1",
            "value": "192.0.2.1",
            "score": 3.5,
            "category": "low",
            "first_seen": "2023-05-08 11:22:47",
            "last_seen": "2023-06-08 09:16:33",
            "source_feed": "Anomali",
        },
        # URLs
        {
            "id": 11,
            "ioc_type": "url",
            "ioc_value": "https://malicious-site.com/download.exe",
            "value": "https://malicious-site.com/download.exe",
            "score": 9.2,
            "category": "critical",
            "first_seen": "2023-06-10 08:12:45",
            "last_seen": "2023-06-22 11:35:28",
            "source_feed": "URLhaus",
        },
        {
            "id": 12,
            "ioc_type": "url",
            "ioc_value": "https://fake-login.com/portal/signin.php",
            "value": "https://fake-login.com/portal/signin.php",
            "score": 8.6,
            "category": "critical",
            "first_seen": "2023-06-08 09:15:38",
            "last_seen": "2023-06-21 14:22:56",
            "source_feed": "PhishTank",
        },
        {
            "id": 13,
            "ioc_type": "url",
            "ioc_value": "http://compromised-cdn.net/jquery.min.js",
            "value": "http://compromised-cdn.net/jquery.min.js",
            "score": 7.2,
            "category": "high",
            "first_seen": "2023-06-02 10:18:33",
            "last_seen": "2023-06-18 15:46:58",
            "source_feed": "Symantec",
        },
        # Hashes
        {
            "id": 14,
            "ioc_type": "hash",
            "ioc_value": "5241acbddc07ce49cca44076264344717b30a303acb825075471e83468c5585",
            "value": "5241acbddc07ce49cca44076264344717b30a303acb825075471e83468c5585",
            "score": 8.9,
            "category": "critical",
            "first_seen": "2023-06-05 14:22:36",
            "last_seen": "2023-06-21 09:18:57",
            "source_feed": "VirusTotal",
        },
        {
            "id": 15,
            "ioc_type": "hash",
            "ioc_value": "840c40763110c1f6564bc2b61dcdf7ce77ce0016211385a5ac49cc5ea8b011d2",
            "value": "840c40763110c1f6564bc2b61dcdf7ce77ce0016211385a5ac49cc5ea8b011d2",
            "score": 7.9,
            "category": "high",
            "first_seen": "2023-05-28 12:37:46",
            "last_seen": "2023-06-19 10:48:23",
            "source_feed": "Kaspersky",
        },
        {
            "id": 16,
            "ioc_type": "hash",
            "ioc_value": "685b4307728abd92415c2d9c001761cfa0481b29689b35106f7a5ee1d1117c8a",
            "value": "685b4307728abd92415c2d9c001761cfa0481b29689b35106f7a5ee1d1117c8a",
            "score": 6.5,
            "category": "medium",
            "first_seen": "2023-05-15 09:38:22",
            "last_seen": "2023-06-14 16:27:44",
            "source_feed": "Malwarebytes",
        },
    ]

    # Add ML fields to each IOC
    for ioc in fallback_iocs:
        ioc_type = ioc.get("ioc_type", "")
        ioc_value = ioc.get("ioc_value", "")
        score = ioc.get("score", 0)

        ioc["threat_class"] = get_ml_threat_class(ioc_value, ioc_type)
        ioc["malicious_probability"] = get_ml_probability(score)
        ioc["feature_importance"] = get_feature_importance(ioc_type)
        ioc["similar_known_threats"] = get_similar_threats(ioc_type)
        ioc["attack_techniques"] = get_attack_techniques(ioc_type)

    # Update the global IOCS list with the fallback data
    IOCS.clear()
    IOCS.extend(fallback_iocs)

    return jsonify({"iocs": fallback_iocs, "total": len(fallback_iocs)})


def get_ioc_by_value(ioc_value):
    """
    Look up an IOC by its value using case-insensitive matching from database.

    Args:
        ioc_value (str): The IOC value to look up

    Returns:
        dict or None: The IOC object if found, or None if not found
    """
    print("[API] Searching for IOC case-insensitively in database")
    ioc_value_lower = ioc_value.lower()
    print(f"[API] Lowercase search value: '{ioc_value_lower}'")

    try:
        # Try accessing the database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Search for IOC using case-insensitive matching
            cursor.execute(
                "SELECT * FROM iocs WHERE LOWER(ioc_value) = ? LIMIT 1",
                (ioc_value_lower,),
            )

            row = cursor.fetchone()
            if row:
                ioc = dict(row)
                print(
                    f"[API] Found matching IOC in database: {ioc.get('ioc_value', '')}"
                )
                conn.close()
                return ioc

            conn.close()
            print(f"[API] No matching IOC found in database for {ioc_value}")
            return None

    except Exception as e:
        print(f"[API] Database error in get_ioc_by_value: {e}")

    # Fallback to in-memory search if database fails
    print("[API] Falling back to in-memory search")
    for i, ioc in enumerate(IOCS):
        stored_value = str(ioc.get("value", ""))
        stored_value_lower = stored_value.lower()
        print(
            f"[API] Comparing with IOC #{i}: '{stored_value}' (lower: '{stored_value_lower}')"
        )

        if stored_value_lower == ioc_value_lower:
            print(f"[API] Found matching IOC: {stored_value}")
            return ioc

    print(f"[API] No matching IOC found for {ioc_value}")
    return None


# Commenting out path-based route to avoid conflicts with query parameter approach
# @ioc_bp.route("/api/ioc/<path:ioc_value>", methods=["GET"])
# def get_ioc_by_path(ioc_value):
#     """Get a specific IOC by its value (path parameter)."""
#     print(f"[API] Received path request for IOC: {ioc_value}")
#     ioc = get_ioc_by_value(ioc_value)
#     if ioc is None:
#         return jsonify({"error": "IOC not found"}), 404
#     return jsonify(ioc)


@ioc_bp.route("/api/ioc", methods=["GET"])
def get_ioc_by_query():
    """Get a specific IOC by its value (query parameter)."""
    ioc_value = request.args.get("value")
    print(f"[API] Received IOC value query: {ioc_value}")
    print(f"[API] Request headers: {dict(request.headers)}")
    print(f"[API] Current IOCs in memory: {len(IOCS)}")
    print(f"[API] IOC values in memory: {[ioc.get('value', '') for ioc in IOCS]}")

    if not ioc_value:
        return jsonify({"error": "IOC value is required"}), 400
    print(f"[API] Received query request for IOC: {ioc_value}")
    ioc = get_ioc_by_value(ioc_value)
    if ioc is None:
        return jsonify({"error": "IOC not found"}), 404
    return jsonify(ioc)


@ioc_bp.route("/api/explain/<path:ioc_value>", methods=["GET", "OPTIONS"])
def explain_ml(ioc_value):
    """Generate ML explanation for a specific IOC."""
    if request.method == "OPTIONS":
        # Handle preflight request
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET")
        return response

    # Find the IOC first (with case-insensitive matching)
    print(f"[API] Received ML explanation request for IOC: {ioc_value}")
    ioc = get_ioc_by_value(ioc_value)

    if ioc is None:
        # Return 404 if the IOC is not found
        return jsonify({"error": "IOC not found"}), 404

    try:
        from sentinelforge.scoring import score_ioc_with_explanation

        ioc_type = ioc.get("ioc_type", "unknown")
        source_feeds = [ioc.get("source_feed", "dummy")]
        enrichment_data = {}
        summary = ioc.get("summary", "")

        print(
            f"[API] Generating ML explanation for IOC: {ioc_value} (type: {ioc_type})"
        )

        # Score the IOC with explanation
        score, explanation_text, explanation_data = score_ioc_with_explanation(
            ioc_value=ioc_value,
            ioc_type=ioc_type,
            source_feeds=source_feeds,
            enrichment_data=enrichment_data,
            summary=summary,
        )

        # Create a feature breakdown with weights from the model
        feature_breakdown = []
        if explanation_data and "shap_values" in explanation_data:
            for item in explanation_data["shap_values"]:
                feature = item["feature"]
                importance = item["importance"]

                # Convert feature names to more readable format
                readable_name = feature
                if feature.startswith("type_"):
                    readable_name = feature[5:].title() + " Type"
                elif feature.startswith("feed_"):
                    readable_name = "From " + feature[5:].title() + " Feed"
                elif feature == "feed_count":
                    readable_name = "Number of Source Feeds"
                elif feature == "url_length":
                    readable_name = "URL Length"
                elif feature.startswith("contains_"):
                    readable_name = "Contains '" + feature[9:] + "'"

                feature_value = item.get("feature_value", "")

                feature_breakdown.append(
                    {
                        "feature": readable_name,
                        "value": str(feature_value),
                        "weight": importance,
                    }
                )

        # Response JSON
        response = {
            "value": ioc_value,
            "score": score / 10,  # Normalize to 0-1 range
            "explanation": {
                "summary": explanation_text,
                "feature_breakdown": feature_breakdown,
            },
        }

        print("[API] ML explanation generated successfully")
        return jsonify(response)

    except ImportError as e:
        print(f"[API] Error importing ML modules: {e}")
        # Fall back to mock data if ML modules are not available
        ioc_type = infer_ioc_type(ioc_value)

        # Generate explanation based on IOC type (use the existing mock data)
        if ioc_type == "domain":
            explanation = {
                "summary": "This domain exhibits characteristics associated with malware distribution infrastructure. The domain age, entropy, and lexical patterns strongly suggest malicious intent.",
                "feature_breakdown": [
                    {"feature": "Domain Age", "value": "3 days", "weight": -0.42},
                    {
                        "feature": "Character Entropy",
                        "value": "4.2 (high)",
                        "weight": 0.78,
                    },
                    {"feature": "TLD Type", "value": ".com", "weight": 0.14},
                    {"feature": "DGA-like Pattern", "value": "Yes", "weight": 0.65},
                    {
                        "feature": "Historical Reputation",
                        "value": "None",
                        "weight": -0.25,
                    },
                    {
                        "feature": "Domain Length",
                        "value": "18 characters",
                        "weight": 0.31,
                    },
                ],
            }
        elif ioc_type == "ip":
            explanation = {
                "summary": "This IP address shows behavioral patterns consistent with command and control (C2) infrastructure. The unusual port activity, geographic location, and association with previously identified threat actors indicate high confidence in this assessment.",
                "feature_breakdown": [
                    {
                        "feature": "ASN Reputation",
                        "value": "AS12345 (Poor)",
                        "weight": 0.67,
                    },
                    {
                        "feature": "Geographic Location",
                        "value": "Eastern Europe",
                        "weight": 0.35,
                    },
                    {"feature": "Open Ports", "value": "22, 443, 8080", "weight": 0.45},
                    {
                        "feature": "Passive DNS",
                        "value": "12 domains in 5 days",
                        "weight": 0.72,
                    },
                    {
                        "feature": "TLS Certificate",
                        "value": "Self-signed",
                        "weight": 0.58,
                    },
                    {
                        "feature": "Traffic Pattern",
                        "value": "Beaconing",
                        "weight": 0.83,
                    },
                ],
            }
        else:  # hash, url, or other
            explanation = {
                "summary": "This file hash is associated with a novel ransomware variant. Static and dynamic analysis reveals capabilities including file encryption, process termination, and anti-analysis techniques. The code shares significant similarities with the Ryuk ransomware family.",
                "feature_breakdown": [
                    {"feature": "Entropy", "value": "7.8/8.0", "weight": 0.76},
                    {
                        "feature": "PE Sections",
                        "value": "7 (3 suspicious)",
                        "weight": 0.62,
                    },
                    {
                        "feature": "API Calls",
                        "value": "CryptEncrypt, TerminateProcess",
                        "weight": 0.85,
                    },
                    {"feature": "File Size", "value": "284KB", "weight": 0.21},
                    {"feature": "Anti-Debug", "value": "Present", "weight": 0.73},
                    {
                        "feature": "Code Similarity",
                        "value": "68% match to Ryuk",
                        "weight": 0.69,
                    },
                ],
            }

        # Add mock score using get_ml_probability
        score = ioc.get("score", 5.0)
        probability = get_ml_probability(score)

        response = {
            "value": ioc_value,
            "score": probability,  # Use normalized probability
            "explanation": explanation,
        }

        return jsonify(response)
    except Exception as e:
        print(f"[API] Error generating ML explanation: {e}")
        return jsonify(
            {
                "value": ioc_value,
                "score": ioc.get("score", 5.0) / 10,  # Normalize score to 0-1 range
                "error": f"Error generating explanation: {str(e)}",
                "explanation": {
                    "summary": "Could not generate ML explanation for this IOC.",
                    "feature_breakdown": [],
                },
            }
        )


# Helper functions for ML data (mocked for now)
def get_ml_threat_class(ioc_value, ioc_type):
    """Determine the ML threat class based on IOC type."""
    threat_classes = {
        "domain": ["malware", "phishing", "c2_server"],
        "ip": ["c2_server", "ransomware", "ddos"],
        "hash": ["ransomware", "malware", "infostealer"],
        "url": ["phishing", "malware", "exploit"],
    }

    classes = threat_classes.get(ioc_type, ["unknown"])

    # Use the IOC value to deterministically select a class (for demo consistency)
    hash_value = sum(ord(c) for c in ioc_value)
    return classes[hash_value % len(classes)]


def get_ml_probability(score):
    """Generate a malicious probability based on the score."""
    # Convert score (0-10) to probability (0-1)
    return min(
        1.0, max(0.0, (score / 10) * 1.2)
    )  # Scaled to ensure high scores get high probabilities


def get_feature_importance(ioc_type):
    """Generate feature importance based on IOC type."""
    if ioc_type == "domain":
        return [
            {"feature": "Domain Age", "weight": 0.42},
            {"feature": "Entropy", "weight": 0.38},
            {"feature": "TLD Rarity", "weight": 0.2},
        ]
    elif ioc_type == "ip":
        return [
            {"feature": "ASN Reputation", "weight": 0.45},
            {"feature": "Geolocation", "weight": 0.35},
            {"feature": "Port Scan", "weight": 0.2},
        ]
    elif ioc_type == "hash":
        return [
            {"feature": "File Structure", "weight": 0.55},
            {"feature": "API Calls", "weight": 0.25},
            {"feature": "Packer Detection", "weight": 0.2},
        ]
    else:
        return [
            {"feature": "URL Pattern", "weight": 0.4},
            {"feature": "Domain Reputation", "weight": 0.3},
            {"feature": "Content Analysis", "weight": 0.3},
        ]


def get_similar_threats(ioc_type):
    """Generate similar threats based on IOC type."""
    threats = {
        "domain": [
            {"name": "Emotet", "confidence": 0.85},
            {"name": "Trickbot", "confidence": 0.72},
        ],
        "ip": [
            {"name": "APT29", "confidence": 0.65},
            {"name": "Cobalt Strike", "confidence": 0.77},
        ],
        "hash": [
            {"name": "WannaCry", "confidence": 0.82},
            {"name": "Ryuk", "confidence": 0.68},
        ],
        "url": [
            {"name": "Qakbot", "confidence": 0.75},
            {"name": "AgentTesla", "confidence": 0.63},
        ],
    }

    return threats.get(ioc_type, [{"name": "Unknown", "confidence": 0.5}])


def get_attack_techniques(ioc_type):
    """Generate MITRE ATT&CK techniques based on IOC type."""
    techniques = {
        "domain": [
            {"id": "T1566", "name": "Phishing"},
            {"id": "T1189", "name": "Drive-by Compromise"},
        ],
        "ip": [
            {"id": "T1071", "name": "Application Layer Protocol"},
            {"id": "T1572", "name": "Protocol Tunneling"},
        ],
        "hash": [
            {"id": "T1486", "name": "Data Encrypted for Impact"},
            {"id": "T1489", "name": "Service Stop"},
        ],
        "url": [
            {"id": "T1566.002", "name": "Phishing: Spearphishing Link"},
            {"id": "T1204", "name": "User Execution"},
        ],
    }

    return techniques.get(
        ioc_type, [{"id": "T1027", "name": "Obfuscated Files or Information"}]
    )


@ioc_bp.route("/api/ioc/summary", methods=["GET"])
def get_ioc_summary():
    """Get IOC summary statistics by severity level."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Count IOCs by category/severity
            cursor.execute("""
                SELECT
                    CASE
                        WHEN score >= 9.0 THEN 'critical'
                        WHEN score >= 7.5 THEN 'high'
                        WHEN score >= 5.0 THEN 'medium'
                        ELSE 'low'
                    END as severity,
                    COUNT(*) as count
                FROM iocs
                GROUP BY severity
            """)

            summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for row in cursor.fetchall():
                if "severity" in row and "count" in row:
                    summary[row["severity"]] = row["count"]

            conn.close()
            return jsonify(summary)
    except Exception as e:
        print(f"[API] Database error in get_ioc_summary: {e}")

    # Fallback to counting from in-memory IOCS
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for ioc in IOCS:
        score = ioc.get("score", 0)
        if score >= 9.0:
            summary["critical"] += 1
        elif score >= 7.5:
            summary["high"] += 1
        elif score >= 5.0:
            summary["medium"] += 1
        else:
            summary["low"] += 1

    return jsonify(summary)


@ioc_bp.route("/api/threats/metrics", methods=["GET"])
def get_threats_metrics():
    """Get threat metrics over time for dashboard charts."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Get daily threat counts for the last 7 days
            cursor.execute("""
                SELECT 
                    DATE(first_seen) as day,
                    SUM(CASE WHEN score >= 9.0 THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN score >= 7.5 AND score < 9.0 THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN score >= 5.0 AND score < 7.5 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN score < 5.0 THEN 1 ELSE 0 END) as low
                FROM iocs 
                WHERE first_seen >= date('now', '-7 days')
                GROUP BY DATE(first_seen)
                ORDER BY day DESC
                LIMIT 7
            """)

            daily_counts = []
            for row in cursor.fetchall():
                if "day" in row:
                    daily_counts.append(
                        {
                            "day": row["day"],
                            "critical": row.get("critical", 0),
                            "high": row.get("high", 0),
                            "medium": row.get("medium", 0),
                            "low": row.get("low", 0),
                        }
                    )

            conn.close()

            if daily_counts:
                return jsonify({"daily_counts": daily_counts})
    except Exception as e:
        print(f"[API] Database error in get_threats_metrics: {e}")

    # Fallback to mock data if database fails
    import datetime

    today = datetime.date.today()

    daily_counts = []
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        daily_counts.append(
            {
                "day": day.strftime("%Y-%m-%d"),
                "critical": random.randint(0, 5),
                "high": random.randint(2, 8),
                "medium": random.randint(4, 12),
                "low": random.randint(1, 6),
            }
        )

    return jsonify({"daily_counts": daily_counts})


@ioc_bp.route("/api/ioc/share", methods=["GET"])
def get_shareable_ioc():
    """Get a shareable, public-safe version of an IOC for public viewing."""
    ioc_value = request.args.get("value")
    print(f"[API] Received shareable IOC request: {ioc_value}")

    if not ioc_value:
        return jsonify({"error": "IOC value is required"}), 400

    # Get the full IOC data first
    ioc = get_ioc_by_value(ioc_value)

    if ioc is None:
        return jsonify({"error": "IOC not found"}), 404

    # Create a public-safe version of the IOC data
    # Omit any internal-only or sensitive fields
    public_ioc = {
        "value": ioc.get("value", "") or ioc.get("ioc_value", ""),
        "type": ioc.get("ioc_type", ""),
        "score": ioc.get("score", 0),
        "category": ioc.get("category", ""),
        "first_seen": ioc.get("first_seen", ""),
        "threat_class": ioc.get("threat_class", ""),
        "malicious_probability": ioc.get("malicious_probability", 0),
        "attack_techniques": ioc.get("attack_techniques", []),
        # Include a subset of feature_importance fields
        "feature_importance": [
            {
                "feature": item.get("feature", ""),
                "weight": item.get("weight", 0),
                "description": item.get("description", ""),
            }
            for item in ioc.get("feature_importance", [])[:3]  # Only include top 3
        ],
    }

    # Add a view count tracker (would typically be stored in a database)
    # Here we're just simulating it with a random number
    public_ioc["view_count"] = random.randint(5, 100)

    # Add a shareable ID (in a real app, this would be a database-generated unique ID)
    # For simplicity, we're using a timestamp-based ID here
    current_time = int(time.time())
    public_ioc["share_id"] = f"s{current_time}"

    return jsonify(public_ioc)


# Add in endpoint for ML explanation
@ioc_bp.route("/api/explain/share/<path:ioc_value>", methods=["GET"])
def share_explain_ml(ioc_value):
    """Get a shareable ML explanation for a specific IOC."""
    print(f"[API] Received shareable ML explanation request for IOC: {ioc_value}")

    # Get the IOC
    ioc = get_ioc_by_value(ioc_value)
    if ioc is None:
        return jsonify({"error": "IOC not found"}), 404

    # Public version of the explanation
    explanation = {
        "value": ioc.get("value", "") or ioc.get("ioc_value", ""),
        "score": ioc.get("score", 0) / 10.0,  # Normalize to 0-1
        "explanation": {
            "summary": f"This {ioc.get('ioc_type', '')} indicator shows characteristics typical of malicious activity.",
            "feature_breakdown": [
                {
                    "feature": item.get("feature", ""),
                    "value": item.get("value", ""),
                    "weight": item.get("weight", 0),
                }
                for item in ioc.get("feature_importance", [])[:5]  # Only include top 5
            ],
        },
    }

    return jsonify(explanation)


def generate_mock_alerts():
    """Generate mock alerts for testing purposes."""
    global ALERTS

    # Sample mock alerts
    mock_alerts = [
        {
            "id": "AL1",
            "name": "Suspicious Network Connection",
            "timestamp": 1651234567,
            "formatted_time": "2022-04-29 12:34:56",
            "threat_type": "Command and Control",
            "severity": "High",
            "confidence": 85,
            "description": "Alert triggered by detection of domain example.com in network traffic.",
            "ioc_values": ["example.com"],
            "related_iocs": ["example.com"],
            "source": "SIEM",
        },
        {
            "id": "AL2",
            "name": "Malicious File Download",
            "timestamp": 1651234800,
            "formatted_time": "2022-04-29 12:40:00",
            "threat_type": "Malware",
            "severity": "Critical",
            "confidence": 95,
            "description": "Detected download from known malicious domain example.com",
            "ioc_values": ["example.com"],
            "related_iocs": ["example.com"],
            "source": "EDR",
        },
        {
            "id": "AL3",
            "name": "Suspicious IP Communication",
            "timestamp": 1651235000,
            "formatted_time": "2022-04-29 12:43:20",
            "threat_type": "Reconnaissance",
            "severity": "Medium",
            "confidence": 70,
            "description": "Communication detected with suspicious IP address 1.1.1.1",
            "ioc_values": ["1.1.1.1"],
            "related_iocs": ["1.1.1.1"],
            "source": "Firewall",
        },
    ]

    ALERTS.clear()
    ALERTS.extend(mock_alerts)
    print(f"[API] Generated {len(ALERTS)} mock alerts")


# Alert-related endpoints
@ioc_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Get a list of alerts with optional filtering, sorting, and pagination."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Parse query parameters
            name = request.args.get("name")
            ioc_value = request.args.get("ioc")
            page = int(request.args.get("page", 1))
            limit = int(request.args.get("limit", 10))

            # Parse sorting parameters
            sort_field = request.args.get("sort", "id")
            sort_order = request.args.get("order", "asc").lower()

            # Validate sort field against allowed columns
            allowed_sort_fields = ["id", "name", "timestamp", "risk_score"]
            if sort_field not in allowed_sort_fields:
                sort_field = "id"  # Default to id if invalid field provided

            # Validate sort order
            if sort_order not in ["asc", "desc"]:
                sort_order = "asc"  # Default to ascending if invalid order provided

            # Calculate offset from page
            offset = (page - 1) * limit

            # Build base query - always include risk_score and overridden_risk_score, and additional fields for sorting
            base_fields = (
                "a.id, a.name, a.description, a.risk_score, a.overridden_risk_score"
            )
            if sort_field in ["timestamp"] and sort_field not in base_fields:
                query = f"SELECT DISTINCT {base_fields}, a.{sort_field} FROM alerts a"
            else:
                query = f"SELECT DISTINCT {base_fields} FROM alerts a"
            count_query = "SELECT COUNT(DISTINCT a.id) as count FROM alerts a"
            params = []
            where_conditions = []

            # Filter by alert name (case-insensitive partial match)
            if name:
                where_conditions.append("LOWER(a.name) LIKE LOWER(?)")
                params.append(f"%{name}%")

            # Filter by IOC value (case-insensitive partial match)
            if ioc_value:
                query += " JOIN ioc_alert ia ON a.id = ia.alert_id JOIN iocs i ON ia.ioc_value = i.ioc_value"
                count_query += " JOIN ioc_alert ia ON a.id = ia.alert_id JOIN iocs i ON ia.ioc_value = i.ioc_value"
                where_conditions.append("LOWER(i.ioc_value) LIKE LOWER(?)")
                params.append(f"%{ioc_value}%")

            # Add WHERE clause if we have conditions
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query += where_clause
                count_query += where_clause

            # Add ordering and pagination - use overridden_risk_score if available, otherwise risk_score
            if sort_field == "risk_score":
                query += f" ORDER BY COALESCE(a.overridden_risk_score, a.risk_score) {sort_order.upper()} LIMIT ? OFFSET ?"
            else:
                query += (
                    f" ORDER BY a.{sort_field} {sort_order.upper()} LIMIT ? OFFSET ?"
                )
            query_params = params + [limit, offset]

            # Execute main query
            cursor.execute(query, query_params)
            alerts = []
            for row in cursor.fetchall():
                alert = dict(row)
                alerts.append(alert)

            conn.close()

            # Return simplified JSON array as requested, including risk_score and overridden_risk_score
            return jsonify(
                [
                    {
                        "id": alert["id"],
                        "name": alert["name"],
                        "description": alert["description"],
                        "risk_score": alert.get(
                            "risk_score", 50
                        ),  # Default to 50 if not present
                        "overridden_risk_score": alert.get(
                            "overridden_risk_score"
                        ),  # None if not overridden
                    }
                    for alert in alerts
                ]
            )

    except Exception as e:
        print(f"Database error in get_alerts: {e}")

    # Return empty array if database fails
    return jsonify([])


@ioc_bp.route("/api/ioc/<path:ioc_value>/alerts", methods=["GET"])
def get_alerts_for_ioc(ioc_value):
    """Get alerts associated with a specific IOC."""
    # First check if the IOC exists
    ioc = get_ioc_by_value(ioc_value)
    if ioc is None:
        return jsonify({"error": "IOC not found"}), 404

    # Use the actual IOC value from the database for case-sensitive database query
    actual_ioc_value = ioc.get("ioc_value") or ioc.get("value", ioc_value)

    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Find alerts related to this IOC through the junction table
            # Use the actual IOC value from the database to ensure case-sensitive match
            cursor.execute(
                """
                SELECT a.* FROM alerts a
                JOIN ioc_alert ia ON a.id = ia.alert_id
                WHERE ia.ioc_value = ?
                ORDER BY a.timestamp DESC
            """,
                (actual_ioc_value,),
            )

            alerts = []
            for row in cursor.fetchall():
                alert = dict(row)
                # Keep integer IDs as they are for database consistency
                alerts.append(alert)

            conn.close()

            return jsonify(
                {
                    "ioc_value": ioc_value,
                    "alerts": alerts,
                    "total": len(alerts),
                    "total_alerts": len(alerts),  # For test compatibility
                }
            )

    except Exception as e:
        print(f"Database error in get_alerts_for_ioc: {e}")

    # Return empty result if database fails but IOC exists
    return jsonify(
        {
            "ioc_value": ioc_value,
            "alerts": [],
            "total": 0,
            "total_alerts": 0,  # For test compatibility
        }
    )


@ioc_bp.route("/api/alert/<int:alert_id>/iocs", methods=["GET"])
def get_iocs_for_alert(alert_id):
    """Get IOCs associated with a specific alert."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # First get the alert details
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            alert_row = cursor.fetchone()

            if not alert_row:
                return jsonify({"error": "Alert not found"}), 404

            alert = dict(alert_row)

            # Find IOCs related to this alert through the junction table
            cursor.execute(
                """
                SELECT i.* FROM iocs i
                JOIN ioc_alert ia ON i.ioc_value = ia.ioc_value
                WHERE ia.alert_id = ?
                ORDER BY i.score DESC
            """,
                (alert_id,),
            )

            iocs = []
            for row in cursor.fetchall():
                ioc = dict(row)
                # Add the 'value' alias for compatibility
                ioc["value"] = ioc.get("ioc_value", "")
                iocs.append(ioc)

            conn.close()

            return jsonify(
                {
                    "alert_id": alert_id,
                    "alert_name": alert.get("name", ""),
                    "timestamp": alert.get("timestamp", 0),
                    "formatted_time": alert.get("formatted_time", ""),
                    "total_iocs": len(iocs),
                    "iocs": iocs,
                }
            )

    except Exception as e:
        print(f"Database error in get_iocs_for_alert: {e}")

    # Return error if database fails or alert not found
    return jsonify({"error": "Alert not found"}), 404


@ioc_bp.route("/api/alert/<int:alert_id>", methods=["GET"])
def get_alert(alert_id):
    """Get detailed information about a specific alert."""
    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Get the alert details
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            alert_row = cursor.fetchone()

            if not alert_row:
                conn.close()
                return jsonify({"error": "Alert not found"}), 404

            alert = dict(alert_row)
            conn.close()

            # Return complete alert information including risk_score and overridden_risk_score
            return jsonify(
                {
                    "id": alert["id"],
                    "name": alert["name"],
                    "description": alert.get("description", ""),
                    "timestamp": alert.get("timestamp", 0),
                    "formatted_time": alert.get("formatted_time", ""),
                    "threat_type": alert.get("threat_type", ""),
                    "severity": alert.get("severity", "medium"),
                    "confidence": alert.get("confidence", 50),
                    "risk_score": alert.get("risk_score", 50),
                    "overridden_risk_score": alert.get("overridden_risk_score"),
                    "source": alert.get("source", ""),
                    "created_at": alert.get("created_at", ""),
                    "updated_at": alert.get("updated_at", ""),
                }
            )

    except Exception as e:
        print(f"Database error in get_alert: {e}")

    # Return error if database fails or alert not found
    return jsonify({"error": "Alert not found"}), 404


@ioc_bp.route("/api/alert/<int:alert_id>/override", methods=["PATCH"])
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def override_alert_risk_score(alert_id):
    """Override the risk score for a specific alert. Requires analyst or admin role."""
    try:
        # Parse JSON body
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate risk_score field
        if "risk_score" not in data:
            return jsonify({"error": "risk_score field is required"}), 400

        risk_score = data["risk_score"]
        justification = data.get("justification", "")  # Optional justification

        # Get current user from auth system
        current_user = g.current_user
        user_id = current_user.user_id if current_user else data.get("user_id", 1)

        # Validate risk_score value
        if not isinstance(risk_score, (int, float)):
            return jsonify({"error": "risk_score must be a number"}), 400

        risk_score = int(risk_score)
        if risk_score < 0 or risk_score > 100:
            return jsonify({"error": "risk_score must be between 0 and 100"}), 400

        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Check if alert exists and get current risk score
            cursor.execute(
                "SELECT id, risk_score, overridden_risk_score FROM alerts WHERE id = ?",
                (alert_id,),
            )
            alert_data = cursor.fetchone()
            if not alert_data:
                conn.close()
                return jsonify({"error": "Alert not found"}), 404

            # Get the original score (use overridden if it exists, otherwise use risk_score)
            original_score = alert_data.get("overridden_risk_score") or alert_data.get(
                "risk_score", 50
            )

            # Update the overridden_risk_score
            cursor.execute(
                "UPDATE alerts SET overridden_risk_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (risk_score, alert_id),
            )

            # Create audit log entry
            cursor.execute(
                """INSERT INTO audit_logs (alert_id, user_id, original_score, override_score, justification, timestamp)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (alert_id, user_id, original_score, risk_score, justification),
            )

            conn.commit()

            # Fetch the updated alert
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            alert_row = cursor.fetchone()
            alert = dict(alert_row)
            conn.close()

            # Return the updated alert
            return jsonify(
                {
                    "id": alert["id"],
                    "name": alert["name"],
                    "description": alert.get("description", ""),
                    "timestamp": alert.get("timestamp", 0),
                    "formatted_time": alert.get("formatted_time", ""),
                    "threat_type": alert.get("threat_type", ""),
                    "severity": alert.get("severity", "medium"),
                    "confidence": alert.get("confidence", 50),
                    "risk_score": alert.get("risk_score", 50),
                    "overridden_risk_score": alert.get("overridden_risk_score"),
                    "source": alert.get("source", ""),
                    "created_at": alert.get("created_at", ""),
                    "updated_at": alert.get("updated_at", ""),
                    "message": f"Risk score overridden to {risk_score}",
                }
            )
        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        print(f"Database error in override_alert_risk_score: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/user/current", methods=["GET"])
@require_authentication()
def get_current_user_info():
    """Get current user information and permissions."""
    try:
        current_user = g.current_user
        return jsonify(current_user.to_dict())
    except Exception as e:
        print(f"Error getting current user info: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/audit", methods=["GET"])
@require_role([UserRole.AUDITOR, UserRole.ADMIN])
def get_audit_logs():
    """Get audit logs with optional filtering. Requires auditor or admin role."""
    try:
        # Get query parameters
        alert_id = request.args.get("alert_id", type=int)
        user_id = request.args.get("user_id", type=int)
        start_date = request.args.get("start_date")  # ISO format: 2023-12-01
        end_date = request.args.get("end_date")  # ISO format: 2023-12-31
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        # Build the query
        query = """
            SELECT al.*, a.name as alert_name
            FROM audit_logs al
            JOIN alerts a ON al.alert_id = a.id
            WHERE 1=1
        """
        params = []

        # Add filters
        if alert_id:
            query += " AND al.alert_id = ?"
            params.append(alert_id)

        if user_id:
            query += " AND al.user_id = ?"
            params.append(user_id)

        if start_date:
            query += " AND DATE(al.timestamp) >= ?"
            params.append(start_date)

        if end_date:
            query += " AND DATE(al.timestamp) <= ?"
            params.append(end_date)

        # Add ordering and pagination
        query += " ORDER BY al.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute query
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            audit_logs = []
            for row in cursor.fetchall():
                log = dict(row)
                audit_logs.append(
                    {
                        "id": log["id"],
                        "alert_id": log["alert_id"],
                        "alert_name": log["alert_name"],
                        "user_id": log["user_id"],
                        "original_score": log["original_score"],
                        "override_score": log["override_score"],
                        "justification": log.get("justification", ""),
                        "timestamp": log["timestamp"],
                    }
                )

            # Get total count for pagination
            count_query = """
                SELECT COUNT(*) as total
                FROM audit_logs al
                WHERE 1=1
            """
            count_params = []

            if alert_id:
                count_query += " AND al.alert_id = ?"
                count_params.append(alert_id)

            if user_id:
                count_query += " AND al.user_id = ?"
                count_params.append(user_id)

            if start_date:
                count_query += " AND DATE(al.timestamp) >= ?"
                count_params.append(start_date)

            if end_date:
                count_query += " AND DATE(al.timestamp) <= ?"
                count_params.append(end_date)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()["total"]

            conn.close()

            return jsonify(
                {
                    "audit_logs": audit_logs,
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                }
            )
        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        print(f"Database error in get_audit_logs: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/alert/<int:alert_id>/timeline", methods=["GET"])
def get_alert_timeline(alert_id):
    """Get a chronological timeline of events and IOCs related to a specific alert."""
    try:
        # Try accessing the database to verify alert exists
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # First verify the alert exists
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            alert_row = cursor.fetchone()

            if not alert_row:
                conn.close()
                return jsonify({"error": "Alert not found"}), 404

            alert = dict(alert_row)
            conn.close()

            # Generate mock timeline data based on alert information
            timeline_events = generate_mock_timeline(alert_id, alert)

            return jsonify(timeline_events)

        else:
            # Fallback to mock data if database is not available
            timeline_events = generate_mock_timeline(
                alert_id, {"name": f"Alert {alert_id}", "timestamp": 1651234567}
            )
            return jsonify(timeline_events)

    except Exception as e:
        print(f"Database error in get_alert_timeline: {e}")
        # Return mock data on error
        timeline_events = generate_mock_timeline(
            alert_id, {"name": f"Alert {alert_id}", "timestamp": 1651234567}
        )
        return jsonify(timeline_events)


def generate_mock_timeline(alert_id, alert_info):
    """Generate mock timeline data for an alert."""
    import datetime
    import random

    # Base timestamp from alert or current time
    base_timestamp = alert_info.get(
        "timestamp", int(datetime.datetime.now().timestamp())
    )
    base_datetime = datetime.datetime.fromtimestamp(base_timestamp)

    # Generate timeline events based on alert ID for consistency
    random.seed(alert_id)  # Ensure consistent data for same alert

    timeline_events = []

    # Event templates based on alert type
    event_templates = [
        {
            "type": "network",
            "descriptions": [
                "Outbound connection to malicious IP {ip}",
                "DNS query for suspicious domain {domain}",
                "Unusual network traffic pattern detected",
                "Connection attempt to known C2 server",
                "Data exfiltration attempt detected",
            ],
        },
        {
            "type": "file",
            "descriptions": [
                "Downloaded suspicious executable {filename}",
                "File modification detected: {filename}",
                "Malicious file hash identified: {hash}",
                "Unauthorized file access attempt",
                "Suspicious file creation in system directory",
            ],
        },
        {
            "type": "process",
            "descriptions": [
                "Suspicious process execution: {process}",
                "Process injection detected",
                "Privilege escalation attempt",
                "Unusual command line execution",
                "Process hollowing technique identified",
            ],
        },
        {
            "type": "registry",
            "descriptions": [
                "Registry modification detected",
                "Persistence mechanism installed",
                "Autorun entry created",
                "Security setting bypassed",
                "System configuration altered",
            ],
        },
        {
            "type": "authentication",
            "descriptions": [
                "Failed login attempt from {ip}",
                "Suspicious authentication pattern",
                "Account lockout triggered",
                "Credential harvesting attempt",
                "Brute force attack detected",
            ],
        },
    ]

    # Sample data for placeholders
    sample_ips = ["192.168.1.100", "10.0.0.50", "172.16.1.25", "203.0.113.45"]
    sample_domains = ["malicious-site.com", "phishing-domain.net", "c2-server.org"]
    sample_files = ["malware.exe", "trojan.dll", "suspicious.bat", "payload.scr"]
    sample_hashes = ["a1b2c3d4e5f6", "f6e5d4c3b2a1", "123456789abc"]
    sample_processes = ["cmd.exe", "powershell.exe", "rundll32.exe", "svchost.exe"]

    # Generate 5-8 timeline events
    num_events = random.randint(5, 8)

    for i in range(num_events):
        # Generate timestamp (events spread over 30 minutes before and after alert)
        time_offset = random.randint(-1800, 1800)  # ±30 minutes in seconds
        event_datetime = base_datetime + datetime.timedelta(seconds=time_offset)

        # Choose random event type
        event_template = random.choice(event_templates)
        event_type = event_template["type"]
        description_template = random.choice(event_template["descriptions"])

        # Fill in placeholders in description
        description = description_template.format(
            ip=random.choice(sample_ips),
            domain=random.choice(sample_domains),
            filename=random.choice(sample_files),
            hash=random.choice(sample_hashes),
            process=random.choice(sample_processes),
        )

        timeline_events.append(
            {
                "timestamp": event_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": event_type,
                "description": description,
            }
        )

    # Sort events chronologically
    timeline_events.sort(key=lambda x: x["timestamp"])

    return timeline_events


# Register the Blueprint with the main app
app.register_blueprint(ioc_bp)


@app.route("/iocs")
def iocs_redirect():
    """Redirect /iocs to /api/iocs with the same query parameters."""
    return redirect(url_for("ioc.get_iocs", **request.args))


@app.route("/")
def index():
    return "SentinelForge API Server is running. Use /api/iocs to get IOC details."


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


# Initialize IOCS and ALERTS lists at startup
def initialize_iocs():
    """Load initial IOC data into memory at server startup."""
    global IOCS  # This declaration is fine since IOCS is defined at module level
    print("[API] Initializing IOCs list at startup...")

    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Fetch all IOCs with a simple query
            cursor.execute("SELECT * FROM iocs LIMIT 100")
            iocs = []
            for row in cursor.fetchall():
                ioc = dict(row)
                iocs.append(ioc)

            conn.close()

            if iocs:
                IOCS.clear()
                IOCS.extend(iocs)
                print(f"[API] Loaded {len(IOCS)} IOCs from database")
                return
    except Exception as e:
        print(f"[API] Database error during initialization: {e}")


def initialize_alerts():
    """Load initial Alert data into memory at server startup."""
    global ALERTS
    print("[API] Initializing Alerts list at startup...")

    try:
        # Try accessing the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Fetch all alerts with a simple query
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50")
            alerts = []
            for row in cursor.fetchall():
                alert = dict(row)
                alerts.append(alert)

            conn.close()

            if alerts:
                ALERTS.clear()
                ALERTS.extend(alerts)
                print(f"[API] Loaded {len(ALERTS)} Alerts from database")
                return
    except Exception as e:
        print(f"[API] Database error during alerts initialization: {e}")

    # Fallback to enhanced mock IOCs if database fails
    # Generate random timestamps within the last 14 days
    def random_timestamp(days_ago_max=14, days_ago_min=0):
        days_ago = random.uniform(days_ago_min, days_ago_max)
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Common domains for examples
    domains = [
        "example.com",
        "phishing-attempt.com",
        "malware-delivery.net",
        "suspicious-domain.org",
        "credential-harvester.com",
        "fake-login.net",
        "banking-update.com",
        "secure-verification.net",
        "account-alert.org",
        "payment-confirm.com",
    ]

    # Common IPs for examples
    ips = [
        "1.1.1.1",
        "192.168.1.10",
        "10.0.0.1",
        "172.16.254.1",
        "192.0.2.1",
        "198.51.100.1",
        "203.0.113.1",
        "224.0.0.1",
        "169.254.1.1",
        "127.0.0.1",
    ]

    # Create file hashes
    hashes = [
        "5241acbddc07ce49cca44076264344717b30a303acb825075471e83468c5585",
        "840c40763110c1f6564bc2b61dcdf7ce77ce0016211385a5ac49cc5ea8b011d2",
        "685b4307728abd92415c2d9c001761cfa0481b29689b35106f7a5ee1d1117c8a",
        "13be0a2444ed05fa173dca62cea89c996e0fe93d82d33bb7795d1870eb1b0e2d",
        "3247618d002476e731145da86ec977edf01bae14c9beb3bc3bf4b7fa1ee4a250",
    ]

    # URLs for examples
    urls = [
        "https://malicious-site.com/download.exe",
        "https://fake-login.com/portal/signin.php",
        "http://compromised-cdn.net/jquery.min.js",
        "https://phish.example.org/reset-password.html",
        "http://tracking.malware-delivery.com/beacon.gif",
    ]

    # Create 50 mock IOCs with varied properties
    fallback_iocs = []

    # Add the original fallback data
    fallback_iocs.extend(
        [
            {
                "id": 1,
                "ioc_type": "domain",
                "ioc_value": "example.com",
                "value": "example.com",
                "score": 9,
                "category": "low",
                "first_seen": random_timestamp(30, 25),
                "last_seen": random_timestamp(5, 1),
                "source_feed": "dummy",
                "threat_class": "malware",
                "malicious_probability": 1.0,
                "feature_importance": [
                    {"feature": "Domain Age", "weight": 0.42},
                    {"feature": "Entropy", "weight": 0.38},
                    {"feature": "TLD Rarity", "weight": 0.2},
                ],
                "similar_known_threats": [
                    {"name": "Emotet", "confidence": 0.85},
                    {"name": "Trickbot", "confidence": 0.72},
                ],
                "attack_techniques": [
                    {"id": "T1566", "name": "Phishing"},
                    {"id": "T1189", "name": "Drive-by Compromise"},
                ],
            },
            {
                "id": 2,
                "ioc_type": "ip",
                "ioc_value": "1.1.1.1",
                "value": "1.1.1.1",
                "score": 7.2,
                "category": "medium",
                "first_seen": random_timestamp(30, 25),
                "last_seen": random_timestamp(5, 1),
                "source_feed": "test_feed",
                "threat_class": "c2_server",
                "malicious_probability": 0.78,
                "feature_importance": [
                    {"feature": "WHOIS Age", "weight": 0.35},
                    {"feature": "ASN Reputation", "weight": 0.45},
                    {"feature": "Port Scan Results", "weight": 0.2},
                ],
                "similar_known_threats": [
                    {"name": "APT29", "confidence": 0.65},
                    {"name": "Cobalt Strike", "confidence": 0.77},
                ],
                "attack_techniques": [
                    {"id": "T1071", "name": "Application Layer Protocol"},
                    {"id": "T1572", "name": "Protocol Tunneling"},
                ],
            },
        ]
    )

    # Add domain IOCs
    for i, domain in enumerate(domains[2:], start=3):
        score = random.uniform(3.0, 9.8)
        fallback_iocs.append(
            {
                "id": i,
                "ioc_type": "domain",
                "ioc_value": domain,
                "value": domain,
                "score": score,
                "category": "high" if score > 7.5 else "medium" if score > 5 else "low",
                "first_seen": random_timestamp(30, 15),
                "last_seen": random_timestamp(10, 0),
                "source_feed": random.choice(
                    ["AlienVault", "Mandiant", "Recorded Future", "IBM X-Force"]
                ),
                "threat_class": random.choice(["malware", "phishing", "c2_server"]),
                "malicious_probability": min(1.0, score / 10 * 1.2),
                "feature_importance": [
                    {"feature": "Domain Age", "weight": random.uniform(0.3, 0.5)},
                    {"feature": "Entropy", "weight": random.uniform(0.2, 0.4)},
                    {"feature": "TLD Rarity", "weight": random.uniform(0.1, 0.3)},
                ],
            }
        )

    # Add IP IOCs
    next_id = len(fallback_iocs) + 1
    for i, ip in enumerate(ips[2:], start=next_id):
        score = random.uniform(4.0, 9.5)
        fallback_iocs.append(
            {
                "id": i,
                "ioc_type": "ip",
                "ioc_value": ip,
                "value": ip,
                "score": score,
                "category": "high" if score > 7.5 else "medium" if score > 5 else "low",
                "first_seen": random_timestamp(30, 15),
                "last_seen": random_timestamp(10, 0),
                "source_feed": random.choice(
                    ["FireEye", "Crowdstrike", "ThreatConnect", "Anomali"]
                ),
                "threat_class": random.choice(["c2_server", "ransomware", "ddos"]),
                "malicious_probability": min(1.0, score / 10 * 1.2),
                "feature_importance": [
                    {"feature": "ASN Reputation", "weight": random.uniform(0.3, 0.5)},
                    {"feature": "Geolocation", "weight": random.uniform(0.2, 0.4)},
                    {"feature": "Port Scan", "weight": random.uniform(0.1, 0.3)},
                ],
            }
        )

    # Add Hash IOCs
    next_id = len(fallback_iocs) + 1
    for i, hash_value in enumerate(hashes, start=next_id):
        score = random.uniform(5.0, 9.9)
        fallback_iocs.append(
            {
                "id": i,
                "ioc_type": "hash",
                "ioc_value": hash_value,
                "value": hash_value,
                "score": score,
                "category": "high" if score > 7.5 else "medium" if score > 5 else "low",
                "first_seen": random_timestamp(30, 15),
                "last_seen": random_timestamp(10, 0),
                "source_feed": random.choice(
                    ["VirusTotal", "Trellix", "Malwarebytes", "Kaspersky"]
                ),
                "threat_class": random.choice(["ransomware", "malware", "infostealer"]),
                "malicious_probability": min(1.0, score / 10 * 1.2),
                "feature_importance": [
                    {"feature": "File Structure", "weight": random.uniform(0.4, 0.6)},
                    {"feature": "API Calls", "weight": random.uniform(0.2, 0.3)},
                    {"feature": "Packer Detection", "weight": random.uniform(0.1, 0.3)},
                ],
            }
        )

    # Add URL IOCs
    next_id = len(fallback_iocs) + 1
    for i, url in enumerate(urls, start=next_id):
        score = random.uniform(4.5, 9.7)
        fallback_iocs.append(
            {
                "id": i,
                "ioc_type": "url",
                "ioc_value": url,
                "value": url,
                "score": score,
                "category": "high" if score > 7.5 else "medium" if score > 5 else "low",
                "first_seen": random_timestamp(30, 15),
                "last_seen": random_timestamp(10, 0),
                "source_feed": random.choice(
                    ["PhishTank", "URLhaus", "Symantec", "Cisco Talos"]
                ),
                "threat_class": random.choice(["phishing", "malware", "exploit"]),
                "malicious_probability": min(1.0, score / 10 * 1.2),
                "feature_importance": [
                    {"feature": "URL Pattern", "weight": random.uniform(0.3, 0.5)},
                    {
                        "feature": "Domain Reputation",
                        "weight": random.uniform(0.2, 0.4),
                    },
                    {"feature": "Content Analysis", "weight": random.uniform(0.2, 0.3)},
                ],
            }
        )

    # Generate 20 more random IOCs with varied timestamps for the last 14 days
    next_id = len(fallback_iocs) + 1
    ioc_types = ["domain", "ip", "url", "hash"]
    ioc_sources = {"domain": domains, "ip": ips, "url": urls, "hash": hashes}

    for i in range(20):
        ioc_type = random.choice(ioc_types)
        ioc_value = random.choice(ioc_sources[ioc_type])
        score = random.uniform(1.0, 9.9)
        # Generate timestamps more heavily weighted to recent days
        days_ago = random.triangular(0, 14, 2)  # More weighted toward recent
        fallback_iocs.append(
            {
                "id": next_id + i,
                "ioc_type": ioc_type,
                "ioc_value": ioc_value,
                "value": ioc_value,
                "score": score,
                "category": "high" if score > 7.5 else "medium" if score > 5 else "low",
                "first_seen": random_timestamp(days_ago + 10, days_ago + 5),
                "last_seen": random_timestamp(days_ago + 2, days_ago),
                "source_feed": random.choice(
                    [
                        "VirusTotal",
                        "Trellix",
                        "Malwarebytes",
                        "Kaspersky",
                        "AlienVault",
                        "Mandiant",
                        "Recorded Future",
                        "IBM X-Force",
                    ]
                ),
                "threat_class": get_ml_threat_class(ioc_value, ioc_type),
                "malicious_probability": min(1.0, score / 10 * 1.2),
                "feature_importance": get_feature_importance(ioc_type),
            }
        )

    # Ensure we have a mix of critical/high/medium/low severity IOCs
    # Add a few critical IOCs for dashboard impact
    next_id = len(fallback_iocs) + 1
    for i in range(5):
        ioc_type = random.choice(ioc_types)
        ioc_value = (
            f"critical-{ioc_type}-{i}.malicious.com"
            if ioc_type == "domain"
            else random.choice(ioc_sources[ioc_type])
        )
        score = random.uniform(8.5, 9.9)  # Critical range
        days_ago = random.triangular(0, 5, 1)  # Very recent threats
        fallback_iocs.append(
            {
                "id": next_id + i,
                "ioc_type": ioc_type,
                "ioc_value": ioc_value,
                "value": ioc_value,
                "score": score,
                "category": "critical",
                "first_seen": random_timestamp(days_ago + 3, days_ago + 1),
                "last_seen": random_timestamp(days_ago + 0.5, 0),
                "source_feed": "Critical Threat Intelligence",
                "threat_class": "APT",
                "malicious_probability": 0.99,
                "feature_importance": get_feature_importance(ioc_type),
            }
        )

    IOCS.clear()
    IOCS.extend(fallback_iocs)
    print(f"[API] Loaded {len(IOCS)} enhanced mock IOCs")


if __name__ == "__main__":
    port = 5059
    print(f"Starting API server on port {port}")
    initialize_iocs()  # Initialize IOCS list before starting the server
    initialize_alerts()  # Initialize ALERTS list before starting the server
    app.run(host="0.0.0.0", port=port, debug=True)
