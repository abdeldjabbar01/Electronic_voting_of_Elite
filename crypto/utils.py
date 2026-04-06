"""General cryptographic utilities."""
import hashlib
import base64
from typing import Union


def hash_code(code: str, salt: str = None) -> str:
    """Create a secure hash of a code using SHA-256.
    
    This is used to store hashed versions of voter/creator codes
    without revealing the original codes.
    
    Args:
        code: The code to hash
        salt: Optional salt to add (default: empty string)
    
    Returns:
        Base64-encoded SHA-256 hash
    """
    if salt is None:
        salt = "electronic_voting_system_salt_2024"
    
    data = (salt + code).encode('utf-8')
    hash_digest = hashlib.sha256(data).digest()
    return base64.b64encode(hash_digest).decode('utf-8')


def verify_hash(code: str, expected_hash: str, salt: str = None) -> bool:
    """Verify a code against an expected hash.
    
    Args:
        code: The code to verify
        expected_hash: The expected base64-encoded hash
        salt: Optional salt (must match what was used to create the hash)
    
    Returns:
        True if the code matches the hash
    """
    computed_hash = hash_code(code, salt)
    return computed_hash == expected_hash


def hash_to_bytes(hash_str: str) -> bytes:
    """Convert a base64-encoded hash string back to bytes.
    
    Args:
        hash_str: Base64-encoded hash string
    
    Returns:
        Raw hash bytes
    """
    return base64.b64decode(hash_str.encode('utf-8'))


def bytes_to_hash(hash_bytes: bytes) -> str:
    """Convert raw hash bytes to base64-encoded string.
    
    Args:
        hash_bytes: Raw hash bytes
    
    Returns:
        Base64-encoded hash string
    """
    return base64.b64encode(hash_bytes).decode('utf-8')
