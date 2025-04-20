import logging
from typing import List, Dict, Any

# Import TAXII and STIX clients (ensure taxii2-client and stix2 are installed)
try:
    from taxii2client.v20 import (
        Server,
        Collection,
    )  # Added Collection for type hint maybe?
    from stix2 import parse
    from taxii2client.exceptions import TAXIIClientError
except ImportError:
    print("Error: taxii2-client and stix2 libraries are required for TAXIIIngestor.")
    print("Install them using: pip install -e .[dev]")  # Updated install command suggestion

    # Define dummy classes to avoid runtime errors if imports fail
    class Server:
        pass

    class Collection:
        pass

    class TAXIIClientError(Exception):
        pass

    # Remove dummy parse, rely on actual stix2 library being installed
    # def parse(obj, allow_custom=False): return obj # Dummy parse

# Corrected import path for the base class
from .threat_intel_ingestor import ThreatIntelIngestor

logger = logging.getLogger(__name__)


class TAXIIIngestor(ThreatIntelIngestor):
    """Ingests STIX indicators from a specific TAXII 2.0 Server and Collection."""

    def __init__(self, server_url: str, collection_id: str, **kwargs):
        """
        Initializes the ingestor with TAXII server details.

        Args:
            server_url: The root URL of the TAXII 2.0 server.
            collection_id: The ID of the collection to fetch from.
            **kwargs: Additional keyword arguments passed to taxii2client.Server
                      (e.g., user, password for authentication).
        """
        # Store connection details but handle potential connection errors in get_indicators
        self.server_url = server_url
        self.collection_id = collection_id
        self.conn_kwargs = kwargs
        # Store server instance, or could initialize it lazily in get_indicators
        # self.server = Server(server_url, **kwargs)

    # Method signature matches the base class
    def get_indicators(self, source_url: str = None) -> List[Dict[str, Any]]:
        """
        Fetches STIX indicators from the configured TAXII server and collection.
        The source_url parameter is ignored in favor of the details set during initialization.
        """
        if source_url:
            logger.debug(
                f"Ignoring provided source_url '{source_url}', using configured server/collection."
            )

        results: List[Dict[str, Any]] = []
        try:
            # Initialize server connection here to handle connection errors gracefully
            logger.info(f"Connecting to TAXII server at {self.server_url}...")
            server = Server(self.server_url, **self.conn_kwargs)
            # Assuming get_collection_api does not exist, use get_collection directly?
            # Or maybe iterate through server.collections if ID needs discovery?
            # Let's assume collection_id is valid and directly accessible via server.collections
            collection = None
            for coll_info in server.collections:
                if coll_info.id == self.collection_id:
                    # Found the collection, now create Collection object if necessary
                    # The taxii2client API might differ slightly based on version
                    # Assuming we need a Collection object to call get_objects
                    collection = Collection(coll_info.url, server=server, **self.conn_kwargs)
                    break

            if not collection:
                logger.error(
                    f"Collection ID '{self.collection_id}' not found on server {self.server_url}."
                )
                return []

            logger.info(f"Fetching objects from collection '{self.collection_id}'...")
            bundle = collection.get_objects()  # Fetch objects from the collection
            objs = bundle.get("objects", [])
            logger.info(f"Processing {len(objs)} STIX objects...")

            for obj in objs:
                # Filter for indicators as requested
                if obj.get("type") != "indicator":
                    continue

                try:
                    # Parse the STIX object data
                    stix_obj = parse(obj, allow_custom=True)
                    # Extract id, type, and pattern as value
                    results.append(
                        {
                            "id": stix_obj.id,
                            "type": "stix",  # Use generic 'stix' type for now
                            "value": getattr(stix_obj, "pattern", None),
                            "stix_id": stix_obj.id,  # Explicitly add for testing check
                        }
                    )
                except Exception as parse_exc:
                    # Log parsing errors for individual objects
                    logger.warning(
                        f"Failed to parse STIX object {obj.get('id', '{no id}')}: {parse_exc}"
                    )

        except TAXIIClientError as e:
            logger.error(f"TAXII client error for server {self.server_url}: {e}")
        except ImportError as e:
            logger.error(
                f"Import error for TAXII/STIX libraries: {e}. Ensure taxii2-client and stix2 are installed."
            )
        except Exception as e:
            logger.error(
                f"TAXIIIngestor unexpected error for {self.server_url}/{self.collection_id}: {e}",
                exc_info=True,
            )

        logger.info(f"Finished processing TAXII feed. Extracted {len(results)} indicators.")
        return results


# Example usage: python -m sentinelforge.ingestion.taxii_ingestor
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Running TAXIIIngestor example...")

    # Example server/collection (adjust as needed, requires live server)
    hailataxii_server = "https://cti-taxii.mitre.org/taxii/"
    # Example collection ID (guest collection, may change)
    hailataxii_collection_id = "95ecc380-afe9-11e4-9b6c-751b66dd541e"

    print("\n--- Instantiating TAXIIIngestor (run requires live server/auth) ---")
    try:
        # Instantiate with server URL and collection ID
        # Might need user/password kwargs depending on server auth
        ingestor = TAXIIIngestor(
            server_url=hailataxii_server, collection_id=hailataxii_collection_id
        )
        # user='guest', password='guest')
        print("TAXIIIngestor instantiated successfully.")

        # --- Example of fetching (commented out by default) ---
        # print(f"\n--- Attempting to fetch from {hailataxii_server}, collection {hailataxii_collection_id} ---")
        # indicators = ingestor.get_indicators()
        # if indicators:
        #    print(f"Successfully extracted {len(indicators)} indicators (showing first 5):")
        #    for ind in indicators[:5]:
        #         print(ind)
        #    if len(indicators) > 5: print("...")
        # else:
        #    print("No indicators extracted or an error occurred.")
        # --- End Example Fetch ---

    except ImportError as e:
        print(f"Failed to instantiate TAXIIIngestor due to missing libraries: {e}")
    except Exception as e:
        print(f"Failed to instantiate TAXIIIngestor: {e}")
