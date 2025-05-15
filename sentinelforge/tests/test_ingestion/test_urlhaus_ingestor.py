import pytest
import requests
from sentinelforge.ingestion.urlhaus_ingestor import URLHausIngestor


class DummyResp:
    text = "id,url\n1,http://evil.com\n2,https://bad.example\n"

    def raise_for_status(self):
        pass


@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url: DummyResp())


def test_urlhaus_ingestor_parses_csv():
    ingestor = URLHausIngestor()
    data = ingestor.get_indicators()
    assert isinstance(data, list)
    assert data == [
        {"url": "http://evil.com"},
        {"url": "https://bad.example"},
    ]
