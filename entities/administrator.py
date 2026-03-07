from crypto.rsa_utils import rsa_sign, rsa_verify

def blind_sign(masked_message: int, private_key: tuple) -> int:
    return rsa_sign(masked_message, private_key)

def verify_signature(message: int, signature: int, public_key: tuple) -> bool:
    return rsa_verify(message, signature, public_key)