"""
administrator.py
Member 3: Administrator functions (signing).

Required functions:
- blind_sign(masked_message: int, private_key: tuple) -> int
    Sign the blinded message using private key (calls rsa_sign).

- verify_signature(message: int, signature: int, public_key: tuple) -> bool
    Verify signature (calls rsa_verify).
"""
from crypto.rsa_utils import rsa_sign, rsa_verify

# TODO: Implement the functions listed above