"""
rsa_utils.py
Member 1: Core RSA functions.

Required functions:
- generate_rsa_keys(key_size=2048) -> tuple
    Generate (public_key, private_key) where each is (e, n) or (d, n).

- rsa_encrypt(m: int, pub_key: tuple) -> int
    Encrypt integer m with public key.

- rsa_decrypt(c: int, priv_key: tuple) -> int
    Decrypt integer c with private key.

- rsa_sign(m: int, priv_key: tuple) -> int
    Sign integer m with private key.

- rsa_verify(m: int, s: int, pub_key: tuple) -> bool
    Verify signature s for message m.
"""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# TODO: Implement the functions listed above