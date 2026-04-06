"""
Initialize Supabase database with schema and test data.
Run this to set up your database for testing.
"""
import os
from supabase import create_client
from dotenv import load_dotenv
import uuid
import time

load_dotenv()

# Get Supabase credentials
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    print("Add these to your .env file:")
    print("SUPABASE_URL=your-project-url.supabase.co")
    print("SUPABASE_KEY=your-anon-key")
    exit(1)

print(f"Connecting to Supabase at: {url}")
client = create_client(url, key)

def initialize_schema():
    """Initialize the database schema in Supabase."""
    print("\n=== Initializing Schema ===")
    
    # Note: Supabase schema should be created via the dashboard
    # This is just for reference
    print("Please create these tables in your Supabase dashboard:")
    print("1. votes")
    print("2. voters") 
    print("3. vote_voters")
    print("4. vote_options")
    print("5. admin_keys")
    print("6. counter_keys")
    print("7. encrypted_ballots")
    print("8. decrypted_votes")
    print("\nUse the SQL schema from your schema.sql file")

def create_test_data():
    """Create test vote and voter data."""
    print("\n=== Creating Test Data ===")
    
    # Generate unique codes
    import random
    import string
    def generate_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    n1_code = generate_code()
    n2_code = generate_code()
    import hashlib
    n2_hash = hashlib.sha256(n2_code.encode()).hexdigest()
    
    # Create test vote
    vote_data = {
        'title': 'Test Rating Vote',
        'description': 'This is a test vote for debugging',
        'vote_type': 'rating',
        'creator_code': 'TEST123',
        'is_active': True
    }
    
    try:
        result = client.table('votes').insert(vote_data).execute()
        vote_id = result.data[0]['id']
        print(f"Created test vote with ID: {vote_id}")
        
        # Create test voter
        voter_email = f'test{int(time.time())}@example.com'  # Unique email
        voter_data = {
            'email': voter_email,
            'n1_code': n1_code,  # Unique N1 code
            'n2_hash': n2_hash,  # Use actual SHA-256 hash
            'has_voted': False
        }
        
        result = client.table('voters').insert(voter_data).execute()
        voter_id = result.data[0]['id']
        print(f"Created test voter with N1 code: {n1_code}")
        
        # Link voter to vote with matching N2 hash
        vote_voter_data = {
            'vote_id': vote_id,
            'voter_email': voter_email,
            'n2_hash': n2_hash,  # This must match the hash generated from N2
            'has_voted': False
        }
        
        result = client.table('vote_voters').insert(vote_voter_data).execute()
        print(f"Linked voter to vote")
        
        # Create vote option for rating votes
        option_data = {
            'vote_id': vote_id,
            'option_text': 'Rating Option',
            'option_order': 1
        }
        
        client.table('vote_options').insert(option_data).execute()
        print(f"Created vote option")
        
        # Create admin keys
        admin_keys_data = {
            'public_key_n': 'admin_n_placeholder',
            'public_key_e': 65537,
            'private_key_pem': 'admin_private_placeholder',
            'is_active': True
        }
        client.table('admin_keys').insert(admin_keys_data).execute()
        print(f"Created admin keys")
        
        # Create counter keys
        counter_keys_data = {
            'public_key_n': 'counter_n_placeholder',
            'public_key_e': 65537,
            'private_key_pem': 'counter_private_placeholder',
            'is_active': True
        }
        client.table('counter_keys').insert(counter_keys_data).execute()
        print(f"Created counter keys")
        
        print(f"\n=== TEST DATA CREATED ===")
        print(f"Vote ID: {vote_id}")
        print(f"N1 Code: {n1_code}")
        print(f"N2 Code: {n2_code}")
        print(f"N2 Hash: {n2_hash}")
        print(f"Vote Choice: Any number between 0-10")
        
        return vote_id, n1_code, n2_code
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        return None, None, None

def test_vote_submission(vote_id, n1_code, n2_code):
    """Test vote submission with the created test data."""
    import requests
    
    print(f"\n=== Testing Vote Submission ===")
    
    data = {
        "n1_code": n1_code,
        "n2_code": n2_code, 
        "vote_choice": "5.000"
    }
    
    try:
        response = requests.post(
            f"http://localhost:5000/api/votes/{vote_id}/submit",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("SUPABASE DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Test connection
    try:
        # Try to query votes table
        result = client.table('votes').select('*').limit(1).execute()
        print("Successfully connected to Supabase")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        print("\nMake sure:")
        print("1. Your SUPABASE_URL and SUPABASE_KEY are correct in .env")
        print("2. The tables exist in your Supabase project")
        print("3. Your Supabase project is active")
        exit(1)
    
    # Create test data
    vote_id, n1_code, n2_code = create_test_data()
    
    if vote_id:
        # Test vote submission
        test_vote_submission(vote_id, n1_code, n2_code)
    
    print("\n" + "=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)
