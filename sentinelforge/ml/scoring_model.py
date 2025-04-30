import logging
import os
import contextlib
import sqlite3  # Add this import for SQLite error handling
from typing import Dict, List, Any

# Import ML libraries with error handling
try:
    import numpy as np  # noqa: F401

    # Only import pandas and sklearn when needed for type checking
    import pandas as pd  # noqa: F401
    import joblib
    from sklearn.ensemble import RandomForestClassifier  # noqa: F401

    _ml_libraries_available = True
except ImportError:
    _ml_libraries_available = False
    logging.warning(
        "ML libraries (pandas, numpy, joblib, scikit-learn) not available. ML scoring will be disabled."
    )

# Import settings
from sentinelforge.settings import settings

logger = logging.getLogger(__name__)

# Default model path
MODEL_FILE_PATH = settings.model_path

# These feeds are known by the model during training
KNOWN_SOURCE_FEEDS = [
    "dummy",
    "abusech",
    "urlhaus",
    "malwaredomains",
    "phishtank",
    "openphish",
]

# Expected features the model was trained on
EXPECTED_FEATURES = [
    "type_ip",
    "type_domain",
    "type_url",
    "type_hash",
    "type_other",
    "feed_dummy",
    "feed_abusech",
    "feed_urlhaus",
    "feed_malwaredomains",
    "feed_phishtank",
    "feed_openphish",
    "feed_count",
    "has_country",
    "country_high_risk",
    "country_medium_risk",
    "has_geo_coords",
    "has_registrar",
    "has_creation_date",
    "url_length",
    "dot_count",
    "contains_?",
    "contains_=",
    "contains_&",
    "hash_length",
    "has_summary",
    "summary_length",
    "from_threat_feed",
    "from_url_feed",
    "from_test_feed",
]

# Load the model (if available)
_model = None
try:
    if os.path.exists(MODEL_FILE_PATH) and _ml_libraries_available:
        _model = joblib.load(MODEL_FILE_PATH)
        logger.info(f"ML model loaded successfully from {MODEL_FILE_PATH}")
    else:
        if not os.path.exists(MODEL_FILE_PATH):
            logger.warning(
                f"ML model file not found at {MODEL_FILE_PATH}. ML scoring will be limited."
            )
        # Model remains None
except Exception as e:
    logger.error(f"Error loading ML model: {e}")
    # Model remains None

# Define known IOC types and source feeds for feature generation
# TODO: Keep this list consistent with normalization/ingestion logic
KNOWN_IOC_TYPES = [
    "ip",
    "domain",
    "url",
    "hash",
    "email",
    "other",
]  # Added email, other

# Define the expected features based on the above + feed count
EXPECTED_FEATURES_FULL = (
    [f"type_{t}" for t in KNOWN_IOC_TYPES]
    + [f"feed_{f}" for f in KNOWN_SOURCE_FEEDS]
    + ["feed_count"]
    + [
        "has_country",
        "country_high_risk",
        "country_medium_risk",
        "has_geo_coords",
    ]  # IP features
    + ["has_registrar", "has_creation_date"]  # Domain features
    + ["url_length", "dot_count", "has_ip_in_url"]  # URL features
    + [
        "contains_&",
        "contains_?",
        "contains_=",
        "contains_.",
        "contains_-",
        "contains__",
        "contains_~",
        "contains_%",
        "contains_+",
    ]  # URL special chars
    + ["hash_length"]  # Hash features
    + [
        "has_summary",
        "summary_length",
        "from_threat_feed",
        "from_url_feed",
        "from_test_feed",
    ]  # General features
)


# --- Feature Extraction ---
class SafeDict(dict):
    """
    A dictionary subclass that prevents access to non-existent keys
    and avoids common SQL or access errors.

    This is used to wrap enrichment data to prevent errors in SQL operations
    due to unexpected nested keys or values.
    """

    def __getitem__(self, key):
        try:
            # Safely retrieve value without raising error for missing keys
            value = super().get(key)

            # If value is another dict, wrap it in SafeDict
            if isinstance(value, dict):
                return SafeDict(value)

            # If value is list, ensure all dict items are SafeDict
            if isinstance(value, list):
                return [
                    SafeDict(item) if isinstance(item, dict) else item for item in value
                ]

            return value
        except Exception as e:
            # Log error and return None instead of raising
            logger.error(f"Error accessing dict key '{key}': {e}")
            return None

    def get(self, key, default=None):
        try:
            value = super().get(key, default)

            # If value is another dict, wrap it in SafeDict
            if isinstance(value, dict):
                return SafeDict(value)

            # If value is list, ensure all dict items are SafeDict
            if isinstance(value, list):
                return [
                    SafeDict(item) if isinstance(item, dict) else item for item in value
                ]

            return value
        except Exception as e:
            logger.error(f"Error accessing dict key '{key}': {e}")
            return default

    def __contains__(self, key):
        try:
            return super().__contains__(key)
        except Exception as e:
            logger.error(f"Error checking if key '{key}' in dict: {e}")
            return False


def extract_features(
    ioc_type: str,
    source_feeds: List[str],
    ioc_value: str = "",
    enrichment_data: Dict[str, Any] = None,
    summary: str = "",
) -> Dict[str, float]:
    """
    Extract ML features from an IOC and its metadata.

    Args:
        ioc_type: The type of indicator (e.g., "ip", "domain", "url", "hash")
        source_feeds: List of feed names where the IOC was observed
        ioc_value: The actual indicator value
        enrichment_data: Optional dictionary with enrichment data
        summary: Optional summary/description of the IOC

    Returns:
        A dictionary with feature names and values (all numeric)
    """
    try:
        # First, check for binary data or invalid inputs to prevent errors
        if not isinstance(ioc_value, str):
            logger.warning(
                f"Non-string ioc_value detected: {type(ioc_value)}. Converting to string."
            )
            try:
                ioc_value = str(ioc_value)
            except Exception as e:
                logger.error(f"Could not convert ioc_value to string: {e}")
                ioc_value = ""

        # Check for binary data or problematic characters
        if any(ord(c) < 32 or ord(c) > 126 for c in ioc_value):
            logger.warning(
                "Binary data detected in ioc_value. Using safe processing mode."
            )
            # Don't access the actual value in processing below
            ioc_value = f"[binary-data-{abs(hash(ioc_value)) % 1000:03d}]"

        # Validate ioc_type
        if not isinstance(ioc_type, str):
            logger.warning(
                f"Non-string ioc_type detected: {type(ioc_type)}. Using 'unknown'."
            )
            ioc_type = "unknown"

        # Validate source_feeds
        if not isinstance(source_feeds, list):
            logger.warning(
                f"Non-list source_feeds detected: {type(source_feeds)}. Using empty list."
            )
            source_feeds = []

        # Validate enrichment_data and wrap in SafeDict to prevent access errors
        if enrichment_data is not None and not isinstance(enrichment_data, dict):
            logger.warning(
                f"Non-dict enrichment_data detected: {type(enrichment_data)}. Using empty dict."
            )
            enrichment_data = {}

        # Wrap enrichment_data in SafeDict for safe access
        safe_enrichment = SafeDict(enrichment_data or {})

        # Initialize all expected features to 0
        features = {name: 0 for name in EXPECTED_FEATURES_FULL}

        # 1. One-hot encode IOC type
        normalized_type = ioc_type.lower().strip()
        type_feature = f"type_{normalized_type}"
        if type_feature in features:
            features[type_feature] = 1
        else:
            features["type_other"] = 1  # Fallback for unknown types

        # 2. Source Feed Features
        try:
            unique_feeds = set(
                f.lower().strip() for f in source_feeds if isinstance(f, str)
            )
            features["feed_count"] = len(unique_feeds)
        except Exception as e:
            logger.error(f"Error processing source feeds: {e}")
            features["feed_count"] = 0
            unique_feeds = set()

        # 3. Specific Feed Presence (Binary)
        for feed_name in KNOWN_SOURCE_FEEDS:
            feed_feature = f"feed_{feed_name}"
            if feed_name in unique_feeds:
                features[feed_feature] = 1

        # 4. Feed-specific features
        for feed in unique_feeds:
            if feed == "abusech":
                features["from_threat_feed"] = 1
            elif feed == "urlhaus":
                features["from_url_feed"] = 1
            elif feed == "dummy":
                features["from_test_feed"] = 1

        # 5. IP-specific features - wrap each section in try/except
        if normalized_type == "ip":
            try:
                # Geographical features
                if "country" in safe_enrichment and safe_enrichment["country"]:
                    features["has_country"] = 1
                    # Encode country name - safely convert to string first
                    country = str(safe_enrichment["country"]).lower()
                    features["country_high_risk"] = (
                        1
                        if country in ["russia", "china", "iran", "north korea"]
                        else 0
                    )
                    features["country_medium_risk"] = (
                        1 if country in ["ukraine", "belarus", "romania"] else 0
                    )
            except Exception as e:
                logger.error(f"Error processing IP country features: {e}")

            try:
                # Latitude/longitude features
                if (
                    "latitude" in safe_enrichment
                    and safe_enrichment["latitude"]
                    and "longitude" in safe_enrichment
                    and safe_enrichment["longitude"]
                ):
                    features["has_geo_coords"] = 1
            except Exception as e:
                logger.error(f"Error processing IP geo features: {e}")

        # 6. Domain-specific features
        if normalized_type == "domain":
            try:
                # Registrar features
                if "registrar" in safe_enrichment and safe_enrichment["registrar"]:
                    features["has_registrar"] = 1
            except Exception as e:
                logger.error(f"Error processing domain registrar features: {e}")

            try:
                # Domain age features
                if (
                    "creation_date" in safe_enrichment
                    and safe_enrichment["creation_date"]
                ):
                    features["has_creation_date"] = 1
            except Exception as e:
                logger.error(f"Error processing domain date features: {e}")

        # 7. URL-specific features
        if normalized_type == "url":
            try:
                # Check if this is binary data we marked earlier
                if not ioc_value.startswith("[binary-data-"):
                    # URL length
                    features["url_length"] = len(ioc_value)

                    # Count special characters in URL
                    special_chars = ["&", "?", "=", ".", "-", "_", "~", "%", "+"]
                    for char in special_chars:
                        features[f"contains_{char}"] = 1 if char in ioc_value else 0

                    # Count number of dots in URL
                    features["dot_count"] = ioc_value.count(".")

                    # Check for IP in URL
                    features["has_ip_in_url"] = (
                        1 if any(c.isdigit() for c in ioc_value.split(".")) else 0
                    )
                else:
                    # For binary data, set generic URL features
                    features["url_length"] = 50  # Average URL length
                    features["dot_count"] = 2  # Average number of dots
                    features["has_ip_in_url"] = 0
            except Exception as e:
                logger.error(f"Error processing URL features: {e}")
                # Set default values for URL features
                features["url_length"] = 50  # Average URL length
                features["dot_count"] = 2

        # 8. Hash-specific features
        if normalized_type == "hash":
            try:
                # Check if this is binary data we marked earlier
                if not ioc_value.startswith("[binary-data-"):
                    # Hash length
                    features["hash_length"] = len(ioc_value)
                else:
                    # For binary data, set realistic hash length
                    features["hash_length"] = 64  # SHA-256 length as a safe default
            except Exception as e:
                logger.error(f"Error processing hash features: {e}")
                features["hash_length"] = 64  # SHA-256 length as a safe default

        # 9. Summary features
        try:
            if summary:
                features["has_summary"] = 1
                features["summary_length"] = len(summary)
        except Exception as e:
            logger.error(f"Error processing summary features: {e}")

        logger.debug(f"Extracted features: {features}")
        return features

    except sqlite3.OperationalError as sql_err:
        # Specifically catch SQLite operational errors
        if "no such column: value" in str(sql_err):
            logger.error(
                f"Caught SQLite 'no such column: value' error in extract_features: {sql_err}. Using default features."
            )
            # Return basic features to avoid crashing
            default_features = {
                f"type_{ioc_type}": 1 if ioc_type in KNOWN_IOC_TYPES else 0,
                "type_other": 0 if ioc_type in KNOWN_IOC_TYPES else 1,
                "feed_count": len(source_feeds)
                if isinstance(source_feeds, list)
                else 0,
            }
            # Add feed features
            for feed_name in KNOWN_SOURCE_FEEDS:
                default_features[f"feed_{feed_name}"] = (
                    1
                    if isinstance(source_feeds, list) and feed_name in source_feeds
                    else 0
                )

            return default_features
        else:
            # Log other SQL errors and return safe defaults
            logger.error(f"SQLite error in extract_features: {sql_err}")
            return {
                "type_other": 1,
                "feed_count": 0,
            }
    except Exception as e:
        # Catch the "no such column: value" error which can occur in SQL operations
        if isinstance(e, Exception) and "no such column: value" in str(e):
            logger.error(
                "Caught 'no such column: value' error in extract_features. Using default features."
            )
            # Return basic features to avoid crashing
            default_features = {
                f"type_{ioc_type}": 1 if ioc_type in KNOWN_IOC_TYPES else 0,
                "type_other": 0 if ioc_type in KNOWN_IOC_TYPES else 1,
                "feed_count": len(source_feeds)
                if isinstance(source_feeds, list)
                else 0,
            }
            # Add feed features
            for feed_name in KNOWN_SOURCE_FEEDS:
                default_features[f"feed_{feed_name}"] = (
                    1
                    if isinstance(source_feeds, list) and feed_name in source_feeds
                    else 0
                )

            return default_features
        else:
            # Log the error and return safe defaults instead of re-raising
            logger.error(f"Error in extract_features: {e}")
            # Create a minimal set of features to avoid breaking the application
            return {
                "type_other": 1,
                "feed_count": 0,
            }


# --- Prediction ---
def predict_score(features: Dict[str, Any]) -> float:
    """
    Uses the loaded ML model to predict a score based on extracted features.

    Args:
        features: A dictionary of features.

    Returns:
        A predicted score (e.g., probability of maliciousness 0.0-1.0).
        Returns 0.0 if the model is not loaded.
    """
    if not _model:
        logger.debug("ML model not loaded, returning default score 0.0")
        return 0.0

    try:
        # Get the feature names the model was trained on
        if hasattr(_model, "feature_names_in_"):
            model_features = list(_model.feature_names_in_)
        else:
            # Default to first 34 features if model doesn't have feature_names_in_
            model_features = EXPECTED_FEATURES_FULL[:34]

        # Create a proper pandas DataFrame with feature names to avoid sklearn warnings
        import pandas as pd

        # Prepare feature vector with correct names
        feature_dict = {name: features.get(name, 0) for name in model_features}
        feature_df = pd.DataFrame([feature_dict])

        # Ensure all expected features are present with the right order
        feature_df = feature_df[model_features]

        # Get probability of malicious class (second column of predict_proba output)
        with (
            open(os.devnull, "w") as f,
            contextlib.redirect_stderr(f),
        ):  # Suppress warnings
            prediction = _model.predict_proba(feature_df)[0, 1]

        logger.debug(f"ML model predicted score: {prediction}")
        return float(prediction)

    except Exception as e:
        logger.error(f"ML model prediction failed: {e}", exc_info=True)
        return 0.0
