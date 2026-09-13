import secrets
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    urls = db.relationship('URLMapping', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_api_key():
        return secrets.token_hex(32)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'api_key': self.api_key,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class URLMapping(db.Model):
    __tablename__ = 'url_mappings'

    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    is_custom_alias = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)

    clicks = db.relationship('ClickLog', backref='url_mapping', lazy=True, cascade='all, delete-orphan')

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        # Normalize timezone awareness
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now >= exp

    def to_dict(self, base_url=""):
        full_url = f"{base_url.rstrip('/')}/{self.short_code}" if base_url else f"/{self.short_code}"
        return {
            'short_code': self.short_code,
            'short_url': full_url,
            'original_url': self.original_url,
            'is_custom_alias': self.is_custom_alias,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_deleted': self.is_deleted,
            'user_id': self.user_id
        }

class ClickLog(db.Model):
    __tablename__ = 'click_logs'

    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url_mappings.id'), nullable=False)
    clicked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    referrer = db.Column(db.String(256), nullable=True)
