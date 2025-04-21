# TODO: Add tests for the Export API endpoints
# (e.g., using FastAPI TestClient)

from fastapi.testclient import TestClient
from datetime import datetime  # Import datetime things

# Import the main API app from the __init__.py file
from sentinelforge.api import app

# Import the auth dependency we want to override
from sentinelforge.api.auth import require_api_key

# --- Test Setup ---
client = TestClient(app)


# Define a dummy dependency to override API key check for tests
def override_require_api_key():
    return "test-api-key"  # Return a dummy value


# Apply the override to the FastAPI app instance used by TestClient
app.dependency_overrides[require_api_key] = override_require_api_key


# --- Fake DB Data ---
class FakeIOC:
    # Use correct attribute names from storage.py
    def __init__(
        self,
        ioc_type,
        ioc_value,
        score,
        first_seen,
        last_seen=None,
        category="low",
        source_feed="test",
        summary=None,
        enrichment_data=None,
    ):
        self.ioc_type = ioc_type
        self.ioc_value = ioc_value
        self.score = score
        self.category = category
        self.source_feed = source_feed
        self.first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        self.last_seen = (
            datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            if last_seen
            else self.first_seen
        )
        self.summary = summary
        self.enrichment_data = enrichment_data


# --- Test Cases ---
def test_export_json_unauth():
    """Test hitting endpoint without the overridden dependency (simulates missing/bad key)."""
    # Temporarily remove the override for this test
    app.dependency_overrides = {}
    response = client.get("/export/json")
    assert response.status_code == 403
    # Restore override for other tests
    app.dependency_overrides[require_api_key] = override_require_api_key


def test_export_json_ok(monkeypatch):
    """Test successful JSON export with mocked data."""
    # Prepare mock data
    mock_iocs = [
        FakeIOC(
            ioc_type="ip",
            ioc_value="1.1.1.1",
            score=95,
            first_seen="2025-01-01T10:00:00Z",
        ),
        FakeIOC(
            ioc_type="domain",
            ioc_value="bad.com",
            score=50,
            first_seen="2025-01-02T11:00:00Z",
            category="medium",
        ),
    ]

    # Mock the helper function that fetches IOCs
    monkeypatch.setattr("sentinelforge.api.export.fetch_iocs", lambda db, score: mock_iocs)

    # No need for headers now because auth is overridden
    response = client.get("/export/json")
    assert response.status_code == 200
    data = response.json()
    assert "iocs" in data
    assert len(data["iocs"]) == 2
    assert data["iocs"][0]["value"] == "1.1.1.1"
    assert data["iocs"][0]["type"] == "ip"
    assert data["iocs"][1]["value"] == "bad.com"
    assert data["iocs"][1]["category"] == "medium"


def test_export_csv_ok(monkeypatch):
    """Test successful CSV export with mocked data."""
    mock_iocs = [
        FakeIOC(
            ioc_type="ip",
            ioc_value="2.2.2.2",
            score=80,
            first_seen="2025-02-02T12:00:00Z",
            category="high",
            source_feed="feed_x",
        ),
        FakeIOC(
            ioc_type="hash",
            ioc_value="abc",
            score=10,
            first_seen="2025-02-03T13:00:00Z",
            summary="Test summary",
        ),
    ]
    monkeypatch.setattr("sentinelforge.api.export.fetch_iocs", lambda db, score: mock_iocs)

    response = client.get("/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert (
        'attachment; filename="sentinelforge_iocs.csv"' in response.headers["content-disposition"]
    )
    # Check CSV content
    assert (
        "ioc_value,ioc_type,score,category,source_feed,first_seen,last_seen,summary"
        in response.text
    )  # Check header
    # Check first data row (adjust based on FakeIOC and included columns)
    assert (
        "2.2.2.2,ip,80,high,feed_x,2025-02-02T12:00:00+00:00,2025-02-02T12:00:00+00:00,"
        in response.text
    )
    # Check second data row (adjust based on FakeIOC defaults and included columns)
    assert (
        "abc,hash,10,low,test,2025-02-03T13:00:00+00:00,2025-02-03T13:00:00+00:00,Test summary"
        in response.text
    )
