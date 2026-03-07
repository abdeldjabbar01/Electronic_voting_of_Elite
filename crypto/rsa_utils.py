from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_rsa_keys(key_size=2048):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    p = private_key.private_numbers().p
    q = private_key.private_numbers().q
    d = private_key.private_numbers().d
    e = public_key.public_numbers().e
    n = public_key.public_numbers().n

    return ((e, n), (d, n))

def rsa_encrypt(m: int, pub_key: tuple) -> int:
    e, n = pub_key
    return pow(m, e, n)

def rsa_decrypt(c: int, priv_key: tuple) -> int:
    d, n = priv_key
    return pow(c, d, n)

def rsa_sign(m: int, priv_key: tuple) -> int:
    d, n = priv_key
    return pow(m, d, n)

def rsa_verify(m: int, s: int, pub_key: tuple) -> bool:
    e, n = pub_key
    return pow(s, e, n) == m