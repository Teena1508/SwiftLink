import re
from urllib.parse import urlparse

RESERVED_SLUGS = {
    'shorten', 'stats', 'analytics', 'login', 'register', 'logout',
    'api', 'static', 'admin', 'dashboard', 'user', 'health', 'favicon.ico'
}

UNSAFE_SCHEMES = {'javascript', 'data', 'file', 'vbscript', 'ftp', 'blob'}

ALIAS_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')

def validate_url(url: str) -> tuple[bool, str]:
    """
    Validates whether a string is a safe, properly-formed HTTP/HTTPS URL.
    Returns (is_valid, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL string is required."

    url_str = url.strip()
    if len(url_str) > 2048:
        return False, "URL exceeds maximum allowed length of 2048 characters."

    try:
        parsed = urlparse(url_str)
    except Exception as e:
        return False, f"Malformed URL format: {str(e)}"

    scheme = parsed.scheme.lower() if parsed.scheme else ''

    if scheme in UNSAFE_SCHEMES:
        return False, f"Unsafe URL scheme '{scheme}:' is strictly forbidden."

    if scheme not in ('http', 'https'):
        return False, "URL must use http:// or https:// protocol scheme."

    if not parsed.netloc:
        return False, "URL is missing a valid domain name or hostname."

    # Validate hostname doesn't contain spaces or invalid control characters
    hostname = parsed.hostname
    if not hostname or any(c in hostname for c in (' ', '\n', '\r', '\t', '<', '>', '"')):
        return False, "URL contains an invalid hostname."

    return True, ""

def validate_custom_alias(alias: str, min_len: int = 3, max_len: int = 30) -> tuple[bool, str]:
    """
    Validates custom alias format, length, allowed characters, and reserved slug collisions.
    Returns (is_valid, error_message).
    """
    if not alias:
        return True, ""

    alias = alias.strip()
    if len(alias) < min_len or len(alias) > max_len:
        return False, f"Custom alias length must be between {min_len} and {max_len} characters."

    if not ALIAS_REGEX.match(alias):
        return False, "Custom alias can only contain alphanumeric characters, hyphens, and underscores."

    if alias.lower() in RESERVED_SLUGS:
        return False, f"Custom alias '{alias}' is a reserved system keyword."

    return True, ""
