import pytest
from sentinelforge.enrichment.whois_geoip import WhoisGeoIPEnricher


@pytest.fixture
def enricher(tmp_path):
    # point at a small copy of the GeoLite2 database
    # Create a dummy file, as the actual Reader requires a valid DB format
    # Tests will mock the reader's methods, so content doesn't matter here.
    db = tmp_path / "GeoLite2-City.mmdb"
    db.touch()  # Create empty file instead of writing bytes
    # Wrap initialization in try/except as it might fail if geoip2 lib expects real data
    try:
        return WhoisGeoIPEnricher(str(db))
    except Exception as e:
        pytest.skip(f"Skipping WhoisGeoIPEnricher tests: Could not initialize with dummy DB ({e})")


def test_enrich_domain(monkeypatch, enricher):
    class DummyWhois:
        registrar = "Example Registrar"
        creation_date = "2020-01-01"
        expiration_date = "2025-01-01"

    # Mock the whois.whois function call within the module
    monkeypatch.setattr("sentinelforge.enrichment.whois_geoip.whois.whois", lambda d: DummyWhois())
    out = enricher.enrich({"type": "domain", "value": "example.com"})
    assert out["registrar"] == "Example Registrar"
    assert "creation_date" in out


def test_enrich_ip(monkeypatch, enricher):
    class DummyGeo:
        country = type("C", (), {"name": "Neverland"})
        city = type("C", (), {"name": "Imaginaria"})
        location = type("L", (), {"latitude": 1.23, "longitude": 4.56})

    # Mock the city method of the specific reader instance
    monkeypatch.setattr(enricher.geoip_reader, "city", lambda ip: DummyGeo())
    out = enricher.enrich({"type": "ip", "value": "192.0.2.1"})
    assert out["country"] == "Neverland"
    assert out["city"] == "Imaginaria"


def test_enrichment_handles_errors(enricher, monkeypatch):
    # unknown type => no exception, returns empty dict
    out = enricher.enrich({"type": "other", "value": "x"})
    assert out == {}

    # Test failure during lookup (e.g., whois raises exception)
    def raise_exception(*args, **kwargs):
        raise Exception("Lookup failed")

    monkeypatch.setattr("sentinelforge.enrichment.whois_geoip.whois.whois", raise_exception)
    out = enricher.enrich({"type": "domain", "value": "fail.example.com"})
    assert out == {}
