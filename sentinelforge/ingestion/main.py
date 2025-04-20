import datetime

# Removed factory import, added direct imports
# from .factory import get_ingestor
from .dummy_ingestor import DummyIngestor
from .urlhaus_ingestor import URLHausIngestor
from .abuse_ch_ingestor import AbuseChIngestor

# Import the normalization function
from .normalize import normalize_indicators


def run_ingestion_pipeline():
    """Runs the ingestion pipeline for configured feeds."""
    # Directly instantiate ingestors
    ingestors = [
        DummyIngestor(),
        URLHausIngestor(),
        AbuseChIngestor(),
    ]

    # Loop over instantiated ingestors
    for ingestor in ingestors:
        # Infer feed name from class name for logging
        feed_name = ingestor.__class__.__name__.replace("Ingestor", "").lower()
        # Add URLHausIngestor specific name handling if needed, it's currently urlhausingestor
        if isinstance(ingestor, URLHausIngestor):
            feed_name = "urlhaus"  # Keep consistent name
        if isinstance(ingestor, AbuseChIngestor):
            feed_name = "abusech"  # Keep consistent name

        try:
            # Fetch raw indicators
            raw_indicators = ingestor.get_indicators()
            # Normalize and deduplicate
            normalized_indicators = normalize_indicators(raw_indicators)

            timestamp = datetime.datetime.now().isoformat()
            # Log the count of *normalized* indicators
            print(
                f"[{timestamp}] {feed_name}: fetched {len(normalized_indicators)} unique IOCs (from {len(raw_indicators)} raw)"
            )
        # Removed ValueError catch as we no longer use the factory
        # except ValueError as e:
        #     print(f"Error getting ingestor for {feed_name}: {e}")
        except Exception as e:
            # Catch potential issues during get_indicators or normalization
            timestamp = datetime.datetime.now().isoformat()
            print(f"[{timestamp}] {feed_name}: failed to process feed - {e}")


if __name__ == "__main__":
    run_ingestion_pipeline()
