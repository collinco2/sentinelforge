from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


def _get_value_and_type(item: Dict[str, Any]) -> Optional[tuple[str, str]]:
    """Extracts the primary value and its type from an indicator dict."""
    
    # Debug logging
    logger.debug(f"Normalizing item: {item}")
    
    if "ip" in item:
        logger.debug(f"Extracted IP: {item['ip']}")
        return str(item["ip"]), "ip"
    if "domain" in item:
        logger.debug(f"Extracted domain: {item['domain']}")
        return str(item["domain"]), "domain"
    if "url" in item:
        # Basic check if it's just a domain or a full URL path
        # You might want more sophisticated URL parsing here
        logger.debug(f"Extracted URL: {item['url']}")
        return str(item["url"]), "url"
    if "hash" in item:
        # Could check for specific hash types (md5, sha1, sha256) if needed
        logger.debug(f"Extracted hash: {item['hash']}")
        return str(item["hash"]), "hash"
    if "value" in item and "type" in item:
        # Handle generic STIX-like format from DummyIngestor
        value = str(item["value"])
        type_ = str(item["type"])
        logger.debug(f"Extracted STIX format - type: {type_}, value: {value}")
        if type_ == "ipv4-addr":
            type_ = "ip"
        if type_ == "domain-name":
            type_ = "domain"
        if type_ == "file":
            # Try to extract a hash value if present
            hashes = item.get("hashes", {})
            if "MD5" in hashes:
                return str(hashes["MD5"]), "hash"
            if "SHA-1" in hashes:
                return str(hashes["SHA-1"]), "hash"
            if "SHA-256" in hashes:
                return str(hashes["SHA-256"]), "hash"
            # Fallback if only file type is known but no hash
            logger.debug(f"Cannot extract hash value from file type")
            return None  # Cannot uniquely identify without a value
        return value, type_
        
    logger.debug(f"Failed to extract value and type from item: {item}")
    return None  # Indicate item couldn't be processed


def normalize_indicators(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    - Deduplicate indicators based on their primary value and type.
    - Standardize values (strip http(s)://, lowercase, trim whitespace).
    - Return list of unique indicator dicts, potentially adding normalized keys.
      (Original implementation returned original dicts)
    """
    logger.info(f"Normalizing {len(raw)} raw indicators")
    
    seen = set()
    result = []  # This will now store modified dicts or tuples
    skipped = 0
    
    for item in raw:
        value_type = _get_value_and_type(item)
        if value_type is None:
            skipped += 1
            continue

        value, type_ = value_type

        # Standardize value
        normalized_value = value.strip().lower()
        if type_ in ["domain", "url"]:
            if normalized_value.startswith("https://"):
                normalized_value = normalized_value[8:]
            elif normalized_value.startswith("http://"):
                normalized_value = normalized_value[7:]
            if normalized_value.endswith("/"):
                normalized_value = normalized_value[:-1]

        # Use (type, normalized_value) for deduplication key
        key = (type_, normalized_value)

        if key not in seen:
            seen.add(key)
            # Create a new dictionary or update the original item
            # Let's create a new one with consistent keys
            normalized_item = {
                "original": item,  # Keep original for reference if needed
                "norm_type": type_,  # Use the type identified by _get_value_and_type
                "norm_value": normalized_value,  # Use the processed value
                # Copy other potentially useful fields if needed
                # "description": item.get("description"),
                # "timestamp": item.get("timestamp")
            }
            result.append(normalized_item)
    
    logger.info(f"Normalized {len(result)} indicators, skipped {skipped}")
    return result
