from crypto.rsa_utils import rsa_sign, rsa_verify

def blind_message(m, k, pubkey):
    e, N = pubkey
    blinded = (m * pow(k, e, N)) % N
    return blinded

def sign_blinded_message(blinded_msg, privkey):
    signed_blinded = rsa_sign(blinded_msg, privkey)
    return signed_blinded

def unblind_signature(signed_blinded, k, pubkey):
    _, N = pubkey
    k_inv = pow(k, -1, N) 
    signature = (signed_blinded * k_inv) % N
    return signature

def verify_signature(m, signature, pubkey):
    return rsa_verify(m, signature, pubkey)