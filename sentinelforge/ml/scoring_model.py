import logging
from typing import Dict, Any, List, Set
import joblib  # Example for loading models
from pathlib import Path
import os
import contextlib

# TODO: Define path for saved models
MODEL_PATH = Path("models/ioc_scorer.joblib")  # Example path

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
KNOWN_SOURCE_FEEDS = ["dummy", "urlhaus", "abusech"]  # From scoring_rules.yaml

# Define the expected features based on the above + feed count
EXPECTED_FEATURES = (
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

logger = logging.getLogger(__name__)

# --- Model Loading ---
# Load the trained model once when the module is imported
_model = None
if MODEL_PATH.exists():
    try:
        _model = joblib.load(MODEL_PATH)
        logger.info(f"ML scoring model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        logger.error(
            f"Failed to load ML scoring model from {MODEL_PATH}: {e}", exc_info=True
        )
        _model = None
else:
    logger.warning(
        f"ML scoring model file not found at {MODEL_PATH}. ML scoring will be disabled."
    )


# --- Feature Extraction ---
def extract_features(
    ioc_type: str,
    source_feeds: List[str],
    ioc_value: str = "",
    enrichment_data: Dict = None,
    summary: str = "",
) -> Dict[str, Any]:
    """
    Extracts features for the ML model based on IOC type, value, source feeds, and optional enrichment data.

    Args:
        ioc_type: The type of the indicator (e.g., 'ip', 'domain').
        source_feeds: List of feed names where the IOC appeared.
        ioc_value: The actual value of the IOC (e.g., the IP address, domain name).
        enrichment_data: Optional dictionary containing enrichment data.
        summary: Optional text summary of the IOC.

    Returns:
        A dictionary of features ready for the model.
    """
    # Initialize enrichment data if None
    if enrichment_data is None:
        enrichment_data = {}

    # Initialize all expected features to 0
    features = {name: 0 for name in EXPECTED_FEATURES}

    # 1. One-hot encode IOC type
    normalized_type = ioc_type.lower().strip()
    type_feature = f"type_{normalized_type}"
    if type_feature in features:
        features[type_feature] = 1
    else:
        features["type_other"] = 1  # Fallback for unknown types

    # 2. Source Feed Features
    unique_feeds: Set[str] = set(f.lower().strip() for f in source_feeds)
    features["feed_count"] = len(unique_feeds)

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

    # 5. IP-specific features
    if normalized_type == "ip":
        # Geographical features
        if "country" in enrichment_data and enrichment_data["country"]:
            features["has_country"] = 1
            # Encode country name
            country = str(enrichment_data["country"]).lower()
            features["country_high_risk"] = (
                1 if country in ["russia", "china", "iran", "north korea"] else 0
            )
            features["country_medium_risk"] = (
                1 if country in ["ukraine", "belarus", "romania"] else 0
            )

        # Latitude/longitude features
        if (
            "latitude" in enrichment_data
            and enrichment_data["latitude"]
            and "longitude" in enrichment_data
            and enrichment_data["longitude"]
        ):
            features["has_geo_coords"] = 1

    # 6. Domain-specific features
    if normalized_type == "domain":
        # Registrar features
        if "registrar" in enrichment_data and enrichment_data["registrar"]:
            features["has_registrar"] = 1

        # Domain age features
        if "creation_date" in enrichment_data and enrichment_data["creation_date"]:
            features["has_creation_date"] = 1

    # 7. URL-specific features
    if normalized_type == "url":
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

    # 8. Hash-specific features
    if normalized_type == "hash":
        # Hash length
        features["hash_length"] = len(ioc_value)

    # 9. Summary features
    if summary:
        features["has_summary"] = 1
        features["summary_length"] = len(summary)

    logger.debug(f"Extracted features: {features}")
    return features


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
        # Prepare feature vector in the correct order using EXPECTED_FEATURES
        # This ensures we match exactly what the model was trained with
        feature_vector = [features.get(name, 0) for name in EXPECTED_FEATURES]

        # Reshape for scikit-learn (assuming single sample)
        import numpy as np

        feature_array = np.array([feature_vector])

        # Get probability of malicious class (second column of predict_proba output)
        with (
            open(os.devnull, "w") as f,
            contextlib.redirect_stderr(f),
        ):  # Suppress warnings
            prediction = _model.predict_proba(feature_array)[0, 1]

        logger.debug(f"ML model predicted score: {prediction}")
        return float(prediction)

    except Exception as e:
        logger.error(f"ML model prediction failed: {e}", exc_info=True)
        return 0.0
