# SentinelForge Explainability Tools

This document describes the explainability features in SentinelForge, which provide transparency into why certain IOCs receive specific risk scores.

## Overview

SentinelForge uses an ML-based scoring system that evaluates indicators of compromise (IOCs) based on various features. To make these scores more transparent and actionable, we've implemented SHAP (SHapley Additive exPlanations) to provide explanations of model decisions.

## Testing and Development Tools

### Enhanced Explanations Test Script

The `test_enhanced_explanations.py` script provides a robust way to test the explanation system with various IOC types:

```bash
# Basic usage - test a single IOC
python test_enhanced_explanations.py --ioc example.com --type domain --feeds urlhaus,abusech

# Test with a score override (to simulate high-severity)
python test_enhanced_explanations.py --ioc malware.example.com --type domain --score 85

# Run in debug mode for verbose logging
python test_enhanced_explanations.py --ioc example.com --type domain --debug

# Batch test multiple IOCs from a JSON file
python test_enhanced_explanations.py --batch test_batch.json --output results.json
```

#### Key Features

1. **Input Validation**
   - Validates IOC types and values against patterns
   - Prevents malicious input with content filtering
   - Enforces size limits to prevent memory issues

2. **Performance Optimizations**
   - Caches enrichment data and explanations
   - Implements timeouts to prevent hanging operations
   - Tracks execution time for performance monitoring

3. **Enhanced Error Handling**
   - Provides specific error types and messages
   - Implements graceful degradation for component failures
   - Logs detailed information for troubleshooting

4. **Batch Processing**
   - Processes multiple IOCs from a JSON file
   - Supports output to JSON for further analysis
   - Handles errors individually without stopping the batch

5. **Security Improvements**
   - Sanitizes input values
   - Prevents command injection and XSS
   - Handles encoded inputs safely

### Batch Test Format

The batch test file should be a JSON file with this structure:

```json
[
  {
    "ioc_value": "malware.example.com",
    "ioc_type": "domain",
    "source_feeds": ["urlhaus", "abusech"],
    "score_override": 90
  },
  {
    "ioc_value": "192.168.1.1",
    "ioc_type": "ip",
    "source_feeds": ["urlhaus"]
  }
]
```

## API Endpoints

The dashboard provides API endpoints for accessing explanations:

- `/api/explain/<ioc_value>` - Get explanation for specific IOC
- `/api/ioc/<ioc_value>` - Get details including explanations for IOC

## Explanation Components

### SHAP Explanations

SHAP values explain the contribution of each feature to the final score:

```
Factors influencing this score (in order of importance):
- URL Length: strongly increasing the score (impact: 0.354)
- Contains '?': moderately increasing the score (impact: 0.212)
- Contains '&': moderately increasing the score (impact: 0.198)
- From URL Feed: moderately increasing the score (impact: 0.157)
- URL Type: slightly increasing the score (impact: 0.083)
```

### Contextual Insights

Based on IOC type, the system provides additional insights:

- For domains: age analysis, registration details
- For IPs: geolocation insights
- For URLs: component analysis (domain, path, query)
- For hashes: file type information

### Slack Notifications

High-severity alerts include explanation data in Slack notifications, showing:

1. Score and severity level
2. Key factors influencing the score
3. Enrichment data insights
4. Contextual information

## Implementing Your Own Explanations

To extend the explanation system for a new IOC type:

1. Add pattern validation in `IOC_PATTERNS`
2. Create mock enrichment data in `get_test_enrichment_data()`
3. Extend the contextual insights in `generate_explanation()`
4. Test with the script and Slack notifications

## Future Improvements

Planned enhancements to the explanation system:

1. Interactive visualizations in the dashboard
2. Comparative analysis of IOCs
3. Feedback loop for model improvement
4. Explanation-based clustering of related threats
5. Explanation history to track model evolution 