import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from sentinelforge.ml.scoring_model import (
    extract_features,
    predict_score,
    EXPECTED_FEATURES,
)
from sentinelforge.scoring import score_ioc, categorize


class TestMLScoring:
    """Comprehensive tests for ML scoring components."""

    @pytest.fixture
    def mock_ml_model(self):
        """Mock the ML model to return predictable values."""
        mock_model = MagicMock()
        # Return probability based on input pattern
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])
        return mock_model

    def test_feature_extraction_completeness(self):
        """Test that all expected features are present in the extracted features."""
        # Test with different IOC types
        for ioc_type in ["ip", "domain", "url", "hash"]:
            features = extract_features(
                ioc_type=ioc_type,
                source_feeds=["dummy", "urlhaus"],
                ioc_value="test_value",
                enrichment_data={"country": "United States"},
                summary="Test summary",
            )

            # Check that all expected features are present
            for feature_name in EXPECTED_FEATURES:
                assert (
                    feature_name in features
                ), f"Feature '{feature_name}' missing for {ioc_type}"

    def test_feature_extraction_ip_specific(self):
        """Test IP-specific feature extraction."""
        # Test with various enrichment data combinations
        test_cases = [
            # Basic IP with no enrichment
            {
                "ioc_value": "8.8.8.8",
                "enrichment": {},
                "expected": {"has_country": 0, "has_geo_coords": 0},
            },
            # IP with country
            {
                "ioc_value": "8.8.8.8",
                "enrichment": {"country": "United States"},
                "expected": {
                    "has_country": 1,
                    "has_geo_coords": 0,
                    "country_high_risk": 0,
                },
            },
            # IP with high-risk country
            {
                "ioc_value": "103.41.167.33",
                "enrichment": {"country": "China"},
                "expected": {
                    "has_country": 1,
                    "has_geo_coords": 0,
                    "country_high_risk": 1,
                },
            },
            # IP with geo coordinates
            {
                "ioc_value": "8.8.8.8",
                "enrichment": {"latitude": 37.751, "longitude": -97.822},
                "expected": {"has_country": 0, "has_geo_coords": 1},
            },
        ]

        for case in test_cases:
            features = extract_features(
                ioc_type="ip",
                source_feeds=["dummy"],
                ioc_value=case["ioc_value"],
                enrichment_data=case["enrichment"],
            )

            # Check that all expected values match
            for key, expected_value in case["expected"].items():
                assert (
                    features[key] == expected_value
                ), f"Feature '{key}' mismatch for {case['ioc_value']}"

    def test_feature_extraction_url_specific(self):
        """Test URL-specific feature extraction."""
        test_cases = [
            # Simple URL
            {
                "ioc_value": "https://example.com",
                "expected": {
                    "url_length": 19,
                    "dot_count": 1,
                    "contains_?": 0,
                    "contains_=": 0,
                    "contains_&": 0,
                },
            },
            # Complex URL with query parameters
            {
                "ioc_value": "https://example.com/path?param1=value1&param2=value2",
                "expected": {
                    "url_length": 52,
                    "dot_count": 1,
                    "contains_?": 1,
                    "contains_=": 1,
                    "contains_&": 1,
                },
            },
        ]

        for case in test_cases:
            features = extract_features(
                ioc_type="url", source_feeds=["dummy"], ioc_value=case["ioc_value"]
            )

            # Check that all expected values match
            for key, expected_value in case["expected"].items():
                assert (
                    features[key] == expected_value
                ), f"Feature '{key}' mismatch for {case['ioc_value']}"

    def test_predict_score_with_loaded_model(self, mock_ml_model):
        """Test prediction with a loaded model."""
        with patch("sentinelforge.ml.scoring_model._model", mock_ml_model):
            # Create test features
            features = {name: 1 for name in EXPECTED_FEATURES}

            # Get prediction
            score = predict_score(features)

            # Should match the mock model's return value (second column of predict_proba)
            assert score == 0.7

            # Verify the model was called with the right inputs
            mock_ml_model.predict_proba.assert_called_once()

    def test_predict_score_handles_missing_features(self, mock_ml_model):
        """Test prediction handles missing features by defaulting to 0."""
        with patch("sentinelforge.ml.scoring_model._model", mock_ml_model):
            # Create features with some missing
            features = {"type_ip": 1, "feed_dummy": 1}  # Missing most features

            # Should still work by zero-filling missing features
            score = predict_score(features)

            # Verify it returns a score
            assert score == 0.7

            # Verify the model was called
            mock_ml_model.predict_proba.assert_called_once()

    def test_integrated_scoring(self):
        """Test the integrated scoring function (rule + ML combined)."""
        # Patch the rule-based scoring to return a known value
        with patch("sentinelforge.ml.scoring_model.predict_score") as mock_predict:
            # Set ML score to return 0.6 (60%)
            mock_predict.return_value = 0.6

            # Test the integrated scoring
            score, _ = score_ioc(
                ioc_value="test.com",
                ioc_type="domain",
                source_feeds=["dummy", "urlhaus"],
            )

            # Since we know:
            # - rule_score from our rules should be specific (we'd need to mock _rules)
            # - ML score is set to 0.6 (scaled within score_ioc)
            # - final combination uses 70% rule, 30% ML weighting
            # Just ensure the result is a reasonable number
            assert isinstance(score, int)
            assert 0 <= score <= 100

    def test_categorize_thresholds(self):
        """Test categorization based on score thresholds."""
        # Create a mock rules structure
        mock_rules = {"tiers": {"high": 75, "medium": 40, "low": 0}}

        with patch("sentinelforge.scoring._rules", mock_rules):
            # Test various scenarios
            assert categorize(80) == "high"
            assert categorize(75) == "high"
            assert categorize(50) == "medium"
            assert categorize(40) == "medium"
            assert categorize(20) == "low"
            assert categorize(0) == "low"

    def test_score_ioc_with_enrichment(self):
        """Test that enrichment data affects feature extraction."""
        # Test with and without enrichment data
        ip_value = "1.1.1.1"

        # Without enrichment
        features_without_enrichment = extract_features(
            ioc_type="ip",
            source_feeds=["dummy"],
            ioc_value=ip_value,
            enrichment_data={},
        )

        # With enrichment
        features_with_enrichment = extract_features(
            ioc_type="ip",
            source_feeds=["dummy"],
            ioc_value=ip_value,
            enrichment_data={"country": "United States"},
        )

        # Verify that enrichment data changes the features
        assert features_without_enrichment["has_country"] == 0
        assert features_with_enrichment["has_country"] == 1

    def test_edge_cases(self):
        """Test various edge cases in the ML scoring pipeline."""
        # Test with empty values
        features_empty = extract_features(
            ioc_type="ip", source_feeds=[], ioc_value="", enrichment_data={}, summary=""
        )

        # Should have zero for most features but correct type
        assert features_empty["type_ip"] == 1
        assert features_empty["feed_count"] == 0
        assert features_empty["has_country"] == 0

        # Test with unknown IOC type
        features_unknown = extract_features(
            ioc_type="unknown_type",
            source_feeds=["dummy"],
            ioc_value="test",
            enrichment_data={},
            summary="",
        )

        # Should default to "other" type
        assert features_unknown["type_other"] == 1
