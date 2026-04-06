"""Voting Protocol - Main orchestrator."""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from database.models import Vote, Voter, VoteOption, EncryptedBallot
from database.queries import VoteQueries
from .creator import VoteCreator
from .commissioner import Commissioner
from .administrator import Administrator
from .anonymizer import Anonymizer
from .counter import Counter
from .config import CODE_LENGTH, CHAR_SET
import random
import string


class VotingProtocol:
    """Main orchestrator for the blind signature voting protocol."""
    
    def __init__(self, queries: VoteQueries):
        self.queries = queries
        self.creator = VoteCreator()
        self.commissioner = Commissioner()
        self.administrator = Administrator()
        self.anonymizer = Anonymizer()
        self.counter = Counter()
        
        # Load admin keys
        admin_keys = self.queries.get_admin_keys()
        if admin_keys:
            key_parts = admin_keys.private_key_pem.split(':')
            if len(key_parts) >= 3:
                n = int(key_parts[0])
                e = int(key_parts[1])
                d = int(key_parts[2])
                self.administrator.set_keys(n, e, d)
        else:
            # Generate new keys
            n, e, d = self.administrator.generate_keys(key_size=1024)
            from database.models import AdminKeys
            admin_keys = AdminKeys(
                id=1,
                public_key_n=str(n),
                public_key_e=e,
                private_key_pem=f"{n}:{e}:{d}",
                is_active=True
            )
            self.queries.save_admin_keys(admin_keys)
        
        # Load counter keys
        counter_keys = self.queries.get_counter_keys()
        if counter_keys:
            key_parts = counter_keys.private_key_pem.split(':')
            if len(key_parts) >= 3:
                n = int(key_parts[0])
                e = int(key_parts[1])
                d = int(key_parts[2])
                self.counter.set_keys(n, e, d)
        else:
            # Generate new counter keys
            temp_key_gen = Administrator()
            n, e, d = temp_key_gen.generate_keys(key_size=1024)
            from database.models import CounterKeys
            counter_keys = CounterKeys(
                id=1,
                public_key_n=str(n),
                public_key_e=e,
                private_key_pem=f"{n}:{e}:{d}",
                is_active=True
            )
            self.queries.save_counter_keys(counter_keys)
            self.counter.set_keys(n, e, d)
    
    def _generate_code(self) -> str:
        """Generate a random 12-character code."""
        return ''.join(random.choices(CHAR_SET, k=CODE_LENGTH))
    
    def _register_voter_and_send_email(self, email: str, vote_id: int) -> Tuple[bool, str, str]:
        """Register voter and send codes via email."""
        n1_code = self._generate_code()
        n2_code = self._generate_code()
        n2_hash = self.commissioner.generate_n2_hash(n2_code)
        
        existing_voter = self.queries.get_voter_by_email(email)
        if existing_voter:
            voter = existing_voter
            self.queries.update_voter_codes(voter.id, n1_code, n2_hash)
            voter.n1_code = n1_code
            voter.n2_hash = n2_hash
        else:
            voter = Voter(
                email=email,
                n1_code=n1_code,
                n2_hash=n2_hash
            )
            voter = self.queries.create_voter(voter)
        
        if not voter or not voter.id:
            return False, "", ""
        
        try:
            from mailer.sender import send_voter_codes_email
            vote = self.queries.get_vote_by_id(vote_id)
            vote_title = vote.title if vote else "Unknown Vote"
            
            success = send_voter_codes_email(
                recipient_email=email,
                n1_code=n1_code,
                n2_code=n2_code,
                vote_title=vote_title,
                vote_id=vote_id
            )
            return success, n1_code, n2_hash
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            return False, "", ""
    
    def create_vote_with_voters(self, vote_data: Dict[str, Any], voter_emails: List[str]) -> Tuple[Optional[Vote], Optional[str]]:
        """Create vote and register voters."""
        from datetime import datetime
        
        vote = Vote(
            title=vote_data.get('title', ''),
            description=vote_data.get('description', ''),
            vote_type=vote_data.get('vote_type', 'choice'),
            creator_code=vote_data.get('creator_code', ''),
            is_active=True,
            end_date=vote_data.get('end_date')
        )
        
        vote = self.queries.create_vote(vote)
        if not vote or not vote.id:
            return None, "Failed to create vote"
        
        # Create options for choice votes
        if vote.vote_type == 'choice':
            options = vote_data.get('options', [])
            for i, option_text in enumerate(options):
                vote_option = VoteOption(
                    vote_id=vote.id,
                    option_text=option_text,
                    option_order=i + 1
                )
                self.queries.create_vote_option(vote_option)
        
        # Register voters
        for email in voter_emails:
            success, n1_code, n2_hash = self._register_voter_and_send_email(email, vote.id)
            if success:
                self.queries.link_voter_to_vote(vote.id, email, n2_hash)
        
        return vote, None
    
    def submit_vote(self, n1_code: str, n2_code: str, vote_id: int, vote_choice: str) -> Tuple[bool, Optional[str]]:
        """Submit vote with blind signature protocol."""
        voter = self.queries.get_voter_by_n1(n1_code)
        if not voter:
            return False, "Invalid N1 code (voter ID)"
        
        vote_voter = self.queries.get_vote_voter(vote_id, voter.email)
        if not vote_voter:
            return False, "You are not registered for this vote"
        
        n2_hash_computed = self.commissioner.generate_n2_hash(n2_code)
        if n2_hash_computed != vote_voter.n2_hash:
            return False, "Invalid N2 code (ballot ID)"
        
        if vote_voter.has_voted:
            return False, "You have already voted in this election"
        
        existing_ballots = self.queries.get_encrypted_ballots(vote_id)
        for ballot in existing_ballots:
            if ballot.n1_code == n1_code:
                return False, "A vote has already been submitted with this N1 code"
        
        import secrets
        random_bits = secrets.token_hex(8)
        ballot_message = f"{vote_choice}:{n2_code}:{random_bits}"
        
        tth_root = self.commissioner.generate_n2_hash(ballot_message)
        
        blind_signature = self.administrator.blind_sign(ballot_message)
        if not blind_signature:
            return False, "Failed to obtain blind signature"
        
        ballot_data = f"{ballot_message}:{blind_signature}"
        
        counter_keys = self.queries.get_counter_keys()
        if not counter_keys:
            return False, "Counter keys not found"
        
        encrypted_ballot = self.anonymizer.encrypt_ballot(ballot_data, counter_keys.public_key_n)
        if not encrypted_ballot:
            return False, "Failed to encrypt ballot"
        
        from database.models import EncryptedBallot
        encrypted_ballot_record = EncryptedBallot(
            vote_id=vote_id,
            n1_code=n1_code,
            encrypted_ballot=encrypted_ballot,
            blind_signature=blind_signature,
            tth_root=tth_root,
            processed=False
        )
        
        stored_ballot = self.queries.create_encrypted_ballot(encrypted_ballot_record)
        if not stored_ballot:
            return False, "Failed to store ballot"
        
        self.queries.mark_vote_voter_as_voted(vote_id, voter.email)
        
        try:
            from mailer.sender import send_vote_confirmation_email
            send_vote_confirmation_email(voter.email, vote_id)
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
        
        return True, None
    
    def get_vote_results(self, vote_id: int) -> Dict[str, Any]:
        """Get results for a specific vote."""
        vote = self.queries.get_vote_by_id(vote_id)
        if not vote:
            return {"error": "Vote not found"}
        
        decrypted_votes = self.queries.get_decrypted_votes_by_vote(vote_id)
        
        option_map = {}
        if vote.vote_type == 'choice':
            options = self.queries.get_vote_options(vote_id)
            for opt in options:
                option_map[str(opt.id)] = opt.option_text
        
        results = {}
        total_votes = 0
        
        for dv in decrypted_votes:
            if dv.signature_valid and dv.n2_hash_valid:
                choice = dv.vote_choice
                if vote.vote_type == 'choice' and choice in option_map:
                    display_choice = option_map[choice]
                else:
                    display_choice = choice
                results[display_choice] = results.get(display_choice, 0) + 1
                total_votes += 1
        
        formatted_results = []
        for choice, count in results.items():
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            formatted_results.append({
                "option": choice,
                "count": count,
                "percentage": round(percentage, 1)
            })
        
        return {
            "vote_id": vote_id,
            "vote_title": vote.title,
            "vote_type": vote.vote_type,
            "total_votes": total_votes,
            "results": formatted_results
        }
    
    def decrypt_and_process_ballots(self, vote_id: int) -> bool:
        """Decrypt ballots and store results."""
        try:
            encrypted_ballots = self.queries.get_encrypted_ballots(vote_id)
            
            for ballot in encrypted_ballots:
                if ballot.processed:
                    continue
                
                decrypted_data = self.counter.decrypt_ballot(ballot.encrypted_ballot)
                if not decrypted_data:
                    print(f"Failed to decrypt ballot {ballot.id}")
                    continue
                
                parts = decrypted_data.split(':')
                if len(parts) < 4:
                    print(f"Invalid format: {decrypted_data}")
                    continue
                
                vote_choice = parts[0]
                n2_code = parts[1]
                random_bits = parts[2]
                signature = parts[3]
                
                ballot_message = f"{vote_choice}:{n2_code}:{random_bits}"
                
                signature_valid = self.administrator.verify_signature(ballot_message, signature)
                
                tth_computed = self.commissioner.generate_n2_hash(ballot_message)
                tth_valid = (tth_computed == ballot.tth_root)
                
                voter = self.queries.get_voter_by_n1(ballot.n1_code)
                n2_hash_valid = False
                if voter:
                    vote_voter = self.queries.get_vote_voter(vote_id, voter.email)
                    if vote_voter:
                        n2_hash_computed = self.commissioner.generate_n2_hash(n2_code)
                        n2_hash_valid = (n2_hash_computed == vote_voter.n2_hash)
                
                if signature_valid and tth_valid and n2_hash_valid:
                    from database.models import DecryptedVote
                    decrypted_vote = DecryptedVote(
                        ballot_id=ballot.id,
                        n2_code=n2_code,
                        vote_choice=vote_choice,
                        signature_valid=signature_valid,
                        n2_hash_valid=n2_hash_valid
                    )
                    self.queries.create_decrypted_vote(decrypted_vote)
                    self.queries.mark_ballot_processed(ballot.id)
                else:
                    print(f"Invalid ballot {ballot.id}: sig={signature_valid}, tth={tth_valid}, n2={n2_hash_valid}")
            
            print(f"Processed ballots for vote {vote_id}")
            return True
        except Exception as e:
            print(f"Error processing ballots: {e}")
            return False
