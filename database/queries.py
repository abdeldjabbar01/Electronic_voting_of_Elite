"""All database CRUD operations."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import Client
from .client import get_supabase_client
from .models import Vote, VoteOption, VoteSubmission, Voter, EncryptedBallot, DecryptedVote, AdminKeys, CounterKeys


class VoteQueries:
    """Handles all database queries for the voting system."""

    def __init__(self, client: Client = None):
        self.client = client or get_supabase_client()

    # ===== VOTE CRUD =====
    
    def create_vote(self, vote: Vote) -> Vote:
        """Insert a new vote and return it with ID."""
        # Handle both string and datetime types for dates
        start_date = vote.start_date
        end_date = vote.end_date
        
        # Convert to ISO format string if datetime, use as-is if already string
        if start_date:
            if isinstance(start_date, datetime):
                start_date = start_date.isoformat()
        else:
            start_date = None
            
        if end_date:
            if isinstance(end_date, datetime):
                end_date = end_date.isoformat()
        else:
            end_date = None
        
        data = {
            'title': vote.title,
            'description': vote.description,
            'vote_type': vote.vote_type,
            'creator_code': vote.creator_code,
            'start_date': start_date,
            'end_date': end_date,
            'is_active': vote.is_active,
        }
        result = self.client.table('votes').insert(data).execute()
        if result.data:
            vote.id = result.data[0]['id']
            vote.created_at = result.data[0].get('created_at')
        return vote

    def get_vote_by_id(self, vote_id: int) -> Optional[Vote]:
        """Get a vote by its ID."""
        try:
            result = self.client.table('votes').select('*').eq('id', vote_id).single().execute()
            if result.data:
                return self._dict_to_vote(result.data)
        except Exception:
            # Vote not found or other error
            pass
        return None

    def get_all_active_votes(self) -> List[Vote]:
        """Get all currently active votes."""
        result = self.client.table('votes') \
            .select('*') \
            .eq('is_active', True) \
            .execute()
        return [self._dict_to_vote(row) for row in result.data or []]

    def get_all_votes(self) -> List[Vote]:
        """Get all votes (active and finished)."""
        result = self.client.table('votes') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        return [self._dict_to_vote(row) for row in result.data or []]

    def get_vote_by_creator_code(self, creator_code: str) -> Optional[Vote]:
        """Get a vote by its creator code."""
        try:
            result = self.client.table('votes').select('*').eq('creator_code', creator_code).single().execute()
            if result.data:
                return self._dict_to_vote(result.data)
        except Exception:
            # Vote not found or other error
            pass
        return None

    def update_vote(self, vote_id: int, **kwargs) -> bool:
        """Update vote fields."""
        result = self.client.table('votes').update(kwargs).eq('id', vote_id).execute()
        return len(result.data or []) > 0

    def end_vote(self, vote_id: int) -> bool:
        """Mark a vote as ended/inactive."""
        return self.update_vote(vote_id, is_active=False)

    # ===== VOTE OPTIONS CRUD =====
    
    def create_vote_option(self, option: VoteOption) -> VoteOption:
        """Insert a new vote option."""
        data = {
            'vote_id': option.vote_id,
            'option_text': option.option_text,
            'option_order': option.option_order,
        }
        result = self.client.table('vote_options').insert(data).execute()
        if result.data:
            option.id = result.data[0]['id']
        return option

    def get_vote_options(self, vote_id: int) -> List[VoteOption]:
        """Get all options for a vote, ordered by option_order."""
        result = self.client.table('vote_options') \
            .select('*') \
            .eq('vote_id', vote_id) \
            .order('option_order') \
            .execute()
        return [self._dict_to_option(row) for row in result.data or []]

    def delete_vote_options(self, vote_id: int) -> bool:
        """Delete all options for a vote."""
        result = self.client.table('vote_options').delete().eq('vote_id', vote_id).execute()
        return True

    # ===== VOTE SUBMISSIONS CRUD =====
    
    def create_submission(self, submission: VoteSubmission) -> VoteSubmission:
        """Insert a new encrypted vote submission."""
        data = {
            'vote_id': submission.vote_id,
            'voter_code_hash': submission.voter_code_hash,
            'encrypted_choice': submission.encrypted_choice,
            'tth_root': submission.tth_root,
        }
        result = self.client.table('vote_submissions').insert(data).execute()
        if result.data:
            submission.id = result.data[0]['id']
            submission.submitted_at = result.data[0].get('submitted_at')
        return submission

    def get_submissions_by_vote(self, vote_id: int) -> List[VoteSubmission]:
        """Get all vote submissions for a vote."""
        result = self.client.table('vote_submissions').select('*').eq('vote_id', vote_id).execute()
        return [self._dict_to_submission(row) for row in result.data or []]

    def count_submissions(self, vote_id: int) -> int:
        """Count total submissions for a vote."""
        result = self.client.table('vote_submissions').select('id', count='exact').eq('vote_id', vote_id).execute()
        return result.count or 0

    def has_voter_voted(self, vote_id: int, voter_code_hash: str) -> bool:
        """Check if a voter has already submitted a vote."""
        result = self.client.table('vote_submissions') \
            .select('id') \
            .eq('vote_id', vote_id) \
            .eq('voter_code_hash', voter_code_hash) \
            .execute()
        return len(result.data or []) > 0

    # ===== VOTER CRUD =====
    
    def create_voter(self, voter: Voter) -> Voter:
        """Create a new voter (no plaintext N2 stored)."""
        try:
            data = {
                'email': voter.email,
                'gender': voter.gender,
                'n1_code': voter.n1_code,
                'n2_hash': voter.n2_hash,
                'has_voted': voter.has_voted,
            }
            result = self.client.table('voters').insert(data).execute()
            if result.data:
                voter.id = result.data[0]['id']
                voter.created_at = result.data[0].get('created_at')
            return voter
        except Exception as e:
            # Check if it's a duplicate email error
            if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                print(f"Voter {voter.email} already exists, skipping...")
                # Return existing voter instead of failing
                existing = self.get_voter_by_email(voter.email)
                return existing if existing else voter
            raise e

    def get_voter_by_email(self, email: str) -> Optional[Voter]:
        """Get a voter by email."""
        try:
            result = self.client.table('voters').select('*').eq('email', email).single().execute()
            if result.data:
                return self._dict_to_voter(result.data)
        except Exception:
            # Voter not found or other error - return None
            pass
        return None

    def get_voter_by_code_hash(self, code_hash: str) -> Optional[Voter]:
        """Get a voter by their code hash."""
        result = self.client.table('voters').select('*').eq('code_hash', code_hash).single().execute()
        if result.data:
            return self._dict_to_voter(result.data)
        return None

    def update_voter_voted_status(self, voter_id: int, has_voted: bool = True) -> bool:
        """Update a voter's voted status."""
        result = self.client.table('voters').update({'has_voted': has_voted}).eq('id', voter_id).execute()
        return len(result.data or []) > 0

    # ===== VOTE VOTERS CRUD =====
    
    def link_voter_to_vote(self, vote_id: int, voter_email: str, n2_hash: str) -> bool:
        """Link a voter to a vote with per-vote N2 hash."""
        try:
            data = {
                'vote_id': vote_id,
                'voter_email': voter_email,
                'n2_hash': n2_hash,
                'has_voted': False,
            }
            result = self.client.table('vote_voters').insert(data).execute()
            return len(result.data or []) > 0
        except Exception:
            return False

    def get_voters_by_vote(self, vote_id: int) -> List[str]:
        """Get all voter emails linked to a vote."""
        result = self.client.table('vote_voters').select('voter_email').eq('vote_id', vote_id).execute()
        return [row['voter_email'] for row in result.data or []]

    def get_votes_by_voter(self, voter_email: str) -> List[int]:
        """Get all vote IDs linked to a voter."""
        result = self.client.table('vote_voters').select('vote_id').eq('voter_email', voter_email).execute()
        return [row['vote_id'] for row in result.data or []]

    def unlink_voter_from_vote(self, vote_id: int, voter_email: str) -> bool:
        """Unlink a voter from a vote."""
        result = self.client.table('vote_voters') \
            .delete() \
            .eq('vote_id', vote_id) \
            .eq('voter_email', voter_email) \
            .execute()
        return len(result.data or []) > 0

    def get_vote_voter(self, vote_id: int, voter_email: str):
        """Get vote_voter record for a specific vote and voter."""
        try:
            result = self.client.table('vote_voters') \
                .select('*') \
                .eq('vote_id', vote_id) \
                .eq('voter_email', voter_email) \
                .single().execute()
            if result.data:
                return self._dict_to_vote_voter(result.data)
        except Exception:
            pass
        return None

    def mark_vote_voter_as_voted(self, vote_id: int, voter_email: str) -> bool:
        """Mark a vote_voter record as having voted."""
        result = self.client.table('vote_voters') \
            .update({'has_voted': True}) \
            .eq('vote_id', vote_id) \
            .eq('voter_email', voter_email) \
            .execute()
        return len(result.data or []) > 0

    def has_voter_voted_in_vote(self, vote_id: int, voter_email: str) -> bool:
        """Check if a voter has already voted in a specific vote."""
        try:
            result = self.client.table('vote_voters') \
                .select('has_voted') \
                .eq('vote_id', vote_id) \
                .eq('voter_email', voter_email) \
                .single().execute()
            if result.data:
                return result.data.get('has_voted', False)
        except Exception:
            pass
        return False

    def create_voter(self, voter: Voter) -> Voter:
        """Create a new voter (no plaintext N2 stored)."""
        try:
            data = {
                'email': voter.email,
                'gender': voter.gender,
                'n1_code': voter.n1_code,
                'n2_hash': voter.n2_hash,
                'has_voted': voter.has_voted,
            }
            result = self.client.table('voters').insert(data).execute()
            if result.data:
                voter.id = result.data[0]['id']
                voter.created_at = result.data[0].get('created_at')
            return voter
        except Exception as e:
            # Check if it's a duplicate email error
            if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                print(f"Voter {voter.email} already exists, skipping...")
                # Return existing voter instead of failing
                existing = self.get_voter_by_email(voter.email)
                return existing if existing else voter
            raise e

    def bulk_import_voters(self, voters: List[Voter]) -> int:
        """Import multiple voters at once."""
        if not voters:
            return 0
        data = [
            {
                'email': v.email,
                'gender': v.gender,
                'n1_code': v.n1_code,
                'n2_hash': v.n2_hash,
                'has_voted': v.has_voted,
            }
            for v in voters
        ]
        result = self.client.table('voters').insert(data).execute()
        return len(result.data or [])

    # ===== CONVERTER METHODS =====
    
    def _dict_to_vote(self, row: Dict[str, Any]) -> Vote:
        """Convert database row to Vote object."""
        from datetime import datetime
        return Vote(
            id=row.get('id'),
            title=row.get('title', ''),
            description=row.get('description', ''),
            vote_type=row.get('vote_type', 'choice'),
            creator_code=row.get('creator_code', ''),
            start_date=datetime.fromisoformat(row['start_date'].replace('Z', '+00:00')) if row.get('start_date') else None,
            end_date=datetime.fromisoformat(row['end_date'].replace('Z', '+00:00')) if row.get('end_date') else None,
            is_active=row.get('is_active', True),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else None,
        )

    def _dict_to_option(self, row: Dict[str, Any]) -> VoteOption:
        """Convert database row to VoteOption object."""
        return VoteOption(
            id=row.get('id'),
            vote_id=row.get('vote_id', 0),
            option_text=row.get('option_text', ''),
            option_order=row.get('option_order', 0),
        )

    def _dict_to_submission(self, row: Dict[str, Any]) -> VoteSubmission:
        """Convert database row to VoteSubmission object."""
        from datetime import datetime
        return VoteSubmission(
            id=row.get('id'),
            vote_id=row.get('vote_id', 0),
            voter_code_hash=row.get('voter_code_hash', ''),
            encrypted_choice=row.get('encrypted_choice', ''),
            tth_root=row.get('tth_root', ''),
            submitted_at=datetime.fromisoformat(row['submitted_at'].replace('Z', '+00:00')) if row.get('submitted_at') else None,
        )

    def _dict_to_voter(self, row: Dict[str, Any]) -> Voter:
        """Convert database row to Voter object."""
        from datetime import datetime
        return Voter(
            id=row.get('id'),
            email=row.get('email', ''),
            gender=row.get('gender', ''),
            n1_code=row.get('n1_code', ''),
            n2_hash=row.get('n2_hash', ''),
            has_voted=row.get('has_voted', False),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else None,
        )

    def _dict_to_vote_voter(self, row: Dict[str, Any]):
        """Convert database row to VoteVoter object."""
        from datetime import datetime
        from .models import VoteVoter
        return VoteVoter(
            id=row.get('id'),
            vote_id=row.get('vote_id', 0),
            voter_email=row.get('voter_email', ''),
            n2_hash=row.get('n2_hash', ''),
            has_voted=row.get('has_voted', False),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else None,
        )

    # ===== ADMIN KEYS =====

    def save_admin_keys(self, keys: AdminKeys) -> AdminKeys:
        """Save Administrator RSA keys."""
        data = {
            'id': keys.id,
            'public_key_n': keys.public_key_n,
            'public_key_e': keys.public_key_e,
            'private_key_pem': keys.private_key_pem,
            'is_active': keys.is_active,
        }
        result = self.client.table('admin_keys').insert(data).execute()
        if result.data:
            keys.created_at = result.data[0].get('created_at')
        return keys

    def get_admin_keys(self) -> Optional[AdminKeys]:
        """Get Administrator keys."""
        try:
            result = self.client.table('admin_keys').select('*').eq('is_active', True).single().execute()
            if result.data:
                return self._dict_to_admin_keys(result.data)
        except Exception:
            pass
        return None

    # ===== COUNTER KEYS =====

    def save_counter_keys(self, keys: CounterKeys) -> CounterKeys:
        """Save Counter RSA keys."""
        data = {
            'id': keys.id,
            'public_key_n': keys.public_key_n,
            'public_key_e': keys.public_key_e,
            'private_key_pem': keys.private_key_pem,
            'is_active': keys.is_active,
        }
        result = self.client.table('counter_keys').insert(data).execute()
        if result.data:
            keys.created_at = result.data[0].get('created_at')
        return keys

    def get_counter_keys(self) -> Optional[CounterKeys]:
        """Get Counter keys."""
        try:
            result = self.client.table('counter_keys').select('*').eq('is_active', True).single().execute()
            if result.data:
                return self._dict_to_counter_keys(result.data)
        except Exception:
            pass
        return None

    def _dict_to_admin_keys(self, row: Dict[str, Any]) -> AdminKeys:
        """Convert database row to AdminKeys object."""
        from datetime import datetime
        return AdminKeys(
            id=row.get('id', 1),
            public_key_n=row.get('public_key_n', ''),
            public_key_e=row.get('public_key_e', 65537),
            private_key_pem=row.get('private_key_pem', ''),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else None,
            is_active=row.get('is_active', True),
        )

    def _dict_to_counter_keys(self, row: Dict[str, Any]) -> CounterKeys:
        """Convert database row to CounterKeys object."""
        from datetime import datetime
        return CounterKeys(
            id=row.get('id', 1),
            public_key_n=row.get('public_key_n', ''),
            public_key_e=row.get('public_key_e', 65537),
            private_key_pem=row.get('private_key_pem', ''),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row.get('created_at') else None,
            is_active=row.get('is_active', True),
        )
    
    # ===== ENCRYPTED BALLOTS =====

    def create_encrypted_ballot(self, ballot: EncryptedBallot) -> EncryptedBallot:
        """Create an encrypted ballot with TTH root."""
        data = {
            'vote_id': ballot.vote_id,
            'n1_code': ballot.n1_code,
            'encrypted_ballot': ballot.encrypted_ballot,
            'blind_signature': ballot.blind_signature,
            'tth_root': ballot.tth_root,
            'processed': ballot.processed,
        }
        result = self.client.table('encrypted_ballots').insert(data).execute()
        if result.data:
            ballot.id = result.data[0]['id']
            ballot.submitted_at = result.data[0].get('submitted_at')
        return ballot
    
    def get_encrypted_ballots(self, vote_id: int) -> List[EncryptedBallot]:
        """Get all encrypted ballots for a vote."""
        result = self.client.table('encrypted_ballots').select('*').eq('vote_id', vote_id).execute()
        return [self._dict_to_encrypted_ballot(row) for row in result.data]
    
    def get_unprocessed_ballots(self, vote_id: int) -> List[EncryptedBallot]:
        """Get unprocessed ballots for a vote."""
        result = self.client.table('encrypted_ballots').select('*').eq('vote_id', vote_id).eq('processed', False).execute()
        return [self._dict_to_encrypted_ballot(row) for row in result.data]
    
    def mark_ballot_processed(self, ballot_id: int) -> bool:
        """Mark a ballot as processed."""
        result = self.client.table('encrypted_ballots').update({'processed': True}).eq('id', ballot_id).execute()
        return len(result.data) > 0
    
    def mark_ballots_for_processing(self, vote_id: int) -> bool:
        """Mark all ballots for a vote as ready for processing."""
        result = self.client.table('encrypted_ballots').update({'processed': True}).eq('vote_id', vote_id).eq('processed', False).execute()
        return True
    
    def get_ballot_count(self, vote_id: int) -> int:
        """Get count of ballots for a vote."""
        result = self.client.table('encrypted_ballots').select('id', count='exact').eq('vote_id', vote_id).execute()
        return result.count or 0
    
    # ===== DECRYPTED VOTES =====
    
    def create_decrypted_vote(self, vote: DecryptedVote) -> DecryptedVote:
        """Create a decrypted vote record."""
        data = {
            'ballot_id': vote.ballot_id,
            'n2_code': vote.n2_code,
            'vote_choice': vote.vote_choice,
            'signature_valid': vote.signature_valid,
            'n2_hash_valid': vote.n2_hash_valid,
        }
        result = self.client.table('decrypted_votes').insert(data).execute()
        if result.data:
            vote.id = result.data[0]['id']
            vote.processed_at = result.data[0].get('processed_at')
        return vote
    
    def get_decrypted_votes_by_vote(self, vote_id: int) -> List[DecryptedVote]:
        """Get all decrypted votes for a specific vote."""
        # First get ballot IDs for this vote
        ballot_result = self.client.table('encrypted_ballots') \
            .select('id') \
            .eq('vote_id', vote_id) \
            .execute()
        
        if not ballot_result.data:
            return []
        
        ballot_ids = [str(row['id']) for row in ballot_result.data]
        
        # Then get decrypted votes for those ballots
        if ballot_ids:
            result = self.client.table('decrypted_votes') \
                .select('*') \
                .in_('ballot_id', ballot_ids) \
                .execute()
            return [self._dict_to_decrypted_vote(row) for row in result.data]
        else:
            return []
    
    def get_valid_decrypted_votes(self, vote_id: int) -> List[DecryptedVote]:
        """Get all valid decrypted votes for a vote."""
        # First get ballot IDs for this vote
        ballot_result = self.client.table('encrypted_ballots') \
            .select('id') \
            .eq('vote_id', vote_id) \
            .execute()
        
        if not ballot_result.data:
            return []
        
        ballot_ids = [str(row['id']) for row in ballot_result.data]
        
        # Then get valid decrypted votes for those ballots
        if ballot_ids:
            result = self.client.table('decrypted_votes') \
                .select('*') \
                .in_('ballot_id', ballot_ids) \
                .eq('signature_valid', True) \
                .eq('n2_hash_valid', True) \
                .execute()
            return [self._dict_to_decrypted_vote(row) for row in result.data]
        else:
            return []
    
    # ===== VOTER OPERATIONS =====
    
    def get_voter_by_n1(self, n1_code: str) -> Optional[Voter]:
        """Get voter by N1 code."""
        try:
            result = self.client.table('voters').select('*').eq('n1_code', n1_code).single().execute()
            if result.data:
                return self._dict_to_voter(result.data)
        except Exception:
            # Voter not found or other error
            pass
        return None
    
    def get_voter_by_n2_hash(self, n2_hash: str) -> Optional[Voter]:
        """Get voter by N2 hash."""
        try:
            result = self.client.table('voters').select('*').eq('n2_hash', n2_hash).single().execute()
            if result.data:
                return self._dict_to_voter(result.data)
        except Exception:
            # Voter not found or other error
            pass
        return None
    
    def mark_voter_voted(self, n1_code: str) -> bool:
        """Mark voter as having voted."""
        result = self.client.table('voters').update({'has_voted': True}).eq('n1_code', n1_code).execute()
        return len(result.data) > 0
    
    def update_voter_codes(self, voter_id: int, n1_code: str, n2_hash: str) -> bool:
        """Update voter codes for an existing voter (N2 is hash only)."""
        data = {
            'n1_code': n1_code,
            'n2_hash': n2_hash,
            'has_voted': False
        }
        result = self.client.table('voters').update(data).eq('id', voter_id).execute()
        return len(result.data or []) > 0
    
    def get_all_voters(self) -> List[Voter]:
        """Get all voters."""
        result = self.client.table('voters').select('*').execute()
        return [self._dict_to_voter(row) for row in result.data]
    
    # ===== AUDIT TRAIL =====
    
    def get_audit_trail(self, vote_id: int) -> List[Dict[str, Any]]:
        """Get audit trail for a vote."""
        # This would join encrypted_ballots and decrypted_votes
        # Simplified for now
        result = self.client.table('decrypted_votes') \
            .select('*, encrypted_ballots(*)') \
            .eq('ballot_id', 'in', f"(SELECT id FROM encrypted_ballots WHERE vote_id = {vote_id})") \
            .execute()
        return result.data
    
    # ===== CONVERTER METHODS =====
    
    def _dict_to_server_keys(self, row: Dict[str, Any]):
        """Legacy converter - not used with new schema."""
        return None
    
    def _dict_to_encrypted_ballot(self, row: Dict[str, Any]) -> EncryptedBallot:
        """Convert database row to EncryptedBallot object."""
        from datetime import datetime
        return EncryptedBallot(
            id=row.get('id'),
            vote_id=row.get('vote_id', 0),
            n1_code=row.get('n1_code', ''),
            encrypted_ballot=row.get('encrypted_ballot', ''),
            blind_signature=row.get('blind_signature', ''),
            tth_root=row.get('tth_root', ''),
            submitted_at=datetime.fromisoformat(row['submitted_at'].replace('Z', '+00:00')) if row.get('submitted_at') else None,
            processed=row.get('processed', False),
        )
    
    def _dict_to_decrypted_vote(self, row: Dict[str, Any]) -> DecryptedVote:
        """Convert database row to DecryptedVote object."""
        from datetime import datetime
        return DecryptedVote(
            id=row.get('id'),
            ballot_id=row.get('ballot_id', 0),
            n2_code=row.get('n2_code', ''),
            vote_choice=row.get('vote_choice', ''),
            signature_valid=row.get('signature_valid', False),
            n2_hash_valid=row.get('n2_hash_valid', False),
            processed_at=datetime.fromisoformat(row['processed_at'].replace('Z', '+00:00')) if row.get('processed_at') else None,
        )
