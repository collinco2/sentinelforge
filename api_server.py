#!/usr/bin/env python3
from flask import Flask, jsonify, request, Blueprint, g, session
from flask_cors import CORS
import os
import sqlite3
import time
import re
import random
import datetime
import secrets
import json
import hashlib
import hmac
from auth import (
    require_role,
    require_authentication,
    UserRole,
    get_user_by_credentials,
    get_user_by_session,
    create_session,
    invalidate_session,
    create_password_reset_token,
    validate_password_reset_token,
    use_password_reset_token,
    update_user_password,
)
from email_service import (
    send_password_reset_email,
    send_password_reset_confirmation_email,
)
from services.ingestion import FeedIngestionService

import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure Flask session
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours

# Enable CORS for all routes and all origins
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization", "X-Session-Token"],
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "supports_credentials": True,
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

        # Custom row factory to avoid tuple index errors
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


# ===== API KEY UTILITY FUNCTIONS =====


def generate_api_key():
    """Generate a secure API key with prefix."""
    # Generate 32 bytes (256 bits) of random data
    key_bytes = secrets.token_bytes(32)
    # Convert to URL-safe base64 string
    key_string = secrets.token_urlsafe(32)
    # Add prefix to identify as SentinelForge API key
    return f"sf_live_{key_string}"


def hash_api_key(api_key):
    """Hash an API key using SHA-256 with salt."""
    # Use a consistent salt for API keys (in production, use environment variable)
    salt = "sentinelforge_api_key_salt_2024"
    return hashlib.sha256((api_key + salt).encode()).hexdigest()


def create_api_key_preview(api_key):
    """Create a preview version of the API key (first 8 chars + ... + last 4 chars)."""
    if len(api_key) < 12:
        return api_key[:4] + "..."
    return api_key[:8] + "..." + api_key[-4:]


def validate_api_key_from_header():
    """
    Validate API key from X-API-Key header and return user info.
    Returns tuple: (is_valid, user_info, error_message)
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return False, None, "Missing API key"

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    try:
        conn = get_db_connection()
        if not conn:
            return False, None, "Database connection failed"

        cursor = conn.cursor()

        # Look up the API key and get user info
        cursor.execute(
            """
            SELECT uak.*, u.email, u.role, u.is_active as user_active
            FROM user_api_keys uak
            JOIN users u ON uak.user_id = u.user_id
            WHERE uak.key_hash = ? AND uak.is_active = 1
        """,
            (key_hash,),
        )

        key_record = cursor.fetchone()
        conn.close()

        if not key_record:
            return False, None, "Invalid API key"

        # Check if user is active
        if not key_record["user_active"]:
            return False, None, "User account is inactive"

        # Check if key is expired
        if key_record["expires_at"]:
            expires_at = datetime.datetime.fromisoformat(key_record["expires_at"])
            if datetime.datetime.now() > expires_at:
                return False, None, "API key has expired"

        # Update last_used timestamp
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE user_api_keys
                    SET last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (key_record["id"],),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Warning: Could not update last_used timestamp: {e}")

        # Return user info in format compatible with existing auth system
        user_info = {
            "user_id": key_record["user_id"],
            "email": key_record["email"],
            "role": key_record["role"],
            "api_key_id": key_record["id"],
            "api_key_name": key_record["name"],
            "access_scope": json.loads(key_record["access_scope"])
            if key_record["access_scope"]
            else ["read"],
        }

        return True, user_info, None

    except Exception as e:
        print(f"Error validating API key: {e}")
        return False, None, "Internal server error"


def require_api_key_auth(f):
    """Decorator to require valid API key authentication."""

    def decorated_function(*args, **kwargs):
        is_valid, user_info, error_msg = validate_api_key_from_header()

        if not is_valid:
            return jsonify(
                {"error": f"API key authentication failed: {error_msg}"}
            ), 401

        # Inject user info into Flask's g object (similar to session auth)
        g.current_user = type("User", (), user_info)()
        g.auth_method = "api_key"

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


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
            f"[API] Comparing with IOC #{i}: '{stored_value}' "
            f"(lower: '{stored_value_lower}')"
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


# Authentication endpoints
@ioc_bp.route("/api/login", methods=["POST"])
def login():
    """Authenticate user and create session."""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Authenticate user
        user = get_user_by_credentials(username, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        # Create session
        session_token = create_session(user.user_id)
        if not session_token:
            return jsonify({"error": "Failed to create session"}), 500

        # Set session cookie
        session["user_id"] = user.user_id
        session["session_token"] = session_token
        session.permanent = True

        return jsonify(
            {
                "message": "Login successful",
                "user": user.to_dict(),
                "session_token": session_token,
            }
        )

    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/logout", methods=["POST"])
def logout():
    """Logout user and invalidate session."""
    try:
        # Get session token from header or session
        session_token = request.headers.get("X-Session-Token") or session.get(
            "session_token"
        )

        if session_token:
            # Invalidate session in database
            invalidate_session(session_token)

        # Clear Flask session
        session.clear()

        return jsonify({"message": "Logout successful"})

    except Exception as e:
        print(f"Error during logout: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/request-password-reset", methods=["POST"])
def request_password_reset():
    """Request a password reset token via email."""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"error": "Email address is required"}), 400

        # Basic email validation
        if "@" not in email or "." not in email:
            return jsonify({"error": "Invalid email address format"}), 400

        # Get client IP for logging
        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        # Create password reset token
        reset_token = create_password_reset_token(email, client_ip)

        if reset_token:
            # Send password reset email
            # Note: We get username from the token validation for security
            token_info = validate_password_reset_token(reset_token)
            if token_info:
                email_sent = send_password_reset_email(
                    email=email,
                    username=token_info["username"],
                    reset_token=reset_token,
                )

                if email_sent:
                    print(f"Password reset email sent to {email}")
                else:
                    print(f"Failed to send password reset email to {email}")

        # Always return success to prevent email enumeration attacks
        return jsonify(
            {
                "message": "If an account with that email exists, a password reset link has been sent."
            }
        )

    except Exception as e:
        print(f"Error during password reset request: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/reset-password", methods=["POST"])
def reset_password():
    """Reset user password using a valid token."""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        token = data.get("token", "").strip()
        new_password = data.get("new_password", "")

        if not token:
            return jsonify({"error": "Reset token is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        # Password strength validation
        if len(new_password) < 8:
            return jsonify(
                {"error": "Password must be at least 8 characters long"}
            ), 400

        # Validate reset token
        token_info = validate_password_reset_token(token)
        if not token_info:
            return jsonify({"error": "Invalid or expired reset token"}), 401

        # Get client IP for logging
        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        # Update user password
        password_updated = update_user_password(token_info["user_id"], new_password)
        if not password_updated:
            return jsonify({"error": "Failed to update password"}), 500

        # Mark token as used
        token_used = use_password_reset_token(token, client_ip)
        if not token_used:
            print(
                f"Warning: Failed to mark reset token as used for user {token_info['user_id']}"
            )

        # Send confirmation email
        confirmation_sent = send_password_reset_confirmation_email(
            email=token_info["email"], username=token_info["username"]
        )

        if not confirmation_sent:
            print(
                f"Warning: Failed to send password reset confirmation to {token_info['email']}"
            )

        print(
            f"Password successfully reset for user {token_info['username']} ({token_info['email']})"
        )

        return jsonify(
            {
                "message": "Password has been successfully reset. You can now log in with your new password."
            }
        )

    except Exception as e:
        print(f"Error during password reset: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/session", methods=["GET"])
def get_session():
    """Get current session information."""
    try:
        # Get session token from header or session
        session_token = request.headers.get("X-Session-Token") or session.get(
            "session_token"
        )

        if not session_token:
            return jsonify({"authenticated": False, "user": None})

        # Get user by session
        user = get_user_by_session(session_token)
        if not user:
            # Session is invalid, clear it
            session.clear()
            return jsonify({"authenticated": False, "user": None})

        return jsonify(
            {
                "authenticated": True,
                "user": user.to_dict(),
                "session_token": session_token,
            }
        )

    except Exception as e:
        print(f"Error getting session: {e}")
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


@ioc_bp.route("/api/auth/token-info", methods=["GET"])
@require_authentication()
def get_token_info():
    """Get current authentication token information."""
    try:
        current_user = g.current_user

        # Get session token from header or session
        session_token = request.headers.get("X-Session-Token") or session.get(
            "session_token"
        )

        if not session_token:
            return jsonify({"error": "No active session"}), 401

        # Get session info from database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT created_at, last_activity, expires_at
            FROM user_sessions
            WHERE session_token = ? AND user_id = ? AND is_active = 1
        """,
            (session_token, current_user.user_id),
        )

        session_info = cursor.fetchone()
        conn.close()

        if not session_info:
            return jsonify({"error": "Session not found"}), 404

        return jsonify(
            {
                "token_type": "session",
                "user_id": current_user.user_id,
                "username": current_user.username,
                "created_at": session_info["created_at"],
                "last_activity": session_info["last_activity"],
                "expires_at": session_info["expires_at"],
                "is_active": True,
            }
        )

    except Exception as e:
        print(f"Error getting token info: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/users", methods=["GET"])
@require_role([UserRole.ADMIN])
def get_all_users():
    """Get all users with their roles. Admin only."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, email, role, is_active, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = []
        for row in cursor.fetchall():
            user_dict = dict(row)
            # Convert boolean for JSON serialization
            user_dict["is_active"] = bool(user_dict["is_active"])
            users.append(user_dict)

        conn.close()

        return jsonify({"users": users, "total": len(users)})

    except Exception as e:
        print(f"Error getting all users: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/user/<int:user_id>/role", methods=["PATCH"])
@require_role([UserRole.ADMIN])
def update_user_role(user_id):
    """Update a user's role. Admin only."""
    try:
        # Parse request data
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate role field
        if "role" not in data:
            return jsonify({"error": "role field is required"}), 400

        new_role = data["role"]
        valid_roles = ["viewer", "analyst", "auditor", "admin"]
        if new_role not in valid_roles:
            return jsonify(
                {
                    "error": "Invalid role",
                    "message": f"Role must be one of: {valid_roles}",
                }
            ), 400

        # Get current user for audit logging
        current_user = g.current_user

        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get current user data
        cursor.execute(
            """
            SELECT user_id, username, email, role, is_active, created_at
            FROM users
            WHERE user_id = ?
        """,
            (user_id,),
        )

        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        old_role = user_row["role"]

        # Prevent admin from demoting themselves
        if user_id == current_user.user_id and new_role != "admin":
            conn.close()
            return jsonify(
                {
                    "error": "Cannot demote yourself",
                    "message": "Admins cannot change their own role",
                }
            ), 400

        # Update user role
        cursor.execute(
            """
            UPDATE users
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """,
            (new_role, user_id),
        )

        # Create audit log entry for role change
        # We'll use a special format in the audit_logs table for role changes
        cursor.execute(
            """
            INSERT INTO audit_logs (alert_id, user_id, original_score, override_score, justification, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (
                -user_id,  # Use negative user_id to indicate this is a role change audit entry
                current_user.user_id,
                0,  # Not applicable for role changes
                0,  # Not applicable for role changes
                f"ROLE_CHANGE: User '{user_row['username']}' (ID: {user_id}) role changed from '{old_role}' to '{new_role}' by admin '{current_user.username}' (ID: {current_user.user_id})",
            ),
        )

        conn.commit()

        # Get updated user data
        cursor.execute(
            """
            SELECT user_id, username, email, role, is_active, created_at, updated_at
            FROM users
            WHERE user_id = ?
        """,
            (user_id,),
        )

        updated_user = dict(cursor.fetchone())
        updated_user["is_active"] = bool(updated_user["is_active"])

        conn.close()

        print(
            f"Role updated: User {user_row['username']} (ID: {user_id}) from {old_role} to {new_role} by {current_user.username}"
        )

        return jsonify(
            {
                "message": "User role updated successfully",
                "user": updated_user,
                "old_role": old_role,
                "new_role": new_role,
            }
        )

    except Exception as e:
        print(f"Error updating user role: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/audit/roles", methods=["GET"])
@require_role([UserRole.ADMIN])
def get_role_change_audit_logs():
    """Get role change audit logs. Admin only."""
    try:
        # Get query parameters
        limit = request.args.get("limit", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        user_id = request.args.get("user_id", type=int)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Build query for role change audit logs (negative alert_id indicates role changes)
        query = """
            SELECT al.*, u.username as admin_username
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE al.alert_id < 0 AND al.justification LIKE 'ROLE_CHANGE:%'
        """
        params = []

        if user_id:
            query += " AND ABS(al.alert_id) = ?"
            params.append(user_id)

        query += " ORDER BY al.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        audit_logs = []
        for row in cursor.fetchall():
            log_dict = dict(row)
            # Parse the role change information from justification
            justification = log_dict["justification"]
            if justification.startswith("ROLE_CHANGE:"):
                log_dict["action"] = "role_change"
                log_dict["target_user_id"] = abs(log_dict["alert_id"])
            audit_logs.append(log_dict)

        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM audit_logs
            WHERE alert_id < 0 AND justification LIKE 'ROLE_CHANGE:%'
        """
        count_params = []
        if user_id:
            count_query += " AND ABS(alert_id) = ?"
            count_params.append(user_id)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["total"]

        conn.close()

        return jsonify(
            {"audit_logs": audit_logs, "total": total, "limit": limit, "offset": offset}
        )

    except Exception as e:
        print(f"Error getting role change audit logs: {e}")
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


# IOC CRUD endpoints
@ioc_bp.route("/api/ioc", methods=["POST"])
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def create_ioc():
    """Create a new IOC. Requires analyst or admin role."""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        current_user = g.current_user

        # Validate required fields
        required_fields = ["ioc_type", "ioc_value", "source_feed"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate IOC type
        valid_types = ["ip", "domain", "url", "hash", "email", "file"]
        if data["ioc_type"] not in valid_types:
            return jsonify(
                {"error": f"Invalid IOC type. Must be one of: {valid_types}"}
            ), 400

        # Validate severity
        valid_severities = ["low", "medium", "high", "critical"]
        severity = data.get("severity", "medium")
        if severity not in valid_severities:
            return jsonify(
                {"error": f"Invalid severity. Must be one of: {valid_severities}"}
            ), 400

        # Validate confidence
        confidence = data.get("confidence", 50)
        if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
            return jsonify(
                {"error": "Confidence must be an integer between 0 and 100"}
            ), 400

        # Sanitize IOC value
        ioc_value = data["ioc_value"].strip()
        if not ioc_value:
            return jsonify({"error": "IOC value cannot be empty"}), 400

        # Check if IOC already exists
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "SELECT ioc_type, ioc_value FROM iocs WHERE ioc_type = ? AND ioc_value = ?",
            (data["ioc_type"], ioc_value),
        )
        existing_ioc = cursor.fetchone()

        if existing_ioc:
            conn.close()
            return jsonify({"error": "IOC already exists"}), 409

        # Create new IOC
        now = datetime.datetime.utcnow()
        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        cursor.execute(
            """
            INSERT INTO iocs (
                ioc_type, ioc_value, source_feed, first_seen, last_seen,
                score, category, severity, tags, confidence, created_by,
                updated_by, created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["ioc_type"],
                ioc_value,
                data["source_feed"],
                now,
                now,
                data.get("score", 0),
                data.get("category", "low"),
                severity,
                json.dumps(tags),
                confidence,
                current_user.user_id,
                current_user.user_id,
                now,
                now,
                True,
            ),
        )

        # Log the creation
        cursor.execute(
            """
            INSERT INTO ioc_audit_logs (
                ioc_type, ioc_value, action, user_id, changes, justification,
                timestamp, source_ip, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["ioc_type"],
                ioc_value,
                "CREATE",
                current_user.user_id,
                json.dumps({"created": data}),
                data.get("justification", "IOC created via API"),
                now,
                request.remote_addr,
                request.headers.get("User-Agent", ""),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify(
            {
                "message": "IOC created successfully",
                "ioc": {
                    "ioc_type": data["ioc_type"],
                    "ioc_value": ioc_value,
                    "source_feed": data["source_feed"],
                    "severity": severity,
                    "confidence": confidence,
                    "tags": tags,
                    "created_by": current_user.user_id,
                    "created_at": now.isoformat(),
                },
            }
        ), 201

    except Exception as e:
        print(f"Error creating IOC: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/ioc/<path:ioc_value>", methods=["PATCH"])
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def update_ioc(ioc_value):
    """Update an existing IOC. Requires analyst or admin role."""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        current_user = g.current_user

        # Get IOC type from query parameter or data
        ioc_type = request.args.get("type") or data.get("ioc_type")
        if not ioc_type:
            return jsonify({"error": "IOC type must be provided"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Check if IOC exists
        cursor.execute(
            "SELECT * FROM iocs WHERE ioc_type = ? AND ioc_value = ? AND is_active = 1",
            (ioc_type, ioc_value),
        )
        existing_ioc = cursor.fetchone()

        if not existing_ioc:
            conn.close()
            return jsonify({"error": "IOC not found"}), 404

        # Build update query dynamically
        update_fields = []
        update_values = []
        changes = {}

        # Fields that can be updated
        updatable_fields = {
            "source_feed": str,
            "score": int,
            "category": str,
            "severity": str,
            "confidence": int,
            "tags": list,
            "summary": str,
        }

        for field, field_type in updatable_fields.items():
            if field in data:
                new_value = data[field]

                # Type validation
                if field_type is int and not isinstance(new_value, int):
                    return jsonify({"error": f"{field} must be an integer"}), 400
                elif field_type is str and not isinstance(new_value, str):
                    return jsonify({"error": f"{field} must be a string"}), 400
                elif field_type is list and not isinstance(new_value, list):
                    if isinstance(new_value, str):
                        new_value = [
                            tag.strip() for tag in new_value.split(",") if tag.strip()
                        ]
                    else:
                        return jsonify(
                            {
                                "error": f"{field} must be a list or comma-separated string"
                            }
                        ), 400

                # Special validations
                if field == "severity" and new_value not in [
                    "low",
                    "medium",
                    "high",
                    "critical",
                ]:
                    return jsonify({"error": "Invalid severity"}), 400
                elif field == "confidence" and (new_value < 0 or new_value > 100):
                    return jsonify(
                        {"error": "Confidence must be between 0 and 100"}
                    ), 400

                # Store for audit log
                old_value = (
                    existing_ioc[field] if field in existing_ioc.keys() else None
                )
                if field == "tags" and old_value:
                    old_value = (
                        json.loads(old_value)
                        if isinstance(old_value, str)
                        else old_value
                    )

                if old_value != new_value:
                    changes[field] = {"old": old_value, "new": new_value}
                    update_fields.append(f"{field} = ?")
                    if field == "tags":
                        update_values.append(json.dumps(new_value))
                    else:
                        update_values.append(new_value)

        if not update_fields:
            conn.close()
            return jsonify({"message": "No changes detected"}), 200

        # Add updated_by and updated_at
        update_fields.extend(["updated_by = ?", "updated_at = ?"])
        now = datetime.datetime.utcnow()
        update_values.extend([current_user.user_id, now])

        # Add WHERE clause values
        update_values.extend([ioc_type, ioc_value])

        # Execute update
        update_query = f"""
            UPDATE iocs SET {", ".join(update_fields)}
            WHERE ioc_type = ? AND ioc_value = ?
        """
        cursor.execute(update_query, update_values)

        # Log the update
        cursor.execute(
            """
            INSERT INTO ioc_audit_logs (
                ioc_type, ioc_value, action, user_id, changes, justification,
                timestamp, source_ip, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ioc_type,
                ioc_value,
                "UPDATE",
                current_user.user_id,
                json.dumps(changes),
                data.get("justification", "IOC updated via API"),
                now,
                request.remote_addr,
                request.headers.get("User-Agent", ""),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "IOC updated successfully", "changes": changes}), 200

    except Exception as e:
        print(f"Error updating IOC: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/ioc/<path:ioc_value>", methods=["DELETE"])
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def delete_ioc(ioc_value):
    """Delete an IOC (soft delete). Requires analyst or admin role."""
    try:
        current_user = g.current_user

        # Get IOC type from query parameter
        ioc_type = request.args.get("type")
        if not ioc_type:
            return jsonify({"error": "IOC type must be provided"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Check if IOC exists and is active
        cursor.execute(
            "SELECT * FROM iocs WHERE ioc_type = ? AND ioc_value = ? AND is_active = 1",
            (ioc_type, ioc_value),
        )
        existing_ioc = cursor.fetchone()

        if not existing_ioc:
            conn.close()
            return jsonify({"error": "IOC not found"}), 404

        # Soft delete the IOC
        now = datetime.datetime.utcnow()
        cursor.execute(
            """
            UPDATE iocs SET is_active = 0, updated_by = ?, updated_at = ?
            WHERE ioc_type = ? AND ioc_value = ?
        """,
            (current_user.user_id, now, ioc_type, ioc_value),
        )

        # Log the deletion
        cursor.execute(
            """
            INSERT INTO ioc_audit_logs (
                ioc_type, ioc_value, action, user_id, changes, justification,
                timestamp, source_ip, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ioc_type,
                ioc_value,
                "DELETE",
                current_user.user_id,
                json.dumps({"deleted": True}),
                request.get_json().get("justification", "IOC deleted via API")
                if request.is_json
                else "IOC deleted via API",
                now,
                request.remote_addr,
                request.headers.get("User-Agent", ""),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "IOC deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting IOC: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Legacy import endpoint removed - use /api/feeds/upload instead


# Legacy parsing functions removed - now handled by FeedIngestionService


# ===== USER API KEY MANAGEMENT ROUTES =====


@ioc_bp.route("/api/user/api-keys", methods=["GET"])
@require_authentication()
def list_user_api_keys():
    """List all API keys for the current user."""
    try:
        current_user = g.current_user

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get all active API keys for the user
        cursor.execute(
            """
            SELECT id, name, key_preview, access_scope, created_at, last_used,
                   expires_at, is_active, rate_limit_tier, description
            FROM user_api_keys
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """,
            (current_user.user_id,),
        )

        keys = []
        for row in cursor.fetchall():
            key_data = dict(row)
            # Parse access_scope JSON
            try:
                key_data["access_scope"] = (
                    json.loads(key_data["access_scope"])
                    if key_data["access_scope"]
                    else ["read"]
                )
            except:
                key_data["access_scope"] = ["read"]

            keys.append(key_data)

        conn.close()

        return jsonify({"api_keys": keys})

    except Exception as e:
        print(f"Error listing API keys: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/user/api-keys", methods=["POST"])
@require_authentication()
def create_user_api_key():
    """Create a new API key for the current user."""
    try:
        current_user = g.current_user
        data = request.get_json()

        # Validate required fields
        if not data or not data.get("name"):
            return jsonify({"error": "API key name is required"}), 400

        name = data["name"].strip()
        if len(name) < 3:
            return jsonify({"error": "API key name must be at least 3 characters"}), 400

        # Optional fields with defaults
        description = data.get("description", "").strip()
        access_scope = data.get("access_scope", ["read"])
        rate_limit_tier = data.get("rate_limit_tier", "standard")
        ip_restrictions = data.get("ip_restrictions", "").strip()
        expires_in = data.get(
            "expires_in"
        )  # e.g., "30d", "90d", "1y", or None for never

        # Validate access scope
        valid_scopes = ["read", "write", "admin"]
        if not isinstance(access_scope, list) or not all(
            scope in valid_scopes for scope in access_scope
        ):
            return jsonify({"error": "Invalid access scope"}), 400

        # Calculate expiration date
        expires_at = None
        if expires_in:
            try:
                if expires_in == "30d":
                    expires_at = datetime.datetime.now() + datetime.timedelta(days=30)
                elif expires_in == "90d":
                    expires_at = datetime.datetime.now() + datetime.timedelta(days=90)
                elif expires_in == "1y":
                    expires_at = datetime.datetime.now() + datetime.timedelta(days=365)
                else:
                    return jsonify({"error": "Invalid expiration period"}), 400
            except:
                return jsonify({"error": "Invalid expiration period"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Check if user already has a key with this name
        cursor.execute(
            """
            SELECT id FROM user_api_keys
            WHERE user_id = ? AND name = ? AND is_active = 1
        """,
            (current_user.user_id, name),
        )

        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "API key with this name already exists"}), 409

        # Generate the API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_preview = create_api_key_preview(api_key)
        key_id = secrets.token_urlsafe(16)

        # Insert the new API key
        cursor.execute(
            """
            INSERT INTO user_api_keys
            (id, user_id, name, key_hash, key_preview, access_scope,
             expires_at, rate_limit_tier, ip_restrictions, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                key_id,
                current_user.user_id,
                name,
                key_hash,
                key_preview,
                json.dumps(access_scope),
                expires_at,
                rate_limit_tier,
                ip_restrictions if ip_restrictions else None,
                description if description else None,
            ),
        )

        # TODO: Add audit logging for API key creation
        # Note: Current audit_logs table is specific to alert overrides
        print(f"[API] Created API key '{name}' for user {current_user.user_id}")

        conn.commit()
        conn.close()

        return jsonify(
            {
                "message": "API key created successfully",
                "api_key": api_key,  # Only returned once!
                "key_id": key_id,
                "name": name,
                "key_preview": key_preview,
                "access_scope": access_scope,
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
        ), 201

    except Exception as e:
        print(f"Error creating API key: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/user/api-keys/<key_id>/rotate", methods=["POST"])
@require_authentication()
def rotate_user_api_key(key_id):
    """Rotate (regenerate) an existing API key."""
    try:
        current_user = g.current_user

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Check if the key exists and belongs to the user
        cursor.execute(
            """
            SELECT id, name, user_id FROM user_api_keys
            WHERE id = ? AND user_id = ? AND is_active = 1
        """,
            (key_id, current_user.user_id),
        )

        key_record = cursor.fetchone()
        if not key_record:
            conn.close()
            return jsonify({"error": "API key not found"}), 404

        # Generate new API key
        new_api_key = generate_api_key()
        new_key_hash = hash_api_key(new_api_key)
        new_key_preview = create_api_key_preview(new_api_key)

        # Update the key in database
        cursor.execute(
            """
            UPDATE user_api_keys
            SET key_hash = ?, key_preview = ?, created_at = CURRENT_TIMESTAMP, last_used = NULL
            WHERE id = ?
        """,
            (new_key_hash, new_key_preview, key_id),
        )

        # TODO: Add audit logging for API key rotation
        print(
            f"[API] Rotated API key '{key_record['name']}' for user {current_user.user_id}"
        )

        conn.commit()
        conn.close()

        return jsonify(
            {
                "message": "API key rotated successfully",
                "api_key": new_api_key,  # Only returned once!
                "key_id": key_id,
                "name": key_record["name"],
                "key_preview": new_key_preview,
            }
        )

    except Exception as e:
        print(f"Error rotating API key: {e}")
        return jsonify({"error": "Internal server error"}), 500


@ioc_bp.route("/api/user/api-keys/<key_id>", methods=["DELETE"])
@require_authentication()
def revoke_user_api_key(key_id):
    """Revoke (delete) an API key."""
    try:
        current_user = g.current_user

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Check if the key exists and belongs to the user
        cursor.execute(
            """
            SELECT id, name, user_id FROM user_api_keys
            WHERE id = ? AND user_id = ? AND is_active = 1
        """,
            (key_id, current_user.user_id),
        )

        key_record = cursor.fetchone()
        if not key_record:
            conn.close()
            return jsonify({"error": "API key not found"}), 404

        # Soft delete the key (set is_active = 0)
        cursor.execute(
            """
            UPDATE user_api_keys
            SET is_active = 0
            WHERE id = ?
        """,
            (key_id,),
        )

        # TODO: Add audit logging for API key revocation
        print(
            f"[API] Revoked API key '{key_record['name']}' for user {current_user.user_id}"
        )

        conn.commit()
        conn.close()

        return jsonify(
            {
                "message": "API key revoked successfully",
                "key_id": key_id,
                "name": key_record["name"],
            }
        )

    except Exception as e:
        print(f"Error revoking API key: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Register the Blueprint with the main app
app.register_blueprint(ioc_bp)


# Removed /iocs redirect to avoid conflict with React UI routing
# @app.route("/iocs")
# def iocs_redirect():
#     """Redirect /iocs to /api/iocs with the same query parameters."""
#     return redirect(url_for("ioc.get_iocs", **request.args))


@app.route("/")
def index():
    return "SentinelForge API Server is running. Use /api/iocs to get IOC details."


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found", "details": str(error)}), 404


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


# ============================================================================
# THREAT FEED INGESTION ENDPOINTS
# ============================================================================


@app.route("/api/feeds", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def get_feeds():
    """Get all registered threat feeds."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, u.username as created_by_username
            FROM threat_feeds f
            LEFT JOIN users u ON f.created_by = u.user_id
            ORDER BY f.created_at DESC
        """)

        feeds = []
        for row in cursor.fetchall():
            feed = dict(row)
            # Parse format_config JSON
            if feed.get("format_config"):
                try:
                    feed["format_config"] = json.loads(feed["format_config"])
                except (json.JSONDecodeError, TypeError):
                    feed["format_config"] = {}
            feeds.append(feed)

        conn.close()
        return jsonify({"feeds": feeds})

    except Exception as e:
        return jsonify({"error": f"Failed to get feeds: {str(e)}"}), 500


@app.route("/api/feeds", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def create_feed():
    """Create a new threat feed configuration."""
    try:
        data = request.get_json()
        current_user = g.current_user

        # Validate required fields
        required_fields = ["name", "feed_type"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate feed type
        valid_types = ["csv", "json", "txt", "stix"]
        if data["feed_type"] not in valid_types:
            return jsonify(
                {
                    "error": f"Invalid feed type. Must be one of: {', '.join(valid_types)}"
                }
            ), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Check for duplicate name
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM threat_feeds WHERE name = ?", (data["name"],)
        )
        if cursor.fetchone()["count"] > 0:
            conn.close()
            return jsonify({"error": "Feed name already exists"}), 409

        # Insert new feed
        now = datetime.datetime.utcnow()
        cursor.execute(
            """
            INSERT INTO threat_feeds (
                name, description, url, feed_type, format_config,
                is_active, auto_import, import_frequency, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data.get("description", ""),
                data.get("url", ""),
                data["feed_type"],
                json.dumps(data.get("format_config", {})),
                data.get("is_active", True),
                data.get("auto_import", False),
                data.get("import_frequency", 24),
                current_user.user_id,
                now,
                now,
            ),
        )

        feed_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify(
            {"message": "Feed created successfully", "feed_id": feed_id}
        ), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create feed: {str(e)}"}), 500


@app.route("/api/feeds/<int:feed_id>", methods=["PATCH"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def update_feed(feed_id):
    """Update a threat feed configuration."""
    try:
        data = request.get_json()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Check if feed exists
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM threat_feeds WHERE id = ?", (feed_id,))
        feed = cursor.fetchone()
        if not feed:
            conn.close()
            return jsonify({"error": "Feed not found"}), 404

        # Build update query
        update_fields = []
        update_values = []

        for field in [
            "name",
            "description",
            "url",
            "feed_type",
            "is_active",
            "auto_import",
            "import_frequency",
        ]:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])

        if "format_config" in data:
            update_fields.append("format_config = ?")
            update_values.append(json.dumps(data["format_config"]))

        if update_fields:
            update_fields.append("updated_at = ?")
            update_values.append(datetime.datetime.utcnow())
            update_values.append(feed_id)

            query = f"UPDATE threat_feeds SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            conn.commit()

        conn.close()
        return jsonify({"message": "Feed updated successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to update feed: {str(e)}"}), 500


@app.route("/api/feeds/<int:feed_id>", methods=["DELETE"])
@require_authentication()
@require_role([UserRole.ADMIN])
def delete_feed(feed_id):
    """Delete a threat feed configuration."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("DELETE FROM threat_feeds WHERE id = ?", (feed_id,))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Feed not found"}), 404

        conn.commit()
        conn.close()
        return jsonify({"message": "Feed deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete feed: {str(e)}"}), 500


@app.route("/api/feeds/upload", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def upload_feed():
    """Upload and import IOCs from a file."""
    try:
        current_user = g.current_user

        # Check if file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Get form data
        source_feed = request.form.get("source_feed", "Manual Upload")
        justification = request.form.get("justification", "")

        # Validate file type
        allowed_extensions = {".csv", ".json", ".txt", ".stix"}
        file_ext = (
            "." + file.filename.rsplit(".", 1)[-1].lower()
            if "." in file.filename
            else ""
        )

        if file_ext not in allowed_extensions:
            return jsonify(
                {
                    "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                }
            ), 400

        # Read file content
        try:
            content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "File must be UTF-8 encoded"}), 400

        # Initialize ingestion service
        ingestion_service = FeedIngestionService()

        # Import IOCs
        result = ingestion_service.import_from_content(
            content=content,
            filename=secure_filename(file.filename),
            source_feed=source_feed,
            user_id=current_user.user_id,
            justification=justification,
        )

        if result["success"]:
            return jsonify(
                {
                    "message": "File imported successfully",
                    "imported_count": result["imported_count"],
                    "skipped_count": result["skipped_count"],
                    "error_count": result["error_count"],
                    "errors": result.get("errors", []),
                    "total_records": result["total_records"],
                    "duration_seconds": result["duration_seconds"],
                }
            )
        else:
            return jsonify(
                {
                    "error": result.get("error", "Import failed"),
                    "imported_count": result["imported_count"],
                    "skipped_count": result["skipped_count"],
                    "error_count": result["error_count"],
                    "errors": result.get("errors", []),
                }
            ), 400

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route("/api/feeds/<int:feed_id>/import", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.ADMIN])
def import_from_feed(feed_id):
    """Import IOCs from a registered feed URL."""
    try:
        current_user = g.current_user
        data = request.get_json() or {}
        justification = data.get("justification", "")

        # Get feed configuration
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM threat_feeds WHERE id = ?", (feed_id,))
        feed = cursor.fetchone()
        conn.close()

        if not feed:
            return jsonify({"error": "Feed not found"}), 404

        if not feed["url"]:
            return jsonify({"error": "Feed has no URL configured"}), 400

        if not feed["is_active"]:
            return jsonify({"error": "Feed is not active"}), 400

        # Fetch content from URL
        try:
            # Prepare headers for authentication if needed
            headers = {"User-Agent": "SentinelForge/1.0 (Threat Intelligence Platform)"}

            # Add API key if configured
            if feed.get("api_key"):
                if "alienvault" in feed["url"].lower() or "otx" in feed["url"].lower():
                    headers["X-OTX-API-KEY"] = feed["api_key"]
                elif "virustotal" in feed["url"].lower():
                    headers["x-apikey"] = feed["api_key"]
                else:
                    # Generic API key header
                    headers["Authorization"] = f"Bearer {feed['api_key']}"

            print(f"[FEED] Fetching from URL: {feed['url']}")
            response = requests.get(feed["url"], headers=headers, timeout=30)

            # Handle authentication errors specifically
            if response.status_code == 401:
                error_msg = (
                    "Authentication required - please configure API key for this feed"
                )
                print(f"[FEED] Authentication error for {feed['name']}: {error_msg}")
                return jsonify({"error": error_msg}), 401
            elif response.status_code == 403:
                error_msg = "Access forbidden - check API key permissions"
                print(f"[FEED] Access forbidden for {feed['name']}: {error_msg}")
                return jsonify({"error": error_msg}), 403
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded - please try again later"
                print(f"[FEED] Rate limit for {feed['name']}: {error_msg}")
                return jsonify({"error": error_msg}), 429

            response.raise_for_status()
            content = response.text
            print(
                f"[FEED] Successfully fetched {len(content)} bytes from {feed['name']}"
            )

        except requests.Timeout:
            error_msg = (
                "Request timeout - feed server did not respond within 30 seconds"
            )
            print(f"[FEED] Timeout error for {feed['name']}")
            return jsonify({"error": error_msg}), 408
        except requests.ConnectionError:
            error_msg = "Connection error - unable to reach feed server"
            print(f"[FEED] Connection error for {feed['name']}")
            return jsonify({"error": error_msg}), 503
        except requests.RequestException as e:
            error_msg = f"Failed to fetch feed: {str(e)}"
            print(f"[FEED] Request error for {feed['name']}: {error_msg}")
            return jsonify({"error": error_msg}), 400

        # Initialize ingestion service
        ingestion_service = FeedIngestionService()

        # Import IOCs
        result = ingestion_service.import_from_content(
            content=content,
            filename=f"feed_{feed_id}_{feed['feed_type']}",
            source_feed=feed["name"],
            user_id=current_user.user_id,
            justification=justification,
            feed_id=feed_id,
        )

        # Update feed last import status
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE threat_feeds
                SET last_import = ?, last_import_status = ?, last_import_count = ?
                WHERE id = ?
            """,
                (
                    datetime.datetime.utcnow(),
                    result["import_status"],
                    result["imported_count"],
                    feed_id,
                ),
            )
            conn.commit()
            conn.close()

        if result["success"]:
            return jsonify(
                {
                    "message": "Feed imported successfully",
                    "imported_count": result["imported_count"],
                    "skipped_count": result["skipped_count"],
                    "error_count": result["error_count"],
                    "errors": result.get("errors", []),
                    "total_records": result["total_records"],
                    "duration_seconds": result["duration_seconds"],
                }
            )
        else:
            return jsonify(
                {
                    "error": result.get("error", "Import failed"),
                    "imported_count": result["imported_count"],
                    "skipped_count": result["skipped_count"],
                    "error_count": result["error_count"],
                    "errors": result.get("errors", []),
                }
            ), 400

    except Exception as e:
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@app.route("/api/feeds/health", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def check_feeds_health():
    """Check health status of all threat feeds with caching support."""
    from services.feed_health_monitor import FeedHealthMonitor
    import time
    from datetime import datetime, timezone

    try:
        # Parse query parameters
        force_check = request.args.get("force", "false").lower() == "true"
        feed_id = request.args.get("feed_id", type=int)

        # Initialize health monitor
        monitor = FeedHealthMonitor()
        current_user = g.current_user

        # Check if we should use cached results or force new check
        if not force_check:
            cached_health = monitor.get_cached_health()
            if cached_health and "_last_update" in cached_health:
                last_update = cached_health["_last_update"]
                cache_age_seconds = (
                    datetime.now(timezone.utc) - last_update
                ).total_seconds()

                # Use cache if less than 5 minutes old
                if cache_age_seconds < 300:
                    # Convert cached results to API format
                    health_results = []
                    for feed_id_key, result in cached_health.items():
                        if feed_id_key != "_last_update":
                            # Convert datetime back to string for JSON response
                            if isinstance(result.get("last_checked"), datetime):
                                result["last_checked"] = result[
                                    "last_checked"
                                ].isoformat()
                            health_results.append(result)

                    # Calculate summary
                    total_feeds = len(health_results)
                    healthy_feeds = len(
                        [r for r in health_results if r["status"] == "ok"]
                    )

                    return jsonify(
                        {
                            "success": True,
                            "summary": {
                                "total_feeds": total_feeds,
                                "healthy_feeds": healthy_feeds,
                                "unhealthy_feeds": total_feeds - healthy_feeds,
                                "health_percentage": round(
                                    (healthy_feeds / total_feeds * 100)
                                    if total_feeds > 0
                                    else 0,
                                    1,
                                ),
                            },
                            "feeds": health_results,
                            "checked_at": last_update.isoformat(),
                            "checked_by": current_user.username,
                            "from_cache": True,
                            "cache_age_seconds": int(cache_age_seconds),
                        }
                    )

        # Run fresh health check
        result = monitor.run_health_check(
            feed_id=feed_id, checked_by=current_user.user_id
        )

        if not result.get("success"):
            return jsonify({"error": result.get("error", "Health check failed")}), 500

        # Add API-specific fields
        result["checked_by"] = current_user.username
        result["from_cache"] = False

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500


@app.route("/api/feeds/health/start", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def start_health_check_with_progress():
    """Start a health check with progress tracking."""
    from services.feed_health_monitor import FeedHealthMonitor
    import uuid
    import threading

    try:
        # Parse request parameters
        data = request.get_json() if request.is_json else {}
        feed_id = data.get("feed_id") or request.args.get("feed_id", type=int)

        current_user = g.current_user
        monitor = FeedHealthMonitor()

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Get feeds count for progress tracking
        if feed_id:
            total_feeds = 1
        else:
            feeds = monitor.get_active_feeds()
            total_feeds = len(feeds)

        if total_feeds == 0:
            return jsonify({"error": "No active feeds found"}), 400

        # Create progress session
        session = monitor.create_progress_session(
            session_id, total_feeds, current_user.user_id
        )

        # Start health check in background thread
        def run_background_check():
            try:
                monitor.run_health_check(
                    feed_id=feed_id,
                    checked_by=current_user.user_id,
                    progress_session_id=session_id,
                )
            except Exception as e:
                monitor.update_progress(session_id, status="error", error=str(e))

        thread = threading.Thread(target=run_background_check, daemon=True)
        thread.start()

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "message": "Health check started",
                "progress_url": f"/api/feeds/health/progress/{session_id}",
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to start health check: {str(e)}"}), 500


@app.route("/api/feeds/health/progress/<session_id>", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def get_health_check_progress(session_id):
    """Get real-time progress for a health check session using Server-Sent Events."""
    from services.feed_health_monitor import FeedHealthMonitor
    from flask import Response
    import json
    import time

    def generate_progress_stream():
        monitor = FeedHealthMonitor()

        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

        last_status = None
        while True:
            try:
                progress = monitor.get_progress(session_id)

                if "error" in progress:
                    yield f"data: {json.dumps({'type': 'error', 'error': progress['error']})}\n\n"
                    break

                # Only send updates when status changes
                current_status = {
                    "status": progress["status"],
                    "completed_feeds": progress["completed_feeds"],
                    "total_feeds": progress["total_feeds"],
                    "current_feed": progress.get("current_feed"),
                    "estimated_completion": progress.get("estimated_completion"),
                }

                if current_status != last_status:
                    yield f"data: {json.dumps({'type': 'progress', **current_status})}\n\n"
                    last_status = current_status

                # Send individual feed results
                if "results" in progress and progress["results"]:
                    for result in progress["results"]:
                        yield f"data: {json.dumps({'type': 'feed_result', 'result': result})}\n\n"
                    # Clear results to avoid resending
                    monitor.update_progress(session_id, results=[])

                # Send errors
                if "errors" in progress and progress["errors"]:
                    for error in progress["errors"]:
                        yield f"data: {json.dumps({'type': 'error', 'error': error})}\n\n"
                    # Clear errors to avoid resending
                    monitor.update_progress(session_id, errors=[])

                # Check if completed or cancelled
                if progress["status"] in ["completed", "cancelled", "error"]:
                    yield f"data: {json.dumps({'type': 'finished', 'status': progress['status']})}\n\n"
                    # Clean up session after a delay
                    time.sleep(2)
                    monitor.cleanup_progress_session(session_id)
                    break

                time.sleep(0.5)  # Poll every 500ms

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                break

    return Response(
        generate_progress_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.route("/api/feeds/health/cancel/<session_id>", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def cancel_health_check(session_id):
    """Cancel a running health check session."""
    from services.feed_health_monitor import FeedHealthMonitor

    try:
        monitor = FeedHealthMonitor()
        success = monitor.cancel_progress_session(session_id)

        if success:
            return jsonify({"success": True, "message": "Health check cancelled"})
        else:
            return jsonify({"error": "Session not found or already completed"}), 404

    except Exception as e:
        return jsonify({"error": f"Failed to cancel health check: {str(e)}"}), 500


@app.route("/api/feeds/health/demo", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def demo_health_check_with_progress():
    """Demo health check with simulated progress for testing the UI."""
    import uuid
    import threading
    import time
    from datetime import datetime, timezone

    try:
        current_user = g.current_user
        session_id = str(uuid.uuid4())

        # Mock feeds for demo
        demo_feeds = [
            {
                "name": "IPsum",
                "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
            },
            {
                "name": "MalwareDomainList",
                "url": "http://www.malwaredomainlist.com/hostslist/hosts.txt",
            },
            {
                "name": "Abuse.ch URLhaus",
                "url": "https://urlhaus.abuse.ch/downloads/csv/",
            },
            {
                "name": "PhishTank",
                "url": "http://data.phishtank.com/data/online-valid.csv",
            },
            {
                "name": "AlienVault OTX",
                "url": "https://reputation.alienvault.com/reputation.data",
            },
        ]

        # Create a simple progress tracker
        progress_data = {
            "session_id": session_id,
            "total_feeds": len(demo_feeds),
            "completed_feeds": 0,
            "current_feed": None,
            "status": "starting",
            "start_time": datetime.now(timezone.utc),
            "results": [],
            "errors": [],
        }

        # Store in a simple global dict for demo (in production, use proper storage)
        if not hasattr(app, "demo_sessions"):
            app.demo_sessions = {}
        app.demo_sessions[session_id] = progress_data

        def run_demo_health_check():
            try:
                app.demo_sessions[session_id]["status"] = "running"

                for i, feed in enumerate(demo_feeds):
                    # Update current feed
                    app.demo_sessions[session_id]["current_feed"] = {
                        "name": feed["name"],
                        "url": feed["url"],
                        "index": i + 1,
                    }

                    # Simulate checking time (1-3 seconds per feed)
                    time.sleep(2)

                    # Simulate result
                    status = "ok" if i < 4 else "timeout"  # Last feed fails
                    result = {
                        "feed_id": i + 1,
                        "feed_name": feed["name"],
                        "url": feed["url"],
                        "status": status,
                        "http_code": 200 if status == "ok" else None,
                        "response_time_ms": 150 + (i * 50),
                        "error_message": None
                        if status == "ok"
                        else "Request timed out",
                        "last_checked": datetime.now(timezone.utc).isoformat(),
                        "is_active": True,
                    }

                    app.demo_sessions[session_id]["results"].append(result)
                    app.demo_sessions[session_id]["completed_feeds"] = i + 1
                    app.demo_sessions[session_id]["current_feed"] = None

                app.demo_sessions[session_id]["status"] = "completed"

                # Clean up after 30 seconds
                time.sleep(30)
                if session_id in app.demo_sessions:
                    del app.demo_sessions[session_id]

            except Exception as e:
                app.demo_sessions[session_id]["status"] = "error"
                app.demo_sessions[session_id]["errors"].append(str(e))

        # Start background thread
        thread = threading.Thread(target=run_demo_health_check, daemon=True)
        thread.start()

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "message": "Demo health check started",
                "progress_url": f"/api/feeds/health/demo/progress/{session_id}",
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to start demo health check: {str(e)}"}), 500


@app.route("/api/feeds/health/demo/progress/<session_id>", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def get_demo_health_check_progress(session_id):
    """Get demo health check progress using Server-Sent Events."""
    from flask import Response
    import json
    import time

    def generate_demo_progress_stream():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

        if not hasattr(app, "demo_sessions") or session_id not in app.demo_sessions:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Session not found'})}\n\n"
            return

        last_status = None
        last_results_count = 0

        while True:
            try:
                if session_id not in app.demo_sessions:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Session expired'})}\n\n"
                    break

                progress = app.demo_sessions[session_id]

                # Send progress updates
                current_status = {
                    "status": progress["status"],
                    "completed_feeds": progress["completed_feeds"],
                    "total_feeds": progress["total_feeds"],
                    "current_feed": progress.get("current_feed"),
                }

                if current_status != last_status:
                    yield f"data: {json.dumps({'type': 'progress', **current_status})}\n\n"
                    last_status = current_status

                # Send new results
                results = progress.get("results", [])
                if len(results) > last_results_count:
                    for result in results[last_results_count:]:
                        yield f"data: {json.dumps({'type': 'feed_result', 'result': result})}\n\n"
                    last_results_count = len(results)

                # Send errors
                errors = progress.get("errors", [])
                for error in errors:
                    yield f"data: {json.dumps({'type': 'error', 'error': error})}\n\n"

                # Check if completed
                if progress["status"] in ["completed", "cancelled", "error"]:
                    yield f"data: {json.dumps({'type': 'finished', 'status': progress['status']})}\n\n"
                    break

                time.sleep(0.5)  # Poll every 500ms

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                break

    return Response(
        generate_demo_progress_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.route("/api/feeds/health/trigger", methods=["POST"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def trigger_health_check():
    """Trigger a one-time health check for all active feeds (legacy endpoint)."""
    from services.feed_health_monitor import FeedHealthMonitor

    try:
        # Parse request parameters
        data = request.get_json() if request.is_json else {}
        feed_id = data.get("feed_id") or request.args.get("feed_id", type=int)

        current_user = g.current_user
        monitor = FeedHealthMonitor()

        # Run health check
        result = monitor.run_health_check(
            feed_id=feed_id, checked_by=current_user.user_id
        )

        if not result.get("success"):
            return jsonify({"error": result.get("error", "Health check failed")}), 500

        # Add trigger information
        result["triggered_by"] = current_user.username
        result["trigger_type"] = "manual"

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to trigger health check: {str(e)}"}), 500


@app.route("/api/feeds/health/scheduler", methods=["GET", "POST"])
@require_authentication()
@require_role([UserRole.ADMIN])
def manage_health_scheduler():
    """Manage the health check scheduler (Admin only)."""
    from services.feed_health_monitor import FeedHealthMonitor

    try:
        monitor = FeedHealthMonitor()

        if request.method == "GET":
            # Get scheduler status
            status = monitor.get_scheduler_status()
            return jsonify({"success": True, "scheduler": status})

        elif request.method == "POST":
            # Start/stop scheduler
            data = request.get_json() if request.is_json else {}
            action = data.get("action", "start")
            interval_minutes = data.get("interval_minutes", 1)

            if action == "start":
                success = monitor.start_cron_scheduler(interval_minutes)
                if success:
                    return jsonify(
                        {
                            "success": True,
                            "message": f"Health check scheduler started with {interval_minutes}-minute interval",
                            "scheduler": monitor.get_scheduler_status(),
                        }
                    )
                else:
                    return jsonify({"error": "Failed to start scheduler"}), 500

            elif action == "stop":
                monitor.stop_cron_scheduler()
                return jsonify(
                    {
                        "success": True,
                        "message": "Health check scheduler stopped",
                        "scheduler": monitor.get_scheduler_status(),
                    }
                )

            else:
                return jsonify({"error": "Invalid action. Use 'start' or 'stop'"}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to manage scheduler: {str(e)}"}), 500


@app.route("/api/feeds/health/history", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def get_feed_health_history():
    """Get feed health check history with filtering."""
    try:
        # Parse query parameters
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        feed_id = request.args.get("feed_id", type=int)
        status = request.args.get("status")
        hours = request.args.get("hours", 24, type=int)  # Default last 24 hours

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Build query with filters
        where_conditions = [
            "last_checked >= datetime('now', '-{} hours')".format(hours)
        ]
        params = []

        if feed_id:
            where_conditions.append("feed_id = ?")
            params.append(feed_id)

        if status:
            where_conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(where_conditions)

        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM feed_health_logs
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Get paginated results
        query = f"""
            SELECT fhl.*, u.username as checked_by_username
            FROM feed_health_logs fhl
            LEFT JOIN users u ON fhl.checked_by = u.user_id
            WHERE {where_clause}
            ORDER BY fhl.last_checked DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)

        health_logs = []
        for row in cursor.fetchall():
            log = dict(row)
            health_logs.append(log)

        conn.close()

        return jsonify(
            {
                "success": True,
                "health_logs": health_logs,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count,
                },
                "filters": {"feed_id": feed_id, "status": status, "hours": hours},
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get health history: {str(e)}"}), 500


@app.route("/api/admin/setup-demo-feeds", methods=["POST"])
@require_authentication()
@require_role([UserRole.ADMIN])
def setup_demo_feeds():
    """Setup demo threat feeds for testing/demo purposes. Admin only."""
    try:
        # Parse request data
        data = request.get_json() if request.is_json else {}
        confirm = data.get("confirm", False) or request.args.get("confirm") == "true"
        import_data = (
            data.get("import_data", False) or request.args.get("import_data") == "true"
        )

        if not confirm:
            return jsonify(
                {
                    "error": "Confirmation required",
                    "message": "Add ?confirm=true or include 'confirm': true in request body to proceed",
                }
            ), 400

        current_user = g.current_user

        # Demo feed configurations
        demo_feeds = [
            {
                "name": "MalwareDomainList - Domains",
                "feed_type": "txt",
                "description": "Known malicious domains from MalwareDomainList project",
                "url": "https://www.malwaredomainlist.com/hostslist/hosts.txt",
                "ioc_type": "domain",
                "format_config": {
                    "delimiter": "\n",
                    "comment_prefix": "#",
                    "extract_pattern": r"0\.0\.0\.0\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                },
                "sample_data": [
                    "malicious-domain1.com",
                    "evil-site.net",
                    "phishing-example.org",
                    "malware-host.biz",
                    "suspicious-domain.info",
                ],
            },
            {
                "name": "Abuse.ch URLhaus - Malware URLs",
                "feed_type": "csv",
                "description": "Malware URLs from Abuse.ch URLhaus database",
                "url": "https://urlhaus.abuse.ch/downloads/csv_recent/",
                "ioc_type": "url",
                "format_config": {
                    "has_header": True,
                    "delimiter": ",",
                    "url_column": "url",
                    "threat_column": "threat",
                    "tags_column": "tags",
                },
                "sample_data": [
                    {
                        "url": "http://malicious-payload.xyz/download.php?id=1234",
                        "threat": "trojan",
                        "tags": "exe,payload",
                    },
                    {
                        "url": "https://evil-site.com/malware.zip",
                        "threat": "ransomware",
                        "tags": "zip,crypto",
                    },
                    {
                        "url": "http://phishing-bank.net/login.html",
                        "threat": "phishing",
                        "tags": "banking,credential",
                    },
                    {
                        "url": "https://fake-update.org/flash_update.exe",
                        "threat": "trojan",
                        "tags": "exe,fake-update",
                    },
                ],
            },
            {
                "name": "IPsum Threat Intelligence",
                "feed_type": "txt",
                "description": "Malicious IP addresses from IPsum aggregated feeds",
                "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
                "ioc_type": "ip",
                "format_config": {
                    "delimiter": "\n",
                    "comment_prefix": "#",
                    "extract_pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                },
                "sample_data": [
                    "192.168.100.50",
                    "10.0.0.100",
                    "203.0.113.45",
                    "198.51.100.78",
                    "172.16.0.200",
                ],
            },
            {
                "name": "MITRE ATT&CK STIX Feed",
                "feed_type": "json",
                "description": "MITRE ATT&CK techniques and indicators in STIX 2.0 format",
                "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
                "ioc_type": "mixed",
                "format_config": {
                    "stix_version": "2.0",
                    "bundle_key": "objects",
                    "indicator_types": ["indicator", "malware", "tool"],
                },
                "sample_data": {
                    "type": "bundle",
                    "id": "bundle--demo-12345",
                    "objects": [
                        {
                            "type": "indicator",
                            "id": "indicator--demo-1",
                            "created": "2024-01-01T00:00:00.000Z",
                            "modified": "2024-01-01T00:00:00.000Z",
                            "pattern": "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
                            "labels": ["malicious-activity"],
                        },
                        {
                            "type": "indicator",
                            "id": "indicator--demo-2",
                            "created": "2024-01-01T00:00:00.000Z",
                            "modified": "2024-01-01T00:00:00.000Z",
                            "pattern": "[domain-name:value = 'evil-command-control.com']",
                            "labels": ["malicious-activity"],
                        },
                    ],
                },
            },
            {
                "name": "Emerging Threats - Compromised IPs",
                "feed_type": "txt",
                "description": "Compromised IP addresses from Emerging Threats",
                "url": "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt",
                "ioc_type": "ip",
                "format_config": {
                    "delimiter": "\n",
                    "comment_prefix": "#",
                    "extract_pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                },
                "sample_data": [
                    "185.220.100.240",
                    "45.142.214.48",
                    "91.219.236.166",
                    "194.147.78.112",
                    "23.129.64.131",
                ],
            },
        ]

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        feeds_created = []
        iocs_imported = 0

        try:
            # Register demo feeds
            for feed in demo_feeds:
                # Check if feed already exists
                cursor.execute(
                    "SELECT id FROM threat_feeds WHERE name = ?", (feed["name"],)
                )
                if cursor.fetchone():
                    continue  # Skip existing feeds

                # Insert feed record (let database auto-generate ID)
                cursor.execute(
                    """
                    INSERT INTO threat_feeds
                    (name, feed_type, description, url, format_config,
                     is_active, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        feed["name"],
                        feed["feed_type"],
                        feed["description"],
                        feed["url"],
                        json.dumps(feed["format_config"]),
                        1,  # is_active
                        current_user.user_id,
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    ),
                )

                # Get the generated feed ID
                feed_id = cursor.lastrowid

                feeds_created.append(
                    {"id": feed_id, "name": feed["name"], "type": feed["feed_type"]}
                )

                # Import sample data if requested
                if import_data:
                    # Create import log entry (let database auto-generate ID)
                    cursor.execute(
                        """
                        INSERT INTO feed_import_logs
                        (feed_id, feed_name, import_type, import_status, user_id, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            feed_id,
                            feed["name"],
                            "demo_setup",
                            "processing",
                            current_user.user_id,
                            datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        ),
                    )

                    import_log_id = cursor.lastrowid

                    # Process sample data based on type
                    feed_iocs_imported = 0

                    if feed["feed_type"] in ["txt"]:
                        for ioc_value in feed["sample_data"]:
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO iocs
                                (ioc_type, ioc_value, source_feed, severity, confidence,
                                 first_seen, last_seen, is_active, created_by, score, category)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    feed["ioc_type"],
                                    ioc_value,
                                    feed["name"],
                                    "medium",
                                    85,
                                    datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).isoformat(),
                                    datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).isoformat(),
                                    1,
                                    current_user.user_id,
                                    75,  # score
                                    "malicious",  # category
                                ),
                            )
                            if cursor.rowcount > 0:
                                feed_iocs_imported += 1

                    elif feed["feed_type"] == "csv":
                        for item in feed["sample_data"]:
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO iocs
                                (ioc_type, ioc_value, source_feed, severity, confidence,
                                 tags, first_seen, last_seen, is_active, created_by, score, category)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    feed["ioc_type"],
                                    item["url"],
                                    feed["name"],
                                    "high",
                                    90,
                                    item.get("tags", ""),
                                    datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).isoformat(),
                                    datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).isoformat(),
                                    1,
                                    current_user.user_id,
                                    85,  # score
                                    "malicious",  # category
                                ),
                            )
                            if cursor.rowcount > 0:
                                feed_iocs_imported += 1

                    elif feed["feed_type"] == "json":
                        # Process STIX bundle
                        if "objects" in feed["sample_data"]:
                            for obj in feed["sample_data"]["objects"]:
                                if obj.get("type") == "indicator":
                                    # Extract IOC from STIX pattern
                                    pattern = obj.get("pattern", "")
                                    if "domain-name:value" in pattern:
                                        ioc_value = (
                                            pattern.split("'")[1]
                                            if "'" in pattern
                                            else ""
                                        )
                                        ioc_type = "domain"
                                    elif "file:hashes.MD5" in pattern:
                                        ioc_value = (
                                            pattern.split("'")[1]
                                            if "'" in pattern
                                            else ""
                                        )
                                        ioc_type = "hash"
                                    else:
                                        continue

                                    if ioc_value:
                                        cursor.execute(
                                            """
                                            INSERT OR IGNORE INTO iocs
                                            (ioc_type, ioc_value, source_feed, severity, confidence,
                                             first_seen, last_seen, is_active, created_by, score, category)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                            (
                                                ioc_type,
                                                ioc_value,
                                                feed["name"],
                                                "high",
                                                95,
                                                datetime.datetime.now(
                                                    datetime.timezone.utc
                                                ).isoformat(),
                                                datetime.datetime.now(
                                                    datetime.timezone.utc
                                                ).isoformat(),
                                                1,
                                                current_user.user_id,
                                                90,  # score
                                                "malicious",  # category
                                            ),
                                        )
                                        if cursor.rowcount > 0:
                                            feed_iocs_imported += 1

                    # Update import log
                    cursor.execute(
                        """
                        UPDATE feed_import_logs
                        SET import_status = ?, imported_count = ?,
                            total_records = ?, timestamp = ?
                        WHERE id = ?
                    """,
                        (
                            "completed",
                            feed_iocs_imported,
                            len(feed["sample_data"])
                            if isinstance(feed["sample_data"], list)
                            else 2,
                            datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            import_log_id,
                        ),
                    )

                    iocs_imported += feed_iocs_imported

            conn.commit()

            return jsonify(
                {
                    "success": True,
                    "message": "Demo feeds setup completed successfully",
                    "feeds_created": feeds_created,
                    "total_feeds": len(feeds_created),
                    "iocs_imported": iocs_imported if import_data else 0,
                    "import_data": import_data,
                }
            )

        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Failed to setup demo feeds: {str(e)}"}), 500
        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": f"Failed to setup demo feeds: {str(e)}"}), 500


@app.route("/api/feeds/<int:feed_id>/health", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def get_single_feed_health(feed_id):
    """Get health status for a specific feed."""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import time
    from datetime import datetime, timezone

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Get feed details
        cursor.execute(
            """
            SELECT id, name, url, feed_type, format_config, is_active
            FROM threat_feeds
            WHERE id = ?
        """,
            (feed_id,),
        )

        feed = cursor.fetchone()
        if not feed:
            conn.close()
            return jsonify({"error": "Feed not found"}), 404

        if not feed["url"]:
            conn.close()
            return jsonify({"error": "Feed has no URL configured"}), 400

        # Get recent health history
        cursor.execute(
            """
            SELECT * FROM feed_health_logs
            WHERE feed_id = ?
            ORDER BY last_checked DESC
            LIMIT 10
        """,
            (feed_id,),
        )

        recent_checks = [dict(row) for row in cursor.fetchall()]

        # Perform new health check
        feed_name = feed["name"]
        url = feed["url"]
        feed_type = feed["feed_type"]
        format_config = feed.get("format_config")

        # Parse format_config if it's a JSON string
        if isinstance(format_config, str):
            try:
                format_config = json.loads(format_config)
            except (json.JSONDecodeError, TypeError):
                format_config = {}

        start_time = time.time()
        last_checked = datetime.now(timezone.utc)
        current_user = g.current_user

        # Setup HTTP session
        session = requests.Session()
        retry_strategy = Retry(
            total=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET"],
            backoff_factor=0.3,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Determine request method
        use_head = feed_type in ["csv", "txt"] and "phishtank" not in feed_name.lower()

        # Initialize response variable
        response = None

        try:
            headers = {"User-Agent": "SentinelForge-HealthChecker/1.0", "Accept": "*/*"}

            # Handle authentication
            auth = None
            params = {}

            if format_config and format_config.get("requires_auth"):
                auth_config = format_config.get("auth_config", {})

                if auth_config.get("api_key"):
                    if "phishtank" in feed_name.lower():
                        params["format"] = "json"
                        params["api_key"] = auth_config["api_key"]
                    else:
                        headers["Authorization"] = f"Bearer {auth_config['api_key']}"
                elif auth_config.get("username") and auth_config.get("password"):
                    auth = (auth_config["username"], auth_config["password"])

            # Make request
            if use_head:
                response = session.head(
                    url, headers=headers, params=params, auth=auth, timeout=10
                )
            else:
                response = session.get(
                    url,
                    headers=headers,
                    params=params,
                    auth=auth,
                    timeout=10,
                    stream=True,
                )
                response.close()

            response_time_ms = int((time.time() - start_time) * 1000)

            # Determine status
            if response.status_code == 200:
                status = "ok"
            elif response.status_code in [401, 403]:
                status = "unauthorized"
            elif response.status_code == 429:
                status = "rate_limited"
            elif response.status_code >= 500:
                status = "server_error"
            else:
                status = "unreachable"

            error_message = None
            if status != "ok":
                error_message = f"HTTP {response.status_code}: {response.reason}"

        except requests.exceptions.Timeout:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = "timeout"
            error_message = "Request timeout"

        except requests.exceptions.ConnectionError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = "unreachable"
            error_message = f"Connection error: {str(e)}"

        except requests.exceptions.RequestException as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            status = "error"
            error_message = f"Request error: {str(e)}"

        # Log the health check
        cursor.execute(
            """
            INSERT INTO feed_health_logs (
                feed_id, feed_name, url, status, http_code,
                response_time_ms, error_message, last_checked, checked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                feed_id,
                feed_name,
                url,
                status,
                getattr(response, "status_code", None),
                response_time_ms,
                error_message,
                last_checked,
                current_user.user_id,
            ),
        )

        conn.commit()
        conn.close()

        # Create current health result
        current_health = {
            "feed_id": feed_id,
            "feed_name": feed_name,
            "url": url,
            "status": status,
            "http_code": getattr(response, "status_code", None),
            "response_time_ms": response_time_ms,
            "last_checked": last_checked.isoformat(),
            "is_active": bool(feed["is_active"]),
            "error_message": error_message,
        }

        return jsonify(
            {
                "success": True,
                "current_health": current_health,
                "recent_checks": recent_checks,
                "feed_details": {
                    "id": feed["id"],
                    "name": feed["name"],
                    "url": feed["url"],
                    "feed_type": feed["feed_type"],
                    "is_active": bool(feed["is_active"]),
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500


@app.route("/api/feeds/import-logs", methods=["GET"])
@require_authentication()
@require_role([UserRole.ANALYST, UserRole.AUDITOR, UserRole.ADMIN])
def get_import_logs():
    """Get feed import logs with filtering."""
    try:
        # Parse query parameters
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        feed_id = request.args.get("feed_id", type=int)
        import_status = request.args.get("import_status")

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Build query
        query = """
            SELECT l.*, f.name as feed_name, u.username as user_name
            FROM feed_import_logs l
            LEFT JOIN threat_feeds f ON l.feed_id = f.id
            LEFT JOIN users u ON l.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        if feed_id:
            query += " AND l.feed_id = ?"
            params.append(feed_id)

        if import_status:
            query += " AND l.import_status = ?"
            params.append(import_status)

        query += " ORDER BY l.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.cursor()
        cursor.execute(query, params)

        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            # Parse errors JSON
            if log.get("errors"):
                try:
                    log["errors"] = json.loads(log["errors"])
                except (json.JSONDecodeError, TypeError):
                    log["errors"] = []
            logs.append(log)

        # Get total count
        count_query = """
            SELECT COUNT(*) as count FROM feed_import_logs l
            WHERE 1=1
        """
        count_params = []

        if feed_id:
            count_query += " AND l.feed_id = ?"
            count_params.append(feed_id)

        if import_status:
            count_query += " AND l.import_status = ?"
            count_params.append(import_status)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["count"]

        conn.close()
        return jsonify({"logs": logs, "total": total})

    except Exception as e:
        return jsonify({"error": f"Failed to get import logs: {str(e)}"}), 500


if __name__ == "__main__":
    port = 5059
    print(f"Starting API server on port {port}")

    # Initialize authentication tables and default users
    from auth import init_auth_tables

    if init_auth_tables():
        print("[AUTH] Authentication tables initialized successfully")
    else:
        print("[AUTH] Warning: Failed to initialize authentication tables")

    initialize_iocs()  # Initialize IOCS list before starting the server
    initialize_alerts()  # Initialize ALERTS list before starting the server

    # Run startup health check in background (non-blocking)
    import threading

    def background_health_check():
        try:
            from services.feed_health_monitor import run_startup_health_check

            run_startup_health_check()
        except Exception as e:
            print(f"⚠️  Startup health check failed: {e}")

    health_thread = threading.Thread(target=background_health_check, daemon=True)
    health_thread.start()
    print("🏥 Health check started in background")

    # Start health check scheduler in background (non-blocking)
    def background_scheduler():
        try:
            from services.feed_health_monitor import FeedHealthMonitor

            monitor = FeedHealthMonitor()

            # Start with 1-minute interval for testing
            if monitor.start_cron_scheduler(interval_minutes=1):
                print("✅ Health check scheduler started (1-minute interval)")
            else:
                print("⚠️  Failed to start health check scheduler")
        except Exception as e:
            print(f"⚠️  Health scheduler startup failed: {e}")

    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Health scheduler started in background")

    print("🌐 API Server ready on http://0.0.0.0:5059")
    app.run(host="0.0.0.0", port=port, debug=True)
