import time
import threading
from functools import wraps
from flask import request, jsonify, make_response, current_app

class SlidingWindowRateLimiter:
    def __init__(self):
        self._requests = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> tuple[bool, int]:
        """
        Checks if the given key is allowed to make a request under the sliding window algorithm.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            if key not in self._requests:
                self._requests[key] = []
            
            # Remove expired timestamps
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]
            
            if len(self._requests[key]) >= max_requests:
                oldest = self._requests[key][0]
                retry_after = int(oldest + window_seconds - now) + 1
                return False, max(retry_after, 1)

            self._requests[key].append(now)
            return True, 0

    def reset(self):
        """Resets all rate limit tracking (useful for testing)."""
        with self._lock:
            self._requests.clear()

rate_limiter = SlidingWindowRateLimiter()

def rate_limit(endpoint_name: str = "shorten"):
    """
    Decorator for Flask route handlers to enforce manual rate limiting per client IP.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Bypass rate limit during unit testing if explicitly disabled
            if current_app.config.get('TESTING') and current_app.config.get('DISABLE_RATE_LIMIT'):
                return f(*args, **kwargs)

            # Get client IP address
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()

            key = f"{endpoint_name}:{client_ip}"
            limit = current_app.config.get('RATE_LIMIT_PER_MINUTE', 10)

            allowed, retry_after = rate_limiter.is_allowed(key, max_requests=limit, window_seconds=60)
            if not allowed:
                response = make_response(jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit is {limit} requests per minute. Try again in {retry_after} seconds.",
                    "retry_after_seconds": retry_after
                }), 429)
                response.headers['Retry-After'] = str(retry_after)
                return response

            return f(*args, **kwargs)
        return decorated_function
    return decorator
