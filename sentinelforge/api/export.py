from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
import csv
import io
import logging
from typing import List, Dict, Any

# Use correct import path and model name
from sentinelforge.storage import SessionLocal, IOC
from sentinelforge.api.auth import require_api_key

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/export",
    tags=["Export"],
    dependencies=[Depends(require_api_key)],  # Apply auth to all routes in this router
)


# --- Dependency to get DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Helper function to fetch IOCs ---
def fetch_iocs(db: Session, min_score: int) -> List[IOC]:
    """Fetches IOCs from the database with a minimum score."""
    logger.info(f"Fetching IOCs with score >= {min_score}")
    try:
        results = (
            db.query(IOC)
            .filter(IOC.score >= min_score)
            .order_by(IOC.score.desc())  # Optional: order by score
            .all()
        )
        logger.info(f"Found {len(results)} IOCs.")
        return results
    except Exception as e:
        logger.error(f"Database error fetching IOCs: {e}", exc_info=True)
        # Re-raise or return empty list depending on desired error handling
        return []


# --- JSON Export Endpoint ---
@router.get("/json", response_model=Dict[str, List[Dict[str, Any]]])
def export_json(
    min_score: int = Query(0, description="Minimum score for IOCs to include"),
    db: Session = Depends(get_db),
    # API key dependency is handled at the router level
):
    """Exports filtered IOCs in JSON format."""
    iocs = fetch_iocs(db, min_score)
    payload = []
    for i in iocs:
        ioc_data = {
            "value": i.ioc_value,  # Use correct column name
            "type": i.ioc_type,  # Use correct column name
            "score": i.score,
            "category": i.category,
            "source_feed": i.source_feed,
            "first_seen": i.first_seen.isoformat(),
            "last_seen": i.last_seen.isoformat(),
            "summary": i.summary,
            "enrichment_data": i.enrichment_data,  # Use correct column name
        }
        payload.append(ioc_data)

    return {"iocs": payload}


# --- CSV Export Endpoint ---
@router.get("/csv")
def export_csv(
    min_score: int = Query(0, description="Minimum score for IOCs to include"),
    db: Session = Depends(get_db),
    # API key dependency is handled at the router level
):
    """Exports filtered IOCs in CSV format."""
    iocs = fetch_iocs(db, min_score)
    output = io.StringIO()

    # Define header row more robustly
    # Including enrichment keys dynamically might be complex for CSV
    # Let's include standard fields + summary
    header = [
        "ioc_value",
        "ioc_type",
        "score",
        "category",
        "source_feed",
        "first_seen",
        "last_seen",
        "summary",
    ]
    writer = csv.writer(output)
    writer.writerow(header)

    for i in iocs:
        writer.writerow(
            [
                i.ioc_value,
                i.ioc_type,
                i.score,
                i.category,
                i.source_feed,
                i.first_seen.isoformat(),
                i.last_seen.isoformat(),
                i.summary,
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="sentinelforge_iocs.csv"'
        },
    )
