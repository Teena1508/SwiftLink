from flask import Blueprint, redirect, jsonify, request, render_template, make_response
from app.models import db, URLMapping, ClickLog

redirect_bp = Blueprint('redirect', __name__)

@redirect_bp.route('/<string:code>', methods=['GET'])
def handle_redirect(code):
    """
    GET /<code>
    Redirects to original URL if active and not expired.
    Increments click count and logs analytics.
    Returns 410 Gone if expired, 404 Not Found if missing/deleted.
    """
    url_mapping = URLMapping.query.filter_by(short_code=code, is_deleted=False).first()

    if not url_mapping:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                "error": "Not Found",
                "message": f"Short URL '/{code}' was not found."
            }), 404
        return render_template('base.html', page_title="404 Not Found", content_error=f"Short URL '/{code}' does not exist or has been deleted."), 404

    # Check expiration
    if url_mapping.is_expired:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                "error": "Gone",
                "message": f"Short URL '/{code}' has expired."
            }), 410
        response = make_response(render_template('base.html', page_title="410 Gone - Expired Link", content_error=f"The link '/{code}' has expired and is no longer accessible."), 410)
        return response

    # Increment click count & record click details
    url_mapping.click_count += 1
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    click_log = ClickLog(
        url_id=url_mapping.id,
        ip_address=client_ip,
        user_agent=request.user_agent.string if request.user_agent else None,
        referrer=request.referrer
    )
    
    try:
        db.session.add(click_log)
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Perform 302 Found redirect to original URL
    return redirect(url_mapping.original_url, code=302)
