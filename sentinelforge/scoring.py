import yaml
from pathlib import Path
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Define path to rules file relative to this file's directory or project root?
# Assuming project root for now.
RULES_FILE_PATH = Path("scoring_rules.yaml")

# load rules once
_rules: Dict[str, Any] = {}
try:
    _rules = yaml.safe_load(RULES_FILE_PATH.read_text())
    logger.info(f"Scoring rules loaded successfully from {RULES_FILE_PATH}")
except FileNotFoundError:
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
    logger.error(
        f"Unexpected error loading scoring rules {RULES_FILE_PATH}: {e}. Scoring will default to 0."
    )
    # Provide default structure
    _rules = {
        "feed_scores": {},
        "multi_feed_bonus": {"threshold": 999, "points": 0},
        "tiers": {"high": 999, "medium": 998, "low": 0},
    }


def score_ioc(ioc_value: str, source_feeds: List[str]) -> int:
    """
    Compute a score based on feeds and multi-feed bonuses.
    :param ioc_value: the indicator value (currently unused in scoring)
    :param source_feeds: list of feed names where the IOC appeared
    :return: integer score
    """
    score = 0
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
        score += feed_score

    # bonus for multi-feed
    if len(unique_feeds) >= bonus_threshold:
        logger.debug(
            f"  - Multi-feed bonus applied ({len(unique_feeds)} >= {bonus_threshold}): +{bonus_points} points"
        )
        score += bonus_points

    logger.debug(f"  - Final score for '{ioc_value}': {score}")
    return score


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
