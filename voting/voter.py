# voter.py
# Purpose: Represent a voter in the system
# Functionality:
#   - Enter N1 and N2 codes
#   - Prepare ballot message
#   - Apply masking for blind signature
# What it does:
#   - Uses crypto/blind_signature.py and hash_utils.py
# Returns:
#   - Signed ballot ready for anonymizer
# Notes:
#   - Contributors implement voter interface and communication logic