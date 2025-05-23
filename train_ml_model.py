#!/usr/bin/env python3

import logging
import sys
from pathlib import Path
import sqlite3
import json

# Set up logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("train_ml_model")

# Try to import ML libraries, exit gracefully if not available
try:
    import pandas as pd
    import numpy as np  # noqa: F401
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, confusion_matrix
    import joblib

    _ml_libraries_available = True
except ImportError as e:
    logger.error(f"Required ML libraries not available: {e}")
    logger.error(
        "Please install required packages: pip install pandas numpy scikit-learn joblib"
    )
    _ml_libraries_available = False
    if __name__ == "__main__":
        sys.exit(1)

# Import our existing feature extraction code
try:
    from sentinelforge.ml.scoring_model import extract_features
except ImportError as e:
    logger.error(f"Could not import from sentinelforge.ml.scoring_model: {e}")
    if __name__ == "__main__":
        sys.exit(1)


def extract_db_data(db_path="ioc_store.db"):
    """Extract IOC data from the SQLite database."""

    logger.info(f"Extracting data from {db_path}")

    conn = sqlite3.connect(db_path)

    # Query all IOCs with their details
    query = """
    SELECT 
        ioc_type, 
        ioc_value, 
        source_feed, 
        score,
        category,
        enrichment_data,
        summary
    FROM iocs
    """

    df = pd.read_sql_query(query, conn)
    logger.info(f"Retrieved {len(df)} records from database")

    # Close connection
    conn.close()

    # Create binary target: 1 if score > threshold
    # Use percentile to ensure some class balance
    # Use the 25th percentile to get approximately 75% in "malicious" class
    percentile_25 = df["score"].quantile(0.25)
    df["is_malicious"] = (df["score"] > percentile_25).astype(int)

    logger.info(f"Using threshold {percentile_25} for binary classification")
    logger.info(f"Class distribution: {df['is_malicious'].value_counts().to_dict()}")

    # Parse JSON from enrichment_data column
    df["enrichment_data"] = df["enrichment_data"].apply(
        lambda x: json.loads(x) if isinstance(x, str) and x.strip() else {}
    )

    return df


def prepare_ml_features(df):
    """Prepare features for machine learning."""

    features = []

    for idx, row in df.iterrows():
        # Start with basic features from IOC type and feed
        ioc_type = row["ioc_type"]
        source_feed = [
            row["source_feed"]
        ]  # We only have one feed per IOC in this dataset

        # Extract standard features using our existing function
        ioc_features = extract_features(ioc_type, source_feed)

        # Add enrichment features when available
        enrichment = (
            row["enrichment_data"] if not pd.isna(row["enrichment_data"]) else {}
        )

        # === Enrichment Feature Engineering ===

        # IP-specific features
        if ioc_type == "ip":
            # Geographical features
            if "country" in enrichment and enrichment["country"]:
                ioc_features["has_country"] = 1
                # Encode country name (simplified approach - one-hot would be better for production)
                country = str(enrichment["country"]).lower()
                ioc_features["country_high_risk"] = (
                    1 if country in ["russia", "china", "iran", "north korea"] else 0
                )
                ioc_features["country_medium_risk"] = (
                    1 if country in ["ukraine", "belarus", "romania"] else 0
                )
            else:
                ioc_features["has_country"] = 0
                ioc_features["country_high_risk"] = 0
                ioc_features["country_medium_risk"] = 0

            # Latitude/longitude features
            if (
                "latitude" in enrichment
                and enrichment["latitude"]
                and "longitude" in enrichment
                and enrichment["longitude"]
            ):
                ioc_features["has_geo_coords"] = 1
            else:
                ioc_features["has_geo_coords"] = 0

        # Domain-specific features
        if ioc_type == "domain":
            # Registrar features
            if "registrar" in enrichment and enrichment["registrar"]:
                ioc_features["has_registrar"] = 1
            else:
                ioc_features["has_registrar"] = 0

            # Domain age features (important for phishing domains!)
            if "creation_date" in enrichment and enrichment["creation_date"]:
                ioc_features["has_creation_date"] = 1
                # Could calculate domain age here
            else:
                ioc_features["has_creation_date"] = 0

        # URL-specific features
        if ioc_type == "url":
            # Extract URL length as a feature (longer URLs are often more suspicious)
            url_value = row["ioc_value"]
            ioc_features["url_length"] = len(url_value)

            # Count special characters in URL (more special chars often indicate malicious URLs)
            special_chars = ["&", "?", "=", ".", "-", "_", "~", "%", "+"]
            for char in special_chars:
                ioc_features[f"contains_{char}"] = 1 if char in url_value else 0

            # Count number of dots in URL (more subdomains can be suspicious)
            ioc_features["dot_count"] = url_value.count(".")

            # Check for IP in URL (suspicious)
            ioc_features["has_ip_in_url"] = (
                1 if any(c.isdigit() for c in url_value.split(".")) else 0
            )

        # Hash-specific features
        if ioc_type == "hash":
            # Hash length can indicate hash type (MD5=32, SHA1=40, SHA256=64)
            hash_value = row["ioc_value"]
            ioc_features["hash_length"] = len(hash_value)

        # === General Features ===

        # Summary features
        if not pd.isna(row["summary"]) and row["summary"]:
            ioc_features["has_summary"] = 1
            # Add summary length as potential feature
            ioc_features["summary_length"] = len(str(row["summary"]))
        else:
            ioc_features["has_summary"] = 0
            ioc_features["summary_length"] = 0

        # Source feed-specific enrichment/features
        feed = row["source_feed"].lower()
        if feed == "abusech":
            ioc_features["from_threat_feed"] = 1
        elif feed == "urlhaus":
            ioc_features["from_url_feed"] = 1
        elif feed == "dummy":
            ioc_features["from_test_feed"] = 1

        # Add the target variables
        ioc_features["score"] = row["score"]
        ioc_features["is_malicious"] = row["is_malicious"]

        features.append(ioc_features)

    # Convert to DataFrame
    features_df = pd.DataFrame(features)

    # Fill NaN values with 0
    features_df = features_df.fillna(0)

    logger.info(
        f"Prepared {len(features_df)} feature vectors with {features_df.shape[1]} features"
    )
    logger.info(f"Features: {features_df.columns.tolist()}")

    return features_df


def train_model(data):
    """Train a RandomForest model."""

    # Separate features and target
    X = data.drop(["is_malicious", "score"], axis=1, errors="ignore")
    y_classification = data["is_malicious"]

    # Make sure we have enough samples of each class for cross-validation
    class_counts = pd.Series(y_classification).value_counts()
    min_class_samples = class_counts.min()

    # Determine CV folds based on data size (min 2 folds, max 5)
    cv_folds = min(5, max(2, min_class_samples))
    logger.info(f"Using {cv_folds} folds for cross-validation based on sample size")

    # Cross validation with adjusted folds
    try:
        cv_scores = cross_val_score(
            RandomForestClassifier(n_estimators=100, random_state=42),
            X,
            y_classification,
            cv=cv_folds,
            scoring="f1_macro",
        )

        logger.info(f"Cross-validation F1 scores: {cv_scores}")
        logger.info(f"Mean CV F1 score: {cv_scores.mean():.4f}")
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}. Skipping CV evaluation.")
        cv_scores = None

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_classification, test_size=0.2, random_state=42, stratify=y_classification
    )

    # Create and train the model
    model = RandomForestClassifier(
        n_estimators=100, max_depth=None, min_samples_split=2, random_state=42
    )

    # Store feature names in the model to avoid warnings
    feature_names = X.columns.tolist()

    model.fit(X_train, y_train)

    # Store feature names as a model attribute to avoid warnings during prediction
    model.feature_names_in_ = feature_names

    # Evaluate on test set
    y_pred = model.predict(X_test)

    logger.info("Model Performance:")
    logger.info(classification_report(y_test, y_pred))

    # Show confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    # Extract feature importance
    feature_importance = pd.DataFrame(
        {"Feature": X.columns, "Importance": model.feature_importances_}
    ).sort_values("Importance", ascending=False)

    logger.info("Top 10 important features:")
    logger.info(feature_importance.head(10))

    return model


def save_model(model, path="models/ioc_scorer.joblib"):
    """Save the trained model to disk."""
    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"Model saved to {path}")


if __name__ == "__main__":
    # Make sure required libraries are available
    if not _ml_libraries_available:
        logger.error("Required ML libraries not available. Exiting.")
        sys.exit(1)

    logger.info("Starting ML model training with real data")

    try:
        # Extract data from database
        df = extract_db_data()

        # Prepare features
        features_df = prepare_ml_features(df)

        logger.info("Training model...")
        model = train_model(features_df)

        logger.info("Saving model...")
        save_model(model)

        logger.info("Done!")
    except Exception as e:
        logger.error(f"Error during model training: {e}", exc_info=True)
        sys.exit(1)
