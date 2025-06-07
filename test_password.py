#!/usr/bin/env python3
"""Test password verification"""

import hashlib


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        salt, hash_value = password_hash.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    except ValueError:
        return False


# Test with the actual hash from database
password = "admin123"
stored_hash = "e4d66a010bbfd2a15307ae7d900e2bab:4a6d0cef927eeb9fc1ad71864e94acd7cb894446ab694ac570777f3a396fda2e"

result = verify_password(password, stored_hash)
print(f"Password verification result: {result}")

# Let's also manually verify
salt, hash_value = stored_hash.split(":")
computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
print(f"Expected hash: {hash_value}")
print(f"Computed hash: {computed_hash}")
print(f"Match: {computed_hash == hash_value}")
