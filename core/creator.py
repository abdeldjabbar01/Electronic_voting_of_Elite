"""Business logic for creating new votes."""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from database.models import Vote, VoteOption, Voter
from database.queries import VoteQueries
from crypto.rsa_utils import generate_rsa_keys, serialize_public_key
from crypto.code_generator import generate_creator_code
from crypto.utils import hash_code


class VoteCreator:
    """Handles creation of new voting events."""

    def __init__(self, queries: VoteQueries = None):
        self.queries = queries or VoteQueries()

    def create_vote(
        self,
        title: str,
        description: str,
        options: List[str],
        creator_email: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        duration_days: int = 7
    ) -> Tuple[Optional[Vote], Optional[str], Optional[str]]:
        """Create a new voting event.
        
        Args:
            title: Title of the vote
            description: Description of the vote
            options: List of voting options
            creator_email: Email of the vote creator
            start_date: When voting starts (default: now)
            end_date: When voting ends (default: start + duration_days)
            duration_days: Default duration if end_date not specified
        
        Returns:
            Tuple of (Vote object, creator code, error message)
        """
        # Validate inputs
        if not title or len(title.strip()) < 3:
            return None, None, "Title must be at least 3 characters."
        
        if not options or len(options) < 2:
            return None, None, "At least 2 options are required."
        
        if len(options) > 10:
            return None, None, "Maximum 10 options allowed."
        
        # Set default dates
        if start_date is None:
            start_date = datetime.utcnow()
        
        if end_date is None:
            end_date = start_date + timedelta(days=duration_days)
        
        if end_date <= start_date:
            return None, None, "End date must be after start date."
        
        # Generate creator code
        creator_code = generate_creator_code()
        creator_code_hash = hash_code(creator_code)
        
        # Generate RSA keys for this vote
        key_pair = generate_rsa_keys()
        n, e = serialize_public_key(key_pair.public_key)
        
        # Store private key securely (in production, this should be stored encrypted)
        # For now, we'll return it to the creator
        private_key_pem = key_pair.get_private_pem()
        
        # Create vote record
        vote = Vote(
            title=title.strip(),
            description=description.strip() if description else "",
            vote_type="choice",  # Default to choice vote
            creator_code=creator_code_hash,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        try:
            vote = self.queries.create_vote(vote)
        except Exception as ex:
            return None, None, f"Failed to create vote: {str(ex)}"
        
        # Create vote options
        for i, option_text in enumerate(options):
            option = VoteOption(
                vote_id=vote.id,
                option_text=option_text.strip(),
                option_order=i + 1
            )
            try:
                self.queries.create_vote_option(option)
            except Exception as ex:
                # Rollback - delete the vote and options created so far
                # In production, use transactions
                return None, None, f"Failed to create option: {str(ex)}"
        
        # Return vote, creator code (plaintext), and private key
        return vote, creator_code, private_key_pem

    def verify_creator_code(self, vote_id: int, creator_code: str) -> bool:
        """Verify if a creator code is valid for a vote.
        
        Args:
            vote_id: The ID of the vote
            creator_code: The creator code to verify
        
        Returns:
            True if valid, False otherwise
        """
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return False
        
        code_hash = hash_code(creator_code)
        return vote.creator_code == code_hash

    def end_vote_early(self, vote_id: int, creator_code: str) -> Tuple[bool, Optional[str]]:
        """End a vote early using the creator code.
        
        Args:
            vote_id: The ID of the vote
            creator_code: The creator code
        
        Returns:
            Tuple of (success, error message)
        """
        if not self.verify_creator_code(vote_id, creator_code):
            return False, "Invalid creator code."
        
        try:
            self.queries.end_vote(vote_id)
            return True, None
        except Exception as ex:
            return False, f"Failed to end vote: {str(ex)}"
