# ML Scoring Test Plan

## 1. Model Feature Extraction Testing

- **Test Feature Completeness**: Verify all EXPECTED_FEATURES in scoring_model.py are correctly generated
- **Test Edge Cases**: Empty values, malformed inputs, unusual characters in IOCs
- **Test Enrichment Data Processing**: Various combinations of enrichment data for each IOC type
- **Test Feature Normalization**: Ensure numerical features are properly scaled/normalized

## 2. Model Prediction Testing

- **Test Model Loading**: Verify graceful handling when model file is missing or corrupted
- **Test Prediction Consistency**: Same inputs should produce same scores consistently
- **Test Performance**: Measure prediction speed for large batches of IOCs
- **Test Invalid Inputs**: Verify model handles feature vectors with missing or unexpected features

## 3. Integrated Scoring Testing

- **Test Rule/ML Weight Balance**: Verify the 70/30 weighting is applied correctly
- **Test Score Range**: Confirm final scores stay within expected bounds
- **Test Category Thresholds**: Verify high/medium/low categorization works correctly 
- **Test Feed Scoring**: Verify how different feed combinations affect scores

## 4. Training Pipeline Testing

- **Test Data Extraction**: Verify database queries get the right records
- **Test Feature Preparation**: Ensure features match the scoring model's expectations
- **Test Model Metrics**: Validate model performance metrics are calculated correctly
- **Test Model Output**: Verify saved model can be loaded and used for predictions

## 5. End-to-End Testing

- **Test Real-World IOCs**: Use known-good and known-bad IOCs to verify scoring
- **Test Against Previous Model**: Compare new model predictions against previous versions
- **Test Threshold Sensitivity**: Analyze how changes to thresholds affect classification
- **Test Explainability**: Add tests to explain why specific scores are given

## 6. Integration Tests

- **Test Database Updates**: Verify scores are correctly stored in the database
- **Test API Responses**: Ensure scoring data is correctly returned via APIs
- **Test Logging**: Verify appropriate logging at each step for troubleshooting 