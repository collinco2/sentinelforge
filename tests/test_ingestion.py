from sentinelforge.ingestion import hello


def test_hello():
    assert hello() == "Ingestion skeleton ready"
