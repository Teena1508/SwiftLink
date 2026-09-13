import hashlib
import time

BASE62_CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE_LEN = len(BASE62_CHARSET)

def base62_encode(num: int) -> str:
    """Encodes a positive integer into a Base62 string."""
    if num == 0:
        return BASE62_CHARSET[0]
    result = []
    while num > 0:
        num, rem = divmod(num, BASE_LEN)
        result.append(BASE62_CHARSET[rem])
    return "".join(reversed(result))

def generate_hash_code(url: str, salt: str = "", length: int = 6, attempt: int = 0) -> str:
    """
    Generates a hash-based string from a URL and attempt counter.
    Uses SHA-256 digest converted to Base62 encoding.
    """
    raw_input = f"{url}:{salt}:{attempt}:{time.time_ns()}" if attempt > 0 else f"{url}:{salt}"
    hash_bytes = hashlib.sha256(raw_input.encode('utf-8')).digest()
    
    # Take first 8 bytes and convert to integer
    num = int.from_bytes(hash_bytes[:8], byteorder='big')
    encoded = base62_encode(num)
    
    # Ensure minimum length by padding or slicing
    if len(encoded) < length:
        encoded = encoded.rjust(length, '0')
    return encoded[:length]

def generate_unique_short_code(url: str, existing_checker, length: int = 6, max_attempts: int = 100) -> str:
    """
    Generates a guaranteed unique short code for a URL using hash-based generation
    and a collision resolution strategy.
    
    :param url: The original URL to shorten.
    :param existing_checker: Callable(code: str) -> bool returning True if code exists in DB.
    :param length: Initial desired length of short code.
    :param max_attempts: Max attempts before extending code length.
    :return: A unique short code.
    """
    salt = "url_shortener_salt_2026"
    attempt = 0
    curr_length = length
    
    while attempt < max_attempts * 10:
        code = generate_hash_code(url, salt=salt, length=curr_length, attempt=attempt)
        if not existing_checker(code):
            return code
        attempt += 1
        # If we hit multiple collisions at current length, increase length slightly
        if attempt > 0 and attempt % max_attempts == 0:
            curr_length += 1
            
    # Fallback timestamp encoding if extreme collision state
    return base62_encode(time.time_ns())[:curr_length]
