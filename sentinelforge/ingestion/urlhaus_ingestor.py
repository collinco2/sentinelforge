import requests
from typing import List, Dict, Any
from sentinelforge.ingestion.threat_intel_ingestor import ThreatIntelIngestor


class URLHausIngestor(ThreatIntelIngestor):
    """
    Ingestor for the URLhaus CSV threat feed.
    """

    def __init__(self, feed_url: str = "https://urlhaus.abuse.ch/downloads/csv/"):
        self.feed_url = feed_url

    def get_indicators(self, source_url: str = None) -> List[Dict[str, Any]]:
        url = source_url or self.feed_url
        resp = requests.get(url)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        # skip header
        records: List[Dict[str, Any]] = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 2:
                record_data = {"url": parts[1].strip()}
                records.append(record_data)
        return records
