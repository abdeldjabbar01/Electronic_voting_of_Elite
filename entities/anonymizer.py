from . import commissioner
from supabase_client import get_supabase

def accept_ballot(election_id: int, n1: str, encrypted_ballot: int, signature: int) -> bool:
    if not commissioner.validate_n1(election_id, n1):
        return False

    supabase = get_supabase()
    data = {
        'election_id': election_id,
        'encrypted_ballot': str(encrypted_ballot),
        'signature': str(signature)
    }
    supabase.table('ballots').insert(data).execute()
    commissioner.use_n1(election_id, n1)
    return True