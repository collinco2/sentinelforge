import logging
from typing import List, Dict, Any
import requests

# Corrected import path for the base class
from .threat_intel_ingestor import ThreatIntelIngestor

logger = logging.getLogger(__name__)


class JSONIngestor(ThreatIntelIngestor):
    """Ingests threat intelligence data from a predefined JSON feed URL."""

    def __init__(self, url: str):
        """
        Initializes the ingestor with the specific feed URL.
        Args:
            url: The URL of the JSON feed to fetch.
        """
        self.url = url
        # Add requests session with retries for robustness (optional but recommended)
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)  # Simple retry
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # Method signature matches the base class
    def get_indicators(self, source_url: str = None) -> List[Dict[str, Any]]:
        """
        Fetches indicators from the configured JSON feed URL.
        The source_url parameter is ignored in favor of the URL set during initialization.
        """
        # Use self.url which was set during initialization
        fetch_url = self.url
        if source_url:
            logger.debug(
                f"Ignoring provided source_url '{source_url}', using configured URL '{fetch_url}'"
            )

        try:
            # Use the session with retries
            resp = self.session.get(fetch_url, timeout=10)
            resp.raise_for_status()  # Check for HTTP errors
            data = resp.json()

            if not isinstance(data, list):
                logger.warning(
                    f"Expected a list from {fetch_url}, got {type(data)}. Returning empty list."
                )
                return []

            # Basic filtering as requested
            # Note: This assumes items are dicts; more robust checking could be added
            valid_items = []
            for item in data:
                if isinstance(item, dict) and "value" in item and "type" in item:
                    valid_items.append(item)
                else:
                    logger.debug(
                        f"Skipping item missing 'type' or 'value', or not a dict: {item}"
                    )
            return valid_items

        except requests.exceptions.RequestException as e:
            logger.warning(f"JSONIngestor network error for {fetch_url}: {e}")
            return []
        except ValueError as e:  # Catches JSONDecodeError
            logger.warning(f"JSONIngestor invalid JSON from {fetch_url}: {e}")
            return []
        except Exception as e:
            logger.error(
                f"JSONIngestor unexpected error for {fetch_url}: {e}", exc_info=True
            )
            return []


# Keep the example block, but adjust it for the new __init__ style
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger.info("Running JSONIngestor example...")

    # Instantiate with a specific URL
    sample_url = "https://raw.githubusercontent.com/stamparm/maltrail/master/trails/static/suspicious/botnet_cnc.json"
    ingestor = JSONIngestor(url=sample_url)

    print(f"\n--- Reading indicators from {sample_url} ---")
    # Call get_indicators (can optionally pass the same url, it will be ignored)
    indicators_from_url = ingestor.get_indicators(source_url=sample_url)

    if indicators_from_url:
        print(
            f"Successfully extracted {len(indicators_from_url)} indicators (showing first 5):"
        )
        for ind in indicators_from_url[:5]:
            print(ind)
        if len(indicators_from_url) > 5:
            print("...")
    else:
        print("No indicators extracted or an error occurred.")

    print("\n--- Attempting to read from non-existent URL ---")
    bad_ingestor = JSONIngestor(url="http://localhost/nonexistent.json")
    indicators_nonexistent = bad_ingestor.get_indicators()
    print(f"Indicators from non-existent URL: {len(indicators_nonexistent)}")
