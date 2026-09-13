from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from app.models import db, URLMapping, User
from app.utils.generator import generate_unique_short_code
from app.utils.validator import validate_url, validate_custom_alias
from app.utils.rate_limiter import rate_limit
from app.utils.auth import require_api_key, get_current_user

api_bp = Blueprint('api', __name__)

def is_code_taken(code: str) -> bool:
    """Check if short code exists in DB (active or deleted)."""
    return db.session.query(URLMapping.id).filter_by(short_code=code).first() is not None

@api_bp.route('/shorten', methods=['POST'])
@rate_limit('shorten')
def shorten_url():
    """
    POST /shorten
    JSON payload: { "url": "...", "custom_alias": "...", "ttl_seconds": 3600 }
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "error": "Bad Request",
            "message": "Invalid or missing JSON payload."
        }), 400

    url = data.get('url')
    custom_alias = data.get('custom_alias')
    ttl_seconds = data.get('ttl_seconds')

    # 1. Input URL Validation
    is_valid_url, url_error = validate_url(url)
    if not is_valid_url:
        return jsonify({
            "error": "Bad Request",
            "message": url_error
        }), 400

    url = url.strip()

    # 2. Custom Alias Handling & Validation
    short_code = None
    is_custom = False

    if custom_alias:
        custom_alias = custom_alias.strip()
        is_valid_alias, alias_error = validate_custom_alias(custom_alias)
        if not is_valid_alias:
            return jsonify({
                "error": "Bad Request",
                "message": alias_error
            }), 400

        if is_code_taken(custom_alias):
            return jsonify({
                "error": "Conflict",
                "message": f"Custom alias '{custom_alias}' is already in use."
            }), 409

        short_code = custom_alias
        is_custom = True
    else:
        # Generate hash-based unique short code with collision handling
        short_code = generate_unique_short_code(url, is_code_taken, length=6)

    # 3. Expiry / TTL Calculation
    expires_at = None
    if ttl_seconds is not None:
        try:
            ttl_int = int(ttl_seconds)
            if ttl_int <= 0:
                return jsonify({
                    "error": "Bad Request",
                    "message": "ttl_seconds must be a positive integer."
                }), 400
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_int)
        except (ValueError, TypeError):
            return jsonify({
                "error": "Bad Request",
                "message": "ttl_seconds must be a valid integer."
            }), 400

    # 4. User Association (if logged in or API Key provided)
    current_user = get_current_user()
    user_id = current_user.id if current_user else None

    # 5. Persist to Database
    url_mapping = URLMapping(
        short_code=short_code,
        original_url=url,
        is_custom_alias=is_custom,
        user_id=user_id,
        expires_at=expires_at
    )

    try:
        db.session.add(url_mapping)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to create short URL. Please try again."
        }), 500

    base_url = current_app.config.get('BASE_URL', request.host_url.rstrip('/'))
    # Use request.host_url dynamically if default config
    if request.host_url:
        base_url = request.host_url.rstrip('/')

    result = url_mapping.to_dict(base_url=base_url)
    return jsonify(result), 201

@api_bp.route('/stats/<string:code>', methods=['GET'])
def get_stats(code):
    """
    GET /stats/<code>
    Returns click count, created_at, original URL, expires_at, etc.
    """
    url_mapping = URLMapping.query.filter_by(short_code=code, is_deleted=False).first()

    if not url_mapping:
        return jsonify({
            "error": "Not Found",
            "message": f"Short code '{code}' does not exist or has been deleted."
        }), 404

    base_url = request.host_url.rstrip('/') if request.host_url else current_app.config.get('BASE_URL')
    data = url_mapping.to_dict(base_url=base_url)
    return jsonify(data), 200

@api_bp.route('/<string:code>', methods=['DELETE'])
@require_api_key
def delete_mapping(code):
    """
    DELETE /<code>
    Deletes mapping (Requires X-API-Key or Authorization Bearer header).
    """
    url_mapping = URLMapping.query.filter_by(short_code=code, is_deleted=False).first()

    if not url_mapping:
        return jsonify({
            "error": "Not Found",
            "message": f"Short code '{code}' does not exist or has already been deleted."
        }), 404

    # Ownership check: If URL belongs to a specific user, verify api_user owns it
    api_user = getattr(request, 'api_user', None)
    if url_mapping.user_id is not None and api_user and url_mapping.user_id != api_user.id:
        return jsonify({
            "error": "Forbidden",
            "message": "You do not have permission to delete this URL."
        }), 403

    url_mapping.is_deleted = True
    db.session.commit()

    return jsonify({
        "message": f"Short code '{code}' deleted successfully.",
        "short_code": code
    }), 200

@api_bp.route('/analytics/top', methods=['GET'])
def get_top_analytics():
    """
    GET /analytics/top
    Returns Top 5 most-clicked active links.
    """
    top_links = URLMapping.query.filter_by(is_deleted=False)\
        .order_by(URLMapping.click_count.desc(), URLMapping.created_at.desc())\
        .limit(5).all()

    base_url = request.host_url.rstrip('/') if request.host_url else current_app.config.get('BASE_URL')
    result = [link.to_dict(base_url=base_url) for link in top_links]
    return jsonify({
        "top_links": result,
        "count": len(result)
    }), 200
