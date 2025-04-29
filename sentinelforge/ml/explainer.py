"""
Module for providing explainability for ML model predictions using SHAP.
"""

import logging
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, Optional

from sentinelforge.ml.scoring_model import _model, EXPECTED_FEATURES

logger = logging.getLogger(__name__)

# Create an explainer once when the module is loaded
_explainer = None
if _model is not None:
    try:
        logger.info("Initializing SHAP explainer for the ML model")
        _explainer = shap.TreeExplainer(_model)
        logger.info("SHAP explainer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SHAP explainer: {e}", exc_info=True)
        _explainer = None
else:
    logger.warning("ML model not loaded, SHAP explainer will not be available")


def get_explanation(features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate SHAP values to explain a model prediction.

    Args:
        features: Dictionary of features used for prediction.

    Returns:
        Dictionary containing explanation data including:
        - shap_values: The SHAP values for each feature
        - top_features: List of the top 5 most influential features
        - base_value: The expected value (model's base prediction)
        - plot_path: Path to a saved force plot image
    """
    if _explainer is None:
        logger.warning("SHAP explainer not available, cannot provide explanation")
        return None

    try:
        # Convert feature dictionary to a pandas DataFrame
        feature_names = list(EXPECTED_FEATURES)
        feature_array = np.array([[features.get(name, 0) for name in feature_names]])
        feature_df = pd.DataFrame(feature_array, columns=feature_names)

        # Calculate SHAP values
        shap_values = _explainer.shap_values(feature_df)

        # Handle different SHAP value structures
        # For RandomForestClassifier, shap_values may be a list of arrays
        # (one per class for classification models)
        if isinstance(shap_values, list) and len(shap_values) > 1:
            # For binary classification, use the second class (malicious class)
            class_shap_values = shap_values[1]
        else:
            # For regression or other cases, use the values directly
            class_shap_values = shap_values

        # Ensure we're working with a 2D array and extract the first row
        if len(class_shap_values.shape) > 1:
            if class_shap_values.shape[0] == 1:  # Just one sample
                flat_shap_values = class_shap_values[0]
            else:
                # This shouldn't happen with a single prediction, but just in case
                flat_shap_values = class_shap_values[0]
                logger.warning(
                    f"Unexpected SHAP values shape: {class_shap_values.shape}, using first row"
                )
        else:
            # Already a 1D array
            flat_shap_values = class_shap_values

        # Extract SHAP values as Python native types to avoid NumPy issues
        features_with_shap = []
        for i, name in enumerate(feature_names):
            # Safely convert to Python float
            try:
                if i < len(flat_shap_values):
                    shap_val = float(flat_shap_values[i])
                else:
                    logger.warning(f"Missing SHAP value for feature {name}, using 0.0")
                    shap_val = 0.0
                features_with_shap.append((name, shap_val))
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"Error converting SHAP value for {name}: {e}, using 0.0"
                )
                features_with_shap.append((name, 0.0))

        # Sort by absolute SHAP value
        features_with_shap.sort(key=lambda x: abs(x[1]), reverse=True)
        top_features = features_with_shap[:5]

        # Get expected value (base prediction)
        if hasattr(_explainer, "expected_value"):
            base_value = _explainer.expected_value

            # Handle different expected_value structures
            if isinstance(base_value, list) or isinstance(base_value, np.ndarray):
                if len(base_value) > 1:
                    # For binary classification, use the second class (malicious class)
                    base_value = base_value[1]
                else:
                    base_value = base_value[0]

            # Ensure it's a Python float
            try:
                base_value = float(base_value)
            except (TypeError, ValueError):
                if hasattr(base_value, "item"):
                    base_value = (
                        base_value.item()
                    )  # Convert NumPy scalar to Python scalar
                else:
                    logger.warning("Could not convert base_value to float, using 0.5")
                    base_value = 0.5
        else:
            # If no expected_value is available, use a default
            logger.warning("No expected_value in explainer, using default 0.5")
            base_value = 0.5

        # Generate force plot visualization
        shap_plot_path = None
        try:
            # Create visualizations directory if it doesn't exist
            Path("visualizations").mkdir(exist_ok=True)

            # Create a unique filename for this plot
            import time

            timestamp = int(time.time())
            plot_path = f"visualizations/shap_plot_{timestamp}.png"

            # Create a SHAP summary plot instead of force plot (more reliable)
            plt.figure(figsize=(10, 6))
            shap.summary_plot(
                class_shap_values, feature_df, plot_type="bar", show=False
            )
            plt.tight_layout()
            plt.savefig(plot_path, bbox_inches="tight")
            plt.close()

            shap_plot_path = plot_path
            logger.info(f"SHAP summary plot saved to {shap_plot_path}")
        except Exception as e:
            logger.error(f"Failed to create SHAP visualization: {e}")

        return {
            "shap_values": {name: value for name, value in features_with_shap},
            "top_features": [(name, value) for name, value in top_features],
            "base_value": base_value,
            "plot_path": shap_plot_path,
        }

    except Exception as e:
        logger.error(f"Failed to generate SHAP explanation: {e}", exc_info=True)
        return None


def explain_prediction_text(features: Dict[str, Any]) -> str:
    """
    Generate a human-readable text explanation of a prediction based on SHAP values.

    Args:
        features: Dictionary of features used for prediction.

    Returns:
        String containing a text explanation of the prediction.
    """
    explanation = get_explanation(features)

    if explanation is None:
        return "No explanation available."

    text = ["Factors influencing this score (in order of importance):"]

    for feature_name, value in explanation["top_features"]:
        direction = "increasing" if value > 0 else "decreasing"

        # Format the feature name to be more human-readable
        readable_name = feature_name.replace("_", " ").title()
        # Handle special cases
        if feature_name.startswith("type_"):
            ioc_type = feature_name[5:].upper()
            readable_name = f"IOC Type: {ioc_type}"
        elif feature_name.startswith("feed_"):
            feed_name = feature_name[5:].title()
            readable_name = f"Feed: {feed_name}"
        elif feature_name.startswith("contains_"):
            char = feature_name[9:]
            readable_name = f"Contains '{char}'"

        # Format the impact
        impact = abs(value)
        if impact > 0.3:
            strength = "strongly"
        elif impact > 0.1:
            strength = "moderately"
        else:
            strength = "slightly"

        text.append(
            f"- {readable_name}: {strength} {direction} the score (impact: {impact:.3f})"
        )

    return "\n".join(text)
