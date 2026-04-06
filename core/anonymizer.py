"""Anonymizer module for ballot encryption and anonymization."""
from typing import Optional
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class Anonymizer:
    """Handles ballot encryption and anonymization."""
    
    def __init__(self):
        pass
    
    def encrypt_ballot(self, ballot_data: str, public_key: str) -> Optional[str]:
        """Encrypt ballot data using hybrid encryption (AES for data, RSA for key)."""
        try:
            # Generate random AES key (Fernet generates 32-byte URL-safe base64-encoded key)
            aes_key = Fernet.generate_key()  # This is 32 bytes base64-encoded = 32 chars
            f = Fernet(aes_key)
            
            # Encrypt ballot data with AES
            encrypted_data = f.encrypt(ballot_data.encode('utf-8'))
            
            # Convert public key string to int
            n = int(public_key)
            e = 65537  # Standard RSA public exponent
            
            # Ensure AES key fits in RSA modulus by using proper padding
            # Fernet key is 32 bytes, we need to ensure it's smaller than n
            aes_key_bytes = base64.urlsafe_b64decode(aes_key)  # Decode from base64 to get raw 32 bytes
            
            # Add padding to make it exactly 128 bytes (1024 bits) with leading zeros
            # This ensures the integer representation is always smaller than n
            padded_key = b'\x00' * (128 - len(aes_key_bytes)) + aes_key_bytes
            
            # Encrypt padded AES key with RSA
            aes_key_int = int.from_bytes(padded_key, byteorder='big')
            if aes_key_int >= n:
                print(f"AES key too large for RSA modulus")
                return None
                
            encrypted_key_int = pow(aes_key_int, e, n)
            encrypted_key = hex(encrypted_key_int)[2:]
            
            # Return format: encrypted_key:encrypted_data (hex:base64)
            result = f"{encrypted_key}:{encrypted_data.decode('utf-8')}"
            return result
        except Exception as ex:
            print(f"Encryption error: {ex}")
            import traceback
            traceback.print_exc()
            return None
    
    def store_encrypted_ballot(self, vote_id: int, n1_code: str, encrypted_ballot: str) -> bool:
        """Store encrypted ballot in database."""
        # Placeholder - implement database storage
        return True
    
    def get_ballot_by_n1(self, n1_code: str) -> Optional[dict]:
        """Retrieve ballot by N1 code (for double voting prevention)."""
        # Placeholder - implement database retrieval
        return None
