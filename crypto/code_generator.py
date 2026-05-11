"""Code generation utilities for voter and creator codes."""
import secrets
import string
from typing import Final

from constants import CODE_LENGTH, CHAR_SET


def generate_random_string(length: int = CODE_LENGTH, charset: str = None) -> str:
    """Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string to generate
        charset: Character set to use (defaults to CODE_LENGTH and CHAR_SET from config)
    
    Returns:
        A secure random string
    """
    if charset is None:
        charset = CHAR_SET
    return ''.join(secrets.choice(charset) for _ in range(length))


def generate_voter_code() -> str:
    """Generate a unique voter code.
    
    Format: VOT-XXXX-XXXX-XXXX (16 chars excluding dashes)
    
    Returns:
        A unique voter code string
    """
    code = generate_random_string(12, string.ascii_uppercase + string.digits)
    return f"VOT-{code[:4]}-{code[4:8]}-{code[8:12]}"


def generate_creator_code() -> str:
    """Generate a unique creator/admin code.
    
    Format: ADM-XXXX-XXXX-XXXX (16 chars excluding dashes)
    
    Returns:
        A unique creator code string
    """
    code = generate_random_string(12, string.ascii_uppercase + string.digits)
    return f"ADM-{code[:4]}-{code[4:8]}-{code[8:12]}"
