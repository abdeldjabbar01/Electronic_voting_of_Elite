
import random
from config import CODE_LENGTH, CHAR_SET

def generate_code():
    return ''.join(random.choices(CHAR_SET, k=CODE_LENGTH))

def generate_voter_codes():
    return generate_code(), generate_code()