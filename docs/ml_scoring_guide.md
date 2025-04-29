# Machine Learning Scoring System Documentation

## Overview

SentinelForge uses a machine learning (ML) model to enhance the rule-based scoring system, providing more accurate threat assessments for Indicators of Compromise (IOCs). The ML scoring system works alongside traditional rule-based scoring to provide a weighted final score.

## How the ML Model Works

### Architecture

The ML scoring system uses a Random Forest classifier to predict the likelihood that an IOC is malicious. The model:

1. Takes various features extracted from IOCs as input
2. Outputs a probability score between 0.0 and 1.0 (where higher values indicate higher likelihood of being malicious)
3. This probability is then scaled to match the range of the rule-based scoring system
4. Finally, a weighted combination of rule-based and ML scores determines the final score

### Feature Engineering

Features are extracted based on the IOC type (IP, domain, URL, hash) and include:

- **Type-specific features**: One-hot encoded IOC types
- **Feed-specific features**: Source feeds where the IOC was observed
- **Enrichment-based features**: Geographical data, domain registrar info, etc.
- **Content-based features**: URL length, special character counts, etc.
- **Metadata features**: Summary text availability and length

### Integration with Scoring System

The ML score is combined with the rule-based score using a weighted average:
- 70% weight for rule-based score
- 30% weight for ML-based score

This balance ensures that we maintain the reliability of rule-based scoring while benefiting from ML insights.

## How to Retrain the Model with New Data

The model can be retrained as new data becomes available, improving its accuracy over time.

### Prerequisites

- Python 3.9+
- scikit-learn
- pandas
- numpy
- joblib

### Training Data

The model is trained using the IOCs stored in the SQLite database (`ioc_store.db`). This ensures that the model learns from real-world data processed by SentinelForge.

### Training Process

1. **Run the training script**:
   ```bash
   python train_ml_model.py
   ```

2. **What happens during training**:
   - Data is extracted from the database
   - Features are generated for each IOC
   - The model is trained to predict maliciousness
   - Model performance metrics are logged
   - The trained model is saved to `models/ioc_scorer.joblib`

3. **The script automatically**:
   - Sets a threshold based on score distribution (using the 25th percentile)
   - Creates a balanced dataset for training
   - Performs cross-validation to evaluate model quality
   - Outputs feature importance to help understand what factors are most predictive

### Customizing Training

You can modify the `train_ml_model.py` script to:
- Change the classification threshold
- Adjust feature importance
- Add new features
- Change model hyperparameters

## Feature Extraction Process

The feature extraction process (defined in `sentinelforge/ml/scoring_model.py`) converts raw IOC data into numerical features that the ML model can process.

### Core Feature Types

1. **IOC Type Features**:
   - `type_ip`, `type_domain`, `type_url`, `type_hash`, etc.
   - One-hot encoded representation of the IOC type

2. **Feed-Based Features**:
   - `feed_dummy`, `feed_urlhaus`, `feed_abusech`, etc.
   - Binary indicators of which feeds reported the IOC
   - `feed_count`: Number of feeds that reported the IOC

3. **IP-Specific Features** (when IOC is an IP):
   - `has_country`: Whether country information is available
   - `country_high_risk`: Whether the country is considered high risk
   - `country_medium_risk`: Whether the country is considered medium risk
   - `has_geo_coords`: Whether geographical coordinates are available

4. **Domain-Specific Features** (when IOC is a domain):
   - `has_registrar`: Whether registrar information is available
   - `has_creation_date`: Whether domain creation date is available

5. **URL-Specific Features** (when IOC is a URL):
   - `url_length`: Length of the URL string
   - `dot_count`: Number of dots in the URL
   - `has_ip_in_url`: Whether the URL contains IP-like segments
   - `contains_X`: Presence of special characters (?, &, =, etc.)

6. **Hash-Specific Features** (when IOC is a hash):
   - `hash_length`: Length of the hash (indicates hash type)

7. **General Features**:
   - `has_summary`: Whether a summary description is available
   - `summary_length`: Length of the summary text
   - `from_threat_feed`: Whether from a dedicated threat feed
   - `from_url_feed`: Whether from a URL-focused feed

### Feature Extraction Flow

1. An IOC is passed to `extract_features()` function with its type, value, feeds, and enrichment data
2. The function initializes a feature dictionary with zeros for all expected features
3. Based on IOC type, specific feature extraction routines are applied
4. The resulting feature dictionary is returned, ready for use by the ML model

### Adding New Features

To add new features:
1. Update the `EXPECTED_FEATURES` list in `scoring_model.py`
2. Modify the `extract_features()` function to extract and populate the new features
3. Retrain the model using the updated feature set

## Troubleshooting

### Common Issues

- **Model loads but predictions are all 0.0**: Check if the model file exists and is valid
- **Feature mismatch errors**: Ensure the features used during training match those used during prediction
- **Low prediction quality**: You may need more training data or better features

### Logging

The ML system logs information at various levels:
- DEBUG: Detailed information on feature extraction and prediction
- INFO: Model loading status and prediction summary
- ERROR: Issues with model loading or prediction execution

Enable DEBUG logging to troubleshoot model issues:
```python
import logging
logging.getLogger("sentinelforge.ml.scoring_model").setLevel(logging.DEBUG)
``` 