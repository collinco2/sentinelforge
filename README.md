# SentinelForge

AI‑powered threat‑intel aggregator.

## Running SentinelForge

After installing (`pip install -e .`), you can use the following commands:

*   **`sentinel-ingest`**: Runs the full ingestion pipeline (fetches feeds, normalizes, scores, enriches, stores, notifies).
*   **`sentinel-dashboard top [OPTIONS]`**: Shows top-scoring IOCs from the database (use `--help` for options like `--limit`, `--type`, `--since`).
*   **`sentinel-api`**: Starts the FastAPI server (on `http://0.0.0.0:8000` by default) providing TAXII-like and export endpoints.

## Storage Schema

We persist normalized IOCs into SQLite via SQLAlchemy.  
**Database file**: `ioc_store.db`

**Table**: `iocs`  
| Column      | Type     | Description                                 |
|-------------|----------|---------------------------------------------|
| ioc_type    | string   | Indicator type (ip, domain, hash, etc.)     |
| ioc_value   | string   | Indicator value                            |
| source_feed | string   | Feed name                                 |
| first_seen  | datetime | Timestamp when first seen                 |
| last_seen   | datetime | Timestamp when last seen                  |

## Rule‑Based Scoring

We drive detection scores via `scoring_rules.yaml`:

1. **feed_scores**: Base points per feed.
2. **multi_feed_bonus**: Extra if an IOC appears in ≥threshold feeds.
3. **tiers**: Numeric thresholds for "low", "medium", "high" categories.

Use:
```python
from sentinelforge.scoring import score_ioc, categorize

score = score_ioc("1.2.3.4", ["urlhaus","abusech"])  # => e.g. 15
tier  = categorize(score)                           # => "medium"
``` 