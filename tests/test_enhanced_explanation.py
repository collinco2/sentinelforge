import pytest
from sentinelforge.ml.explainer import explain_prediction_text


@pytest.mark.explainability
def test_explanation():
    """Test the enhanced explanation functionality."""
    # Simple test to verify the explanation functionality works
    test_features = {"type_domain": 1, "feed_urlhaus": 1, "has_registrar": 1}

    # The explanation function should return a non-empty string
    explanation = explain_prediction_text(test_features)
    assert explanation is not None and explanation, "Explanation should be truthy"
    assert isinstance(explanation, str), "Explanation should be a string"
    assert len(explanation) > 0, "Explanation should not be empty"
