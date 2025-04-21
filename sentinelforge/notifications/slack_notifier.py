import logging
from slack_sdk.webhook import WebhookClient

from sentinelforge.settings import settings

logger = logging.getLogger(__name__)
webhook = None

if settings.slack_webhook_url:
    webhook = WebhookClient(str(settings.slack_webhook_url))
    logger.info("Slack webhook client initialized.")
else:
    logger.warning(
        "SLACK_WEBHOOK_URL not set in settings. Slack notifications disabled."
    )


def send_high_severity_alert(ioc_value: str, ioc_type: str, score: int, link: str = ""):
    """Sends a formatted alert to Slack for high-severity IOCs."""
    if not webhook:
        logger.debug("Slack client not initialized, skipping notification.")
        return

    # Format the text message using mrkdwn
    text = (
        f":rotating_light: *High-Severity IOC Detected* :rotating_light:\n"
        f"> *Value*: `{ioc_value}`\n"
        f"> *Type*: `{ioc_type}`\n"
        f"> *Score*: `{score}`\n"
    )
    # Conditionally add the link if provided
    if link:
        text += f"> <{link}|View Details>"

    try:
        response = webhook.send(text=text)
        if response.status_code == 200:
            logger.info(
                f"Successfully sent Slack alert for IOC: {ioc_type}:{ioc_value}"
            )
        else:
            logger.error(
                f"Failed to send Slack alert for {ioc_type}:{ioc_value}. "
                f"Status: {response.status_code}, Body: {response.body}"
            )
    except Exception as e:
        logger.error(
            f"Error sending Slack notification for {ioc_type}:{ioc_value}: {e}",
            exc_info=True,
        )


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if webhook:
        print("Sending test Slack notification...")
        send_high_severity_alert(
            ioc_value="8.8.8.8",
            ioc_type="ip",
            score=99,
            link="http://example.com/ioc/8.8.8.8",
        )
        print("Test notification sent (check Slack).")
    else:
        print(
            "Skipping Slack test notification as webhook is not configured in settings."
        )
