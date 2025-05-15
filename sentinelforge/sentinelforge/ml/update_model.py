#!/usr/bin/env python3
"""
Script to update the ML model to fix the feature names warning.

This script:
1. Loads the existing ML model
2. Updates it to work with the latest scikit-learn version by setting feature_names_in_
3. Saves the updated model
"""

import os
import logging
import joblib
import numpy as np
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentinelforge.settings import settings
from sentinelforge.ml.scoring_model import EXPECTED_FEATURES_FULL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def update_model():
    """Update the ML model to fix feature names warning."""
    model_path = settings.model_path

    # Check if model exists
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at: {model_path}")
        return False

    try:
        # Load the existing model
        logger.info(f"Loading model from {model_path}")
        model = joblib.load(model_path)

        # Save original model as backup
        backup_path = str(model_path) + ".backup"
        logger.info(f"Creating backup at {backup_path}")
        joblib.dump(model, backup_path)

        # Get the expected number of features from the model
        if hasattr(model, "n_features_in_"):
            expected_feature_count = model.n_features_in_
            logger.info(f"Model expects {expected_feature_count} features")
        else:
            # Try to infer from model parameters
            if hasattr(model, "estimators_") and len(model.estimators_) > 0:
                # For RandomForest
                expected_feature_count = model.estimators_[0].n_features_in_
                logger.info(
                    f"Model expects {expected_feature_count} features (inferred from estimators)"
                )
            else:
                # Default to first 34 features (common for v1 models)
                expected_feature_count = 34
                logger.info(f"Using default feature count: {expected_feature_count}")

        # Truncate the feature list to match what the model expects
        feature_names = EXPECTED_FEATURES_FULL[:expected_feature_count]
        logger.info(f"Using {len(feature_names)} features: {feature_names}")

        # Update feature_names_in_ attribute
        logger.info("Updating feature_names_in_ attribute")
        model.feature_names_in_ = np.array(feature_names)

        # Save the updated model
        logger.info(f"Saving updated model to {model_path}")
        joblib.dump(model, model_path)

        logger.info("Model updated successfully")
        return True

    except Exception as e:
        logger.error(f"Error updating model: {e}")
        return False


if __name__ == "__main__":
    if update_model():
        print("Model updated successfully.")
    else:
        print("Failed to update model. See logs for details.")
        sys.exit(1)
