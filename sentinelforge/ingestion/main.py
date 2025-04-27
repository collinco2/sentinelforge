import datetime
import hashlib
import logging

# Added storage imports
from sentinelforge.storage import init_db, SessionLocal, IOC

# Added scoring imports
from sentinelforge.scoring import score_ioc, categorize

# Added enrichment import
from sentinelforge.enrichment.whois_geoip import WhoisGeoIPEnricher

# Added summarizer import
from sentinelforge.enrichment.nlp_summarizer import NLPSummarizer

# Added notifications import
from sentinelforge.notifications.slack_notifier import send_high_severity_alert

# Removed factory import, added direct imports
# from .factory import get_ingestor
from .dummy_ingestor import DummyIngestor
from .urlhaus_ingestor import URLHausIngestor
from .abuse_ch_ingestor import AbuseChIngestor

# Import the normalization function
from .normalize import normalize_indicators

# Import centralized settings
from sentinelforge.settings import settings

# Get logger instance
logger = logging.getLogger(__name__)

# --- Configuration ---
# Use settings instead of constant
# GEOIP_DB_PATH = "data/GeoLite2-City.mmdb" # Updated path
# --- End Configuration ---


def run_ingestion_pipeline():
    """Runs the ingestion pipeline for configured feeds."""
    # Initialize DB schema if needed
    logger.info("Initializing database...")
    init_db()
    # Create a DB session
    db = SessionLocal()
    logger.info("Database session created.")

    # --- Initialize Enricher ---
    # Check if path is set in settings
    if settings.geoip_db_path:
        try:
            # Use path from settings
            enricher = WhoisGeoIPEnricher(str(settings.geoip_db_path))
            logger.info(
                f"WhoisGeoIPEnricher initialized with DB: {settings.geoip_db_path}"
            )
        except Exception as enricher_init_err:
            logger.error(
                f"Failed to initialize WhoisGeoIPEnricher from {settings.geoip_db_path}: {enricher_init_err}"
            )
            enricher = None
    else:
        logger.warning("GEOIP_DB_PATH not set in settings. GeoIP enrichment disabled.")
        enricher = None
    # --- End Enricher Init ---

    # --- Initialize Summarizer ---
    try:
        summarizer = NLPSummarizer()  # Use default config path
        logger.info("NLPSummarizer initialized.")
    except Exception as summarizer_init_err:
        logger.error(f"Failed to initialize NLPSummarizer: {summarizer_init_err}")
        summarizer = None  # Set to None if init fails
    # --- End Summarizer Init ---

    # deduplication cache & counter
    seen_hashes: set[str] = set()
    duplicate_count = 0

    # Directly instantiate ingestors
    ingestors = [
        DummyIngestor(),
        URLHausIngestor(),
        AbuseChIngestor(),
    ]

    total_processed = 0
    total_normalized_unique = 0

    # Loop over instantiated ingestors
    for ingestor in ingestors:
        # Infer feed name from class name for logging
        feed_name = ingestor.__class__.__name__.replace("Ingestor", "").lower()
        # Add URLHausIngestor specific name handling if needed, it's currently urlhausingestor
        if isinstance(ingestor, URLHausIngestor):
            feed_name = "urlhaus"  # Keep consistent name
        if isinstance(ingestor, AbuseChIngestor):
            feed_name = "abusech"  # Keep consistent name

        try:
            # Fetch raw indicators
            raw_indicators = ingestor.get_indicators()
            initial_raw_count = len(raw_indicators)
            total_processed += initial_raw_count

            # --- Deduplication based on raw type:value hash ---
            deduplicated_raw_indicators = []
            feed_duplicates_skipped = 0
            for ind in raw_indicators:
                # First check if our item already has explicit type and value fields
                ind_type = ind.get("type")
                ind_value = None

                # If the item has a value field, use it
                if "value" in ind:
                    ind_value = ind.get("value")
                # Otherwise, try to extract value from type-specific fields (ip, url, etc.)
                elif ind_type == "ip" and "ip" in ind:
                    ind_value = ind.get("ip")
                elif ind_type == "url" and "url" in ind:
                    ind_value = ind.get("url")
                elif ind_type == "domain" and "domain" in ind:
                    ind_value = ind.get("domain")
                elif ind_type == "hash" and "hash" in ind:
                    ind_value = ind.get("hash")

                # Debug print to understand what's being processed
                logger.debug(
                    f"Processing indicator - type: {ind_type}, value: {ind_value}, full: {ind}"
                )

                if ind_type is None or ind_value is None:
                    logger.debug(
                        f"Skipping indicator missing type/value before hashing: {ind}"
                    )
                    continue  # Skip if essential keys are missing

                # build a unique key per IOC
                key = f"{ind_type}:{ind_value}"  # Use the fetched type/value
                h = hashlib.sha256(key.encode("utf-8")).hexdigest()
                if h in seen_hashes:
                    duplicate_count += 1
                    feed_duplicates_skipped += 1
                    # Use logger instead of print for internal info
                    logger.info(
                        f"Skipping duplicate IOC {key} (hash: {h[:8]}...) from {feed_name}"
                    )
                    continue
                seen_hashes.add(h)
                deduplicated_raw_indicators.append(
                    ind
                )  # Add the non-duplicate raw item
            # --- End Deduplication ---

            # Normalize and deduplicate further (based on normalized values)
            # Returns list of dicts like {'norm_type': str, 'norm_value': str, 'original': dict}
            normalized_indicators_data = normalize_indicators(
                deduplicated_raw_indicators
            )
            final_unique_count = len(normalized_indicators_data)
            total_normalized_unique += final_unique_count

            # --- Store normalized indicators in DB ---
            stored_count = 0
            # Iterate through the enhanced data structure
            for norm_data in normalized_indicators_data:
                # Extract normalized type/value and original item
                norm_type = norm_data["norm_type"]
                norm_value = norm_data["norm_value"]
                original_item = norm_data["original"]

                # Basic check (already done in normalize, but good practice)
                if not norm_type or not norm_value:
                    # This ideally shouldn't happen if normalize_indicators filters correctly
                    logger.warning(
                        f"Skipping indicator missing normalized type/value: {norm_data}"
                    )
                    continue

                # --- Perform Enrichment ---
                enrichment_data = {}
                if enricher and norm_type in ["domain", "ip"]:
                    try:
                        raw_enrichment = enricher.enrich(
                            {"type": norm_type, "value": norm_value}
                        )
                        # Convert datetime objects in enrichment to ISO strings for JSON storage
                        enrichment_data = {
                            k: (
                                v.isoformat() if isinstance(v, datetime.datetime) else v
                            )
                            for k, v in raw_enrichment.items()
                        }
                        if enrichment_data:
                            logger.debug(
                                f"Enriched {norm_type}:{norm_value} -> {enrichment_data}"
                            )
                    except Exception as enrich_err:
                        logger.warning(
                            f"Enrichment failed for {norm_type}:{norm_value} - {enrich_err}"
                        )
                # --- End Enrichment ---

                # --- Perform Summarization ---
                summary = ""
                if summarizer:
                    # Attempt to find description in the *original* item data
                    description = original_item.get("description", "")
                    if description and isinstance(description, str):
                        try:
                            summary = summarizer.summarize(description)
                            if summary:
                                logger.debug(
                                    f"Summarized description for {norm_type}:{norm_value}"
                                )
                        except Exception as summary_err:
                            logger.warning(
                                f"Summarization failed for {norm_type}:{norm_value} - {summary_err}"
                            )
                    else:
                        logger.debug(
                            f"No description found or not string for {norm_type}:{norm_value}"
                        )
                # --- End Summarization ---

                # Calculate Score and Category using normalized type/value
                feeds_seen = [feed_name]  # Still using current feed, TODO remains
                ioc_score = score_ioc(
                    norm_value,
                    norm_type,
                    feeds_seen,
                    enrichment_data=enrichment_data,
                    summary=summary,
                )
                ioc_cat = categorize(ioc_score)

                # store normalized IOC into DB (upsert) using normalized type/value
                record = IOC(
                    ioc_type=norm_type,  # Use normalized type
                    ioc_value=norm_value,  # Use normalized value
                    source_feed=feed_name,
                    score=ioc_score,
                    category=ioc_cat,
                    enrichment_data=enrichment_data if enrichment_data else None,
                    summary=summary if summary else None,
                )
                try:
                    db.merge(record)
                    stored_count += 1

                    # --- Send Slack Alert if score meets threshold ---
                    # Use normalized type/value for logging/links
                    if ioc_score >= settings.slack_alert_threshold:
                        dashboard_url = f"http://localhost:8080/dashboard/ioc/{norm_type}/{norm_value}"  # Placeholder URL
                        logger.info(
                            f"Score {ioc_score} >= {settings.slack_alert_threshold}, sending Slack alert for {norm_type}:{norm_value}"
                        )
                        send_high_severity_alert(
                            norm_value, norm_type, ioc_score, dashboard_url
                        )
                    # --- End Slack Alert ---

                except Exception as db_err:
                    # Use normalized type/value in error message
                    logger.error(
                        f"Failed to merge IOC to DB: {norm_type}:{norm_value} - Error: {db_err}"
                    )
                    db.rollback()  # Rollback on error for this record
                    continue  # Continue processing other indicators

            logger.info(
                f"Processed {stored_count} IOCs for feed {feed_name} (pending commit)."
            )
            # --- End DB Storage ---

            timestamp = datetime.datetime.now().isoformat()
            # Update log message (add stored count?)
            print(
                f"[{timestamp}] {feed_name}: fetched {final_unique_count} unique IOCs "
                f"(from {len(deduplicated_raw_indicators)} pre-deduped / {initial_raw_count} raw, "
                f"{feed_duplicates_skipped} duplicates skipped)"
            )
        except Exception as e:
            # Catch potential issues during get_indicators or normalization
            timestamp = datetime.datetime.now().isoformat()
            db.rollback()  # Rollback on feed processing error
            print(f"[{timestamp}] {feed_name}: failed to process feed - {e}")

    # Optional: Print summary after loop
    print("---")
    print(f"Total Raw IOCs Processed: {total_processed}")
    print(f"Total Duplicates Skipped (by hash): {duplicate_count}")
    print(f"Total Normalized Unique IOCs: {total_normalized_unique}")
    # Add logger info call for duplicate count
    logger.info(f"Skipped {duplicate_count} duplicate IOC(s) across all feeds.")
    # ADD final commit before closing
    try:
        logger.info("Committing final transaction...")
        db.commit()
        logger.info("Commit successful.")
    except Exception as final_commit_err:
        logger.error(f"Final commit failed: {final_commit_err}")
        db.rollback()

    db.close()  # Close the session when done
    logger.info("Database session closed.")


if __name__ == "__main__":
    # Configure basic logging if running as script
    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s"
    )
    run_ingestion_pipeline()
