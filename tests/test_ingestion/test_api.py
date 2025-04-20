from sentinelforge.ingestion.threat_intel_ingestor import ThreatIntelIngestor
from sentinelforge.ingestion.factory import get_ingestor
from sentinelforge.ingestion.dummy_ingestor import DummyIngestor


def test_get_indicators_returns_list_of_dicts():
    ingestor = DummyIngestor()
    data = ingestor.get_indicators()
    assert isinstance(data, list)
    assert len(data) > 0
    assert isinstance(data[0], dict)
    assert data == [
        {"type": "ipv4-addr", "value": "1.1.1.1"},
        {"type": "domain-name", "value": "example.com"},
        {"type": "file", "hashes": {"MD5": "abcd1234ef567890"}},
    ]


def test_dummy_fetch_iocs_returns_list_and_expected_values():
    """Ensure DummyIngestor.fetch_iocs() returns our fixed IOC list."""
    ingestor = get_ingestor("dummy")
    assert isinstance(ingestor, ThreatIntelIngestor)
    iocs = ingestor.fetch_iocs()
    assert isinstance(iocs, list)
    assert iocs == ["1.1.1.1", "example.com", "abcd1234ef567890"]
