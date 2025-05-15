# SentinelForge Ingestion Module

This module provides the base ingestion pipeline for public CTI feeds.

## Running the Pipeline

To run the ingestion process, execute the following command from the project root directory:

```bash
python -m sentinelforge.ingestion.main
```

## Processed Feeds and Output

The pipeline currently processes the following feeds:

*   **dummy**: A static test feed.
*   **urlhaus**: Fetches recent malicious URL submissions from URLhaus.

For each feed processed, the script will output a log line to standard output in the following format:

```
[<ISO-timestamp>] <feed-name>: fetched <number-of-indicators> IOCs
```

If an error occurs while fetching a specific feed, an error message will be logged instead. 

## Fetching Data Programmatically

You can also fetch the data programmatically using Python's `requests` library:

```python
import requests

api_url = "http://localhost:8080/taxii/collections/enriched-iocs/objects/"
params = {"min_score": 70}

try:
    response = requests.get(api_url, params=params)
    response.raise_for_status() # Raise an exception for bad status codes
    stix_bundle = response.json()
    print(f"Fetched {len(stix_bundle.get('objects', [])) - 1} indicators.") # -1 for Identity obj
    # Process the stix_bundle dictionary as needed
    # print(json.dumps(stix_bundle, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
except ValueError:
    print("Error: Could not decode JSON response.")
``` 