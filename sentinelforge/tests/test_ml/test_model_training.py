import pytest
import pandas as pd
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
import numpy as np


@pytest.fixture
def mock_db_connection():
    """Create a temporary SQLite database with test data."""
    # Create a temporary file to hold the test database
    db_fd, db_path = tempfile.mkstemp()

    # Create test data
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE iocs (
            ioc_type TEXT,
            ioc_value TEXT,
            source_feed TEXT,
            score INTEGER,
            category TEXT,
            enrichment_data TEXT,
            summary TEXT
        )
    """)

    # Insert some test data
    test_data = [
        (
            "ip",
            "1.1.1.1",
            "dummy",
            30,
            "medium",
            '{"country": "United States"}',
            "Cloudflare DNS",
        ),
        (
            "domain",
            "example.com",
            "dummy",
            20,
            "low",
            '{"registrar": "Example Inc"}',
            "Example domain",
        ),
        (
            "url",
            "https://malware.com/evil",
            "urlhaus",
            85,
            "high",
            None,
            "Malicious URL",
        ),
        (
            "hash",
            "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
            "abusech",
            75,
            "medium",
            None,
            "Malware hash",
        ),
    ]

    conn.executemany(
        "INSERT INTO iocs (ioc_type, ioc_value, source_feed, score, category, enrichment_data, summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_data,
    )
    conn.commit()
    conn.close()

    yield db_path

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


def test_extract_db_data(mock_db_connection):
    """Test data extraction from the database."""
    # Import function from the training script
    from train_ml_model import extract_db_data

    # Test with our mock database
    df = extract_db_data(db_path=mock_db_connection)

    # Verify data was loaded correctly
    assert len(df) == 4
    assert set(df["ioc_type"]) == {"ip", "domain", "url", "hash"}
    assert "is_malicious" in df.columns  # Binary classification target should be added
    assert "enrichment_data" in df.columns


def test_prepare_ml_features():
    """Test feature preparation from data."""
    # Import function from the training script
    from train_ml_model import prepare_ml_features

    # Create a simple test dataframe
    test_df = pd.DataFrame(
        [
            {
                "ioc_type": "ip",
                "ioc_value": "1.1.1.1",
                "source_feed": "dummy",
                "score": 10,
                "is_malicious": 0,
                "enrichment_data": {"country": "United States"},
                "summary": "Cloudflare DNS",
            },
            {
                "ioc_type": "url",
                "ioc_value": "https://malicious.com/path?id=12345",
                "source_feed": "urlhaus",
                "score": 80,
                "is_malicious": 1,
                "enrichment_data": {},
                "summary": "Phishing URL",
            },
        ]
    )

    # Process the data
    features_df = prepare_ml_features(test_df)

    # Check the output
    assert len(features_df) == 2

    # Ensure all expected features are present
    essential_features = [
        "type_ip",
        "type_url",
        "feed_dummy",
        "feed_urlhaus",
        "url_length",
        "hash_length",
        "score",
        "is_malicious",
    ]
    for feature in essential_features:
        assert feature in features_df.columns


@patch("train_ml_model.joblib")
@patch("train_ml_model.cross_val_score")
@patch("train_ml_model.logger")
def test_train_model(mock_logger, mock_cv_score, mock_joblib):
    """Test model training with a simple dataset."""
    # Import functions from the training script
    from train_ml_model import train_model

    # Set up the mock for cross_val_score to return some reasonable scores
    mock_cv_score.return_value = np.array([0.75, 0.8])

    # Create a test feature dataframe
    features = pd.DataFrame(
        {
            "feature1": [1, 0, 1, 0, 1, 0],
            "feature2": [0, 1, 1, 0, 1, 0],
            "score": [10, 20, 70, 30, 80, 5],
            "is_malicious": [0, 0, 1, 0, 1, 0],
        }
    )

    # Train the model
    model = train_model(features)

    # Check the returned model
    assert model is not None
    assert hasattr(model, "predict_proba")

    # Verify cross-validation was called
    mock_cv_score.assert_called_once()


@patch("train_ml_model.Path")
@patch("train_ml_model.joblib")
def test_save_model(mock_joblib, mock_path):
    """Test model saving functionality."""
    # Import function from the training script
    from train_ml_model import save_model

    # Create a mock model
    mock_model = MagicMock()

    # Test saving the model
    save_model(mock_model, "test_path.joblib")

    # Verify directory creation and model saving
    mock_path.return_value.mkdir.assert_called_once()
    mock_joblib.dump.assert_called_once()
