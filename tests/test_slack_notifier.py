import pytest
from unittest.mock import MagicMock  # Using patch might be cleaner sometimes
from slack_sdk.webhook import WebhookClient

# Module under test
import sentinelforge.notifications.slack_notifier as slack_notifier
from sentinelforge.notifications.slack_notifier import send_high_severity_alert


@pytest.fixture(autouse=True)
def reload_notifier_module(monkeypatch):
    """Ensure the notifier module re-evaluates env vars for each test."""
    # Critical: Since the webhook client is initialized at the module level,
    # we need to force a reload or patch the module-level variable for
    # environment variable changes to take effect reliably across tests.
    # Patching the 'webhook' variable within the module is often simplest.
    # We'll patch it in specific tests where needed.
    pass  # No direct action needed here if patching 'webhook' directly.


@pytest.fixture
def mock_webhook_client(monkeypatch):
    """Mocks the module-level webhook client instance."""
    mock_client = MagicMock(spec=WebhookClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.body = "ok"
    mock_client.send.return_value = mock_response
    # Patch the 'webhook' variable *within* the slack_notifier module
    monkeypatch.setattr(slack_notifier, "webhook", mock_client)
    return mock_client


def test_send_alert_success(mock_webhook_client):
    """Test that send_high_severity_alert calls the webhook client's send method."""
    # Ensure the module-level webhook is the mocked one
    assert slack_notifier.webhook is mock_webhook_client

    send_high_severity_alert(
        ioc_value="9.9.9.9", ioc_type="ip", score=90, link="http://link.example.com"
    )

    # Assert that the mocked client's send method was called once
    mock_webhook_client.send.assert_called_once()
    # Check some basic content of the call args
    args, kwargs = mock_webhook_client.send.call_args

    # Check text field (contains basic info)
    assert "High-Severity IOC Detected" in kwargs.get("text", "")

    # Check blocks content
    blocks = kwargs.get("blocks", [])
    assert len(blocks) > 0

    # Convert blocks to string for easier assertion
    blocks_str = str(blocks)
    assert "9.9.9.9" in blocks_str
    assert "ip" in blocks_str
    assert "90" in blocks_str
    assert "http://link.example.com" in blocks_str


def test_no_webhook_configured(monkeypatch):
    """Test that no attempt is made to send if the webhook URL was never set."""
    # Patch the module-level webhook variable to None
    monkeypatch.setattr(slack_notifier, "webhook", None)
    # Mock the WebhookClient itself just in case (belt and suspenders)
    mock_constructor = MagicMock()
    monkeypatch.setattr(slack_notifier, "WebhookClient", mock_constructor)

    send_high_severity_alert("1.2.3.4", "ip", 99, "http://link")

    # Assert that WebhookClient was NOT called and send was NOT called
    mock_constructor.assert_not_called()
    # If webhook was None, send wouldn't be called anyway, but good to be explicit
    # We can't easily assert on a None object's method, so this test relies
    # on the code's guard `if not webhook:`


def test_send_alert_handles_sdk_error(mock_webhook_client):
    """Test that errors during webhook.send are handled gracefully."""
    # Configure the mock send method to raise an exception
    mock_webhook_client.send.side_effect = Exception("Slack API error")

    # Call the function - it should catch the exception and log it (not fail test)
    try:
        send_high_severity_alert("example.com", "domain", 85, "")
    except Exception as e:
        pytest.fail(f"send_high_severity_alert raised an unexpected exception: {e}")

    # Verify send was still called
    mock_webhook_client.send.assert_called_once()


def test_placeholder():
    """Placeholder test."""
    assert True
