"""Counter module for decrypting and counting votes."""
from typing import List, Optional, Dict
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet


class Counter:
    """Handles vote decryption and counting."""
    
    def __init__(self):
        self.private_key = None
    
    def set_keys(self, n: int, e: int, d: int) -> None:
        """Set RSA keys for decryption."""
        self.n = n
        self.e = e
        self.d = d
    
    def decrypt_ballot(self, encrypted_ballot: str) -> Optional[str]:
        """Decrypt an encrypted ballot using hybrid decryption (RSA for key, AES for data)."""
        if not hasattr(self, 'n') or not hasattr(self, 'd'):
            return None
            
        try:
            # Split encrypted_ballot into encrypted_key and encrypted_data
            parts = encrypted_ballot.split(':')
            if len(parts) != 2:
                print(f"Invalid encrypted ballot format (expected 2 parts, got {len(parts)})")
                return None
            
            encrypted_key_hex = parts[0]
            encrypted_data = parts[1].encode('utf-8')
            
            # Decrypt AES key with RSA private key
            encrypted_key_int = int(encrypted_key_hex, 16)
            aes_key_int = pow(encrypted_key_int, self.d, self.n)
            
            # Convert back to 128 bytes (with leading zeros)
            aes_key_padded = aes_key_int.to_bytes(128, byteorder='big')
            
            # Remove padding (strip leading zeros to get 32 bytes)
            aes_key_bytes = aes_key_padded.lstrip(b'\x00')
            
            # Ensure exactly 32 bytes (pad if necessary, though unlikely)
            if len(aes_key_bytes) < 32:
                aes_key_bytes = b'\x00' * (32 - len(aes_key_bytes)) + aes_key_bytes
            elif len(aes_key_bytes) > 32:
                # Truncate if somehow longer (shouldn't happen)
                aes_key_bytes = aes_key_bytes[:32]
            
            # Re-encode to base64 for Fernet (must be 32 url-safe base64 bytes)
            aes_key = base64.urlsafe_b64encode(aes_key_bytes)
            
            # Decrypt data with AES
            f = Fernet(aes_key)
            decrypted_data = f.decrypt(encrypted_data)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_vote_choice(self, decrypted_ballot: str) -> Optional[str]:
        """Extract vote choice from decrypted ballot (format: vote_choice:N2:random_bits:signature)."""
        try:
            parts = decrypted_ballot.split(':')
            if len(parts) >= 4:
                return parts[0]  # vote_choice is first part
            return None
        except Exception:
            return None
    
    def extract_n2_code(self, decrypted_ballot: str) -> Optional[str]:
        """Extract N2 code from decrypted ballot (format: vote_choice:N2:random_bits:signature)."""
        try:
            parts = decrypted_ballot.split(':')
            if len(parts) >= 4:
                return parts[1]  # n2_code is second part
            return None
        except Exception:
            return None
    
    def verify_signature(self, decrypted_ballot: str, signature: str) -> bool:
        """Verify the blind signature."""
        try:
            # Extract components from ballot
            parts = decrypted_ballot.split(':')
            if len(parts) < 4:
                return False
                
            vote_choice = parts[0]
            n2_code = parts[1]
            random_bits = parts[2]
            
            # Recreate the message that was signed (ballot_message without signature)
            message_to_sign = f"{vote_choice}:{n2_code}:{random_bits}"
            
            # Hash the message
            message_hash = hashlib.sha256(message_to_sign.encode()).hexdigest()
            message_int = int(message_hash, 16)
            
            # RSA verification: m = s^e mod n
            signature_int = int(signature, 16)
            verified_int = pow(signature_int, self.e, self.n)
            
            return verified_int == message_int
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
