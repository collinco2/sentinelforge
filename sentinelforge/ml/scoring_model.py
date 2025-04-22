import logging
from typing import Dict, Any, List, Set
import joblib  # Example for loading models
from pathlib import Path

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
def extract_features(ioc_type: str, source_feeds: List[str]) -> Dict[str, Any]:
    """
    Extracts features for the ML model based on IOC type and source feeds.

    Args:
        ioc_type: The type of the indicator (e.g., 'ip', 'domain').
        source_feeds: List of feed names where the IOC appeared.

    Returns:
        A dictionary of features ready for the model.
    """
    features = {
        name: 0 for name in EXPECTED_FEATURES
    }  # Initialize all expected features to 0

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

    # TODO: Add features from enrichment data (passed via ioc_data if refactored)
    # Example: features['country_risk'] = get_country_risk(ioc_data.get('country'))
    # Example: features['domain_age_days'] = calculate_domain_age(ioc_data.get('creation_date'))

    logger.debug(f"Extracted features: {features}")
    # Ensure the final dictionary only contains keys defined in EXPECTED_FEATURES?
    # Or allow extra features? For now, allow, but model training needs consistency.
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
        # Prepare feature vector in the correct order
        # Comment out unused variable for now
        # feature_vector = [features.get(name, 0) for name in EXPECTED_FEATURES]
        # Reshape for scikit-learn (assuming single sample)
        # Comment out unused variable for now
        # feature_vector_reshaped = [feature_vector]

        # prediction = _model.predict_proba(feature_vector_reshaped)[0, 1] # Example for probability
        prediction = 0.5  # Placeholder prediction

        logger.debug(f"ML model predicted score: {prediction}")
        return float(prediction)

    except Exception as e:
        logger.error(f"ML model prediction failed: {e}", exc_info=True)
        return 0.0
