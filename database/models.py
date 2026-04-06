"""Data models for the voting system."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Vote:
    """Vote model."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    vote_type: str = "choice"  # 'choice' or 'rating'
    creator_code: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class VoteOption:
    """Vote option model."""
    id: Optional[int] = None
    vote_id: int = 0
    option_text: str = ""
    option_order: int = 0


@dataclass
class Voter:
    """Voter model with N1 code only (no plaintext N2 stored)."""
    id: Optional[int] = None
    email: str = ""
    gender: str = ""
    n1_code: str = ""  # 12-character voter ID (plaintext, for Commissioner)
    n2_hash: str = ""  # TTH hash of N2 (never store plaintext N2)
    has_voted: bool = False
    created_at: Optional[datetime] = None


@dataclass
class VoteVoter:
    """Vote-Voter junction model with per-vote N2 hash."""
    id: Optional[int] = None
    vote_id: int = 0
    voter_email: str = ""
    n2_hash: str = ""  # Per-vote N2 hash (N2 code delivered to voter)
    has_voted: bool = False
    created_at: Optional[datetime] = None


@dataclass
class AdminKeys:
    """Administrator RSA keys model."""
    id: int = 1
    public_key_n: str = ""
    public_key_e: int = 65537
    private_key_pem: str = ""  # PEM format includes d, p, q
    created_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class CounterKeys:
    """Counter RSA keys model."""
    id: int = 1
    public_key_n: str = ""
    public_key_e: int = 65537
    private_key_pem: str = ""  # PEM format includes d, p, q
    created_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class EncryptedBallot:
    """Encrypted ballot model with TTH root."""
    id: Optional[int] = None
    vote_id: int = 0
    n1_code: str = ""  # For double-voting check
    encrypted_ballot: str = ""  # Encrypted with Counter's public key
    blind_signature: str = ""  # Unblinded Administrator signature
    tth_root: str = ""  # TTH of (choice + N2 + random bits)
    submitted_at: Optional[datetime] = None
    processed: bool = False


@dataclass
class DecryptedVote:
    """Decrypted vote model."""
    id: Optional[int] = None
    ballot_id: int = 0
    n2_code: str = ""
    vote_choice: str = ""
    signature_valid: bool = False
    n2_hash_valid: bool = False
    processed_at: Optional[datetime] = None


@dataclass
class VoteSubmission:
    """Legacy vote submission model (for compatibility)."""
    id: Optional[int] = None
    vote_id: int = 0
    voter_code_hash: str = ""
    encrypted_choice: str = ""
    tth_root: str = ""
    submitted_at: Optional[datetime] = None
    has_voted: bool = False
