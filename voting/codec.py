from utils.helpers import str_to_int

def encode_ballot(vote: int, n2: str, random_bits: int = 0) -> int:
    n2_int = str_to_int(n2)
    n2_int &= (1 << 128) - 1
    random_bits &= (1 << 32) - 1
    return (vote << 160) | (random_bits << 128) | n2_int

def decode_ballot(ballot_int: int):
    n2_int = ballot_int & ((1 << 128) - 1)
    random_bits = (ballot_int >> 128) & ((1 << 32) - 1)
    vote = (ballot_int >> 160) & ((1 << 16) - 1)
    return vote, random_bits, n2_int