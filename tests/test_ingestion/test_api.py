from typing import Any, Dict, List
from sentinelforge.ingestion.threat_intel_ingestor import ThreatIntelIngestor


class DummyIngestor(ThreatIntelIngestor):
    def get_indicators(self, source_url: str) -> List[Dict[str, Any]]:
        return [{"type": "ipv4-addr", "value": "1.2.3.4"}]


def test_get_indicators_returns_list_of_dicts():
    ingestor = DummyIngestor()
    data = ingestor.get_indicators("http://fake-url/")
    assert isinstance(data, list)
    assert len(data) > 0
    assert isinstance(data[0], dict)
    assert data == [{"type": "ipv4-addr", "value": "1.2.3.4"}]
