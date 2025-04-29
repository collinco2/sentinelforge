import shap
import pandas as pd
import numpy as np
import joblib
import logging
from typing import Dict, List, Any

from .scoring_model import MODEL_FILE_PATH as MODEL_PATH, EXPECTED_FEATURES_FULL

# Configure logging
logger = logging.getLogger(__name__)


def load_model():
    """Load the trained ML model."""
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None


def explain_prediction(features: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate SHAP values to explain model prediction.

    Args:
        features: Dictionary of features used for prediction

    Returns:
        List of dictionaries containing feature importance information
    """
    try:
        # Load the model
        model = load_model()
        if model is None:
            return []

        # Get the feature names the model was trained on
        if hasattr(model, "feature_names_in_"):
            model_features = list(model.feature_names_in_)
        else:
            # Default to first 34 features if model doesn't have feature_names_in_
            model_features = EXPECTED_FEATURES_FULL[:34]

        # Convert features dictionary to DataFrame
        feature_df = pd.DataFrame([features])

        # Ensure all expected features are present
        for feature in model_features:
            if feature not in feature_df.columns:
                feature_df[feature] = 0

        # Reorder columns to match training data
        feature_df = feature_df[model_features]

        # Create a simpler explanation since TreeExplainer is causing issues
        # We'll use a permutation-based approach
        importances = []

        # Get baseline prediction
        baseline_pred = model.predict_proba(feature_df.values)[0, 1]

        # Test importance of each feature
        for i, feature_name in enumerate(model_features):
            # Skip features with zero value
            if feature_df[feature_name].iloc[0] == 0:
                continue

            # Create a copy with this feature zeroed
            modified = feature_df.copy()
            modified[feature_name] = 0

            # Get new prediction
            new_pred = model.predict_proba(modified.values)[0, 1]

            # Calculate importance (difference from baseline)
            importance = baseline_pred - new_pred

            importances.append(
                {
                    "feature": feature_name,
                    "importance": float(importance),
                    "value": float(feature_df[feature_name].iloc[0])
                    if pd.api.types.is_numeric_dtype(feature_df[feature_name])
                    else str(feature_df[feature_name].iloc[0]),
                }
            )

        # Sort by absolute importance
        importances.sort(key=lambda x: abs(x["importance"]), reverse=True)

        # Return top 10 features
        return importances[:10]

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return []
