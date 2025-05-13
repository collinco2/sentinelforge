from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ThreatIntelIngestor(ABC):
    """Interface for CTI feed ingestors."""

    @abstractmethod
    def get_indicators(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Fetch the feed at `source_url` and return a list of IOC dicts.

        Args:
            source_url: The URL of the threat feed.

        Returns:
            A list of dictionaries, where each dictionary represents an IOC.
        """
        ...
