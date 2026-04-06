# constants.py
import string

# Code generation settings
CODE_LENGTH = 16
CHAR_SET = string.ascii_uppercase + string.ascii_lowercase + string.digits

# RSA encryption settings
RSA_KEY_SIZE = 2048  # bits

# Tiger Tree Hash settings
TTH_BLOCK_SIZE = 1024  # bytes

# Application settings
MAX_VOTE_OPTIONS = 10
MIN_VOTE_OPTIONS = 2
VOTE_CODE_EXPIRY_DAYS = 30

# Database settings
DATABASE_TIMEOUT = 30  # seconds

# Email settings
EMAIL_TEMPLATES_DIR = 'mailer/templates'

# Security settings
ALLOWED_VOTE_EMAIL_DOMAINS = []  # Empty = allow all domains