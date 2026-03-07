from supabase_client import get_supabase
from entities.counter import count_ballots

supabase = get_supabase()

def tally_votes():
    print("=== Tally Votes ===")
    try:
        election_id = int(input("Election ID: "))
    except:
        print(" Invalid input")
        return

    # Fetch election keys (convert from strings to integers)
    election = supabase.table('elections').select('*').eq('id', election_id).execute()
    if not election.data:
        print(" Election not found")
        return
    e = election.data[0]

    counter_private = (int(e['counter_priv_d']), int(e['counter_priv_n']))
    admin_public = (int(e['admin_pub_e']), int(e['admin_pub_n']))

    results = count_ballots(election_id, counter_private, admin_public)

    if results:
        print(f" Votes: {results}")
        print(f" Average: {sum(results)/len(results):.2f}")
        print(f" Count: {len(results)} votes")
    else:
        print(" No valid votes found")

if __name__ == "__main__":
    tally_votes()