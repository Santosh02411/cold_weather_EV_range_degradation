from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .. import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Nullable now: an OAuth-only account (Google/GitHub) never sets a
    # local password. check_password() below handles that case
    # explicitly rather than crashing on a None hash.
    password_hash = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # --- Email verification ---
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(64), nullable=True, unique=True, index=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)

    # --- Password reset ---
    password_reset_token = db.Column(db.String(64), nullable=True, unique=True, index=True)
    password_reset_expires_at = db.Column(db.DateTime, nullable=True)

    # --- OTP login (email-delivered one-time code, not SMS -- no SMS
    # provider integration in this project; see docs/MEMORY.md) ---
    otp_code_hash = db.Column(db.String(256), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0)  # failed-attempt counter, resets on new OTP request

    # --- OAuth (Google / GitHub sign-in) ---
    google_id = db.Column(db.String(64), nullable=True, unique=True, index=True)
    github_id = db.Column(db.String(64), nullable=True, unique=True, index=True)

    # --- Profile picture ---
    profile_picture_path = db.Column(db.String(255), nullable=True)  # relative path under uploads

    # --- Notification preferences ---
    email_notifications_enabled = db.Column(db.Boolean, default=True)  # master switch: cold-snap alerts, security emails
    security_alert_emails_enabled = db.Column(db.Boolean, default=True)  # "new device logged in" style emails

    # Relationships
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False  # OAuth-only account -- no local password to check
        return check_password_hash(self.password_hash, password)

    @property
    def has_password(self):
        return bool(self.password_hash)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'has_password': self.has_password,
            'google_linked': bool(self.google_id),
            'github_linked': bool(self.github_id),
            'profile_picture_path': self.profile_picture_path,
            'email_notifications_enabled': self.email_notifications_enabled,
            'security_alert_emails_enabled': self.security_alert_emails_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
