import requests
import csv
from io import StringIO
from typing import List, Dict, Any
from sentinelforge.ingestion.threat_intel_ingestor import ThreatIntelIngestor
import logging

logger = logging.getLogger(__name__)


class URLHausIngestor(ThreatIntelIngestor):
    """
    Ingestor for the URLhaus CSV threat feed.
    https://urlhaus.abuse.ch/downloads/csv/
    """

    def __init__(self, feed_url: str = "https://urlhaus.abuse.ch/downloads/csv/"):
        self.feed_url = feed_url

    def get_indicators(self, source_url: str = None) -> List[Dict[str, Any]]:
        url = source_url or self.feed_url
        records: List[Dict[str, Any]] = []

        try:
            logger.info(f"Fetching URLhaus data from {url}")
            resp = requests.get(url)
            resp.raise_for_status()

            # Skip comment lines that start with '#'
            csv_content = "\n".join(
                line for line in resp.text.splitlines() if not line.startswith("#")
            )

            # Parse CSV
            csv_reader = csv.reader(StringIO(csv_content))

            # Skip header (first line) if present
            next(csv_reader, None)

            # Process rows
            for row in csv_reader:
                if len(row) >= 3:  # Ensure minimal fields are present
                    # Map to appropriate field names expected by normalizer
                    record = {
                        "url": row[2].strip(),  # The actual malicious URL
                        "type": "url",  # Explicit type
                        "description": f"URLhaus - {row[4] if len(row) > 4 else 'Malicious URL'}",
                    }

                    # Add status and tags if available
                    if len(row) > 3:
                        record["status"] = row[3].strip()

                    # Add tags if available (often contains malware family info)
                    if len(row) > 5:
                        record["tags"] = row[5].strip()

                    records.append(record)

            logger.info(f"URLhaus feed extracted {len(records)} records")

        except Exception as e:
            logger.error(f"Error fetching/parsing URLhaus feed: {e}")

        return records
