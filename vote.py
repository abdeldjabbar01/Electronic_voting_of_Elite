import random
from supabase_client import get_supabase
from entities.commissioner import validate_n1, validate_n2_hash
from entities.administrator import blind_sign
from entities.anonymizer import accept_ballot
from crypto.blind_signature import blind_message, unblind_signature
from crypto.rsa_utils import rsa_encrypt
from voting.codec import encode_ballot

supabase = get_supabase()

def cast_vote():
    print("=== Cast Your Vote ===")
    try:
        election_id = int(input("Election ID: "))
        n1 = input("N1 code: ").strip()
        n2 = input("N2 code: ").strip()
        vote_value = int(input("Your vote (0-10): "))
        if not 0 <= vote_value <= 10:
            print(" Vote must be between 0 and 10")
            return
    except:
        print(" Invalid input")
        return

    # Fetch election keys (convert from strings to integers)
    election = supabase.table('elections').select('*').eq('id', election_id).execute()
    if not election.data:
        print(" Election not found")
        return
    e = election.data[0]

    # Convert string fields to integers
    admin_pub = (int(e['admin_pub_e']), int(e['admin_pub_n']))
    admin_priv = (int(e['admin_priv_d']), int(e['admin_priv_n']))
    counter_pub = (int(e['counter_pub_e']), int(e['counter_pub_n']))

    # Validate N1
    if not validate_n1(election_id, n1):
        print(" N1 is invalid or already used")
        return

    # Validate N2 hash
    if not validate_n2_hash(election_id, n2):
        print(" N2 is invalid")
        return

    # Create ballot message
    random_bits = random.randint(0, 2**32-1)
    message = encode_ballot(vote_value, n2, random_bits)

    # Blind signature
    k = 7  # In practice, generate random k coprime with N
    blinded = blind_message(message, k, admin_pub)
    signed_blinded = blind_sign(blinded, admin_priv)
    signature = unblind_signature(signed_blinded, k, admin_pub)

    # Encrypt with counter's public key
    encrypted = rsa_encrypt(message, counter_pub)

    # Send to anonymizer
    if accept_ballot(election_id, n1, encrypted, signature):
        print(" Your vote has been successfully recorded!")
    else:
        print(" Failed to record your vote")

if __name__ == "__main__":
    cast_vote()