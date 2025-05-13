from .threat_intel_ingestor import ThreatIntelIngestor
from .dummy_ingestor import DummyIngestor
from .urlhaus_ingestor import URLHausIngestor


def get_ingestor(name: str) -> ThreatIntelIngestor:
    """
    Factory for CTI ingestors.
    Args:
        name: identifier of the feed ingestor (e.g. "dummy")
    Returns:
        An instance implementing ThreatIntelIngestor
    Raises:
        ValueError if the name is unknown.
    """
    if name.lower() == "dummy":
        return DummyIngestor()
    elif name.lower() == "urlhaus":
        return URLHausIngestor()
    raise ValueError(f"Unknown ingestor: {name}")
