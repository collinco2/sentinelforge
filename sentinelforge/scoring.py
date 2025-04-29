import yaml

# from pathlib import Path # No longer needed directly
import logging
from typing import List, Dict, Any

# Import centralized settings
from sentinelforge.settings import settings

# Import ML scoring functions
from sentinelforge.ml.scoring_model import (
    extract_features,
    predict_score,
    KNOWN_SOURCE_FEEDS,
)

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


def score_ioc(
    ioc_value: str,
    ioc_type: str,
    source_feeds: List[str],
    enrichment_data: Dict = None,
    summary: str = "",
) -> int:
    """
    Compute a score based on feeds, multi-feed bonuses, and ML prediction.
    :param ioc_value: the indicator value
    :param ioc_type: the indicator type (e.g., 'ip', 'domain')
    :param source_feeds: list of feed names where the IOC appeared
    :param enrichment_data: optional enrichment data dictionary
    :param summary: optional IOC summary
    :return: integer score (combined rule-based and ML-based)
    """
    # --- Rule-Based Score ---
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
    for feed in KNOWN_SOURCE_FEEDS:
        max_rule_score += feed_scores.get(feed, 0)
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

    return final_score


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
