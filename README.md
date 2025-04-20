# SentinelForge

AI‑powered threat‑intel aggregator.

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
``` 