"""Blind signature utilities for RSA."""
import base64
import secrets
import math
from typing import Tuple

from crypto.rsa_utils import RSAKeyPair
from constants import RSA_KEY_SIZE


class BlindSignature:
    """Implements RSA blind signatures."""
    
    @staticmethod
    def generate_blinding_factor(modulus_n: int) -> int:
        """Generate a random blinding factor k that is coprime with N.
        
        Args:
            modulus_n: The RSA modulus N
            
        Returns:
            A random integer k such that gcd(k, N) = 1
        """
        while True:
            # Generate random k in range [2, N-2]
            k = secrets.randbelow(modulus_n - 3) + 2
            # Check if k is coprime with N (simplified check)
            # In production, use proper gcd calculation
            if math.gcd(k, modulus_n) == 1:
                return k
    
    @staticmethod
    def blind_message(message_int: int, blinding_factor: int, public_e: int, modulus_n: int) -> int:
        """Blind a message using RSA blinding.
        
        Args:
            message_int: Message as integer
            blinding_factor: Random blinding factor k
            public_e: Public exponent e
            modulus_n: Modulus N
            
        Returns:
            Blinded message m' = m * k^e mod N
        """
        k_e = pow(blinding_factor, public_e, modulus_n)
        blinded = (message_int * k_e) % modulus_n
        return blinded
    
    @staticmethod
    def unblind_signature(blinded_signature_int: int, blinding_factor: int, modulus_n: int) -> int:
        """Unblind a signature.
        
        Args:
            blinded_signature_int: Blinded signature s' as integer
            blinding_factor: The original blinding factor k
            modulus_n: Modulus N
            
        Returns:
            Unblinded signature s = s' / k mod N
        """
        # Compute modular inverse of k
        k_inv = pow(blinding_factor, -1, modulus_n)
        unblinded = (blinded_signature_int * k_inv) % modulus_n
        return unblinded
    
    @staticmethod
    def message_to_int(message: str) -> int:
        """Convert message string to integer.
        
        Args:
            message: The message to convert
            
        Returns:
            Message as integer
        """
        return int.from_bytes(message.encode('utf-8'), 'big')
    
    @staticmethod
    def int_to_message(message_int: int) -> str:
        """Convert integer back to message string.
        
        Args:
            message_int: Message as integer
            
        Returns:
            Message string
        """
        # Calculate byte length
        byte_length = (message_int.bit_length() + 7) // 8
        message_bytes = message_int.to_bytes(byte_length, 'big')
        return message_bytes.decode('utf-8')
    
    @staticmethod
    def create_ballot_message(vote_choice: str, n2_code: str, random_bits: str = None) -> str:
        """Create the ballot message m = (choice, N2, random bits).
        
        Args:
            vote_choice: The vote choice (option or rating)
            n2_code: The N2 ballot identifier
            random_bits: Random bits for additional security
            
        Returns:
            JSON string of the ballot message
        """
        import json
        
        if random_bits is None:
            # Generate 64 random bits as hex string
            random_bits = secrets.token_hex(8)
        
        ballot = {
            "vote_choice": vote_choice,
            "n2_code": n2_code,
            "random_bits": random_bits
        }
        
        return json.dumps(ballot, separators=(',', ':'), sort_keys=True)
