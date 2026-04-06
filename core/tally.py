"""Business logic for tallying vote results."""
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives import serialization

from database.models import Vote, VoteOption, VoteSubmission
from database.queries import VoteQueries
from crypto.rsa_utils import decrypt_message
from crypto.utils import hash_code
from crypto.tth import verify_tth
from core.creator import VoteCreator


class VoteTally:
    """Handles computation of vote results."""

    def __init__(self, queries: VoteQueries = None):
        self.queries = queries or VoteQueries()

    def get_results(
        self,
        vote_id: int,
        private_key_pem: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Get decrypted vote results for a vote.
        
        Args:
            vote_id: The ID of the vote
            private_key_pem: The private key PEM string for decryption
        
        Returns:
            Tuple of (results dict, error message)
        """
        # Get vote and verify it exists
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return None, "Vote not found."
        
        # Load private key
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
        except Exception as ex:
            return None, f"Invalid private key: {str(ex)}"
        
        # Get all submissions and options
        submissions = self.queries.get_submissions_by_vote(vote_id)
        options = self.queries.get_vote_options(vote_id)
        
        if not submissions:
            return {
                "vote_id": vote_id,
                "title": vote.title,
                "total_votes": 0,
                "results": {opt.option_text: 0 for opt in options},
                "is_final": not vote.is_active
            }, None
        
        # Initialize results
        results = defaultdict(int)
        invalid_votes = 0
        
        # Decrypt each vote
        for submission in submissions:
            try:
                decrypted_choice = decrypt_message(submission.encrypted_choice, private_key)
                results[decrypted_choice] += 1
            except Exception:
                invalid_votes += 1
        
        # Build result dictionary
        option_results = {}
        for opt in options:
            option_results[opt.option_text] = results.get(opt.option_text, 0)
        
        return {
            "vote_id": vote_id,
            "title": vote.title,
            "description": vote.description,
            "total_votes": len(submissions),
            "valid_votes": len(submissions) - invalid_votes,
            "invalid_votes": invalid_votes,
            "results": option_results,
            "is_final": not vote.is_active
        }, None

    def get_tally_for_creator(
        self,
        vote_id: int,
        creator_code: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Get tally results using creator code.
        
        In a real implementation, this would look up the private key
        stored securely against the creator code.
        
        Args:
            vote_id: The ID of the vote
            creator_code: The creator code
        
        Returns:
            Tuple of (results dict, error message)
        """
        # Verify creator code
        creator = VoteCreator(self.queries)
        
        if not creator.verify_creator_code(vote_id, creator_code):
            return None, "Invalid creator code."
        
        # In a production system, the private key would be retrieved
        # from secure storage using the creator code hash
        # For now, this requires the private key to be passed separately
        return None, "Private key required for decryption. Use get_results() with private key."

    def verify_submission_integrity(
        self,
        submission: VoteSubmission
    ) -> bool:
        """Verify the integrity of a vote submission using TTH.
        
        Args:
            submission: The vote submission to verify
        
        Returns:
            True if integrity is verified
        """
        # Reconstruct the data that was hashed
        vote_data = f"{submission.vote_id}:{submission.voter_code_hash}:{submission.encrypted_choice}"
        
        return verify_tth(vote_data.encode('utf-8'), submission.tth_root)

    def get_vote_statistics(self, vote_id: int) -> Dict:
        """Get general statistics about a vote.
        
        Args:
            vote_id: The ID of the vote
        
        Returns:
            Dictionary with vote statistics
        """
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return {"exists": False}
        
        submissions = self.queries.get_submissions_by_vote(vote_id)
        
        # Check integrity of all submissions
        integrity_passed = 0
        integrity_failed = 0
        
        for sub in submissions:
            if self.verify_submission_integrity(sub):
                integrity_passed += 1
            else:
                integrity_failed += 1
        
        return {
            "exists": True,
            "vote_id": vote_id,
            "title": vote.title,
            "is_active": vote.is_active,
            "total_submissions": len(submissions),
            "integrity_passed": integrity_passed,
            "integrity_failed": integrity_failed,
            "start_date": vote.start_date,
            "end_date": vote.end_date
        }
