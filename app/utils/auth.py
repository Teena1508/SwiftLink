from functools import wraps
from flask import request, session, jsonify, redirect, url_for
from app.models import User

def get_api_key_from_request() -> str | None:
    """Extracts API key from X-API-Key header, Authorization Bearer header, or query string."""
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key.strip()

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:].strip()

    return request.args.get('api_key')

def get_current_user() -> User | None:
    """Retrieves the authenticated User object from session or API Key header."""
    # 1. Try API Key Header
    api_key = get_api_key_from_request()
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    # 2. Try Web Session
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)

    return None

def require_api_key(f):
    """Decorator requiring a valid API key header for endpoint access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key_from_request()
        if not api_key:
            return jsonify({
                "error": "Unauthorized",
                "message": "Missing API key. Provide header 'X-API-Key' or 'Authorization: Bearer <key>'."
            }), 401

        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid API key provided."
            }), 401

        request.api_user = user
        return f(*args, **kwargs)
    return decorated_function

def require_login(f):
    """Decorator requiring web session login for UI pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
