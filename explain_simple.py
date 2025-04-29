#!/usr/bin/env python3
"""
SentinelForge ML Model Explainer

Simple command-line tool to explain model predictions for IOCs.
"""

import argparse
import sys
import logging
import os
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import seaborn as sns
from typing import List, Optional

# Import SentinelForge modules
from sentinelforge.ml.scoring_model import extract_features
from sentinelforge.ml.shap_explainer import explain_prediction
from sentinelforge.scoring import score_ioc

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def generate_explanation_text(explanation):
    """Generate human-readable text from explanation data."""
    if not explanation:
        return "No explanation available for this prediction."

    # Create a readable explanation
    text = "Factors influencing this score (in order of importance):\n"

    for item in explanation[:5]:  # Show top 5 factors
        feature = item["feature"]
        importance = item["importance"]

        # Describe the impact
        if importance > 0.3:
            impact = "strongly increasing"
        elif importance > 0.1:
            impact = "moderately increasing"
        elif importance > 0:
            impact = "slightly increasing"
        elif importance > -0.1:
            impact = "slightly decreasing"
        elif importance > -0.3:
            impact = "moderately decreasing"
        else:
            impact = "strongly decreasing"

        # Make the feature name more readable
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

        text += (
            f"- {readable_name}: {impact} the score (impact: {abs(importance):.3f})\n"
        )

    return text


def visualize_explanation(explanation, ioc_value: str, output_dir: str = "./"):
    """Generate visualization for explanation data."""
    if not explanation:
        return None

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create sanitized filename
    safe_name = "".join(c for c in ioc_value if c.isalnum() or c in ".-_")[:30]
    if not safe_name:
        safe_name = "ioc"

    # Create filenames
    summary_file = os.path.join(output_dir, f"{safe_name}_summary.png")
    waterfall_file = os.path.join(output_dir, f"{safe_name}_waterfall.png")

    # Extract data
    feature_names = [item["feature"] for item in explanation]
    importance_values = [item["importance"] for item in explanation]

    # Create summary plot
    plt.figure(figsize=(10, 8))
    sns.barplot(
        x=importance_values,
        y=feature_names,
        hue=[imp < 0 for imp in importance_values],
        palette=["red", "green"],
        legend=False,
    )
    plt.title(f"Feature Importance for {ioc_value}")
    plt.xlabel("SHAP Value (Impact on Score)")
    plt.tight_layout()
    plt.savefig(summary_file)
    plt.close()

    # Create simplified waterfall plot
    plt.figure(figsize=(12, 8))

    # Get number of features to show, up to 8
    n_features = min(len(feature_names), 8)

    # Sort by absolute importance for waterfall
    sorted_indices = sorted(
        range(len(importance_values)),
        key=lambda i: abs(importance_values[i]),
        reverse=True,
    )

    # Get top features for clarity
    top_indices = sorted_indices[:n_features]
    top_features = [feature_names[i] for i in top_indices]
    top_values = [importance_values[i] for i in top_indices]

    # Baseline value (0.5 for binary classification)
    baseline = 0.5
    cumulative = baseline

    # Create axis positions
    n_positions = n_features + 2  # features + baseline + final
    positions = list(range(n_positions))

    # Plot the waterfall
    plt.barh([positions[-1]], [baseline], color="gray", label="Baseline")

    for i, (feature, value) in enumerate(zip(top_features, top_values)):
        plt.barh(
            [positions[i + 1]],
            [value],
            left=cumulative,
            color="green" if value > 0 else "red",
        )
        cumulative += value

    plt.barh([positions[0]], [cumulative], color="blue", label="Final Score")

    # Add feature names as y-tick labels
    labels = ["Final"] + top_features + ["Baseline"]
    plt.yticks(positions, labels)
    plt.title(f"Score Contribution Waterfall for {ioc_value}")
    plt.xlabel("Contribution to Score")
    plt.tight_layout()
    plt.savefig(waterfall_file)
    plt.close()

    return summary_file, waterfall_file


def explain_ioc(
    ioc_value: str, ioc_type: str, feeds: List[str], output_dir: Optional[str] = None
) -> dict:
    """
    Generate an explanation for an IOC.

    Args:
        ioc_value: The IOC value (e.g., IP address, domain name)
        ioc_type: The IOC type (e.g., ip, domain, url, hash)
        feeds: List of feed names where the IOC was observed
        output_dir: Optional directory for saving visualizations

    Returns:
        A dictionary with explanation results
    """
    try:
        # Score the IOC
        score, category = score_ioc(
            ioc_value=ioc_value, ioc_type=ioc_type, source_feeds=feeds
        )

        # Extract features
        features = extract_features(
            ioc_type=ioc_type, source_feeds=feeds, ioc_value=ioc_value
        )

        # Generate explanation
        explanation = explain_prediction(features)

        # Generate human-readable explanation
        explanation_text = generate_explanation_text(explanation)

        # Create visualizations if output_dir is provided
        visualization_files = None
        if output_dir:
            visualization_files = visualize_explanation(
                explanation, ioc_value, output_dir
            )

        return {
            "ioc_value": ioc_value,
            "ioc_type": ioc_type,
            "source_feeds": feeds,
            "score": score,
            "category": category,
            "explanation": explanation,
            "explanation_text": explanation_text,
            "visualization_files": visualization_files,
        }

    except Exception as e:
        logger.error(f"Error explaining IOC: {e}")
        return {
            "ioc_value": ioc_value,
            "ioc_type": ioc_type,
            "source_feeds": feeds,
            "error": str(e),
        }


def main():
    """Parse command-line arguments and run the explainer."""
    parser = argparse.ArgumentParser(
        description="Explain SentinelForge ML model predictions for IOCs."
    )

    parser.add_argument(
        "ioc_value", help="The IOC value to explain (e.g., IP address, domain, URL)"
    )

    parser.add_argument(
        "ioc_type", choices=["ip", "domain", "url", "hash"], help="The type of IOC"
    )

    parser.add_argument(
        "--feeds",
        nargs="+",
        default=["dummy"],
        help="Source feeds where the IOC was observed (space-separated)",
    )

    parser.add_argument(
        "--output-dir",
        default="./visualizations",
        help="Directory to save visualization files",
    )

    args = parser.parse_args()

    # Run the explainer
    result = explain_ioc(
        ioc_value=args.ioc_value,
        ioc_type=args.ioc_type,
        feeds=args.feeds,
        output_dir=args.output_dir,
    )

    # Print the results
    print(f"\nIOC: {result['ioc_value']} ({result['ioc_type']})")
    print(f"Source Feeds: {', '.join(result['source_feeds'])}")

    if "error" in result:
        print(f"Error: {result['error']}")
        return 1

    print(f"Score: {result['score']} ({result.get('category', 'unknown')})")
    print("\n" + result["explanation_text"])

    if result.get("visualization_files"):
        summary_file, waterfall_file = result["visualization_files"]
        print(f"\nVisualizations saved to:")
        print(f"  - Summary Plot: {summary_file}")
        print(f"  - Waterfall Plot: {waterfall_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
