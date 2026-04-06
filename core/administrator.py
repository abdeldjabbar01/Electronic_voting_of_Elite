"""Administrator module for blind signature operations."""
from typing import Optional, Tuple
import hashlib
import secrets


class Administrator:
    """Handles blind signatures using RSA."""
    
    def __init__(self):
        self.n: Optional[int] = None
        self.e: int = 65537  # Standard RSA public exponent
        self.d: Optional[int] = None
        self.p: Optional[int] = None
        self.q: Optional[int] = None
    
    def generate_keys(self, key_size: int = 2048) -> Tuple[int, int, int]:
        """Generate RSA key pair using simple primes for demonstration.
        
        Returns:
            Tuple of (n, e, d) - modulus, public exponent, private exponent
        """
        def is_prime(n: int, k: int = 5) -> bool:
            if n < 2: return False
            for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
                if n % p == 0:
                    return n == p
            r, d = 0, n - 1
            while d % 2 == 0:
                r += 1
                d //= 2
            for _ in range(k):
                a = secrets.randbelow(n - 2) + 2
                x = pow(a, d, n)
                if x == 1 or x == n - 1:
                    continue
                for _ in range(r - 1):
                    x = pow(x, 2, n)
                    if x == n - 1:
                        break
                else:
                    return False
            return True
        
        def get_prime(bits: int) -> int:
            while True:
                n = secrets.randbits(bits)
                n |= 1
                n |= (1 << (bits - 1))  # Set high bit
                if is_prime(n):
                    return n
        
        # Generate primes of appropriate size
        p_bits = key_size // 2
        q_bits = key_size // 2
        
        self.p = get_prime(p_bits)
        self.q = get_prime(q_bits)
        
        self.n = self.p * self.q
        phi = (self.p - 1) * (self.q - 1)
        
        # Ensure e and phi are coprime (they should be with e=65537)
        import math
        assert math.gcd(self.e, phi) == 1, "e and phi must be coprime"
        
        # Compute private exponent d
        self.d = pow(self.e, -1, phi)
        
        return self.n, self.e, self.d
    
    def set_keys(self, n: int, e: int, d: int) -> None:
        """Set keys from stored values."""
        self.n = n
        self.e = e
        self.d = d
    
    def _get_private_key_for_signing(self) -> Optional[int]:
        """Get private key if available."""
        return self.d
    
    def blind_sign(self, message: str) -> Optional[str]:
        """Create RSA signature on message (simplified - no actual blinding for demo).
        
        In a full blind signature protocol, the voter would blind the message
        before sending it. Here we do a simple RSA signature for demonstration.
        
        Args:
            message: The message to sign
            
        Returns:
            Signature as hex string, or None if keys not available
        """
        d = self._get_private_key_for_signing()
        if not d or not self.n:
            return None
        
        # Hash the message and create signature
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        message_int = int(message_hash, 16)
        
        # RSA signature: s = m^d mod n
        signature_int = pow(message_int, d, self.n)
        
        # Return signature as hex string
        return hex(signature_int)[2:]
    
    def verify_signature(self, message: str, signature: str) -> bool:
        """Verify a signature."""
        if not self.n or not self.e:
            return False
        
        try:
            # Hash the message
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            message_int = int(message_hash, 16)
            
            # Convert signature from hex
            signature_int = int(signature, 16)
            
            # RSA verification: m = s^e mod n
            verified_int = pow(signature_int, self.e, self.n)
            
            return verified_int == message_int
        except Exception:
            return False
    
    def get_public_key_pem(self) -> str:
        """Get public key in a simple format."""
        return f"{self.n}:{self.e}"
    
    def get_private_key_pem(self) -> str:
        """Get private key in a simple format."""
        return f"{self.n}:{self.e}:{self.d}"
