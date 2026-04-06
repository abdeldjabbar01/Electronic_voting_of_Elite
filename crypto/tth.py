"""Tiger Tree Hash (TTH) implementation.

Tiger Tree Hash is a Merkle tree hash based on the Tiger hash algorithm.
It's used for file integrity checking and is particularly useful for
large files as it allows verification of individual chunks.

For this voting system, we use a simplified TTH implementation for
code integrity verification.
"""
import hashlib
import base64
from typing import List, Optional

from constants import TTH_BLOCK_SIZE


def _compute_tiger_hash(data: bytes) -> bytes:
    """Compute a Tiger-like hash using SHA-256 (since tiger isn't available in stdlib).
    
    In a real implementation, you would use the actual Tiger algorithm.
    For educational purposes, we use SHA-256 with a prefix to simulate Tiger.
    
    Args:
        data: Bytes to hash
    
    Returns:
        24-byte hash digest (Tiger produces 192-bit/24-byte hashes)
    """
    # Use SHA-256 and truncate to 24 bytes (192 bits like Tiger)
    hasher = hashlib.sha256()
    hasher.update(b'TIGER:' + data)  # Prefix to differentiate
    return hasher.digest()[:24]


def compute_tth(data: bytes, block_size: int = None) -> List[bytes]:
    """Compute Tiger Tree Hash for data.
    
    Splits data into blocks, hashes each block, then builds a Merkle tree.
    
    Args:
        data: The data to hash
        block_size: Size of each block (default from config)
    
    Returns:
        List of hash values at each level of the tree
    """
    if block_size is None:
        block_size = TTH_BLOCK_SIZE
    
    if not data:
        return [_compute_tiger_hash(b'')]
    
    # Split into blocks
    blocks = [data[i:i + block_size] for i in range(0, len(data), block_size)]
    
    # Compute leaf hashes
    level = [_compute_tiger_hash(block) for block in blocks]
    tree_levels = [level.copy()]
    
    # Build tree upwards
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                # Combine two hashes
                combined = level[i] + level[i + 1]
                next_level.append(_compute_tiger_hash(combined))
            else:
                # Odd node - promote to next level
                next_level.append(level[i])
        level = next_level
        tree_levels.append(level)
    
    return tree_levels


def compute_tth_root(data: bytes, block_size: int = None) -> str:
    """Compute the TTH root hash for data.
    
    This is the Merkle root that can be used to verify data integrity.
    
    Args:
        data: The data to hash
        block_size: Size of each block (default from config)
    
    Returns:
        Base64-encoded root hash string
    """
    tree_levels = compute_tth(data, block_size)
    if tree_levels and tree_levels[-1]:
        root_hash = tree_levels[-1][0]
        return base64.b64encode(root_hash).decode('utf-8')
    return base64.b64encode(_compute_tiger_hash(data)).decode('utf-8')


def verify_tth(data: bytes, expected_root: str, block_size: int = None) -> bool:
    """Verify data against a TTH root hash.
    
    Args:
        data: The data to verify
        expected_root: Base64-encoded expected root hash
        block_size: Size of each block (default from config)
    
    Returns:
        True if data matches the expected hash
    """
    computed_root = compute_tth_root(data, block_size)
    return computed_root == expected_root


def compute_tth_from_chunks(chunks: List[bytes]) -> str:
    """Compute TTH root from pre-computed chunk hashes.
    
    This is useful when you have the leaf hashes and want to verify
    the tree structure.
    
    Args:
        chunks: List of data chunks
    
    Returns:
        Base64-encoded root hash string
    """
    if not chunks:
        return base64.b64encode(_compute_tiger_hash(b'')).decode('utf-8')
    
    # Compute leaf hashes
    level = [_compute_tiger_hash(chunk) for chunk in chunks]
    
    # Build tree
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                combined = level[i] + level[i + 1]
                next_level.append(_compute_tiger_hash(combined))
            else:
                next_level.append(level[i])
        level = next_level
    
    return base64.b64encode(level[0]).decode('utf-8')
