import pytest
from unittest.mock import patch
from sentinelforge.scoring import score_ioc, categorize


@pytest.fixture
def mock_ml_prediction():
    """Set up a mock for the ML prediction function."""
    with patch("sentinelforge.ml.scoring_model.predict_score") as mock_predict:
        # Default to returning 0.5 (50% malicious)
        mock_predict.return_value = 0.5
        yield mock_predict


def test_score_ioc_basic():
    """Test basic scoring functionality by mocking all components."""
    with patch("sentinelforge.scoring.extract_features", return_value={"type_ip": 1}):
        with patch(
            "sentinelforge.scoring.predict_score", return_value=0.3
        ) as mock_ml_score:
            with patch("sentinelforge.scoring.rule_based_score") as mock_rule_score:
                # Set return values
                mock_rule_score.return_value = 20

                # Call the function
                score, _ = score_ioc(
                    ioc_value="test.com", ioc_type="domain", source_feeds=["test"]
                )

                # Verify calls were made
                mock_rule_score.assert_called_once()
                mock_ml_score.assert_called_once()

                # Verify result type
                assert isinstance(score, int)
                assert 0 <= score <= 100


def test_score_ioc_with_enrichment():
    """Test that enrichment data is properly passed to feature extraction."""
    with patch("sentinelforge.scoring.extract_features") as mock_extract:
        with patch("sentinelforge.scoring.predict_score", return_value=0.3):
            with patch("sentinelforge.scoring.rule_based_score", return_value=15):
                # Set up the mock to return a simple feature dict
                mock_extract.return_value = {"type_ip": 1}

                # Call with enrichment data
                enrichment_data = {"country": "United States", "asn": "AS13335"}
                score_ioc(
                    ioc_value="1.1.1.1",
                    ioc_type="ip",
                    source_feeds=["dummy"],
                    enrichment_data=enrichment_data,
                )[0]  # Only use the score part of the tuple

                # Verify extract_features was called with the enrichment data
                mock_extract.assert_called_once()
                args, kwargs = mock_extract.call_args
                assert kwargs["enrichment_data"] == enrichment_data


def test_categorize():
    """Test the categorization of scores into tiers."""
    # Mock the threshold values
    mock_tiers = {"high": 75, "medium": 40, "low": 0}

    with patch("sentinelforge.scoring._rules") as mock_rules:
        # Configure the mock to return our thresholds when accessed
        mock_rules.get.return_value = mock_tiers

        # Test various scores with our mocked thresholds
        assert categorize(80) == "high"  # Above high threshold (75)
        assert categorize(60) == "medium"  # Between medium and high
        assert categorize(20) == "low"  # Below medium threshold (40)
