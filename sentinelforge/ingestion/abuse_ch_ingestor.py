import csv
import requests

# Corrected import path
from .threat_intel_ingestor import ThreatIntelIngestor


class AbuseChIngestor(ThreatIntelIngestor):
    """Pull IP blocklist from Abuse.ch Feodo Tracker."""

    # Adjusted method signature to match the base class abstract method
    def get_indicators(self, source_url: str = None) -> list[dict]:
        # Use default URL if source_url is not provided
        url = source_url or "https://feodotracker.abuse.ch/downloads/ipblocklist.csv"
        r = requests.get(url)
        r.raise_for_status()

        # Decode content explicitly assuming UTF-8, handle potential decoding errors
        try:
            text_content = r.content.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback or raise a more specific error if needed
            text_content = r.text

        # Filter out comment lines starting with '#'
        lines = [
            line
            for line in text_content.splitlines()
            if not line.strip().startswith("#")
        ]

        if not lines:
            return []  # Return empty list if no data lines found

        # Check header based on the first *data* line
        first_data_line = lines[0]
        sniffer = csv.Sniffer()
        try:
            # Use the first data line to detect dialect (delimiter, quoting)
            dialect = sniffer.sniff(first_data_line)
            has_header = sniffer.has_header(
                text_content
            )  # Sniff header from the whole text
        except csv.Error:
            # Handle cases where sniffing fails (e.g., single column, no clear delimiter)
            dialect = csv.excel  # Fallback to default dialect
            # Simple header check: is the first field likely an IP or a label?
            has_header = not ("." in first_data_line or ":" in first_data_line)

        # Create reader using detected dialect, skip header if detected
        reader = csv.reader(lines[1:] if has_header else lines, dialect=dialect)

        # Process rows, ensure row is not empty and has at least one column
        indicators = []
        for row in reader:
            if row and len(row) > 0:
                # Basic validation: check if the first column looks like an IP address
                # This is a simple check and might need refinement for robustness
                ip_candidate = row[0].strip()
                if (
                    "." in ip_candidate or ":" in ip_candidate
                ):  # Basic check for IPv4 or IPv6
                    indicators.append({"ip": ip_candidate})
                # else: Log or handle non-IP data if necessary

        return indicators
