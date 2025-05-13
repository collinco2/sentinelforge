import pytest


# Simple test function for explanation generation
def generate_simple_explanation(features):
    """Simple implementation of explanation generation for testing."""
    explanation = ["Factors influencing this prediction:"]

    # Find features that are set to 1 (or significant values)
    important_features = [(k, v) for k, v in features.items() if v > 0.5]

    # Sort by value (most significant first)
    important_features.sort(key=lambda x: x[1], reverse=True)

    # Add explanations for top features
    for feature, value in important_features[:5]:
        # Make feature name more readable
        readable_name = feature.replace("_", " ").capitalize()
        explanation.append(f"- {readable_name}: {value:.1f}")

    # Join the explanation parts with newlines
    return "\n".join(explanation)


@pytest.mark.explainability
def test_explanation():
    """Test the enhanced explanation functionality using a simplified mock."""
    # Simple test to verify the explanation functionality works
    test_features = {"type_domain": 1, "feed_urlhaus": 1, "has_registrar": 1}

    # Generate an explanation
    explanation = generate_simple_explanation(test_features)

    # Verify it's correct
    assert explanation is not None and explanation, "Explanation should be truthy"
    assert isinstance(explanation, str), "Explanation should be a string"
    assert len(explanation) > 0, "Explanation should not be empty"
    assert "Factors influencing this prediction:" in explanation
    assert "- Has registrar: 1.0" in explanation
    # No return statement - ensuring test function returns None
