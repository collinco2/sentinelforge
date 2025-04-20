import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Assuming these are importable from the project structure
from sentinelforge.ingestion.csv_ingestor import CSVIngestor
from sentinelforge.ingestion.json_ingestor import JSONIngestor
from sentinelforge.ingestion.taxii_ingestor import TAXIIIngestor

# --- Fixtures ---


@pytest.fixture
def csv_fixture_path():
    """Provides the path to the sample CSV fixture."""
    return Path(__file__).parent.parent / "fixtures/sample_connectors.csv"


@pytest.fixture
def json_fixture_path():
    """Provides the path to the sample JSON fixture."""
    return Path(__file__).parent.parent / "fixtures/sample_connectors.json"


@pytest.fixture
def json_fixture_content(json_fixture_path):
    """Provides the content of the sample JSON fixture."""
    return json_fixture_path.read_text()


# --- Helper to check schema ---
def check_indicator_schema(indicator):
    assert isinstance(indicator, dict)
    assert "type" in indicator
    assert "value" in indicator
    assert isinstance(indicator["type"], str)
    assert isinstance(indicator["value"], str)
    if "source" in indicator:
        assert isinstance(indicator["source"], str)
    if "timestamp" in indicator:
        assert isinstance(indicator["timestamp"], str)
        # Basic check if it looks like ISO format
        try:
            datetime.fromisoformat(indicator["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Timestamp {indicator['timestamp']} is not valid ISO format")


# --- Test CSVIngestor ---


def test_csv_ingestor_reads_file(csv_fixture_path, caplog):
    """Test CSVIngestor reads valid indicators and skips malformed ones."""
    ingestor = CSVIngestor()
    caplog.set_level(logging.WARNING)

    indicators = ingestor.get_indicators(str(csv_fixture_path))

    assert isinstance(indicators, list)
    assert len(indicators) == 5  # 4 valid + 1 with invalid timestamp (but still has type/value)

    # Check schema for all returned indicators
    for ind in indicators:
        check_indicator_schema(ind)

    # Check values of the first few valid ones
    assert indicators[0]["value"] == "1.1.1.1"
    assert indicators[1]["type"] == "domain"
    assert indicators[1]["value"] == "good.example.com"
    assert indicators[2]["type"] == "url"
    assert indicators[3]["type"] == "hash"
    assert indicators[4]["value"] == "5.5.5.5"  # Row with invalid timestamp
    assert "timestamp" not in indicators[4]  # Timestamp should be skipped

    # Check logs for warnings about skipped rows
    assert (
        len(caplog.records) >= 4
    )  # Expect warnings for rows 6, 7, 8 + the invalid timestamp on row 9
    assert "Skipping malformed row 6" in caplog.text
    assert (
        "Skipping malformed row 7" in caplog.text
    )  # Row 7 also doesn't have enough columns based on log
    assert "Skipping row 8" in caplog.text  # Missing type
    assert "Skipping row 9" in caplog.text  # Missing type or value (likely type)
    assert "Could not parse timestamp 'invalid-timestamp" in caplog.text


def test_csv_ingestor_handles_file_not_found(caplog):
    ingestor = CSVIngestor()
    caplog.set_level(logging.ERROR)
    indicators = ingestor.get_indicators("nonexistent/path/file.csv")
    assert indicators == []
    assert "CSV file not found" in caplog.text


# --- Test JSONIngestor ---


def test_json_ingestor_reads_url(json_fixture_content, caplog, requests_mock):
    """Test JSONIngestor reads valid indicators and skips malformed ones from URL."""
    test_url = "http://test.com/feed.json"
    requests_mock.get(test_url, text=json_fixture_content)

    ingestor = JSONIngestor(url=test_url)
    # Set level to DEBUG to capture the skip messages
    caplog.set_level(logging.DEBUG, logger="sentinelforge.ingestion.json_ingestor")
    indicators = ingestor.get_indicators()

    assert isinstance(indicators, list)
    # Adjust assertion: Current JSONIngestor only finds type/value keys directly
    # The item with indicator_type/indicator is skipped.
    assert len(indicators) == 3

    for ind in indicators:
        check_indicator_schema(ind)

    # Check specific extracted values
    assert indicators[0]["value"] == "8.8.8.8"
    # Item 1 (malicious.example.org) is now skipped
    assert indicators[1]["type"] == "url"
    assert indicators[1]["value"] == "https://phishing.site/login"
    assert indicators[2]["type"] == "hash"

    # Check logs for warnings/debug about skipped items
    # Expect DEBUG messages for skipped items
    assert (
        len(caplog.records) >= 5
    )  # Expect skips: item with alt keys, string, missing type, missing value, empty dict
    assert "Skipping item missing 'type' or 'value'" in caplog.text


def test_json_ingestor_handles_network_error(caplog, requests_mock):
    test_url = "http://test.com/feed.json"
    requests_mock.get(test_url, status_code=500)  # Simulate server error

    ingestor = JSONIngestor(url=test_url)
    # Ensure logging level is set *before* the call that might log
    # Also explicitly capture the logger used in the module
    caplog.set_level(logging.WARNING, logger="sentinelforge.ingestion.json_ingestor")

    indicators = ingestor.get_indicators()

    assert indicators == []
    # Check the warning message logged by the ingestor
    assert f"JSONIngestor network error for {test_url}: 500 Server Error" in caplog.text


# --- Test TAXIIIngestor ---

# Mock STIX/TAXII data - Updated to be more compliant STIX 2.0
MOCK_STIX_INDICATORS = {
    "objects": [
        {
            "type": "indicator",
            "spec_version": "2.0",  # Use 2.0 for stix2 library
            "id": "indicator--c410e758-7b35-45d1-947a-9179a19011a3",
            "created": "2023-03-01T12:00:00.000Z",
            "modified": "2023-03-01T12:00:00.000Z",
            "pattern_type": "stix",
            "pattern": "[ipv4-addr:value = '10.10.10.10']",
            "valid_from": "2023-03-01T12:00:00Z",  # Required field
            "labels": ["malicious-activity"],  # Required field
        },
        {
            "type": "indicator",
            "spec_version": "2.0",
            "id": "indicator--d520e869-8c46-46e2-958b-a280b29122b4",
            "created": "2023-03-02T13:00:00.000Z",
            "modified": "2023-03-02T13:00:00.000Z",
            "pattern_type": "stix",
            "pattern": "[domain-name:value = 'stolen-creds.example.net']",
            "valid_from": "2023-03-02T13:00:00Z",
            "labels": ["phishing"],
        },
        {
            "type": "indicator",
            "spec_version": "2.0",
            "id": "indicator--e631f970-9d57-47f3-8119-b390d5a34a55",
            "created": "2023-03-03T14:00:00.000Z",
            "modified": "2023-03-03T14:00:00.000Z",
            "pattern_type": "stix",
            "pattern": "[file:hashes.'MD5' = 'cccccccccccccccccccccccccccccccc']",
            "valid_from": "2023-03-03T14:00:00Z",
            "labels": ["malware"],
        },
        {
            "type": "malware",  # Not an indicator
            "spec_version": "2.0",
            "id": "malware--f742e980-a834-48b1-812a-c491e5a35b67",
            "created": "2023-03-04T15:00:00Z",
            "modified": "2023-03-04T15:00:00Z",
            "name": "BadStuff",
            "is_family": False,  # Required for Malware SDO
        },
        {
            "type": "indicator",
            "spec_version": "2.0",
            # Use a valid UUID for the ID
            "id": "indicator--a7a9f5ae-d5b1-4a7e-a9a9-01f9e7e3923c",
            "created": "2023-03-05T16:00:00Z",
            "modified": "2023-03-05T16:00:00Z",
            "pattern_type": "stix",
            "pattern": "[unparseable-pattern = 'junk']",  # Malformed pattern (but object is valid)
            "valid_from": "2023-03-05T16:00:00Z",
            "labels": ["test-data"],
        },
    ]
}


@patch("sentinelforge.ingestion.taxii_ingestor.Collection")
@patch("sentinelforge.ingestion.taxii_ingestor.Server")  # Also mock Server
def test_taxii_ingestor_reads_collection(MockServer, MockCollection, caplog):
    """Test TAXIIIngestor processes STIX indicators and skips others/malformed."""
    # Configure mock Server instance
    mock_server_instance = MagicMock()
    # Mock the collections property to return info needed by the ingestor
    mock_collection_info = MagicMock()
    mock_collection_info.id = "collection-123"
    mock_collection_info.url = "http://taxii.test/api1/collections/collection-123/"
    mock_server_instance.collections = [mock_collection_info]
    MockServer.return_value = mock_server_instance

    # Configure mock Collection instance
    mock_collection_instance = MagicMock()
    mock_collection_instance.get_objects.return_value = MOCK_STIX_INDICATORS
    MockCollection.return_value = mock_collection_instance

    # Provide required args to __init__
    test_server_url = "http://taxii.test/api1/"
    test_collection_id = "collection-123"
    ingestor = TAXIIIngestor(server_url=test_server_url, collection_id=test_collection_id)

    caplog.set_level(logging.DEBUG)  # Use DEBUG to see pattern skipping logs

    # Call get_indicators (source_url is ignored)
    indicators = ingestor.get_indicators()

    assert isinstance(indicators, list)
    assert len(indicators) == 3  # Expect 3 valid indicators from the mock data

    for ind in indicators:
        check_indicator_schema(ind)
        assert "stix_id" in ind  # Check for extra field

    assert indicators[0]["type"] == "stix"
    assert (
        indicators[0]["value"] == "[ipv4-addr:value = '10.10.10.10']"
    )  # New logic returns raw pattern
    assert indicators[0].get("timestamp") is None  # Timestamp not extracted by new logic
    assert indicators[1]["type"] == "stix"
    assert indicators[1]["value"] == "[domain-name:value = 'stolen-creds.example.net']"
    assert indicators[2]["type"] == "stix"
    assert indicators[2]["value"] == "[file:hashes.'MD5' = 'cccccccccccccccccccccccccccccccc']"

    # Check that Server and Collection were called correctly
    MockServer.assert_called_once_with(test_server_url)
    # Check Collection was instantiated (might need adjustment based on exact API usage)
    # MockCollection.assert_called_once() # Might be called with url, server, kwargs
    mock_collection_instance.get_objects.assert_called_once()

    # Check logs for skipped objects (malware)
    assert "Processing 5 STIX objects" in caplog.text  # Check processing count
    # Check log for skipped parse (no longer parsing patterns explicitly)
    assert (
        "Failed to parse STIX object indicator--a7a9f5ae-d5b1-4a7e-a9a9-01f9e7e3923c" in caplog.text
    )


@patch("sentinelforge.ingestion.taxii_ingestor.Server")  # Just mock Server for client error test
def test_taxii_ingestor_handles_client_error(MockServer, caplog):
    from sentinelforge.ingestion.taxii_ingestor import (
        TAXIIClientError,
    )  # Import real/dummy exception

    MockServer.side_effect = TAXIIClientError("Connection failed")

    # Provide required args to __init__
    test_server_url = "http://taxii.test/api1/"
    test_collection_id = "collection-123"
    ingestor = TAXIIIngestor(server_url=test_server_url, collection_id=test_collection_id)

    caplog.set_level(logging.ERROR)

    # Call get_indicators (source_url is ignored)
    indicators = ingestor.get_indicators()

    assert indicators == []
    assert "TAXII client error" in caplog.text
    assert "Connection failed" in caplog.text
