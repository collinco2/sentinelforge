import logging
import uuid
from datetime import timezone
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from stix2 import (
    Bundle,
    Indicator,
    Identity,
)  # Added Identity, Relationship

# Use correct import path and model name
from sentinelforge.storage import SessionLocal, IOC, Base, engine  # Import Base, engine

# Import scoring rules/functions if needed for defaults or logic
# from sentinelforge.scoring import _rules as scoring_rules

logger = logging.getLogger(__name__)

# --- Configuration ---
ORG_NAME = "SentinelForge"  # Name for the STIX Identity
ORG_NAMESPACE = uuid.UUID(
    "f2e1e42c-4a7f-487e-9a8f-3f1b0b0b0b0b"
)  # Generate a stable UUID5 namespace for your org
COLLECTION_ID = "enriched-iocs"
DEFAULT_MIN_SCORE = 50  # Default minimum score for the feed

# --- FastAPI App ---
app = FastAPI(
    title="SentinelForge TAXII Output Server",
    description="Serves scored and enriched IOCs as STIX 2.x via a TAXII-like API.",
    version="0.1.0",
)


# --- Dependency to get DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Helper Functions ---


def create_stix_identity() -> Identity:
    """Creates a STIX Identity object for the organization."""
    return Identity(
        name=ORG_NAME,
        identity_class="organization",
        description=f"{ORG_NAME} Threat Intelligence Feed",
        # Allow custom properties if needed, but try to stick to spec
        allow_custom=True,
    )


ORG_IDENTITY = create_stix_identity()


def generate_stix_id(ioc_type: str, ioc_value: str) -> str:
    """Generates a stable UUIDv5-based STIX ID for an indicator."""
    hash_input = f"{ioc_type}:{ioc_value}".lower()
    # Use a namespace specific to your organization
    derived_uuid = uuid.uuid5(ORG_NAMESPACE, hash_input)
    # STIX IDs have the format: type--uuid
    return f"indicator--{derived_uuid}"


def create_stix_pattern(ioc_type: str, ioc_value: str) -> Optional[str]:
    """Creates a basic STIX pattern string based on IOC type."""
    stix_type_map = {
        "ip": "ipv4-addr",  # Assuming IPv4 for now, could add ipv6-addr logic
        "ipv4": "ipv4-addr",
        "ipv6": "ipv6-addr",
        "domain": "domain-name",
        "url": "url",
        "hash": "file:hashes.'MD5'",  # Defaulting to MD5, adjust if type is known
        "md5": "file:hashes.'MD5'",
        "sha1": "file:hashes.'SHA-1'",
        "sha256": "file:hashes.'SHA-256'",
        # Add other mappings as needed (e.g., email-addr)
    }
    stix_type = stix_type_map.get(ioc_type.lower())
    if not stix_type:
        logger.warning(f"Unsupported ioc_type '{ioc_type}' for STIX pattern generation.")
        return None
    # Basic value escaping (replace single quotes, could be more robust)
    escaped_value = ioc_value.replace("'", "\\'")
    return f"[{stix_type}:value = '{escaped_value}']"


def ioc_to_stix_indicator(ioc: IOC) -> Optional[Indicator]:
    """Converts a DB IOC record to a STIX Indicator object."""
    pattern = create_stix_pattern(ioc.ioc_type, ioc.ioc_value)
    if not pattern:
        return None

    stix_id = generate_stix_id(ioc.ioc_type, ioc.ioc_value)

    # Ensure timestamps are timezone-aware (UTC)
    created_ts = ioc.first_seen.replace(tzinfo=timezone.utc)
    modified_ts = ioc.last_seen.replace(tzinfo=timezone.utc)

    indicator = Indicator(
        id=stix_id,
        created_by_ref=ORG_IDENTITY.id,  # Link to our Org Identity
        created=created_ts,
        modified=modified_ts,
        indicator_types=["malicious-activity"],  # Example default, could vary
        pattern_type="stix",
        pattern=pattern,
        confidence=int(ioc.score),  # Direct mapping, ensure score is 0-100
        labels=[
            ioc.category,
            ioc.source_feed,
            ioc.ioc_type,
        ],  # Add category, source as labels
        description=(
            ioc.summary
            if ioc.summary
            else f"Indicator {ioc.ioc_value} observed in feed {ioc.source_feed}"
        ),
        # Allow custom properties if enrichment data needs to be stored differently
        # custom_properties=ioc.enrichment_data or {}
        allow_custom=True,
    )
    return indicator


# --- API Endpoints ---
@app.get(
    "/taxii/collections/{collection_id}/objects/",
    response_model=Dict,  # FastAPI handles Bundle serialization
    summary="Get STIX Objects from Collection",
    tags=["TAXII2-like"],
)
def get_objects_from_collection(
    collection_id: str,
    min_score: int = Query(DEFAULT_MIN_SCORE, description="Minimum score for IOCs to include"),
    db: Session = Depends(get_db),
):
    """
    Simulates fetching objects from a TAXII collection, filtered by score.
    Returns a STIX 2.x Bundle.
    """
    if collection_id != COLLECTION_ID:
        raise HTTPException(status_code=404, detail="Collection not found")

    logger.info(f"Fetching IOCs for collection '{collection_id}' with min_score >= {min_score}")
    try:
        # Query DB for IOCs meeting the score threshold
        db_iocs = db.query(IOC).filter(IOC.score >= min_score).all()
        logger.info(f"Found {len(db_iocs)} IOCs in DB meeting criteria.")

        stix_indicators = []
        for ioc in db_iocs:
            stix_indicator = ioc_to_stix_indicator(ioc)
            if stix_indicator:
                stix_indicators.append(stix_indicator)
            else:
                logger.warning(f"Could not convert DB IOC to STIX: {ioc.ioc_type}:{ioc.ioc_value}")

        # Include the Org Identity in the bundle
        bundle_objects = [ORG_IDENTITY] + stix_indicators

        # Create the STIX Bundle
        bundle = Bundle(objects=bundle_objects, allow_custom=True)

        # FastAPI will automatically convert the Bundle object to JSON
        return bundle.serialize(pretty=False)

    except Exception as e:
        logger.error(f"Error generating STIX bundle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error generating STIX bundle")


# --- Optional: Add basic discovery/collection endpoints if needed ---
# Example:
# @app.get("/taxii/", tags=["TAXII2-like"])
# def get_api_roots(): ...

# @app.get("/taxii/collections/", tags=["TAXII2-like"])
# def get_collections(): ...

# --- Run with Uvicorn ---
# Example: uvicorn sentinelforge.api.taxii:app --reload
if __name__ == "__main__":
    # This block is for direct execution, usually run via uvicorn
    import uvicorn

    logger.info("Starting Uvicorn server for TAXII API...")
    # Ensure DB exists before starting server if running directly
    # Note: In production, use Alembic or similar for migrations
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="0.0.0.0", port=8000)
