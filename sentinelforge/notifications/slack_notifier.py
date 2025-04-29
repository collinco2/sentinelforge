import logging
from slack_sdk.webhook import WebhookClient
from typing import Optional

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


def send_high_severity_alert(
    ioc_value: str,
    ioc_type: str,
    score: int,
    link: str = "",
    explanation: Optional[str] = None,
):
    """
    Sends a formatted alert to Slack for high-severity IOCs.

    Args:
        ioc_value: The IOC value
        ioc_type: The IOC type (e.g., domain, ip)
        score: The numeric risk score
        link: Optional link to the IOC details page
        explanation: Optional SHAP-based explanation text
    """
    if not webhook:
        logger.debug("Slack client not initialized, skipping notification.")
        return

    # Determine color based on score (customize as needed)
    if score >= 90:
        color = "#FF0000"  # Red for very high risk
    elif score >= 80:
        color = "#FFA500"  # Orange for high risk
    else:
        color = "#FFFF00"  # Yellow for medium-high risk

    # Create blocks-based message for better formatting
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"⚠️ High-Severity IOC Detected: {score}/100",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Type:*\n`{ioc_type}`"},
                {"type": "mrkdwn", "text": f"*Value:*\n`{ioc_value}`"},
            ],
        },
    ]

    # Add link if provided
    if link:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{link}|View Details in Dashboard>",
                },
            }
        )

    # Add divider
    blocks.append({"type": "divider"})

    # Process explanation into smaller sections if provided
    if explanation:
        # Split the explanation into logical sections
        sections = explanation.split("\n\n")

        for section in sections:
            if not section.strip():
                continue

            # Determine if this is a section with a title
            if ":" in section and len(section.split(":", 1)[0]) < 30:
                title, content = section.split(":", 1)
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title.strip()}*\n{content.strip()}",
                        },
                    }
                )
            else:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": section.strip()},
                    }
                )

    # Create attachments for color coding
    attachments = [{"color": color, "blocks": blocks}]

    try:
        # Send the message with blocks and attachments
        response = webhook.send(
            text=f"High-Severity IOC Detected: {ioc_type}:{ioc_value}",
            blocks=blocks,
            attachments=attachments,
        )

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
            explanation="Factors influencing this score:\n- IP located in high-risk country\n- Associated with malicious traffic in multiple feeds\n- Recent activity increase detected\n\nDetection Sources:\n- URLhaus feed\n- AbuseChTI feed\n\nAdditional Context:\n- Located in United States\n- Associated with Google DNS",
        )
        print("Test notification sent (check Slack).")
    else:
        print(
            "Skipping Slack test notification as webhook is not configured in settings."
        )
