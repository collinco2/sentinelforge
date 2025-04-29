import numpy as np
from sentinelforge.ml.scoring_model import extract_features, predict_score


def test_extract_features_ip():
    """Test feature extraction for IP type IOCs."""
    features = extract_features(
        ioc_type="ip",
        source_feeds=["dummy"],
        ioc_value="1.1.1.1",
        enrichment_data={"country": "United States"},
    )

    # Check correct type features
    assert features["type_ip"] == 1
    assert features["type_domain"] == 0
    assert features["type_url"] == 0

    # Check feed features
    assert features["feed_dummy"] == 1
    assert features["feed_count"] == 1

    # Check enrichment features
    assert features["has_country"] == 1


def test_extract_features_url():
    """Test feature extraction for URL type IOCs."""
    features = extract_features(
        ioc_type="url",
        source_feeds=["urlhaus", "abusech"],
        ioc_value="https://example.com/path?query=value",
    )

    # Check correct type features
    assert features["type_url"] == 1
    assert features["type_ip"] == 0

    # Check feed features
    assert features["feed_urlhaus"] == 1
    assert features["feed_abusech"] == 1
    assert features["feed_count"] == 2

    # Check URL-specific features
    assert features["url_length"] > 0
    assert features["contains_?"] == 1
    assert features["contains_="] == 1
    assert features["dot_count"] > 0


def test_extract_features_hash():
    """Test feature extraction for hash type IOCs."""
    features = extract_features(
        ioc_type="hash",
        source_feeds=["abusech"],
        ioc_value="5f4dcc3b5aa765d61d8327deb882cf99",
        summary="Malware hash for test",
    )

    # Check correct type features
    assert features["type_hash"] == 1

    # Check feed features
    assert features["feed_abusech"] == 1

    # Check hash and summary features
    assert features["hash_length"] == len("5f4dcc3b5aa765d61d8327deb882cf99")
    assert features["has_summary"] == 1
    assert features["summary_length"] > 0


def test_extract_features_unknown_type():
    """Test feature extraction for unknown type IOCs."""
    features = extract_features(
        ioc_type="unknown_type",
        source_feeds=["dummy"],
        ioc_value="test_value",
    )

    # Should use type_other for unknown types
    assert features["type_other"] == 1


def test_predict_score_no_model(monkeypatch):
    """Test prediction behavior when model is not available."""
    # Patch the _model to be None
    from sentinelforge.ml import scoring_model

    monkeypatch.setattr(scoring_model, "_model", None)

    # Prediction should return 0.0 when no model is available
    features = {"type_ip": 1, "feed_dummy": 1}
    score = predict_score(features)
    assert score == 0.0


# Create a mock model class that can be used for testing
class MockRandomForestClassifier:
    def __init__(self, probas=None):
        self.predict_proba_return = probas or np.array([[0.3, 0.7]])

    def predict_proba(self, X):
        return self.predict_proba_return


def test_predict_score_with_model(monkeypatch):
    """Test prediction behavior with a mock model."""
    # Create a mock model that returns a fixed probability
    mock_model = MockRandomForestClassifier()

    # Patch the _model to use our mock
    from sentinelforge.ml import scoring_model

    monkeypatch.setattr(scoring_model, "_model", mock_model)

    # Test prediction
    features = {"type_domain": 1, "feed_dummy": 1}
    score = predict_score(features)

    # Should return the second column (malicious class probability) from the mock
    assert score == 0.7
