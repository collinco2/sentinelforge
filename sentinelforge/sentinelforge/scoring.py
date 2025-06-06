import yaml

# from pathlib import Path # No longer needed directly
import logging
from typing import List, Dict, Any, Optional, Tuple

# Import centralized settings
from sentinelforge.settings import settings

# Import ML scoring functions
from sentinelforge.ml.scoring_model import (
    extract_features,
    predict_score,
    KNOWN_SOURCE_FEEDS,
)

# Import model explainability
try:
    from sentinelforge.ml.explainer import explain_prediction_text, get_explanation

    _explainer_available = True
except ImportError:
    _explainer_available = False

# Import new shap_explainer for enhanced explanations
try:
    from sentinelforge.ml.shap_explainer import explain_prediction

    _shap_explainer_available = True
except ImportError:
    _shap_explainer_available = False

logger = logging.getLogger(__name__)
# Set logger level to INFO to see our messages
logger.setLevel(logging.INFO)

# Define path to rules file relative to this file's directory or project root?
# RULES_FILE_PATH = Path("scoring_rules.yaml") # Use path from settings
RULES_FILE_PATH = settings.scoring_rules_path

# load rules once
_rules: Dict[str, Any] = {}
try:
    # Use Path object from settings
    _rules = yaml.safe_load(RULES_FILE_PATH.read_text())
    logger.info(f"Scoring rules loaded successfully from {RULES_FILE_PATH}")
except FileNotFoundError:
    # Use path from settings in error message
    logger.error(
        f"Scoring rules file not found at {RULES_FILE_PATH}. Scoring will default to 0."
    )
    # Provide default structure to prevent KeyErrors later
    _rules = {
        "feed_scores": {},
        "multi_feed_bonus": {
            "threshold": 999,
            "points": 0,
        },  # High threshold effectively disables bonus
        "tiers": {
            "high": 999,
            "medium": 998,
            "low": 0,
        },  # Ensure 'low' is always possible
    }
except yaml.YAMLError as e:
    # Use path from settings in error message
    logger.error(
        f"Error parsing scoring rules file {RULES_FILE_PATH}: {e}. Scoring will default to 0."
    )
    # Provide default structure
    _rules = {
        "feed_scores": {},
        "multi_feed_bonus": {"threshold": 999, "points": 0},
        "tiers": {"high": 999, "medium": 998, "low": 0},
    }
except Exception as e:
    # Use path from settings in error message
    logger.error(
        f"Unexpected error loading scoring rules {RULES_FILE_PATH}: {e}. Scoring will default to 0."
    )
    # Provide default structure
    _rules = {
        "feed_scores": {},
        "multi_feed_bonus": {"threshold": 999, "points": 0},
        "tiers": {"high": 999, "medium": 998, "low": 0},
    }


def rule_based_score(
    ioc_value: str,
    ioc_type: str,
    source_feeds: List[str],
) -> int:
    """
    Compute a rule-based score based on feeds and multi-feed bonuses.

    Args:
        ioc_value: The indicator value
        ioc_type: The indicator type (e.g., 'ip', 'domain')
        source_feeds: List of feed names where the IOC appeared

    Returns:
        An integer score based on rule-based scoring
    """
    rule_score = 0
    feed_scores = _rules.get("feed_scores", {})
    multi_feed_bonus = _rules.get("multi_feed_bonus", {})
    bonus_threshold = multi_feed_bonus.get("threshold", 999)  # Default high threshold
    bonus_points = multi_feed_bonus.get("points", 0)  # Default 0 points

    # Debugging: Log the feeds being scored
    logger.debug(f"Scoring IOC '{ioc_value}' seen in feeds: {source_feeds}")

    # add feed scores
    unique_feeds = set(source_feeds)  # Ensure a feed isn't counted twice
    for feed in unique_feeds:
        feed_score = feed_scores.get(feed, 0)
        logger.debug(f"  - Feed '{feed}': +{feed_score} points")
        rule_score += feed_score

    # bonus for multi-feed
    if len(unique_feeds) >= bonus_threshold:
        logger.debug(
            f"  - Multi-feed bonus applied ({len(unique_feeds)} >= {bonus_threshold}): +{bonus_points} points"
        )
        rule_score += bonus_points

    logger.debug(f"  - Rule-based score for '{ioc_value}': {rule_score}")

    return rule_score


def score_ioc(
    ioc_value: str,
    ioc_type: str,
    source_feeds: List[str],
    enrichment_data: Dict = None,
    summary: str = "",
    include_explanation: bool = False,
) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Compute a score based on feeds, multi-feed bonuses, and ML prediction.

    Args:
        ioc_value: The indicator value
        ioc_type: The indicator type (e.g., 'ip', 'domain')
        source_feeds: List of feed names where the IOC appeared
        enrichment_data: Optional enrichment data dictionary
        summary: Optional IOC summary
        include_explanation: Whether to include SHAP explanation data

    Returns:
        A tuple containing:
        - integer score (combined rule-based and ML-based)
        - optional explanation data if include_explanation is True
    """
    # --- Rule-Based Score ---
    rule_score = rule_based_score(ioc_value, ioc_type, source_feeds)

    # --- ML-Based Score ---
    # Pass all parameters to extract_features
    features = extract_features(
        ioc_type=ioc_type,
        source_feeds=source_feeds,
        ioc_value=ioc_value,
        enrichment_data=enrichment_data,
        summary=summary,
    )
    ml_score_prob = predict_score(features)  # Score is 0.0-1.0

    # Convert ML probability to same scale as rule_score (assuming 0-100 scale)
    # Get maximum possible score from rules for scaling
    max_rule_score = 100  # Default assumption
    feed_scores = _rules.get("feed_scores", {})
    for feed in KNOWN_SOURCE_FEEDS:
        max_rule_score += feed_scores.get(feed, 0)
    bonus_points = _rules.get("multi_feed_bonus", {}).get("points", 0)
    max_rule_score += bonus_points

    # Scale ML score to match rule score scale
    ml_score = int(ml_score_prob * max_rule_score)

    logger.info(
        f"  - ML-based score prediction for '{ioc_value}': {ml_score_prob:.4f} (scaled: {ml_score})"
    )
    # Add direct print statement for debugging
    print(
        f"DEBUG - ML score for {ioc_value}: {ml_score_prob:.4f} (scaled to {ml_score})"
    )

    # Combine scores with weighting (adjust weights as needed)
    # Using 70% rule-based, 30% ML-based weighting
    rule_weight = 0.7
    ml_weight = 0.3

    final_score = int((rule_score * rule_weight) + (ml_score * ml_weight))

    logger.info(
        f"  - Final combined score for '{ioc_value}': {final_score} (rule: {rule_score}, ML: {ml_score})"
    )
    # Add direct print statement for debugging
    print(
        f"DEBUG - Final score for {ioc_value}: {final_score} (rule: {rule_score}, ML: {ml_score})"
    )

    # Generate explanation data if requested
    explanation_data = None
    if include_explanation and _explainer_available:
        try:
            # Get the full SHAP explanation
            explanation_data = get_explanation(features)

            if explanation_data:
                # Add a text explanation
                explanation_data["text_explanation"] = explain_prediction_text(features)

                # Add rule-based explanation data
                rule_explanation = []
                for feed in sorted(set(source_feeds)):
                    feed_score = feed_scores.get(feed, 0)
                    if feed_score > 0:
                        rule_explanation.append(f"Feed '{feed}': +{feed_score} points")

                if len(set(source_feeds)) >= _rules.get("multi_feed_bonus", {}).get(
                    "threshold", 999
                ):
                    rule_explanation.append(
                        f"Multi-feed bonus: +{_rules.get('multi_feed_bonus', {}).get('points', 0)} points"
                    )

                explanation_data["rule_explanation"] = rule_explanation

                logger.info(f"Generated explanation data for '{ioc_value}'")
            else:
                logger.warning(f"Failed to generate explanation data for '{ioc_value}'")
        except Exception as e:
            logger.error(
                f"Error generating explanation for '{ioc_value}': {e}", exc_info=True
            )

    return final_score, explanation_data


def categorize(score: int) -> str:
    """
    Map numeric score to tier label based on loaded rules.
    Uses descending order check (high -> medium -> low).
    """
    tiers = _rules.get("tiers", {})
    # Get tier thresholds, providing high defaults if missing to ensure 'low' is reachable
    high_threshold = tiers.get("high", 999)
    medium_threshold = tiers.get("medium", 998)
    # low_threshold = tiers.get("low", 0) # Low is the default fallback

    if score >= high_threshold:
        return "high"
    if score >= medium_threshold:
        return "medium"
    return "low"


def score_ioc_with_explanation(
    ioc_value: str,
    ioc_type: str,
    source_feeds: List[str],
    enrichment_data: Dict = None,
    summary: str = "",
) -> Tuple[int, str, Optional[Dict]]:
    """
    Wrapper that scores an IOC and provides a human-readable explanation.

    Args:
        Same as score_ioc

    Returns:
        Tuple containing:
        - final numeric score
        - human-readable explanation
        - full explanation data dictionary
    """
    score, explanation_data = score_ioc(
        ioc_value=ioc_value,
        ioc_type=ioc_type,
        source_feeds=source_feeds,
        enrichment_data=enrichment_data,
        summary=summary,
        include_explanation=True,
    )

    # Try to use the new shap_explainer if available
    if _shap_explainer_available:
        try:
            # Extract features first
            features = extract_features(
                ioc_type=ioc_type,
                source_feeds=source_feeds,
                ioc_value=ioc_value,
                enrichment_data=enrichment_data,
                summary=summary,
            )

            # Get explanation using the new explainer
            shap_explanation = explain_prediction(features)

            if shap_explanation:
                # Format the text explanation
                text_lines = [
                    "Factors influencing this score (in order of importance):"
                ]

                for item in shap_explanation[:5]:  # Show top 5 factors
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

                    text_lines.append(
                        f"- {readable_name}: {impact} the score (impact: {abs(importance):.3f})"
                    )

                text_explanation = "\n".join(text_lines)

                # Add explanation to explanation_data if it exists
                if explanation_data is None:
                    explanation_data = {}

                explanation_data["text_explanation"] = text_explanation
                explanation_data["shap_values"] = shap_explanation

                return score, text_explanation, explanation_data
        except Exception as e:
            logger.error(f"Error generating enhanced explanation: {e}", exc_info=True)
            # Fall back to original explanation if there's an error

    # Get the human-readable explanation from the original data if enhanced version failed
    if explanation_data and "text_explanation" in explanation_data:
        text_explanation = explanation_data["text_explanation"]
    else:
        if _explainer_available:
            text_explanation = "Could not generate explanation for this score."
        else:
            text_explanation = (
                "ML model explanation is not available. Consider installing SHAP."
            )

    return score, text_explanation, explanation_data
