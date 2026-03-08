"""
codec.py
Member 2: Encode and decode ballot.

Required functions:
- encode_ballot(vote: int, n2: str, random_bits: int = 0) -> int
    Convert (vote, n2, random_bits) into a single integer.
    Bit layout: vote (16 bits) | random_bits (32 bits) | n2_int (128 bits)

- decode_ballot(ballot_int: int) -> tuple
    Return (vote, random_bits, n2_int)
    n2_int must be converted back to string using helpers.int_to_str later.
"""
from utils.helpers import str_to_int

# TODO: Implement the functions listed above