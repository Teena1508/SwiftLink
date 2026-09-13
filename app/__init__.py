from flask import Flask
from config import Config
from app.models import db
from app.routes.api import api_bp
from app.routes.redirect import redirect_bp
from app.routes.auth import auth_bp
from app.routes.web import web_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    # Register redirect_bp last so catch-all /<code> doesn't collide with fixed API routes
    app.register_blueprint(redirect_bp)

    # Create tables automatically
    with app.app_context():
        db.create_all()

    return app
