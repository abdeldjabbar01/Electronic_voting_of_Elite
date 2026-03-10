"""
commissioner.py
Member 3: Commissioner functions (code validation).

Required functions (all use supabase):
- validate_n1(election_id: int, n1: str) -> bool
    Check if N1 exists and is unused in voters table.

- use_n1(election_id: int, n1: str) -> None
    Mark N1 as used (used=True).

- validate_n2_hash(election_id: int, n2: str) -> bool
    Hash n2 and check if it exists in voters table for this election.
"""
from supabase_client import get_supabase
from crypto.hash_utils import hash_value_sha256

# TODO: Implement the functions listed above