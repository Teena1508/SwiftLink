from flask import Blueprint, render_template, session, request, redirect, url_for
from app.models import URLMapping, User
from app.utils.auth import get_current_user, require_login

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@web_bp.route('/dashboard')
@require_login
def dashboard():
    user = get_current_user()
    user_urls = URLMapping.query.filter_by(user_id=user.id, is_deleted=False)\
        .order_by(URLMapping.created_at.desc()).all()
    
    base_url = request.host_url.rstrip('/')
    url_list = [url.to_dict(base_url=base_url) for url in user_urls]
    
    total_clicks = sum(url.click_count for url in user_urls)

    return render_template(
        'dashboard.html',
        user=user,
        urls=url_list,
        total_urls=len(url_list),
        total_clicks=total_clicks,
        api_key=user.api_key
    )

@web_bp.route('/analytics')
def analytics():
    user = get_current_user()
    top_links = URLMapping.query.filter_by(is_deleted=False)\
        .order_by(URLMapping.click_count.desc(), URLMapping.created_at.desc())\
        .limit(5).all()

    base_url = request.host_url.rstrip('/')
    top_links_dict = [link.to_dict(base_url=base_url) for link in top_links]

    return render_template(
        'analytics.html',
        user=user,
        top_links=top_links_dict
    )
