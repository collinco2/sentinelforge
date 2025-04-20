import datetime
import hashlib
import logging

# Added storage imports
from sentinelforge.storage import init_db, SessionLocal, IOC

# Added scoring imports
from sentinelforge.scoring import score_ioc, categorize

# Added enrichment import
from sentinelforge.enrichment.whois_geoip import WhoisGeoIPEnricher

# Removed factory import, added direct imports
# from .factory import get_ingestor
from .dummy_ingestor import DummyIngestor
from .urlhaus_ingestor import URLHausIngestor
from .abuse_ch_ingestor import AbuseChIngestor

# Import the normalization function
from .normalize import normalize_indicators

# Get logger instance
logger = logging.getLogger(__name__)

# --- Configuration ---
# IMPORTANT: Replace this with the actual path to your GeoLite2-City.mmdb file
GEOIP_DB_PATH = "/path/to/GeoLite2-City.mmdb"  # Example placeholder
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
    try:
        enricher = WhoisGeoIPEnricher(GEOIP_DB_PATH)
        logger.info(f"WhoisGeoIPEnricher initialized with DB: {GEOIP_DB_PATH}")
    except Exception as enricher_init_err:
        logger.error(f"Failed to initialize WhoisGeoIPEnricher: {enricher_init_err}")
        enricher = None  # Set enricher to None if init fails
    # --- End Enricher Init ---

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
                # Ensure type and value keys exist before creating hash
                ind_type = ind.get("type")
                ind_value = ind.get("value")

                if ind_type is None or ind_value is None:
                    logger.debug(f"Skipping indicator missing type/value before hashing: {ind}")
                    continue  # Skip if essential keys are missing

                # build a unique key per IOC
                key = f"{ind_type}:{ind_value}"  # Use the fetched type/value
                h = hashlib.sha256(key.encode("utf-8")).hexdigest()
                if h in seen_hashes:
                    duplicate_count += 1
                    feed_duplicates_skipped += 1
                    # Use logger instead of print for internal info
                    logger.info(f"Skipping duplicate IOC {key} (hash: {h[:8]}...) from {feed_name}")
                    continue
                seen_hashes.add(h)
                deduplicated_raw_indicators.append(ind)  # Add the non-duplicate raw item
            # --- End Deduplication ---

            # Normalize and deduplicate further (based on normalized values)
            normalized_indicators = normalize_indicators(deduplicated_raw_indicators)
            final_unique_count = len(normalized_indicators)
            total_normalized_unique += final_unique_count

            # --- Store normalized indicators in DB ---
            stored_count = 0
            for norm in normalized_indicators:
                # Basic check for required fields after normalization
                norm_type = norm.get("type")
                norm_value = norm.get("value")
                if not norm_type or not norm_value:
                    logger.warning(f"Skipping normalized indicator missing type/value: {norm}")
                    continue

                # --- Perform Enrichment ---
                enrichment_data = {}
                if enricher and norm_type in ["domain", "ip"]:
                    try:
                        enrichment_data = enricher.enrich({"type": norm_type, "value": norm_value})
                        if enrichment_data:
                            logger.debug(f"Enriched {norm_type}:{norm_value} -> {enrichment_data}")
                    except Exception as enrich_err:
                        logger.warning(
                            f"Enrichment failed for {norm_type}:{norm_value} - {enrich_err}"
                        )
                # --- End Enrichment ---

                # Calculate Score and Category
                # TODO: Enhance feeds_seen if merging duplicates across feeds in the future
                feeds_seen = [feed_name]
                ioc_score = score_ioc(norm_value, feeds_seen)
                ioc_cat = categorize(ioc_score)

                # store normalized IOC into DB (upsert)
                record = IOC(
                    ioc_type=norm_type,
                    ioc_value=norm_value,
                    source_feed=feed_name,
                    # first_seen=datetime.datetime.utcnow(), # Use DB default
                    # last_seen=datetime.datetime.utcnow(),  # Use DB default
                    score=ioc_score,  # Add calculated score
                    category=ioc_cat,  # Add calculated category
                    enrichment_data=(
                        enrichment_data if enrichment_data else None
                    ),  # Store enrichment
                )
                try:
                    db.merge(record)
                    stored_count += 1
                except Exception as db_err:
                    logger.error(f"Failed to merge IOC to DB: {norm} - Error: {db_err}")
                    db.rollback()  # Rollback on error for this record
                    continue  # Continue processing other indicators

            logger.info(f"Processed {stored_count} IOCs for feed {feed_name} (pending commit).")
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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    run_ingestion_pipeline()
