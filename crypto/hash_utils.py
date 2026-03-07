
import hashlib

# Generate SHA-256 hash of a value (used for N2 code hashing)
def hash_value_sha256(value: str) -> str:
    
    value_bytes = value.encode('utf-8')  
    hash_object = hashlib.sha256(value_bytes)  
    hex_dig = hash_object.hexdigest()  
    return hex_dig  

#implements a simple toy tetragraph hash (TTH) for demonstration purposes. It creates a hash based on character values and their positions in the string. This is not a secure hash function but serves as an example for generating fingerprints for N2 codes.
def hash_value_tth(value: str) -> str:
    
    value = value.replace(" ", "").upper()  
    result = 0
    for i, c in enumerate(value):
        if c.isalpha():  
            num = ord(c) - ord('A') + 1  
        elif c.isdigit():
            num = int(c)  
        else:
            num = 0  
        result += num * (i+1)  
    return hex(result)[2:]  