from supabase_client import get_supabase
from crypto.rsa_utils import rsa_decrypt
from . import commissioner, administrator
from voting.codec import decode_ballot
from utils.helpers import int_to_str

def count_ballots(election_id: int, counter_private_key: tuple, admin_public_key: tuple):
    supabase = get_supabase()
    ballots = supabase.table('ballots')\
        .select('encrypted_ballot, signature')\
        .eq('election_id', election_id)\
        .execute()
    
    results = []
    for b in ballots.data:
        try:
            enc = int(b['encrypted_ballot'])
            sig = int(b['signature'])
        except ValueError:
            continue

        message_int = rsa_decrypt(enc, counter_private_key)
        vote, random_bits, n2_int = decode_ballot(message_int)
        n2_str = int_to_str(n2_int)

        if not administrator.verify_signature(message_int, sig, admin_public_key):
            continue

        if not commissioner.validate_n2_hash(election_id, n2_str):
            continue

        results.append(vote)

    return results