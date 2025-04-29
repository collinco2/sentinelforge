# ML Model Explainability Implementation

## Overview

We've successfully implemented model explainability for the SentinelForge ML scoring system using SHAP (SHapley Additive exPlanations). This provides transparency into how the ML model makes predictions, helping analysts understand why certain IOCs receive specific risk scores.

## Components Implemented

1. **SHAP Integration**: Added a dedicated `explainer.py` module that uses SHAP to explain model predictions.

2. **Database Schema Update**: Added an `explanation_data` column to the database to store SHAP explanations persistently.

3. **Scoring Integration**: Updated the scoring system to optionally include explanations when scoring IOCs.

4. **Slack Notifications**: Enhanced Slack alerts to include ML-based explanations for high-risk IOCs.

5. **Command-line Tool**: Created `explain_simple.py` for generating visual explanations of model predictions.

## Key Features

### 1. Text Explanations

The system now provides human-readable explanations of which features influenced a score the most, for example:

```
Factors influencing this score (in order of importance):
- URL Length: strongly increasing the score (impact: 0.354)
- Contains '?': moderately increasing the score (impact: 0.212)
- Contains '&': moderately increasing the score (impact: 0.198)
- From URL Feed: moderately increasing the score (impact: 0.157)
- URL Type: slightly increasing the score (impact: 0.083)
```

### 2. Visual Explanations

Two types of visualizations are generated:
- **Summary Plots**: Bar charts showing the overall feature importance
- **Waterfall Plots**: Detailed view of how each feature pushes the prediction up or down

### 3. Database Storage

Explanation data is stored in the database, allowing for:
- Historical analysis of why IOCs were flagged
- Comparative analysis between different versions of the model
- Audit trails for security decisions

### 4. Slack Integration

High-severity alerts now include explanation text, helping analysts quickly understand why an IOC was flagged without needing to access the full system.

## Usage Instructions

### Command-line Explanation

```bash
./explain_simple.py "<ioc_value>" <ioc_type> --feeds <feed1> <feed2>
```

Example:
```bash
./explain_simple.py "example.com" domain --feeds urlhaus
```

### Programmatic Explanation

```python
from sentinelforge.scoring import score_ioc_with_explanation

score, explanation_text, explanation_data = score_ioc_with_explanation(
    ioc_value="example.com",
    ioc_type="domain",
    source_feeds=["urlhaus"]
)

print(f"Score: {score}")
print(explanation_text)
```

## Next Steps

1. **Enhanced Visualizations**: Add interactive visualizations using a web dashboard.

2. **Feature Correlation Analysis**: Identify patterns in features that tend to co-occur in malicious IOCs.

3. **Explanation Comparison**: Compare explanations across different IOC types to identify common patterns.

4. **Model Monitoring**: Use explanation data to detect concept drift or model degradation over time.

5. **Feedback Loop**: Allow analysts to provide feedback on explanations to improve future models. 