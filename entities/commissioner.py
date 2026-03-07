from supabase_client import get_supabase
from crypto.hash_utils import hash_value_sha256

def validate_n1(election_id: int, n1: str) -> bool:
    supabase = get_supabase()
    result = supabase.table('voters')\
        .select('used')\
        .eq('election_id', election_id)\
        .eq('n1', n1)\
        .execute()
    if not result.data:
        return False
    return not result.data[0]['used']

def use_n1(election_id: int, n1: str) -> None:
    supabase = get_supabase()
    supabase.table('voters')\
        .update({'used': True})\
        .eq('election_id', election_id)\
        .eq('n1', n1)\
        .execute()

def validate_n2_hash(election_id: int, n2: str) -> bool:
    supabase = get_supabase()
    n2_hash = hash_value_sha256(n2)
    result = supabase.table('voters')\
        .select('id')\
        .eq('election_id', election_id)\
        .eq('n2_hash', n2_hash)\
        .execute()
    return len(result.data) > 0