"""Session Management, Login History, and Device Management.

Flask-Login's default session is a signed cookie with no server-side
record -- there's nothing to list or revoke. To support real "see your
active sessions" / "log out this device" features, this app now also
keeps a server-side UserSession row per login, and validates the
session cookie against it on every request (see the
`before_request` hook wired in app/__init__.py). Deleting a
UserSession row (or marking it revoked) means that device's cookie
stops working on its very next request, not just cosmetically
disappears from a list.
"""
from datetime import datetime
from .. import db


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    session_token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    device_label = db.Column(db.String(120), nullable=True)  # short parsed summary, e.g. "Chrome on Windows"
    login_method = db.Column(db.String(20), default='password')  # password / otp / google / github

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='sessions')

    @property
    def is_active(self):
        return self.revoked_at is None

    def to_dict(self, current_token=None):
        return {
            'id': self.id,
            'device_label': self.device_label,
            'ip_address': self.ip_address,
            'login_method': self.login_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
            'is_current': current_token is not None and self.session_token == current_token,
        }


class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    # Nullable: a failed login with a username/email that doesn't match
    # any real user still gets logged (for security visibility), but
    # there's no user_id to attach it to.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    attempted_identifier = db.Column(db.String(120), nullable=True)  # username/email as typed, for failed attempts

    success = db.Column(db.Boolean, nullable=False)
    method = db.Column(db.String(20), default='password')  # password / otp / google / github
    failure_reason = db.Column(db.String(120), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='login_history')

    def to_dict(self):
        return {
            'id': self.id,
            'success': self.success,
            'method': self.method,
            'failure_reason': self.failure_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
