from typing import Any, Dict, List
from .threat_intel_ingestor import ThreatIntelIngestor


class DummyIngestor(ThreatIntelIngestor):
    """
    A no-op ingestor that returns a fixed IOC list for testing.
    """

    def get_indicators(self, source_url: str = None) -> List[Dict[str, Any]]:
        """Returns a fixed list of IOC dictionaries."""
        # The source_url argument is ignored in this dummy implementation.
        return [
            {"type": "ipv4-addr", "value": "1.1.1.1"},
            {"type": "domain-name", "value": "example.com"},
            {"type": "file", "hashes": {"MD5": "abcd1234ef567890"}},
        ]

    def fetch_iocs(self) -> List[str]:
        """Returns a fixed list of IOC strings for testing."""
        return ["1.1.1.1", "example.com", "abcd1234ef567890"]
