#!/usr/bin/env python3
"""
Simplified script to demonstrate ML model explainability using Kernel SHAP.
"""

import sys
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import joblib
from pathlib import Path
from typing import List

from sentinelforge.ml.scoring_model import extract_features, EXPECTED_FEATURES
from sentinelforge.scoring import score_ioc

# Create directory for plots
Path("visualizations").mkdir(exist_ok=True)


def get_model_features(ioc_value: str, ioc_type: str, feeds: List[str]) -> pd.DataFrame:
    """
    Extract features from an IOC and prepare as DataFrame, ensuring the columns
    are in the exact same order as used during training.
    """
    # Get features dictionary
    features = extract_features(
        ioc_type=ioc_type, source_feeds=feeds, ioc_value=ioc_value
    )

    # Create a single-row DataFrame with all expected features
    # Make sure we get the features in the exact order expected by the model
    # This is critical for sklearn models which expect the same feature order as training
    data = {}
    for name in EXPECTED_FEATURES:
        data[name] = [features.get(name, 0)]

    df = pd.DataFrame(data)
    return df


def sanitize_filename(text: str) -> str:
    """
    Create a safe filename from arbitrary text.
    Removes special characters, limits length, and replaces problem characters.
    """
    # Replace any non-alphanumeric characters with underscores
    safe_text = re.sub(r"[^a-zA-Z0-9_-]", "_", text)

    # Limit the length to avoid excessively long filenames
    if len(safe_text) > 50:
        safe_text = safe_text[:50]

    return safe_text


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python explain_simple.py <ioc_value> <ioc_type> [--feeds feed1 feed2 ...]"
        )
        sys.exit(1)

    ioc_value = sys.argv[1]
    ioc_type = sys.argv[2]

    # Parse feeds
    feeds = ["dummy"]  # Default feed
    if "--feeds" in sys.argv:
        feed_index = sys.argv.index("--feeds")
        if feed_index + 1 < len(sys.argv):
            feeds = []
            for i in range(feed_index + 1, len(sys.argv)):
                if sys.argv[i].startswith("--"):
                    break
                feeds.append(sys.argv[i])

    # Load the trained model
    model_path = "models/ioc_scorer.joblib"
    try:
        model = joblib.load(model_path)
        print(f"Model loaded from {model_path}")
    except FileNotFoundError:
        print(f"Error: Model file not found at {model_path}")
        sys.exit(1)

    # Print the expected feature names from the model
    print("Expected feature names:")
    if hasattr(model, "feature_names_in_"):
        print(f"Model expects {len(model.feature_names_in_)} features:")
        for i, feature in enumerate(model.feature_names_in_):
            print(f"  {i}: {feature}")

    # Extract features
    X = get_model_features(ioc_value, ioc_type, feeds)
    print(f"Extracted {len(X.columns)} features for {ioc_type}: {ioc_value}")

    # Verify that the feature names match
    if hasattr(model, "feature_names_in_"):
        all_match = True
        for i, (expected, actual) in enumerate(zip(model.feature_names_in_, X.columns)):
            if expected != actual:
                print(
                    f"Mismatch at position {i}: expected '{expected}', got '{actual}'"
                )
                all_match = False

        if all_match:
            print("Feature names match model expectations!")

    # Get the model prediction
    try:
        prediction = model.predict_proba(X)[0, 1]  # Probability of class 1 (malicious)
        print(f"ML model prediction: {prediction:.4f}")
    except Exception as e:
        print(f"Error getting prediction: {e}")
        # Try to fix the order if possible
        if hasattr(model, "feature_names_in_"):
            print("Attempting to fix feature order...")
            X_reordered = X[model.feature_names_in_]
            prediction = model.predict_proba(X_reordered)[0, 1]
            print(f"ML model prediction after reordering: {prediction:.4f}")
            X = X_reordered
        else:
            print(
                "Cannot fix feature order, model does not have feature_names_in_ attribute"
            )
            sys.exit(1)

    # Get the score using the scoring function
    score, _ = score_ioc(ioc_value, ioc_type, feeds)
    print(f"Final score: {score}")

    # Create a sanitized filename for output
    safe_ioc_value = sanitize_filename(ioc_value)

    try:
        # Use a simple permutation explainer which is more robust
        explainer = shap.explainers.Permutation(
            model.predict_proba,
            X,
            max_evals=300,  # Increase for more stable results
        )

        # Calculate SHAP values
        shap_values = explainer(X)

        # For classification models, use the positive class values
        if shap_values.shape[1] > 1:  # More than one output dimension
            shap_values = shap_values[:, :, 1]  # Select second class (malicious)

        # Create summary plot (bar plot of feature importance)
        plt.figure(figsize=(12, 8))
        shap.plots.bar(shap_values, show=False)
        plt.title(f"Feature importance for {ioc_type}: {ioc_value}", fontsize=14)
        plt.tight_layout()
        plot_path = f"visualizations/shap_summary_{ioc_type}_{safe_ioc_value}.png"
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()
        print(f"\nSHAP visualization saved to: {plot_path}")

        # Create waterfall plot for detailed explanation
        plt.figure(figsize=(12, 8))
        shap.plots.waterfall(shap_values[0], show=False)
        plt.title(f"SHAP waterfall plot for {ioc_type}: {ioc_value}", fontsize=14)
        waterfall_path = (
            f"visualizations/shap_waterfall_{ioc_type}_{safe_ioc_value}.png"
        )
        plt.savefig(waterfall_path, bbox_inches="tight")
        plt.close()
        print(f"SHAP waterfall plot saved to: {waterfall_path}")

        # Prepare feature importance info
        importance_df = pd.DataFrame(
            {
                "Feature": X.columns,
                "SHAP Value": np.abs(shap_values.values).mean(0),
                "Direction": np.where(
                    shap_values.values.mean(0) > 0, "Increases", "Decreases"
                ),
            }
        )
        importance_df = importance_df.sort_values("SHAP Value", ascending=False)

        # Print top 5 most important features
        print("\nTop 5 most influential features:")
        for i, (_, row) in enumerate(importance_df.head(5).iterrows()):
            print(
                f"  {i + 1}. {row['Feature']}: {row['Direction']} risk (importance: {row['SHAP Value']:.4f})"
            )

    except Exception as e:
        print(f"Error generating explanations: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
