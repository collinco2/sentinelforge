from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

# Import settings
from sentinelforge.settings import settings

# TODO: Replace hardcoded key with a secure method like environment variables or a secrets manager
# Example using environment variable:
# API_KEY = os.environ.get("SENTINELFORGE_API_KEY", "super-secret-token")
# No longer needed, use settings.sentinelforge_api_key

# Remove warning print, handled in settings.py
# if API_KEY == "super-secret-token":
#     print("WARNING: Using default insecure API key for API authentication.") # Add a warning

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def require_api_key(api_key: str = Security(api_key_header)):
    """FastAPI dependency to require a valid API key in the X-API-KEY header."""
    # Use the key from settings
    if not api_key or api_key != settings.sentinelforge_api_key:
        raise HTTPException(
            status_code=403, detail="Forbidden: Invalid or missing API Key"
        )
    return api_key
