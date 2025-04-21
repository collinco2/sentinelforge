import logging
from datetime import datetime, timedelta, timezone  # Added timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import Session  # Import Session for type hint
import sys  # Import sys for argument checking

# Use correct imports from project
from sentinelforge.storage import SessionLocal, IOC
from sentinelforge.settings import settings  # Import centralized settings

logger = logging.getLogger(__name__)

# Setup Jinja
template_dir = (
    settings.scoring_rules_path.parent / "notifications/templates"
)  # Assumes rules/notifications are siblings
if not template_dir.is_dir():  # Use Path object methods
    logger.warning(f"Templates directory not found: {template_dir}")
    env = None
else:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    logger.info(f"Jinja environment loaded from {template_dir}")


# --- Database Query ---
def gather_top_iocs(db: Session, limit: int = 20, since_days: int = 1) -> list[IOC]:
    """Queries DB for top IOCs seen recently."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    logger.info(f"Gathering top {limit} IOCs seen since {cutoff.isoformat()}")
    try:
        results = (
            db.query(IOC)
            .filter(IOC.first_seen >= cutoff)  # Use first_seen (adjust if needed)
            .order_by(IOC.score.desc())
            .limit(limit)
            .all()
        )
        logger.info(f"Found {len(results)} IOCs.")
        return results
    except Exception as e:
        logger.error(f"Error querying IOCs for digest: {e}", exc_info=True)
        return []  # Return empty list on error


# --- Email Sending Logic ---
def send_digest():
    """Gathers IOCs, renders template, and sends email digest."""
    logger.info("Starting email digest generation...")

    # Check prerequisites using settings
    if not settings.sendgrid_api_key:
        logger.error(
            "SENDGRID_API_KEY not configured in settings. Cannot send email digest."
        )
        return
    if not settings.digest_recipients:
        logger.error(
            "DIGEST_RECIPIENTS not configured in settings. Cannot send email digest."
        )
        return
    if not env:
        logger.error("Jinja environment not loaded. Cannot render email digest.")
        return

    db = SessionLocal()
    iocs = []
    html_content = ""  # Initialize html_content
    try:
        iocs = gather_top_iocs(db=db)
        # Render the HTML template
        template = env.get_template("digest.html")
        html_content = template.render(
            iocs=iocs, generated_at=datetime.now(timezone.utc)
        )
        logger.info("Email digest content rendered.")
    except Exception as e:
        # Use more specific message for template rendering error vs data gathering
        logger.error(
            f"Error gathering IOCs or rendering digest template: {e}", exc_info=True
        )
        db.close()
        return  # Don't proceed if data gathering/rendering fails
    finally:
        db.close()

    # Use settings for mail parameters
    message = Mail(
        from_email=str(settings.digest_from),  # Convert EmailStr
        to_emails=[
            str(email) for email in settings.digest_recipients
        ],  # Convert List[EmailStr]
        subject=f"SentinelForge Threat Digest - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        html_content=html_content,  # Use rendered HTML content
    )

    try:
        # Use API key from settings
        client = SendGridAPIClient(settings.sendgrid_api_key)
        response = client.send(message)
        logger.info(f"SendGrid response status code: {response.status_code}")
        if response.status_code >= 300:
            logger.error(f"SendGrid error: {response.body}")
        else:
            # Log success for all recipients
            logger.info(
                f"Email digest sent successfully to {len(settings.digest_recipients)} recipient(s)."
            )
    except Exception as e:
        # Use more specific message
        logger.error(f"Failed to send email digest via SendGrid: {e}", exc_info=True)


# --- Scheduler Setup ---
def schedule_digest():
    """Configures and starts the APScheduler."""
    # Use settings for checks
    if not settings.sendgrid_api_key or not settings.digest_recipients:
        logger.warning(
            "SendGrid key or recipients not configured in settings. Digest scheduler will not start."
        )
        return

    logger.info("Initializing digest scheduler...")
    sched = BlockingScheduler(timezone="UTC")  # Use UTC timezone
    # Schedule daily at 08:00 UTC
    sched.add_job(send_digest, "cron", hour=8, minute=0)
    logger.info("Digest job scheduled daily at 08:00 UTC. Starting scheduler...")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Digest scheduler stopped.")
    except Exception as e:
        logger.error(f"Digest scheduler failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Configure logging for direct script execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Check for a command-line argument like '--once'
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running send_digest function once due to --once flag.")
        send_digest()
    else:
        logger.info("Starting digest scheduler (run with --once to send immediately).")
        schedule_digest()
