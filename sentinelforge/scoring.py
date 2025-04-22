import yaml

# from pathlib import Path # No longer needed directly
import logging
from typing import List, Dict, Any

# Import centralized settings
from sentinelforge.settings import settings

# Import ML scoring functions
from sentinelforge.ml.scoring_model import extract_features, predict_score

logger = logging.getLogger(__name__)

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


def score_ioc(ioc_value: str, ioc_type: str, source_feeds: List[str]) -> int:
    """
    Compute a score based on feeds and multi-feed bonuses.
    Also computes (but doesn't yet use) an ML-based score.
    :param ioc_value: the indicator value
    :param ioc_type: the indicator type (e.g., 'ip', 'domain')
    :param source_feeds: list of feed names where the IOC appeared
    :return: integer score (currently rule-based)
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

    # --- ML-Based Score (Placeholder Integration) ---
    # Pass correct arguments to extract_features
    features = extract_features(ioc_type, source_feeds)
    ml_score_prob = predict_score(features)  # Score is likely 0.0-1.0
    # TODO: Decide how to use ml_score_prob:
    # 1. Combine with rule_score (e.g., weighted average)?
    # 2. Convert prob to 0-100 scale and use instead of rule_score?
    # 3. Use for categorization only?
    # Currently just logging it.
    logger.debug(
        f"  - ML-based score prediction for '{ioc_value}': {ml_score_prob:.4f}"
    )

    # Return the rule-based score for now
    return rule_score


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
