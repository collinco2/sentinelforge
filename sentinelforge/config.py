import os
import logging

logger = logging.getLogger(__name__)

# Load Slack webhook URL from environment variable
# Provide a default empty string if not set
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Load Slack alert threshold from environment variable
# Provide a default of 80 if not set or if conversion fails
SLACK_ALERT_THRESHOLD_STR = os.getenv("SLACK_ALERT_THRESHOLD", "80")
SLACK_ALERT_THRESHOLD = 80  # Default value
try:
    SLACK_ALERT_THRESHOLD = int(SLACK_ALERT_THRESHOLD_STR)
except ValueError:
    logger.warning(
        f"Invalid SLACK_ALERT_THRESHOLD value '{SLACK_ALERT_THRESHOLD_STR}'. "
        f"Using default: {SLACK_ALERT_THRESHOLD}"
    )

# Optional: Add a check/warning if the webhook URL is not set
if not SLACK_WEBHOOK_URL:
    logger.warning(
        "SLACK_WEBHOOK_URL environment variable is not set. Slack notifications will be disabled."
    )
