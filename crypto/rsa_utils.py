"""RSA cryptographic utilities."""
import base64
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from constants import RSA_KEY_SIZE

@dataclass
class RSAKeyPair:
    """Container for RSA key pair."""
    private_key: RSAPrivateKey
    public_key: RSAPublicKey
    
    def get_private_pem(self) -> str:
        """Export private key as PEM string."""
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode('utf-8')
    
    def get_public_pem(self) -> str:
        """Export public key as PEM string."""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')


def generate_rsa_keys(key_size: int = None) -> RSAKeyPair:
    """Generate a new RSA key pair.
    
    Args:
        key_size: Size of the RSA key in bits (default from config)
    
    Returns:
        RSAKeyPair containing private and public keys
    """
    if key_size is None:
        key_size = RSA_KEY_SIZE
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    public_key = private_key.public_key()
    
    return RSAKeyPair(private_key=private_key, public_key=public_key)


def serialize_public_key(public_key: RSAPublicKey) -> Tuple[int, int]:
    """Serialize public key to (n, e) tuple for storage.
    
    Args:
        public_key: The RSA public key
    
    Returns:
        Tuple of (modulus n, public exponent e) as integers
    """
    numbers = public_key.public_numbers()
    return numbers.n, numbers.e


def deserialize_public_key(n: int, e: int = 65537) -> RSAPublicKey:
    """Deserialize public key from (n, e) tuple.
    
    Args:
        n: RSA modulus
        e: RSA public exponent (default 65537)
    
    Returns:
        RSAPublicKey object
    """
    numbers = rsa.RSAPublicNumbers(e=e, n=n)
    return numbers.public_key()


def encrypt_message(message: str, public_key: RSAPublicKey) -> str:
    """Encrypt a message using RSA-OAEP.
    
    Args:
        message: The plaintext message to encrypt
        public_key: The RSA public key for encryption
    
    Returns:
        Base64-encoded encrypted ciphertext
    """
    plaintext = message.encode('utf-8')
    ciphertext = public_key.encrypt(
        plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode('utf-8')


def decrypt_message(ciphertext_b64: str, private_key: RSAPrivateKey) -> str:
    """Decrypt a message using RSA-OAEP.
    
    Args:
        ciphertext_b64: Base64-encoded ciphertext
        private_key: The RSA private key for decryption
    
    Returns:
        Decrypted plaintext message
    """
    ciphertext = base64.b64decode(ciphertext_b64.encode('utf-8'))
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext.decode('utf-8')
