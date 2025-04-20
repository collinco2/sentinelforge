from typing import List, Dict, Optional, Any


def _get_value_and_type(item: Dict[str, Any]) -> Optional[tuple[str, str]]:
    """Extracts the primary value and its type from an indicator dict."""
    if "ip" in item:
        return str(item["ip"]), "ip"
    if "domain" in item:
        return str(item["domain"]), "domain"
    if "url" in item:
        # Basic check if it's just a domain or a full URL path
        # You might want more sophisticated URL parsing here
        return str(item["url"]), "url"
    if "hash" in item:
        # Could check for specific hash types (md5, sha1, sha256) if needed
        return str(item["hash"]), "hash"
    if "value" in item and "type" in item:
        # Handle generic STIX-like format from DummyIngestor
        value = str(item["value"])
        type_ = str(item["type"])
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
            return None  # Cannot uniquely identify without a value
        return value, type_
    return None  # Indicate item couldn't be processed


def normalize_indicators(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    - Deduplicate indicators based on their primary value and type.
    - Standardize values (strip http(s)://, lowercase, trim whitespace).
    - Return list of unique, normalized indicator dicts.
    """
    seen = set()
    result = []
    for item in raw:
        value_type = _get_value_and_type(item)
        if value_type is None:
            # Optionally log items that couldn't be normalized
            # print(f"Skipping unnormalizable item: {item}")
            continue

        value, type_ = value_type

        # Standardize
        normalized_value = value.strip().lower()
        if type_ in ["domain", "url"]:
            if normalized_value.startswith("https://"):
                normalized_value = normalized_value[8:]
            elif normalized_value.startswith("http://"):
                normalized_value = normalized_value[7:]
            # Remove trailing slash for domains/URLs if present
            if normalized_value.endswith("/"):
                normalized_value = normalized_value[:-1]

        # Use (type, normalized_value) for deduplication key
        key = (type_, normalized_value)

        if key not in seen:
            seen.add(key)
            # Store the original item, or potentially a modified one
            # if you want to store the normalized value back into it.
            # For now, appending the original item that passed deduplication.
            result.append(item)

    return result
