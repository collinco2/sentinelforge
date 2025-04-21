from typer.testing import CliRunner
from unittest.mock import MagicMock  # Import MagicMock for db query mocking
from datetime import datetime, timezone

from sentinelforge.__main__ import app

runner = CliRunner()


def test_dashboard_no_db(monkeypatch):
    # stub out the DB session and query to return no IOCs
    import sentinelforge.cli.dashboard as mod

    # datetime is now imported at top level
    # from datetime import datetime # Import for dummy data

    # Use correct model name IOC
    class FakeIOC:
        score = 0
        category = "low"
        ioc_type = "ip"
        ioc_value = "0.0.0.0"
        source_feed = "dummy"
        # Use recommended datetime.now(timezone.utc)
        first_seen = datetime.now(timezone.utc)

    class FakeQuery(list):
        def filter(self, *args, **kwargs):
            return self

        def count(self):
            return 0

        def order_by(self, *args, **kwargs):
            return self

        def limit(self, n):
            return self

        def all(self):
            return []

        def between(self, *args, **kwargs):
            return self  # Add for score range filter

    # Mock SessionLocal to return a mock session object
    mock_session = MagicMock()
    mock_session.query.return_value = FakeQuery()
    mock_session.close.return_value = None
    monkeypatch.setattr(mod, "SessionLocal", lambda: mock_session)

    # Mock the _rules import as well to provide default tiers
    monkeypatch.setattr(
        mod, "scoring_rules", {"tiers": {"high": 50, "medium": 20, "low": 0}}
    )

    result = runner.invoke(app, ["dashboard", "top"])
    print(result.stdout)
    print(result.exception)
    assert result.exit_code == 0
    assert "Total IOCs:" in result.stdout
    assert "0" in result.stdout  # Check count is 0
    assert "No IOCs found" in result.stdout  # Check the message for no results
