import shap
import pandas as pd
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

        # Convert features dictionary to DataFrame
        feature_df = pd.DataFrame([features])

        # Ensure all expected features are present
        for feature in EXPECTED_FEATURES_FULL:
            if feature not in feature_df.columns:
                feature_df[feature] = 0

        # Reorder columns to match training data
        feature_df = feature_df[EXPECTED_FEATURES_FULL]

        # Create a SHAP explainer
        explainer = shap.TreeExplainer(model)

        # Calculate SHAP values
        shap_values = explainer.shap_values(feature_df)

        # For binary classification, shap_values is a list with one array
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class values

        # Get feature importance
        feature_importance = []
        for i, feature_name in enumerate(EXPECTED_FEATURES_FULL):
            # Skip features with zero importance
            if abs(shap_values[0][i]) < 0.001:
                continue

            feature_importance.append(
                {
                    "feature": feature_name,
                    "importance": float(shap_values[0][i]),
                    "value": float(feature_df[feature_name].iloc[0])
                    if pd.api.types.is_numeric_dtype(feature_df[feature_name])
                    else str(feature_df[feature_name].iloc[0]),
                }
            )

        # Sort by absolute importance
        feature_importance.sort(key=lambda x: abs(x["importance"]), reverse=True)

        # Limit to top 10 features
        return feature_importance[:10]

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return []
