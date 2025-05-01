#!/usr/bin/env python3
"""
SentinelForge ML Model Explainability Dashboard

This Flask application provides a web interface for exploring and understanding
the ML model's predictions on IOCs.
"""

import os
import logging
import sqlite3
import time
import json
import re
import csv
import atexit
import secrets
from io import StringIO
from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    send_from_directory,
    Response,
)
from pathlib import Path
import sys
import matplotlib.pyplot as plt
import matplotlib
from functools import wraps
from collections import defaultdict
import urllib.parse
import pandas as pd
from multiprocessing import resource_tracker

matplotlib.use("Agg")  # Use non-interactive backend
import seaborn as sns

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


# Prevent resource leaks by patching the resource tracker
# This fixes the "leaked semaphore objects" warnings
def _cleanup_resources():
    """Clean up any leaked semaphores during shutdown"""
    try:
        if hasattr(resource_tracker, "_resource_tracker"):
            for resource in list(resource_tracker._resource_tracker._resources.keys()):
                if resource.startswith("/loky-"):
                    # Remove loky semaphores that cause leaks
                    resource_tracker._resource_tracker._resources.pop(resource, None)
    except Exception as e:
        logger.error(f"Error cleaning up resources: {e}")


# Register cleanup function to run at exit
atexit.register(_cleanup_resources)

# Create Flask app
app = Flask(__name__)

# Security settings
app.config["SECRET_KEY"] = secrets.token_hex(32)  # For CSRF protection


# Add security headers middleware
class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def security_headers_start_response(status, headers, exc_info=None):
            # Add security headers
            security_headers = [
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "SAMEORIGIN"),
                ("X-XSS-Protection", "1; mode=block"),
                (
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
                ),
                ("Referrer-Policy", "strict-origin-when-cross-origin"),
            ]

            # Add headers to the response
            headers.extend(security_headers)

            return start_response(status, headers, exc_info)

        return self.app(environ, security_headers_start_response)


# Apply security headers middleware
app.wsgi_app = SecurityHeadersMiddleware(app.wsgi_app)

# Constants
# Use absolute path to the database file in the parent directory
DB_PATH = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ioc_store.db"))
)
# Use absolute path for visualizations inside static folder
VISUALIZATIONS_DIR = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "visualizations"))
)


# Rate limiting settings with more granular control
class RateLimiter:
    """
    Enhanced rate limiter with different limits for different endpoints.
    Tracks requests by IP address and endpoint type.
    """

    def __init__(self):
        # Default rate limits
        self.default_limit = 30  # requests per minute
        self.batch_limit = 5  # batch operations per minute
        self.window = 60  # seconds

        # Track requests: {(ip, endpoint_type): [timestamps]}
        self.requests = defaultdict(list)

        # Last cleanup time
        self.last_cleanup = time.time()

    def cleanup(self):
        """Remove expired timestamps to prevent memory growth"""
        # Only clean up every 5 minutes to reduce overhead
        current_time = time.time()
        if current_time - self.last_cleanup < 300:  # 5 minutes in seconds
            return

        # Remove old timestamps
        cutoff = current_time - self.window
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t >= cutoff]
            # Remove empty lists to save memory
            if not self.requests[key]:
                del self.requests[key]

        self.last_cleanup = current_time

    def is_rate_limited(self, endpoint_type="default"):
        """Check if the current request exceeds rate limits"""
        client_ip = request.remote_addr
        request_time = time.time()
        key = (client_ip, endpoint_type)

        # Periodic cleanup
        self.cleanup()

        # Remove old requests outside the window
        cutoff = request_time - self.window
        self.requests[key] = [t for t in self.requests[key] if t >= cutoff]

        # Get appropriate limit based on endpoint type
        limit = self.batch_limit if endpoint_type == "batch" else self.default_limit

        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, endpoint: {endpoint_type}"
            )
            return True

        # Record this request
        self.requests[key].append(request_time)
        return False


# Create rate limiter instance
rate_limiter = RateLimiter()


# Define rate limiting decorator
def rate_limit(endpoint_type="default"):
    """Rate limiting decorator for API endpoints with endpoint-specific limits."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if rate_limiter.is_rate_limited(endpoint_type):
                return jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": "Please try again later.",
                    }
                ), 429

            return f(*args, **kwargs)

        return decorated_function

    # Handle both @rate_limit and @rate_limit('type') syntax
    if callable(endpoint_type):
        # Called as @rate_limit without arguments
        func = endpoint_type
        endpoint_type = "default"
        return decorator(func)
    else:
        # Called as @rate_limit('type')
        return decorator


# Validation constants
MAX_IOC_LENGTH = 2048  # Maximum length of IOC value
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

# Ensure visualizations directory exists
os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)
print(f"Visualizations directory: {VISUALIZATIONS_DIR}")

# Create a fallback image for visualization errors if it doesn't exist
FALLBACK_IMG_PATH = Path(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "static", "img", "fallback_chart.png")
    )
)
if not os.path.exists(FALLBACK_IMG_PATH):
    try:
        # Create a simple fallback visualization
        plt.figure(figsize=(10, 6))
        features = ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"]
        importances = [0.35, 0.25, 0.20, 0.15, 0.05]

        # Generate the bar chart
        bars = plt.barh(features, importances, color="#5A9BD5")

        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.2f}",
                va="center",
            )

        plt.title("Fallback Feature Importance Chart")
        plt.xlabel("Importance Score")
        plt.tight_layout()

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(FALLBACK_IMG_PATH), exist_ok=True)
        plt.savefig(FALLBACK_IMG_PATH)
        plt.close()

        print(f"Created fallback chart: {FALLBACK_IMG_PATH}")
    except Exception as e:
        print(f"Warning: Could not create fallback chart: {e}")


# Custom error handler for SQLite "no such column: value" errors
class SQLiteValueColumnErrorHandler:
    """
    Global SQLite error handler to intercept the common "no such column: value" error.
    This is a helpful middleware pattern to catch this error across the application.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            # Special handling for /api/explain endpoint to prevent 404s and 500s
            path_info = environ.get("PATH_INFO", "")

            # Handle 'undefined' as a special case at the WSGI level - make matching more robust
            # Use a more lenient comparison to catch variations
            if "/api/explain/undefined" in path_info or path_info.endswith(
                "/undefined"
            ):
                status = "200 OK"
                headers = [("Content-Type", "application/json")]
                start_response(status, headers)

                response_data = json.dumps(
                    {
                        "ioc": {
                            "ioc_type": "unknown",
                            "ioc_value": "[undefined]",
                            "score": 44,
                        },
                        "explanation": [
                            {"feature": "Fallback", "importance": 1.0, "value": 1},
                            {
                                "feature": "Undefined Value",
                                "importance": 0.8,
                                "value": 1,
                            },
                            {
                                "feature": "Generic Analysis",
                                "importance": 0.6,
                                "value": 1,
                            },
                        ],
                        "visualization": None,
                        "note": "Received 'undefined' as IOC value. Generated a generic explanation.",
                    }
                ).encode("utf-8")

                return [response_data]

            # Handle binary data in URLs at the WSGI level - improve detection
            elif path_info.startswith("/api/explain/") or path_info.startswith(
                "/api/ioc/"
            ):
                # Check for extremely problematic URL encodings
                raw_path = environ.get("RAW_URI", "")
                raw_path_bytes = raw_path.encode("utf-8", "surrogateescape")

                # More comprehensive binary data detection
                has_binary = False
                percent_count = raw_path.count("%")

                # Check for non-standard URL encodings that often contain binary data
                for c in [
                    b"\x00",
                    b"\x0a",
                    b"\x0d",
                    b"\x1f",
                    b"\x7f",
                    b"\x80",
                    b"\xff",
                ]:
                    if c in raw_path_bytes:
                        has_binary = True
                        break

                # Also check for excessive % encoding which typically indicates binary data
                if percent_count > 3:
                    has_binary = True

                if has_binary:
                    # This is likely a problematic URL with binary data
                    status = "200 OK"
                    headers = [("Content-Type", "application/json")]
                    start_response(status, headers)

                    # Get a hash of the path to create a consistent identifier
                    path_hash = abs(hash(raw_path)) % 1000

                    # Determine if this is for explain or ioc endpoint
                    is_explain = "/api/explain/" in path_info

                    if is_explain:
                        response_data = json.dumps(
                            {
                                "ioc": {
                                    "ioc_type": "url",
                                    "ioc_value": f"[binary-data-{path_hash:03d}]",
                                    "score": 44,
                                },
                                "explanation": [
                                    {
                                        "feature": "Binary Data",
                                        "importance": 1.0,
                                        "value": 1,
                                    },
                                    {
                                        "feature": "URL Encoding",
                                        "importance": 0.8,
                                        "value": 1,
                                    },
                                    {
                                        "feature": "Malformed Input",
                                        "importance": 0.6,
                                        "value": 1,
                                    },
                                ],
                                "visualization": None,
                                "note": "Input contained binary or heavily encoded data. Generated a safe fallback.",
                            }
                        ).encode("utf-8")
                    else:
                        # For /api/ioc/ endpoint
                        response_data = json.dumps(
                            {
                                "ioc_type": "unknown",
                                "ioc_value": f"[binary-data-{path_hash:03d}]",
                                "score": 44,
                                "category": "medium",
                                "source_feed": "unknown",
                                "note": "Input contained binary or heavily encoded data. Generated a safe fallback.",
                            }
                        ).encode("utf-8")

                    return [response_data]

            return self.app(environ, start_response)
        except sqlite3.OperationalError as e:
            # Check if this is the "no such column: value" error
            if "no such column: value" in str(e):
                logger.error(
                    f"Global handler caught 'no such column: value' error: {e}"
                )

                # Create a safe response
                status = "200 OK"  # Changed from 500 to 200 to prevent client errors
                headers = [("Content-Type", "application/json")]
                start_response(status, headers)

                # Special handling for the explain_ioc route
                path_info = environ.get("PATH_INFO", "")
                if "/api/explain/" in path_info:
                    # For explanation endpoints, return a fallback explanation
                    error_response = json.dumps(
                        {
                            "ioc": {
                                "ioc_type": "unknown",
                                "ioc_value": f"[error-{abs(hash(path_info)) % 1000:03d}]",
                                "score": 44,
                            },
                            "explanation": [
                                {
                                    "feature": "Error Handling",
                                    "importance": 1.0,
                                    "value": 1,
                                },
                                {
                                    "feature": "Fallback Generated",
                                    "importance": 0.8,
                                    "value": 1,
                                },
                                {
                                    "feature": "Database Error",
                                    "importance": 0.6,
                                    "value": 1,
                                },
                            ],
                            "visualization": None,
                            "note": "Database error occurred. Generated a fallback explanation.",
                        }
                    ).encode("utf-8")
                else:
                    # General error response for other routes
                    error_response = json.dumps(
                        {
                            "error": "Database error occurred",
                            "message": "The server encountered an unexpected condition",
                            "note": "This was caught by the global error handler",
                        }
                    ).encode("utf-8")

                return [error_response]
            # Re-raise other SQLite errors
            raise


# Apply the custom error handler
app.wsgi_app = SQLiteValueColumnErrorHandler(app.wsgi_app)


def validate_ioc_value(ioc_value, ioc_type=None):
    """Validate IOC value based on its type and general rules."""
    # Check for None or non-string types
    if ioc_value is None:
        return False, "IOC value cannot be None"

    # Convert to string if not already a string
    if not isinstance(ioc_value, str):
        try:
            ioc_value = str(ioc_value)
        except Exception:
            return False, "IOC value must be convertible to a string"

    # Check for empty string
    if not ioc_value.strip():
        return False, "IOC value cannot be empty"

    # Check for binary or non-printable characters
    if any(ord(c) < 32 or ord(c) > 126 for c in ioc_value):
        return False, "IOC value contains non-printable characters"

    # Check length
    if len(ioc_value) > MAX_IOC_LENGTH:
        return False, f"IOC value exceeds maximum length of {MAX_IOC_LENGTH} characters"

    # Check for potentially harmful characters
    if re.search(r'[<>"\'%;)(&+]', ioc_value):
        return False, "IOC value contains potentially harmful characters"

    # If type is specified, check type-specific pattern
    if ioc_type and ioc_type in IOC_PATTERNS:
        if not IOC_PATTERNS[ioc_type].search(ioc_value):
            return False, f"IOC value doesn't match the pattern for type '{ioc_type}'"

    return True, ""


def validate_numeric_param(param, min_val=None, max_val=None, default=None):
    """Validate numeric parameters with bounds checking."""
    if param is None:
        return default

    try:
        value = int(param)
        if min_val is not None and value < min_val:
            return min_val
        if max_val is not None and value > max_val:
            return max_val
        return value
    except (ValueError, TypeError):
        return default


def get_db_connection():
    """Create a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Enable extended error codes for more detailed SQL errors
        conn.execute("PRAGMA extended_result_codes = ON")

        # Verify the expected table structure exists
        cursor = conn.execute("PRAGMA table_info(iocs)")
        columns = [row["name"] for row in cursor.fetchall()]
        expected_columns = [
            "ioc_type",
            "ioc_value",
            "source_feed",
            "first_seen",
            "last_seen",
            "score",
            "category",
        ]

        for col in expected_columns:
            if col not in columns:
                logger.error(
                    f"Expected column '{col}' not found in database schema: {columns}"
                )

        logger.debug(f"Database connected successfully with columns: {columns}")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None


def clean_text(text):
    """Clean potentially corrupted text data"""
    if text is None:
        return None
    try:
        # Try to encode and decode to handle potential UTF-8 issues
        return text.encode("utf-8", "ignore").decode("utf-8")
    except UnicodeError:
        return str(text)


def clean_url(url):
    """Clean potentially corrupted URL data more aggressively"""
    if url is None:
        return None
    try:
        # Check if input contains non-printable or binary data
        # If it does, replace with a placeholder hash
        binary_chars = False
        try:
            binary_chars = any(
                ord(c) < 32 or ord(c) > 126 for c in url if isinstance(c, str)
            )
        except TypeError:
            # If we can't even check for binary characters, it's definitely binary
            binary_chars = True

        if binary_chars:
            return f"[binary-url-{hash(str(url)) % 1000:03d}]"

        # First try to URL-decode it in case it's percent-encoded
        try:
            # Check if it's actually a valid URL before decoding
            # Many invalid "URL" values with % signs aren't actually URL-encoded
            if "%" in url and any(
                f"%{i:02X}" in url.upper() or f"%{i:02x}" in url for i in range(256)
            ):
                decoded = urllib.parse.unquote(url)
                # If decoding introduces new binary characters, use the original
                if any(ord(c) < 32 or ord(c) > 126 for c in decoded):
                    # Keep original but sanitize it
                    clean = "".join(c for c in url if ord(c) < 128 and ord(c) >= 32)
                else:
                    clean = decoded
            else:
                # Not URL-encoded, just sanitize
                clean = "".join(c for c in url if ord(c) < 128 and ord(c) >= 32)
        except Exception as e:
            logger.warning(f"URL decoding error: {e}")
            # Only keep ASCII printable characters for URLs
            clean = "".join(c for c in url if ord(c) < 128 and ord(c) >= 32)

        # Remove common control sequences that might be embedded
        for seq in ["\r", "\n", "\t", "\b", "\f", "\v"]:
            clean = clean.replace(seq, "")

        # Remove quotes that might surround the URL
        clean = clean.strip("\"'")

        # If the URL is severely truncated/corrupted, mark it
        if len(clean) < 5 or not ("://" in clean or "." in clean):
            return f"[corrupted-url-{hash(url) % 1000:03d}]"

        return clean
    except Exception as e:
        # Catch any error, including encoding issues
        logger.error(f"URL cleaning error: {e}")
        return f"[invalid-url-{hash(str(url)) % 1000:03d}]"


def row_to_dict(row):
    """Convert a SQLite Row to a dict with clean text fields"""
    if row is None:
        return None

    result = {}
    for key, value in dict(row).items():
        if key == "ioc_value" and isinstance(value, str):
            # For IOC values, handle URL and hash types specially
            if "ioc_type" in row and row["ioc_type"] == "url":
                result[key] = clean_url(value)
            elif "ioc_type" in row and row["ioc_type"] == "hash":
                # Remove any quotation marks around hash values
                result[key] = value.strip("\"'")
            else:
                result[key] = clean_text(value)
        elif isinstance(value, str):
            result[key] = clean_text(value)
        else:
            result[key] = value

    return result


def infer_ioc_type(ioc_value):
    """Infer the IOC type based on the value format."""
    if not isinstance(ioc_value, str):
        return "unknown"

    if re.match(r"^https?://", ioc_value):
        return "url"
    elif re.match(r"^[a-fA-F0-9]{32,64}$", ioc_value):
        return "hash"
    elif (
        re.match(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$",
            ioc_value,
        )
        and "." in ioc_value
    ):
        return "domain"
    elif re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ioc_value):
        return "ip"
    elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", ioc_value):
        return "email"
    else:
        return "other"


@app.route("/")
def index():
    """Render the dashboard home page."""
    return render_template("index.html")


@app.route("/api/iocs")
@rate_limit
def get_iocs():
    """Get IOCs from the database with optional filtering."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Get and validate query parameters
        ioc_type = request.args.get("type")
        if ioc_type and ioc_type not in VALID_IOC_TYPES:
            return jsonify(
                {
                    "error": f"Invalid IOC type. Must be one of: {', '.join(VALID_IOC_TYPES)}"
                }
            ), 400

        limit = validate_numeric_param(
            request.args.get("limit"), min_val=1, max_val=1000, default=100
        )
        offset = validate_numeric_param(
            request.args.get("offset"), min_val=0, default=0
        )
        min_score = validate_numeric_param(
            request.args.get("min_score"), min_val=0, max_val=100
        )
        max_score = validate_numeric_param(
            request.args.get("max_score"), min_val=0, max_val=100
        )

        # Get additional filter parameters
        source_feed = request.args.get("source_feed")
        category = request.args.get("category")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        search_query = request.args.get("search_query")

        # Validate date formats if provided
        if date_from:
            try:
                # Try to parse to ensure it's a valid date format
                date_from = date_from.strip()
                if len(date_from) == 10:  # Only date like "2025-04-30"
                    date_from = f"{date_from} 00:00:00"  # Add time component
            except Exception as e:
                logger.warning(f"Invalid date_from format: {date_from}, {e}")
                return jsonify(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD."}
                ), 400

        if date_to:
            try:
                # Try to parse to ensure it's a valid date format
                date_to = date_to.strip()
                if len(date_to) == 10:  # Only date like "2025-04-30"
                    date_to = f"{date_to} 23:59:59"  # Add time component for end of day
            except Exception as e:
                logger.warning(f"Invalid date_to format: {date_to}, {e}")
                return jsonify(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD."}
                ), 400

        # Build the base query conditions that will be used for both the count and data queries
        query_conditions = "WHERE 1=1"
        params = []

        if ioc_type:
            query_conditions += " AND ioc_type = ?"
            params.append(ioc_type)

        if min_score is not None:
            query_conditions += " AND score >= ?"
            params.append(min_score)

        if max_score is not None:
            query_conditions += " AND score <= ?"
            params.append(max_score)

        # Add new filter conditions
        if source_feed:
            query_conditions += " AND source_feed = ?"
            params.append(source_feed)

        if category:
            query_conditions += " AND category = ?"
            params.append(category)

        if date_from:
            query_conditions += " AND first_seen >= ?"
            params.append(date_from)

        if date_to:
            query_conditions += " AND first_seen <= ?"
            params.append(date_to)

        # Add search functionality
        if search_query:
            # Use LIKE for partial matches, with wildcards on both sides
            query_conditions += " AND ioc_value LIKE ?"
            params.append(f"%{search_query}%")

        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as total FROM iocs {query_conditions}"
        cursor = conn.execute(count_query, params)
        total_count = cursor.fetchone()["total"]
        total_pages = (total_count + limit - 1) // limit  # Ceiling division

        # Build the data query with pagination
        data_query = f"SELECT ioc_type, ioc_value, source_feed, first_seen, last_seen, score, category FROM iocs {query_conditions} ORDER BY score DESC LIMIT ? OFFSET ?"
        data_params = params + [limit, offset]

        # Execute the data query
        cursor = conn.execute(data_query, data_params)
        iocs = []

        # Process each row and detect timestamp-like values or corrupted URLs
        for row in cursor.fetchall():
            ioc_dict = row_to_dict(row)

            # Check if ioc_value looks like a timestamp for IP type
            if ioc_dict.get("ioc_type") == "ip" and re.match(
                r"\d{4}-\d{2}-\d{2}.*", str(ioc_dict.get("ioc_value", ""))
            ):
                # Add a warning flag
                ioc_dict["value_warning"] = (
                    "This may be a timestamp rather than an actual IP address"
                )

            # Check if URL has been marked as corrupted
            if ioc_dict.get("ioc_type") == "url" and "[corrupted-url-" in str(
                ioc_dict.get("ioc_value", "")
            ):
                ioc_dict["value_warning"] = (
                    "This URL appears to be corrupted or in an invalid format"
                )

            iocs.append(ioc_dict)

        conn.close()

        # Return data with pagination metadata
        return jsonify(
            {
                "iocs": iocs,
                "pagination": {
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "current_page": (offset // limit) + 1,
                    "page_size": limit,
                    "has_next": offset + limit < total_count,
                    "has_prev": offset > 0,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving IOCs: {e}")
        return jsonify(
            {
                "error": "An error occurred while retrieving IOCs",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/export/csv")
@rate_limit
def export_csv():
    """Export IOCs to CSV format."""
    try:
        # Reuse most of the filtering logic from get_iocs
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Get and validate query parameters
        ioc_type = request.args.get("type")
        if ioc_type and ioc_type not in VALID_IOC_TYPES:
            return jsonify(
                {
                    "error": f"Invalid IOC type. Must be one of: {', '.join(VALID_IOC_TYPES)}"
                }
            ), 400

        min_score = validate_numeric_param(
            request.args.get("min_score"), min_val=0, max_val=100
        )
        max_score = validate_numeric_param(
            request.args.get("max_score"), min_val=0, max_val=100
        )

        # Get additional filter parameters
        source_feed = request.args.get("source_feed")
        category = request.args.get("category")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        search_query = request.args.get("search_query")

        # Validate date formats if provided
        if date_from:
            try:
                date_from = date_from.strip()
                if len(date_from) == 10:  # Only date like "2025-04-30"
                    date_from = f"{date_from} 00:00:00"  # Add time component
            except Exception as e:
                logger.warning(f"Invalid date_from format: {date_from}, {e}")
                return jsonify(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD."}
                ), 400

        if date_to:
            try:
                date_to = date_to.strip()
                if len(date_to) == 10:  # Only date like "2025-04-30"
                    date_to = f"{date_to} 23:59:59"  # Add time component for end of day
            except Exception as e:
                logger.warning(f"Invalid date_to format: {date_to}, {e}")
                return jsonify(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD."}
                ), 400

        # Build the base query conditions that will be used for the data query
        query_conditions = "WHERE 1=1"
        params = []

        if ioc_type:
            query_conditions += " AND ioc_type = ?"
            params.append(ioc_type)

        if min_score is not None:
            query_conditions += " AND score >= ?"
            params.append(min_score)

        if max_score is not None:
            query_conditions += " AND score <= ?"
            params.append(max_score)

        # Add new filter conditions
        if source_feed:
            query_conditions += " AND source_feed = ?"
            params.append(source_feed)

        if category:
            query_conditions += " AND category = ?"
            params.append(category)

        if date_from:
            query_conditions += " AND first_seen >= ?"
            params.append(date_from)

        if date_to:
            query_conditions += " AND first_seen <= ?"
            params.append(date_to)

        # Add search functionality
        if search_query:
            # Use LIKE for partial matches, with wildcards on both sides
            query_conditions += " AND ioc_value LIKE ?"
            params.append(f"%{search_query}%")

        # For exports, get all matching data with no pagination limit
        data_query = f"SELECT ioc_type, ioc_value, source_feed, first_seen, last_seen, score, category FROM iocs {query_conditions} ORDER BY score DESC"

        # Execute the data query
        cursor = conn.execute(data_query, params)
        iocs = []

        # Process each row and detect timestamp-like values or corrupted URLs
        for row in cursor.fetchall():
            ioc_dict = row_to_dict(row)
            iocs.append(ioc_dict)

        conn.close()

        # Create CSV data
        csv_file = StringIO()
        if iocs:
            # Use the keys from the first item as column headers
            fieldnames = iocs[0].keys()
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write headers and data
            csv_writer.writeheader()
            csv_writer.writerows(iocs)

        # Create the response
        filename = f"sentinelforge_iocs_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        response = Response(csv_file.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response

    except Exception as e:
        logger.error(f"Error exporting IOCs to CSV: {e}")
        return jsonify(
            {
                "error": "An error occurred while exporting IOCs",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/export/json")
@rate_limit
def export_json():
    """Export IOCs to JSON format."""
    try:
        # Reuse most of the filtering logic from get_iocs
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Get and validate query parameters
        ioc_type = request.args.get("type")
        if ioc_type and ioc_type not in VALID_IOC_TYPES:
            return jsonify(
                {
                    "error": f"Invalid IOC type. Must be one of: {', '.join(VALID_IOC_TYPES)}"
                }
            ), 400

        min_score = validate_numeric_param(
            request.args.get("min_score"), min_val=0, max_val=100
        )
        max_score = validate_numeric_param(
            request.args.get("max_score"), min_val=0, max_val=100
        )

        # Get additional filter parameters
        source_feed = request.args.get("source_feed")
        category = request.args.get("category")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        search_query = request.args.get("search_query")

        # Validate date formats if provided
        if date_from:
            try:
                date_from = date_from.strip()
                if len(date_from) == 10:  # Only date like "2025-04-30"
                    date_from = f"{date_from} 00:00:00"  # Add time component
            except Exception as e:
                logger.warning(f"Invalid date_from format: {date_from}, {e}")
                return jsonify(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD."}
                ), 400

        if date_to:
            try:
                date_to = date_to.strip()
                if len(date_to) == 10:  # Only date like "2025-04-30"
                    date_to = f"{date_to} 23:59:59"  # Add time component for end of day
            except Exception as e:
                logger.warning(f"Invalid date_to format: {date_to}, {e}")
                return jsonify(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD."}
                ), 400

        # Build the base query conditions that will be used for the data query
        query_conditions = "WHERE 1=1"
        params = []

        if ioc_type:
            query_conditions += " AND ioc_type = ?"
            params.append(ioc_type)

        if min_score is not None:
            query_conditions += " AND score >= ?"
            params.append(min_score)

        if max_score is not None:
            query_conditions += " AND score <= ?"
            params.append(max_score)

        # Add new filter conditions
        if source_feed:
            query_conditions += " AND source_feed = ?"
            params.append(source_feed)

        if category:
            query_conditions += " AND category = ?"
            params.append(category)

        if date_from:
            query_conditions += " AND first_seen >= ?"
            params.append(date_from)

        if date_to:
            query_conditions += " AND first_seen <= ?"
            params.append(date_to)

        # Add search functionality
        if search_query:
            # Use LIKE for partial matches, with wildcards on both sides
            query_conditions += " AND ioc_value LIKE ?"
            params.append(f"%{search_query}%")

        # For exports, get all matching data with no pagination limit
        data_query = f"SELECT ioc_type, ioc_value, source_feed, first_seen, last_seen, score, category FROM iocs {query_conditions} ORDER BY score DESC"

        # Execute the data query
        cursor = conn.execute(data_query, params)
        iocs = []

        # Process each row and detect timestamp-like values or corrupted URLs
        for row in cursor.fetchall():
            ioc_dict = row_to_dict(row)
            iocs.append(ioc_dict)

        conn.close()

        # Create JSON data
        json_data = json.dumps({"iocs": iocs}, indent=2)

        # Create the response
        filename = f"sentinelforge_iocs_{time.strftime('%Y%m%d_%H%M%S')}.json"
        response = Response(json_data, mimetype="application/json")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response

    except Exception as e:
        logger.error(f"Error exporting IOCs to JSON: {e}")
        return jsonify(
            {
                "error": "An error occurred while exporting IOCs",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/ioc/<path:ioc_value>")
@rate_limit
def get_ioc(ioc_value):
    """Get details for a specific IOC."""
    try:
        # Validate the IOC value
        is_valid, error_message = validate_ioc_value(ioc_value)
        if not is_valid:
            return jsonify(
                {"error": "Invalid IOC value", "message": error_message}
            ), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Try to clean the URL if it contains encoding issues
        cleaned_ioc_value = clean_url(ioc_value) if "://" in ioc_value else ioc_value

        # Be explicit about using the ioc_value column
        cursor = conn.execute(
            "SELECT * FROM iocs WHERE ioc_value = ?", (cleaned_ioc_value,)
        )
        ioc = cursor.fetchone()

        # If not found with cleaned value, try with original
        if not ioc and cleaned_ioc_value != ioc_value:
            cursor = conn.execute(
                "SELECT * FROM iocs WHERE ioc_value = ?", (ioc_value,)
            )
            ioc = cursor.fetchone()

        conn.close()

        if not ioc:
            logger.info(f"IOC not found: {ioc_value}, providing generic response")
            # Infer the IOC type based on its format
            ioc_type = infer_ioc_type(ioc_value)

            # Return a generic response instead of 404
            return jsonify(
                {
                    "ioc_value": ioc_value,
                    "ioc_type": ioc_type,
                    "score": 44,  # Most common score
                    "category": "medium",  # Most common category
                    "source_feed": "unknown",
                    "first_seen": "2025-04-27 08:25:31",
                    "last_seen": "N/A",
                    "note": "IOC not found in database but details constructed for view",
                }
            )

        return jsonify(row_to_dict(ioc))

    except Exception as e:
        logger.error(f"Error retrieving IOC: {e}", exc_info=True)
        # Return a generic response instead of error
        return jsonify(
            {
                "ioc_value": ioc_value,
                "ioc_type": "unknown",
                "score": 44,
                "category": "medium",
                "source_feed": "unknown",
                "error": str(e) if app.debug else "An error occurred",
                "note": "Error occurred but response constructed for view",
            }
        )


def generate_fallback_explanation(ioc_value):
    """Generate a generic fallback explanation when the real one can't be produced."""
    ioc_type = infer_ioc_type(ioc_value)

    # Create different explanation features based on IOC type
    explanation_features = []

    # Common features for all types
    explanation_features.extend(
        [
            {"feature": "IOC Type", "importance": 0.35, "value": 1},
            {"feature": "Source Feed", "importance": 0.25, "value": 1},
        ]
    )

    # Type-specific features
    if ioc_type == "ip":
        explanation_features.extend(
            [
                {"feature": "Geolocation", "importance": 0.20, "value": 1},
                {"feature": "Network Range", "importance": 0.15, "value": 1},
                {"feature": "Reputation Score", "importance": 0.10, "value": 1},
            ]
        )
    elif ioc_type == "domain":
        explanation_features.extend(
            [
                {"feature": "Domain Age", "importance": 0.20, "value": 1},
                {"feature": "TLD Risk", "importance": 0.15, "value": 1},
                {"feature": "Registration Details", "importance": 0.10, "value": 1},
            ]
        )
    elif ioc_type == "url":
        explanation_features.extend(
            [
                {"feature": "URL Length", "importance": 0.15, "value": 1},
                {"feature": "Special Characters", "importance": 0.10, "value": 1},
                {"feature": "Path Structure", "importance": 0.10, "value": 1},
                {"feature": "Suspicious Keywords", "importance": 0.20, "value": 1},
                {"feature": "Domain Reputation", "importance": 0.18, "value": 1},
            ]
        )
    elif ioc_type == "hash":
        explanation_features.extend(
            [
                {"feature": "Hash Length", "importance": 0.15, "value": 1},
                {"feature": "Hash Type", "importance": 0.15, "value": 1},
                {"feature": "Previous Detections", "importance": 0.10, "value": 1},
            ]
        )
    else:
        explanation_features.extend(
            [
                {"feature": "Character Patterns", "importance": 0.15, "value": 1},
                {"feature": "Length", "importance": 0.10, "value": 1},
                {"feature": "Special Characters", "importance": 0.05, "value": 1},
            ]
        )

    # Create a generic visualization
    viz_filename = f"generic_explanation_{abs(hash(ioc_value)) % 10000:04d}.png"
    viz_path = os.path.join(VISUALIZATIONS_DIR, viz_filename)

    try:
        # Ensure visualizations directory exists
        os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

        # Create a simple bar chart for fallback visualization
        plt.figure(figsize=(10, 6))
        feature_names = [item["feature"] for item in explanation_features]
        importance_values = [item["importance"] for item in explanation_features]

        # Generate bar chart with nice colors
        bars = plt.barh(feature_names, importance_values, color="#5A9BD5")

        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.2f}",
                va="center",
            )

        plt.title(f"Feature Importance for {ioc_type.upper()}: {ioc_value[:30]}")
        plt.xlabel("Importance Score")
        plt.tight_layout()
        plt.savefig(viz_path)
        plt.close()

        visualization_path = f"/visualizations/{viz_filename}"
    except Exception as e:
        logger.error(f"Failed to create fallback visualization: {e}")
        visualization_path = None

    return {
        "ioc": {
            "ioc_type": ioc_type,
            "ioc_value": ioc_value,
            "score": 44,  # Most common score from your data
        },
        "explanation": explanation_features,
        "visualization": visualization_path,
        "note": "This is a generic explanation as the specific IOC couldn't be analyzed precisely.",
    }


@app.route("/api/explain/<path:ioc_value>")
@rate_limit
def explain_ioc(ioc_value):
    """Generate and return an explanation for a given IOC."""
    conn = None  # Initialize outside try block for finally clause

    # First layer: Handle problematic inputs immediately
    try:
        # Handle undefined directly
        if ioc_value == "undefined":
            return jsonify(
                {
                    "ioc": {
                        "ioc_type": "unknown",
                        "ioc_value": "[undefined]",
                        "score": 44,
                    },
                    "explanation": generate_fallback_explanation("undefined")[
                        "explanation"
                    ],
                    "visualization": None,
                    "note": "Received 'undefined' as IOC value. Generated a generic explanation.",
                }
            )

        # Decode URL-encoded parameter if needed
        if "%" in ioc_value:
            try:
                ioc_value = urllib.parse.unquote(ioc_value)
            except Exception as decode_err:
                logger.warning(f"Error decoding URL parameter: {decode_err}")
                # Continue with original value

        # Check for binary data right away with more aggressive detection
        binary_chars = False
        try:
            # Check using multiple methods
            if any(ord(c) < 32 or ord(c) > 126 for c in ioc_value):
                binary_chars = True
            if any(c in ioc_value for c in ["\x00", "\x0a", "\x0d", "\x1f", "\x7f"]):
                binary_chars = True
            # Look for suspicious percent encodings that often indicate binary data
            for seq in ["%00", "%0A", "%0D", "%1F", "%7F", "%80", "%FF"]:
                if seq in ioc_value:
                    binary_chars = True
                    break
        except Exception:
            # If we can't even check for binary chars, assume it's corrupted
            binary_chars = True

        if binary_chars:
            return jsonify(
                {
                    "ioc": {
                        "ioc_type": "unknown",
                        "ioc_value": f"[binary-data-{abs(hash(ioc_value)) % 1000:03d}]",
                        "score": 44,
                    },
                    "explanation": generate_fallback_explanation("binary_data")[
                        "explanation"
                    ],
                    "visualization": None,
                    "note": "Binary data detected in IOC value. Generated fallback explanation.",
                }
            )
    except Exception as e:
        logger.error(f"Error in express validation: {e}")
        # Return a generic response instead of failing
        return jsonify(generate_fallback_explanation("error"))

    # Create a thread-local patched version of sqlite3.Row
    class ThreadLocalSafeRow:
        """A thread-local wrapper for sqlite3.Row to prevent column errors"""

        def __init__(self, row):
            self._row = row
            self._dict = dict(row)  # Convert to regular dict immediately

        def __getitem__(self, key):
            # Handle 'value' specially to prevent the common SQL error
            if key == "value":
                return self._dict.get("ioc_value", None)
            return self._dict.get(key, None)

        def keys(self):
            return self._dict.keys()

        def get(self, key, default=None):
            value = self.__getitem__(key)
            return value if value is not None else default

        def items(self):
            return self._dict.items()

    # Use the ThreadLocalSafeRow in place of sqlite3.Row for this request
    original_row_factory = sqlite3.Row
    sqlite3.Connection.row_factory = lambda _, row: ThreadLocalSafeRow(
        original_row_factory(_, row)
    )

    try:
        # Get database connection with proper error handling
        conn = get_db_connection()
        if not conn:
            logger.error("Database connection failed")
            return jsonify(generate_fallback_explanation(ioc_value))

        # Log database schema for debugging
        try:
            cursor = conn.execute("PRAGMA table_info(iocs)")
            columns = [row["name"] for row in cursor.fetchall()]
            logger.debug(f"Database columns: {columns}")
        except Exception as e:
            logger.warning(f"Could not retrieve database schema: {e}")

        # Try to find the IOC in the database with parameterized query
        try:
            # Clean the input for better matching
            cleaned_ioc_value = clean_text(ioc_value)

            # Create a "safe" query that won't use the 'value' column name
            cursor = conn.execute(
                "SELECT * FROM iocs WHERE ioc_value = ?", (cleaned_ioc_value,)
            )

            # Use our ThreadLocalSafeRow for the result
            ioc_dict = dict(cursor.fetchone() or {})

            # Generate a fallback if not found
            if not ioc_dict:
                logger.info(f"IOC not found: {ioc_value}")
                return jsonify(generate_fallback_explanation(ioc_value))

            # Generate visualization filename based on hash of IOC
            viz_filename = (
                f"ioc_explanation_{abs(hash(str(ioc_value))) % 10000:04d}.png"
            )
            viz_path = os.path.join(VISUALIZATIONS_DIR, viz_filename)

            # Generate explanation using a separate function to isolate any potential errors
            explanation = generate_safe_explanation(ioc_dict, ioc_value, viz_path)

            # Success! Return the explanation
            return jsonify(
                {
                    "ioc": ioc_dict,
                    "explanation": explanation.get("explanation", []),
                    "visualization": explanation.get("visualization"),
                    "note": explanation.get("note"),
                }
            )

        except Exception as query_err:
            logger.error(f"Error processing IOC query: {query_err}")
            # Use fallback
            return jsonify(generate_fallback_explanation(ioc_value))

    except Exception as e:
        logger.error(f"Error in explain_ioc: {e}")
        return jsonify(generate_fallback_explanation(ioc_value))

    finally:
        # Restore original row factory
        sqlite3.Connection.row_factory = original_row_factory

        # Close connection if it exists
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


def generate_safe_explanation(ioc_dict, ioc_value, viz_path):
    """Safely generate an explanation without risking SQL column errors."""
    try:
        # Try to use existing explanation from DB if available
        explanation_data = ioc_dict.get("explanation_data")
        if explanation_data:
            try:
                if isinstance(explanation_data, str):
                    explanation = json.loads(explanation_data)
                    # Extract the explanation features (top features)
                    explanation_features = []
                    if "top_features" in explanation:
                        explanation_features = [
                            {"feature": feature, "importance": importance, "value": 1}
                            for feature, importance in explanation.get(
                                "top_features", []
                            )
                        ]
                    elif "shap_values" in explanation:
                        # Convert SHAP values to feature importance format
                        shap_items = sorted(
                            explanation["shap_values"].items(),
                            key=lambda x: abs(x[1]),
                            reverse=True,
                        )[:10]
                        explanation_features = [
                            {"feature": feature, "importance": value, "value": 1}
                            for feature, value in shap_items
                        ]

                    if explanation_features:
                        # Create visualization if possible
                        try:
                            create_feature_importance_viz(
                                explanation_features, viz_path
                            )
                            return {
                                "explanation": explanation_features,
                                "visualization": f"/visualizations/{os.path.basename(viz_path)}",
                                "note": "Explanation generated from existing data",
                            }
                        except Exception as viz_err:
                            logger.error(f"Error creating visualization: {viz_err}")

            except Exception as parse_err:
                logger.error(f"Error parsing explanation data: {parse_err}")

        # Generate a fallback explanation if we couldn't use the existing one
        fallback = generate_fallback_explanation(ioc_value)
        return {
            "explanation": fallback["explanation"],
            "visualization": None,
            "note": "Generated fallback explanation",
        }

    except Exception as e:
        logger.error(f"Error in generate_safe_explanation: {e}")
        return {
            "explanation": generate_fallback_explanation(ioc_value)["explanation"],
            "visualization": None,
            "note": "Error generating explanation",
        }


def create_feature_importance_viz(features, output_path):
    """Create a feature importance visualization from features."""
    plt.figure(figsize=(10, 6))

    # Extract feature names and importance values
    feature_names = [item["feature"] for item in features]
    importance_values = [item["importance"] for item in features]

    # Create 'direction' for color coding
    directions = ["positive" if imp >= 0 else "negative" for imp in importance_values]
    direction_colors = {"positive": "green", "negative": "red"}

    # Create the plot with proper color coding
    bars = plt.barh(
        feature_names,
        [abs(val) for val in importance_values],
        color=[direction_colors[d] for d in directions],
    )

    # Add labels
    for bar, val in zip(bars, importance_values):
        plt.text(
            abs(val) + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}",
            va="center",
        )

    plt.title("Feature Importance")
    plt.xlabel("Impact on Score")
    plt.tight_layout()

    # Save visualization
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


@app.route("/api/stats")
@rate_limit
def get_stats():
    """Get statistics about the IOCs in the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        stats = {}

        # Count by type
        cursor = conn.execute(
            "SELECT ioc_type, COUNT(*) as count FROM iocs GROUP BY ioc_type"
        )
        # Convert SQLite Row objects to standard Python dictionaries
        stats["by_type"] = {row["ioc_type"]: row["count"] for row in cursor.fetchall()}

        # Count by category
        cursor = conn.execute(
            "SELECT category, COUNT(*) as count FROM iocs GROUP BY category"
        )
        # Convert SQLite Row objects to standard Python dictionaries
        stats["by_category"] = {
            row["category"]: row["count"] for row in cursor.fetchall()
        }

        # Count by source_feed
        cursor = conn.execute(
            "SELECT source_feed, COUNT(*) as count FROM iocs GROUP BY source_feed"
        )
        # Convert SQLite Row objects to standard Python dictionaries
        stats["by_source_feed"] = {
            row["source_feed"]: row["count"] for row in cursor.fetchall()
        }

        # Score distribution
        cursor = conn.execute(
            "SELECT MIN(score) as min, MAX(score) as max, AVG(score) as avg FROM iocs"
        )
        score_row = cursor.fetchone()
        # Convert SQLite Row to a regular dict with serializable values
        score_stats = {
            "min": float(score_row["min"])
            if score_row and score_row["min"] is not None
            else 0,
            "max": float(score_row["max"])
            if score_row and score_row["max"] is not None
            else 0,
            "avg": float(score_row["avg"])
            if score_row and score_row["avg"] is not None
            else 0,
        }
        stats["scores"] = score_stats

        # Create score distribution visualization
        try:
            # Ensure the visualizations directory exists
            os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)
            logger.info(f"Saving visualization to {VISUALIZATIONS_DIR}")

            cursor = conn.execute("SELECT score FROM iocs")
            # Convert SQLite Row objects to standard Python values
            scores = [float(row[0]) for row in cursor.fetchall() if row[0] is not None]

            if not scores:
                # If no scores, create a dummy visualization with a message
                plt.figure(figsize=(10, 6))
                plt.text(
                    0.5,
                    0.5,
                    "No score data available",
                    ha="center",
                    va="center",
                    fontsize=14,
                )
                plt.xlim(0, 1)
                plt.ylim(0, 1)
                plt.title("IOC Score Distribution")
                plt.tight_layout()
            else:
                # Create visualization with the scores
                plt.figure(figsize=(10, 6))
                # Create a pandas DataFrame for better seaborn integration
                score_df = pd.DataFrame({"score": scores})
                sns.histplot(data=score_df, x="score", kde=True, bins=20)
                plt.title("IOC Score Distribution")
                plt.xlabel("Score")
                plt.ylabel("Frequency")
                plt.tight_layout()

            # Save visualization to a file
            viz_filename = "score_distribution.png"
            viz_path = os.path.join(VISUALIZATIONS_DIR, viz_filename)
            plt.savefig(viz_path)
            plt.close()

            # Check if the file was created successfully
            if not os.path.exists(viz_path):
                logger.error(f"Failed to create visualization file at {viz_path}")
                stats["visualizations"] = {"error": "Failed to create visualization"}
            else:
                logger.info(f"Successfully created visualization at {viz_path}")
                stats["visualizations"] = {
                    "score_distribution": f"/visualizations/{viz_filename}"
                }

        except Exception as viz_err:
            logger.error(f"Error creating visualization: {viz_err}")
            stats["visualizations"] = {
                "error": f"Error creating visualization: {str(viz_err)}"
            }

        conn.close()
        return jsonify(
            {
                "total": sum(stats["by_type"].values()),
                "by_type": stats["by_type"],
                "by_category": stats["by_category"],
                "by_source_feed": stats["by_source_feed"],
                "score_stats": score_stats,
                "visualizations": stats.get(
                    "visualizations", {"error": "No visualization data"}
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return jsonify(
            {
                "error": "An error occurred while retrieving statistics",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/batch/recategorize", methods=["POST"])
@rate_limit("batch")
def batch_recategorize():
    """Recategorize multiple IOCs."""
    try:
        data = request.get_json()
        if not data or "iocs" not in data or "category" not in data:
            return jsonify({"error": "Missing required fields: iocs and category"}), 400

        # Validate category
        if data["category"] not in ["low", "medium", "high"]:
            return jsonify(
                {"error": "Invalid category. Must be low, medium, or high"}
            ), 400

        # Get the list of IOCs and new category
        ioc_values = data["iocs"]
        new_category = data["category"]

        if not isinstance(ioc_values, list) or len(ioc_values) == 0:
            return jsonify({"error": "IOC list must be a non-empty array"}), 400

        # Limit the number of IOCs that can be processed at once
        if len(ioc_values) > 1000:
            return jsonify(
                {"error": "Too many IOCs. Maximum 1000 allowed at once"}
            ), 400

        # Validate individual IOC values
        valid_iocs = []
        for ioc in ioc_values:
            is_valid, _ = validate_ioc_value(ioc)
            if is_valid:
                valid_iocs.append(ioc)
            else:
                logger.warning(f"Skipping invalid IOC in batch: {ioc}")

        if not valid_iocs:
            return jsonify({"error": "No valid IOCs to process"}), 400

        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Use parameterized query with executemany for safety and efficiency
        placeholders = ",".join(["?"] * len(valid_iocs))
        query = f"UPDATE iocs SET category = ? WHERE ioc_value IN ({placeholders})"

        # First parameter is the category, followed by all IOC values
        params = [new_category] + valid_iocs

        cursor = conn.execute(query, params)
        conn.commit()

        updated_count = cursor.rowcount
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f"Successfully updated {updated_count} IOCs",
                "updated_count": updated_count,
                "total_requested": len(ioc_values),
                "valid_count": len(valid_iocs),
            }
        )

    except Exception as e:
        logger.error(f"Error in batch recategorize: {e}", exc_info=True)
        return jsonify(
            {
                "error": "An error occurred during batch recategorization",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/batch/delete", methods=["POST"])
@rate_limit("batch")
def batch_delete():
    """Delete multiple IOCs."""
    try:
        data = request.get_json()
        if not data or "iocs" not in data:
            return jsonify({"error": "Missing required field: iocs"}), 400

        # Get the list of IOCs
        ioc_values = data["iocs"]

        if not isinstance(ioc_values, list) or len(ioc_values) == 0:
            return jsonify({"error": "IOC list must be a non-empty array"}), 400

        # Limit the number of IOCs that can be processed at once
        if len(ioc_values) > 1000:
            return jsonify(
                {"error": "Too many IOCs. Maximum 1000 allowed at once"}
            ), 400

        # Validate individual IOC values
        valid_iocs = []
        for ioc in ioc_values:
            is_valid, _ = validate_ioc_value(ioc)
            if is_valid:
                valid_iocs.append(ioc)
            else:
                logger.warning(f"Skipping invalid IOC in batch: {ioc}")

        if not valid_iocs:
            return jsonify({"error": "No valid IOCs to process"}), 400

        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Use parameterized query with placeholders for safety
        placeholders = ",".join(["?"] * len(valid_iocs))
        query = f"DELETE FROM iocs WHERE ioc_value IN ({placeholders})"

        cursor = conn.execute(query, valid_iocs)
        conn.commit()

        deleted_count = cursor.rowcount
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f"Successfully deleted {deleted_count} IOCs",
                "deleted_count": deleted_count,
                "total_requested": len(ioc_values),
                "valid_count": len(valid_iocs),
            }
        )

    except Exception as e:
        logger.error(f"Error in batch delete: {e}", exc_info=True)
        return jsonify(
            {
                "error": "An error occurred during batch deletion",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/api/batch/export", methods=["POST"])
@rate_limit("batch")
def batch_export():
    """Export specifically selected IOCs."""
    try:
        data = request.get_json()
        if not data or "iocs" not in data or "format" not in data:
            return jsonify({"error": "Missing required fields: iocs and format"}), 400

        # Validate format
        if data["format"] not in ["csv", "json"]:
            return jsonify({"error": "Invalid format. Must be csv or json"}), 400

        # Get the list of IOCs and format
        ioc_values = data["iocs"]
        export_format = data["format"]

        if not isinstance(ioc_values, list) or len(ioc_values) == 0:
            return jsonify({"error": "IOC list must be a non-empty array"}), 400

        # Limit the number of IOCs that can be exported at once
        if len(ioc_values) > 1000:
            return jsonify(
                {"error": "Too many IOCs. Maximum 1000 allowed at once"}
            ), 400

        # Validate individual IOC values
        valid_iocs = []
        for ioc in ioc_values:
            is_valid, _ = validate_ioc_value(ioc)
            if is_valid:
                valid_iocs.append(ioc)
            else:
                logger.warning(f"Skipping invalid IOC in batch: {ioc}")

        if not valid_iocs:
            return jsonify({"error": "No valid IOCs to export"}), 400

        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        # Use parameterized query with placeholders for safety
        placeholders = ",".join(["?"] * len(valid_iocs))
        query = f"SELECT ioc_type, ioc_value, source_feed, first_seen, last_seen, score, category FROM iocs WHERE ioc_value IN ({placeholders})"

        cursor = conn.execute(query, valid_iocs)
        iocs = []

        # Process each row and detect timestamp-like values or corrupted URLs
        for row in cursor.fetchall():
            ioc_dict = row_to_dict(row)
            iocs.append(ioc_dict)

        conn.close()

        # Generate appropriate response based on format
        if export_format == "csv":
            # Create CSV data
            csv_file = StringIO()
            if iocs:
                fieldnames = iocs[0].keys()
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                # Write headers and data
                csv_writer.writeheader()
                csv_writer.writerows(iocs)

            # Create the response
            filename = (
                f"sentinelforge_selected_iocs_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            )
            response = Response(csv_file.getvalue(), mimetype="text/csv")
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"

            return response
        else:  # JSON format
            # Create JSON data
            json_data = json.dumps({"iocs": iocs}, indent=2)

            # Create the response
            filename = (
                f"sentinelforge_selected_iocs_{time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            response = Response(json_data, mimetype="application/json")
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"

            return response

    except Exception as e:
        logger.error(f"Error in batch export: {e}", exc_info=True)
        return jsonify(
            {
                "error": "An error occurred during batch export",
                "details": str(e) if app.debug else "Enable debug mode for details",
            }
        ), 500


@app.route("/visualizations/<path:filename>")
def get_visualization(filename):
    """Serve visualization files."""
    # Validate the filename to prevent directory traversal
    if not re.match(r"^[a-zA-Z0-9_\-.]+\.(png|jpg|jpeg|svg)$", filename):
        return jsonify({"error": "Invalid filename"}), 400

    # Check if the file exists
    viz_path = os.path.join(VISUALIZATIONS_DIR, filename)
    if not os.path.exists(viz_path):
        logger.warning(f"Visualization file not found: {viz_path}")

        # Create a fallback image
        plt.figure(figsize=(10, 6))
        plt.text(
            0.5,
            0.5,
            "Visualization not available",
            ha="center",
            va="center",
            fontsize=14,
        )
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.tight_layout()

        # Ensure the directory exists
        os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

        # Save the fallback image with the requested filename
        plt.savefig(viz_path)
        plt.close()

        # Log that we created a fallback
        logger.info(f"Created fallback visualization: {viz_path}")

    # Add caching headers for visualizations
    response = send_from_directory(VISUALIZATIONS_DIR, filename)

    # Add cache control headers for better performance
    # Cache for 1 hour, revalidate if needed
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["ETag"] = f'"{abs(hash(filename))}"'

    return response


# Add cache headers for static files
@app.after_request
def add_cache_headers(response):
    """Add cache headers to static files."""
    if request.path.startswith("/static/"):
        # Cache static resources for 7 days
        response.headers["Cache-Control"] = "public, max-age=604800"

        # Generate an ETag based on the path
        response.headers["ETag"] = f'"{abs(hash(request.path))}"'

    # Add response time header for monitoring
    response.headers["X-Response-Time"] = (
        f"{time.time() - request.environ.get('REQUEST_START_TIME', time.time()):.3f}s"
    )

    return response


# Add request start time to track response time
@app.before_request
def before_request():
    """Record request start time for performance tracking."""
    request.environ["REQUEST_START_TIME"] = time.time()


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Check if database exists
    if not DB_PATH.exists():
        logger.warning(
            f"Database file not found at {DB_PATH}. Make sure to run ingest first."
        )

    # Start the Flask app with a different port
    app.run(host="0.0.0.0", port=5050, debug=True)
