
def str_to_int(s: str) -> int:
    return int.from_bytes(s.encode('utf-8'), 'big')

def int_to_str(n: int) -> str:
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode('utf-8')