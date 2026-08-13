"""
Real server-side session tracking on top of Flask-Login's cookie-based
sessions -- see models/session.py's docstring for why this exists
(Flask-Login alone has nothing to list or revoke).
"""
from flask import session as flask_session, request
from datetime import datetime

from .auth_tokens import generate_token, parse_device_label


def create_session(user, method='password', remember=True):
    """Call right after login_user(). Creates a server-side
    UserSession row, stores its token in the Flask session cookie, and
    logs the login to LoginHistory. Returns the created UserSession.

    `remember` mirrors the same flag passed to Flask-Login's
    login_user() -- flask_session.permanent controls whether the
    underlying session cookie itself gets a real expiration date
    (~31 days, PERMANENT_SESSION_LIFETIME) or is a browser-session-only
    cookie. Setting this unconditionally to True regardless of the
    user's "remember me" choice would silently weaken that choice for
    the session cookie even though Flask-Login's own remember-cookie
    logic still respected it -- caught before shipping, not after.
    """
    from ..models.session import UserSession, LoginHistory
    from .. import db

    token = generate_token()
    ua_string = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or request.remote_addr

    user_session = UserSession(
        user_id=user.id,
        session_token=token,
        ip_address=ip,
        user_agent=ua_string,
        device_label=parse_device_label(ua_string),
        login_method=method,
    )
    db.session.add(user_session)

    db.session.add(LoginHistory(
        user_id=user.id, success=True, method=method,
        ip_address=ip, user_agent=ua_string,
    ))
    db.session.commit()

    flask_session['session_token'] = token
    flask_session.permanent = remember
    return user_session


def log_failed_login(identifier, reason, user_id=None):
    from ..models.session import LoginHistory
    from .. import db

    ua_string = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or request.remote_addr
    db.session.add(LoginHistory(
        user_id=user_id, attempted_identifier=identifier, success=False,
        failure_reason=reason, ip_address=ip, user_agent=ua_string,
    ))
    db.session.commit()


def validate_current_session():
    """Called from a before_request hook. Returns True if the current
    request's session cookie corresponds to a still-active (not
    revoked) UserSession, or if there's no session_token to check
    (e.g. an older cookie predating this feature, or truly logged out)
    -- in that ambiguous case we don't force-logout, since that would
    also break anyone using a session created before this feature
    shipped. Returns False only when there IS a session_token but it
    was explicitly revoked -- that's the real "someone clicked
    'log out this device' and it should take effect now" case.
    """
    token = flask_session.get('session_token')
    if not token:
        return True

    from ..models.session import UserSession
    user_session = UserSession.query.filter_by(session_token=token).first()
    if user_session is None:
        return True  # unknown token, e.g. pre-feature cookie -- don't punish it
    if user_session.revoked_at is not None:
        return False

    user_session.last_active_at = datetime.utcnow()
    from .. import db
    db.session.commit()
    return True


def revoke_session(session_id, user_id):
    """Revoke one session (device) by ID, scoped to the owning user so
    one user can't revoke another's session by guessing an ID."""
    from ..models.session import UserSession
    from .. import db

    user_session = UserSession.query.get(session_id)
    if not user_session or user_session.user_id != user_id:
        return False
    user_session.revoked_at = datetime.utcnow()
    db.session.commit()
    return True
