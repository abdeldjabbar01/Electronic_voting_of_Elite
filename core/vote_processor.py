"""Business logic for processing vote submissions."""
from datetime import datetime
from typing import Optional, Dict

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from database.models import VoteSubmission
from database.queries import VoteQueries
from crypto.rsa_utils import deserialize_public_key, encrypt_message
from crypto.tth import compute_tth_root
from crypto.utils import hash_code


class VoteProcessor:
    """Handles vote submission processing."""

    def __init__(self, queries: VoteQueries = None):
        self.queries = queries or VoteQueries()

    def validate_voter_code(self, vote_id: int, voter_code: str) -> tuple[bool, Optional[str]]:
        """Validate a voter code for a specific vote.
        
        Args:
            vote_id: The ID of the vote
            voter_code: The voter's unique code
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Hash the voter code
        code_hash = hash_code(voter_code)
        
        # Check if voter exists in system
        voter = self.queries.get_voter_by_code_hash(code_hash)
        if not voter:
            return False, "Invalid voter code."
        
        # Check if voter already voted for this vote
        if self.queries.has_voter_voted(vote_id, code_hash):
            return False, "You have already submitted your vote."
        
        return True, None

    def process_vote(
        self,
        vote_id: int,
        voter_code: str,
        choice: str,
        public_key_n: str,
        public_key_e: int = 65537
    ) -> tuple[bool, Optional[str]]:
        """Process a vote submission.
        
        Args:
            vote_id: The ID of the vote
            voter_code: The voter's unique code
            choice: The selected option (encrypted before storage)
            public_key_n: RSA modulus for encryption
            public_key_e: RSA public exponent (default 65537)
        
        Returns:
            Tuple of (success, error_message)
        """
        # Validate voter code
        is_valid, error = self.validate_voter_code(vote_id, voter_code)
        if not is_valid:
            return False, error
        
        # Check vote is still active
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return False, "Vote not found."
        
        if not vote.is_active:
            return False, "This vote has ended."
        
        now = datetime.utcnow()
        if vote.start_date and now < vote.start_date:
            return False, "This vote has not started yet."
        
        if vote.end_date and now > vote.end_date:
            return False, "This vote has ended."
        
        # Encrypt the vote choice
        try:
            public_key = deserialize_public_key(int(public_key_n), public_key_e)
            encrypted_choice = encrypt_message(choice, public_key)
        except Exception as e:
            return False, f"Encryption failed: {str(e)}"
        
        # Compute TTH for voter code + vote data
        vote_data = f"{vote_id}:{voter_code}:{choice}:{datetime.utcnow().isoformat()}"
        tth_root = compute_tth_root(vote_data.encode('utf-8'))
        
        # Create submission
        code_hash = hash_code(voter_code)
        submission = VoteSubmission(
            vote_id=vote_id,
            voter_code_hash=code_hash,
            encrypted_choice=encrypted_choice,
            tth_root=tth_root
        )
        
        # Save submission
        try:
            self.queries.create_submission(submission)
        except Exception as e:
            return False, f"Failed to save vote: {str(e)}"
        
        return True, None

    def get_vote_status(self, vote_id: int) -> Dict:
        """Get current status of a vote.
        
        Args:
            vote_id: The ID of the vote
        
        Returns:
            Dictionary with vote status information
        """
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return {"exists": False}
        
        submission_count = self.queries.count_submissions(vote_id)
        
        now = datetime.utcnow()
        status = "unknown"
        if not vote.is_active:
            status = "ended"
        elif now < vote.start_date:
            status = "upcoming"
        elif now > vote.end_date:
            status = "ended"
        else:
            status = "active"
        
        return {
            "exists": True,
            "status": status,
            "title": vote.title,
            "submission_count": submission_count,
            "start_date": vote.start_date,
            "end_date": vote.end_date,
            "is_active": vote.is_active
        }
