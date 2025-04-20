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