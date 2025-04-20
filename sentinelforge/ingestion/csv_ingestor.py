import csv
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .threat_intel_ingestor import ThreatIntelIngestor

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CSVIngestor(ThreatIntelIngestor):
    """Ingests threat intelligence data from a CSV file or URL."""

    def get_indicators(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Reads indicators from a CSV source (file path or URL).

        Assumes the CSV has a header row containing at least 'type' and 'value'.
        Optional columns: 'source', 'timestamp'. Column names are case-insensitive.

        Args:
            source_url: Local file path or HTTP/HTTPS URL of the CSV.

        Returns:
            A list of dictionaries, each representing a normalized indicator.
        """
        indicators = []
        content_lines = None

        # Check if source_url is a URL or local file path
        parsed_url = urlparse(source_url)
        if parsed_url.scheme in ["http", "https"]:
            try:
                response = requests.get(source_url)
                response.raise_for_status()
                content_lines = response.text.splitlines()
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch CSV from URL {source_url}: {e}")
                return []
        else:
            file_path = Path(source_url)
            if not file_path.is_file():
                logging.error(f"CSV file not found at path: {source_url}")
                return []
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    content_lines = f.read().splitlines()
            except IOError as e:
                logging.error(f"Failed to read CSV file {source_url}: {e}")
                return []
            except UnicodeDecodeError as e:
                logging.error(f"Encoding error reading CSV file {source_url}: {e}")
                return []

        if not content_lines:
            logging.warning(f"No content found in CSV source: {source_url}")
            return []

        try:
            # Use Sniffer for basic dialect detection (delimiter)
            dialect = csv.Sniffer().sniff(content_lines[0])
            reader = csv.reader(content_lines, dialect=dialect)

            header = [h.strip().lower() for h in next(reader)]
            logging.info(f"Detected header: {header}")

            # Find column indices (case-insensitive)
            try:
                type_idx = header.index("type")
                value_idx = header.index("value")
            except ValueError:
                logging.error(
                    f"CSV source {source_url} must contain 'type' and 'value' columns."
                )
                return []

            source_idx = header.index("source") if "source" in header else -1
            timestamp_idx = header.index("timestamp") if "timestamp" in header else -1

        except (csv.Error, StopIteration) as e:
            logging.error(
                f"Failed to parse CSV header or detect dialect in {source_url}: {e}"
            )
            return []

        # Start enumerate at 2 to get 1-based row number (incl. header)
        for i, row in enumerate(reader, start=2):
            # row_num = i + 2 # Account for header and 0-indexing -> No longer needed
            try:
                # Use i directly for logging row number
                if len(row) <= max(type_idx, value_idx):
                    logging.warning(
                        f"Skipping malformed row {i} in {source_url}: Not enough columns."
                    )
                    continue

                indicator_type = row[type_idx].strip()
                indicator_value = row[value_idx].strip()

                if not indicator_type or not indicator_value:
                    logging.warning(
                        f"Skipping row {i} in {source_url}: Missing type or value."
                    )
                    continue

                item = {
                    "type": indicator_type,
                    "value": indicator_value,
                }

                if (
                    source_idx != -1
                    and len(row) > source_idx
                    and row[source_idx].strip()
                ):
                    item["source"] = row[source_idx].strip()

                if (
                    timestamp_idx != -1
                    and len(row) > timestamp_idx
                    and row[timestamp_idx].strip()
                ):
                    try:
                        # Attempt to parse timestamp (ISO format preferred)
                        # Add more formats if needed
                        item["timestamp"] = datetime.fromisoformat(
                            row[timestamp_idx].strip().replace("Z", "+00:00")
                        ).isoformat()
                    except ValueError:
                        # Use i directly for logging row number
                        logging.warning(
                            f"Could not parse timestamp '{row[timestamp_idx]}' in row {i} of {source_url}. Skipping timestamp."
                        )

                indicators.append(item)

            except IndexError:
                # Use i directly for logging row number
                logging.warning(
                    f"Skipping malformed row {i} in {source_url}: Index out of bounds."
                )
            except Exception as e:
                # Use i directly for logging row number
                logging.warning(
                    f"Skipping row {i} in {source_url} due to unexpected error: {e}"
                )

        return indicators


# Example usage: python -m sentinelforge.ingestion.csv_ingestor
if __name__ == "__main__":
    logging.info("Running CSVIngestor example...")
    ingestor = CSVIngestor()
    sample_file = "feeds/sample.csv"

    print(f"--- Reading indicators from {sample_file} ---")
    indicators_from_file = ingestor.get_indicators(sample_file)

    if indicators_from_file:
        print(f"Successfully read {len(indicators_from_file)} indicators:")
        for ind in indicators_from_file:
            print(ind)
    else:
        print("No indicators read or an error occurred.")

    # Example with a (non-existent) URL - should log an error
    # print("\n--- Attempting to read from non-existent URL ---")
    # indicators_from_url = ingestor.get_indicators("http://localhost/nonexistent.csv")
    # print(f"Indicators from URL: {len(indicators_from_url)}")
