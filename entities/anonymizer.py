"""
anonymizer.py
Member 3: Anonymizer functions (ballot reception).

Required functions:
- accept_ballot(election_id: int, n1: str, encrypted_ballot: int, signature: int) -> bool
    1. Check N1 using commissioner.validate_n1.
    2. If valid, store (encrypted_ballot, signature) in ballots table.
    3. Mark N1 as used using commissioner.use_n1.
    4. Return True on success.
"""
from supabase_client import get_supabase
from . import commissioner

# TODO: Implement the function listed above