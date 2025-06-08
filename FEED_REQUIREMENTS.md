# 🛡️ Feed-Specific Requirements: Threat Feed Ingestion System

This document outlines the specific integration requirements and known considerations for each threat intelligence feed configured in the SentinelForge Threat Feed Ingestion System.

## 🚀 **Quick Start**

To bootstrap all feeds into your SentinelForge instance:

```bash
# Import all predefined feeds from feeds_config.json
python import_feeds.py

# Check feed status via API
curl -H "Authorization: Bearer <token>" http://localhost:5059/api/feeds
```

## 📊 **Feed Status Dashboard**

Monitor feed health and import statistics in the React UI:
- **Feed Management**: `/feed-management` - Configure and monitor all feeds
- **Import Logs**: View detailed import history and error reports
- **IOC Statistics**: Track ingestion rates and duplicate detection

---

## ✅ Current Integrated Feeds

### Test Local CSV Feed

- **Feed Type**: CSV
- **Source**: Local File Upload
- **Authentication Required**: No
- **Special Parser Required**: No
- **Known Issues**: None
- **Usage Notes**: Used for baseline testing. Standard CSV format with `value,type,source,confidence` headers. Validates CSV import and duplicate detection logic.

---

### IPsum Project

- **Feed Type**: CSV (IP Blocklist)
- **URL**: https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt
- **Authentication Required**: No
- **Special Parser Required**: No
- **Known Issues**: Minimal formatting (IP per line)
- **Usage Notes**: Plain IP list; parser infers type as `ip`. Used as a clean and reliable benchmark for IP ingestion.

---

### MalwareDomainList

- **Feed Type**: CSV
- **URL**: http://www.malwaredomainlist.com/hostslist/hosts.txt
- **Authentication Required**: No
- **Special Parser Required**: No
- **Known Issues**: Inconsistent delimiters
- **Usage Notes**: Domain/IP threat indicators with potential comment lines. Parser filters malformed rows. Useful for testing domain recognition and mixed-format parsing.

---

### AlienVault OTX

- **Feed Type**: TXT (custom `#`-delimited format)
- **URL**: https://otx.alienvault.com/feeds/fullhash
- **Authentication Required**: No
- **Special Parser Required**: ✅ Yes — handles `#` delimited rows
- **Known Issues**: Non-standard format, missing headers, occasional malformed lines
- **Usage Notes**: A custom parser is implemented to split lines by `#` and map to IOC fields. May skip lines missing required values. Recommended for admin-configured feeds only.

---

### Abuse.ch URLhaus

- **Feed Type**: CSV
- **URL**: https://urlhaus.abuse.ch/downloads/csv/
- **Authentication Required**: No
- **Special Parser Required**: ✅ Yes — skips header comment blocks
- **Known Issues**: Excessive header comments, malformed URLs
- **Usage Notes**: Parser filters comment lines beginning with `#` and performs validation on each row. Good source for URL threat testing and malformed entry detection.

---

### PhishTank

- **Feed Type**: JSON API
- **URL**: https://data.phishtank.com/data/online-valid.json
- **Authentication Required**: ✅ Yes — API key required for sustained use
- **Special Parser Required**: No
- **Known Issues**: Rate-limited, can return HTTP 429
- **Usage Notes**: Requires API key for heavy or automated usage. Consider throttling requests or scheduling import jobs during off-peak hours.

---

## ➕ Recommended Additional Feeds

### MISP OSINT Feed

- **Feed Type**: JSON (MISP Manifest Format)
- **URL**: https://www.circl.lu/doc/misp/feed-osint/manifest.json
- **Authentication Required**: No
- **Special Parser Required**: ✅ Yes — parse from manifest format
- **Known Issues**: Nested structure, requires interpretation of MISP schema
- **Usage Notes**: Integrates well into security tools. Parser must recursively resolve indicators. Valuable for advanced testing with structured threat data.

---

### CyberCrime Tracker

- **Feed Type**: TXT (IP and domains)
- **URL**: https://cybercrime-tracker.net/all.php
- **Authentication Required**: No
- **Special Parser Required**: No
- **Known Issues**: Format changes occasionally
- **Usage Notes**: Simple newline-separated list. Parser performs IOC inference. Best used for testing robustness against simple or changing formats.

---

### Spamhaus DROP List

- **Feed Type**: TXT (IP Ranges)
- **URL**: https://www.spamhaus.org/drop/drop.txt
- **Authentication Required**: No
- **Special Parser Required**: No
- **Known Issues**: Commented headers
- **Usage Notes**: Useful for ingesting large CIDR-based IP blocklists. Parser strips comment lines and splits IP ranges cleanly.

---

### Proofpoint Emerging Threats

- **Feed Type**: STIX/CSV
- **URL**: https://rules.emergingthreats.net/openioc/
- **Authentication Required**: ✅ Possibly — commercial feed access required
- **Special Parser Required**: ✅ Yes — STIX/CSV hybrid formats
- **Known Issues**: Access control and STIX versioning
- **Usage Notes**: Considered advanced feed source. If integrated, prioritize correct STIX 2.x support and metadata handling.

---

### Limo TAXII Feeds (Anomali)

- **Feed Type**: STIX 2.1 via TAXII 2.0
- **API Root**: https://limo.anomali.com/api/v1/taxii2/
- **Authentication Required**: ✅ Yes (guest/guest supported)
- **Special Parser Required**: ✅ Yes — TAXII poll + STIX parse
- **Known Issues**: TAXII negotiation, content filtering
- **Usage Notes**: Advanced testing for STIX/TAXII handling. Use guest auth for initial connection. Confirms end-to-end ingest of complex threat structures.

---

# 📋 Implementation Details

## 🔧 **Parser Implementation**

The SentinelForge ingestion system uses specialized parsers in `services/ingestion.py`:

```python
# Parser mapping in FeedParser class
PARSER_MAP = {
    "standard_csv": self.parse_csv,
    "ip_list": self.parse_txt,
    "domain_list": self.parse_txt,
    "alienvault_hash": self.parse_txt,  # Custom # delimiter handling
    "urlhaus_csv": self.parse_csv,      # Comment filtering
    "phishtank_json": self.parse_json,
    "misp_manifest": self.parse_json,   # Nested structure handling
    "generic_txt": self.parse_txt,
    "ip_range_list": self.parse_txt,
    "proofpoint_stix": self.parse_stix,
    "taxii_client": self.parse_stix     # TAXII + STIX combination
}
```

## 🚨 **Error Handling & Monitoring**

### Common Issues & Solutions:

1. **HTTP Timeouts**: Default 10-second timeout with retry logic
2. **Rate Limiting**: Exponential backoff for 429 responses
3. **Malformed Data**: Row-level validation with detailed error logging
4. **Authentication Failures**: Clear error messages with setup guidance

### Monitoring Endpoints:

```bash
# Check feed health
GET /api/feeds/{feed_id}/status

# View import logs
GET /api/feeds/import-logs?feed_id={id}&limit=50

# Get error statistics
GET /api/feeds/{feed_id}/errors
```

## 🔍 **Troubleshooting Guide**

### Feed Connection Issues:
```bash
# Test feed connectivity
curl -I https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt

# Check SentinelForge logs
tail -f api_server.log | grep "feed"
```

### Parser Debugging:
```bash
# Test specific feed parsing
python -c "
from services.ingestion import FeedIngestionService
service = FeedIngestionService()
result = service.import_from_file('test_feed.csv', 'Test Feed', user_id=1)
print(result)
"
```

### Database Issues:
```bash
# Check IOC counts by feed
sqlite3 ioc_store.db "SELECT source_feed, COUNT(*) FROM iocs GROUP BY source_feed;"

# View recent import logs
sqlite3 ioc_store.db "SELECT * FROM feed_import_logs ORDER BY timestamp DESC LIMIT 10;"
```

## 📊 **Performance Considerations**

- **Batch Size**: Default 1000 IOCs per transaction
- **Memory Usage**: ~100MB for 10,000 IOC processing
- **Import Speed**: ~15,000 IOCs/second on modern hardware
- **Duplicate Detection**: O(1) lookup using database indexes

## 🔐 **Security Notes**

- **API Keys**: Store in environment variables, never in code
- **Input Validation**: All IOC values validated before database insertion
- **Rate Limiting**: Built-in protection against feed abuse
- **Audit Logging**: Complete trail of all import operations

---

# 📋 Final Notes

- **Parser Registry**: Ensure `ingestion.py` maintains a mapping from feed ID/type to parser function.
- **Error Handling**: External feeds are unreliable — enforce retry logic, HTTP timeouts, and data validation at every step.
- **Monitoring**: Set up automated health checks or alerting to monitor feed connectivity and structure changes.
- **Documentation Sync**: Consider displaying feed notes in the React UI or admin dashboard for transparency.
