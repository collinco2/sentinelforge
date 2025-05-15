from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, EmailStr, FilePath
from typing import List, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    # Automatically load from .env file and environment variables (case-insensitive)
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )

    # --- Core Settings ---
    database_url: str = f"sqlite:///{PROJECT_ROOT}/ioc_store.db"
    scoring_rules_path: FilePath = PROJECT_ROOT / "scoring_rules.yaml"
    model_path: Path = PROJECT_ROOT / "models/ioc_scorer.joblib"

    # --- API Key (used by API auth) ---
    # IMPORTANT: Set SENTINELFORGE_API_KEY in .env or environment
    sentinelforge_api_key: str = "super-secret-token"

    # --- Enrichment Settings ---
    # IMPORTANT: Set GEOIP_DB_PATH in .env or environment
    geoip_db_path: Optional[FilePath] = (
        None  # Path is optional, enrichment will fail if None
    )
    # NOTE: NLP Summarizer config is separate in config/nlp_summarizer.json for now

    # --- Slack Notification Settings ---
    # IMPORTANT: Set SLACK_WEBHOOK_URL in .env or environment
    slack_webhook_url: Optional[AnyHttpUrl] = None  # Optional, use pydantic validation
    slack_alert_threshold: int = 80

    # --- Email Digest Settings ---
    # IMPORTANT: Set SENDGRID_API_KEY, DIGEST_RECIPIENTS, DIGEST_FROM in .env or environment
    sendgrid_api_key: Optional[str] = None
    # Set a default list directly - can still be overridden by env var if needed
    digest_recipients: List[EmailStr] = ["placeholder@example.com"]
    digest_from: EmailStr = "no-reply@example.com"

    # --- API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Ingestion settings
    ingest_interval_minutes: int = 60

    # --- Dashboard settings
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 5050

    # Make sure the models directory exists
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.makedirs(self.model_path.parent, exist_ok=True)


# Create a single instance to be imported by other modules
settings = Settings()

# Optional: Log loaded settings (excluding sensitive ones)
logger.info("Settings loaded:")
logger.info(f"  DATABASE_URL: {settings.database_url}")
logger.info(f"  SCORING_RULES_PATH: {settings.scoring_rules_path}")
logger.info(f"  API_KEY_SET: {settings.sentinelforge_api_key != 'super-secret-token'}")
logger.info(f"  GEOIP_DB_PATH: {settings.geoip_db_path}")
logger.info(f"  SLACK_WEBHOOK_URL: {settings.slack_webhook_url}")
logger.info(f"  SLACK_ALERT_THRESHOLD: {settings.slack_alert_threshold}")
logger.info(f"  SENDGRID_API_KEY_SET: {bool(settings.sendgrid_api_key)}")
logger.info(f"  DIGEST_RECIPIENTS: {settings.digest_recipients}")
logger.info(f"  DIGEST_FROM: {settings.digest_from}")
