import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session as flask_session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from ..models.user import User
from ..models.session import UserSession, LoginHistory
from .. import db, limiter, oauth
from ..services.auth_tokens import generate_token, generate_otp, hash_otp, verify_otp, otp_expiry, is_expired, parse_device_label
from ..services.auth_email import send_verification_email, send_password_reset_email, send_otp_email, send_new_device_alert
from ..services.session_manager import create_session, log_failed_login, revoke_session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────────────────────────
# Login / Register / Logout
# ─────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AUTH', '10 per minute'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html', oauth_providers=_available_oauth_providers())

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return render_template('auth/login.html', oauth_providers=_available_oauth_providers())

            _complete_login(user, method='password', remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            log_failed_login(username, 'invalid credentials', user_id=user.id if user else None)
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html', oauth_providers=_available_oauth_providers())


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AUTH', '10 per minute'))
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html')

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='user'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        _send_verification_email_for(user)

        _complete_login(user, method='password', skip_new_device_alert=True)
        flash('Registration successful! Check your email to verify your account.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    token = flask_session.get('session_token')
    if token:
        user_session = UserSession.query.filter_by(session_token=token).first()
        if user_session:
            user_session.revoked_at = datetime.utcnow()
            db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _complete_login(user, method='password', remember=True, skip_new_device_alert=False):
    """Shared post-authentication steps for every login path (password,
    OTP, Google, GitHub): update last_login, create the server-side
    session record, log the history entry, and email a new-device alert
    if this looks like a device we haven't seen before. `remember`
    controls whether Flask-Login's cookie survives browser close --
    only the password-login form has a "remember me" checkbox, so
    every other path (OTP, OAuth, registration) defaults to True.
    `skip_new_device_alert` is set by register() -- a brand new account
    logging in for the first time is trivially always a "new device";
    sending a security alert for that is just noise stacked on top of
    the verification email the user is already getting.
    """
    is_new_device = (not skip_new_device_alert) and _is_new_device(user, request.headers.get('User-Agent', ''))
    login_user(user, remember=remember)
    user.last_login = datetime.utcnow()
    db.session.commit()
    create_session(user, method=method, remember=remember)
    if is_new_device:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or request.remote_addr
        send_new_device_alert(current_app.config, user, parse_device_label(request.headers.get('User-Agent', '')), ip)


def _is_new_device(user, user_agent_string):
    label = parse_device_label(user_agent_string)
    return not UserSession.query.filter_by(user_id=user.id, device_label=label).first()


def _send_verification_email_for(user):
    user.email_verification_token = generate_token()
    user.email_verification_sent_at = datetime.utcnow()
    db.session.commit()
    verify_url = url_for('auth.verify_email', token=user.email_verification_token, _external=True)
    send_verification_email(current_app.config, user, verify_url)


# ─────────────────────────────────────────────────────────────────
# Email verification
# ─────────────────────────────────────────────────────────────────

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        flash('That verification link is invalid or has already been used.', 'danger')
        return redirect(url_for('auth.login'))

    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()
    flash('Email verified — thank you!', 'success')
    return redirect(url_for('dashboard.index') if current_user.is_authenticated else url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def resend_verification():
    if current_user.email_verified:
        flash('Your email is already verified.', 'info')
    else:
        _send_verification_email_for(current_user)
        flash('Verification email sent.', 'success')
    return redirect(url_for('auth.profile'))


# ─────────────────────────────────────────────────────────────────
# Forgot / reset password
# ─────────────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AUTH', '10 per minute'))
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_reset_token = generate_token()
            user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=user.password_reset_token, _external=True)
            send_password_reset_email(current_app.config, user, reset_url)
        # Always show the same message regardless of whether the email
        # matched an account -- prevents using this form to enumerate
        # which emails are registered.
        flash('If an account with that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or is_expired(user.password_reset_expires_at):
        flash('That reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        db.session.commit()
        flash('Password reset — please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ─────────────────────────────────────────────────────────────────
# OTP login (email-delivered one-time code)
# ─────────────────────────────────────────────────────────────────

@auth_bp.route('/otp-login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def otp_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        # Same anti-enumeration principle as forgot-password: always
        # show the same "code sent" message.
        if user and user.is_active:
            otp = generate_otp()
            user.otp_code_hash = hash_otp(otp)
            user.otp_expires_at = otp_expiry(minutes=5)
            user.otp_attempts = 0
            db.session.commit()
            send_otp_email(current_app.config, user, otp)
        flash('If that account exists, a login code has been sent to its email.', 'info')
        return render_template('auth/otp_login.html', step='verify', identifier=identifier)

    return render_template('auth/otp_login.html', step='request')


@auth_bp.route('/otp-verify', methods=['POST'])
@limiter.limit("10 per hour")
def otp_verify():
    identifier = request.form.get('identifier', '').strip()
    code = request.form.get('otp_code', '').strip()
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

    if not user or is_expired(user.otp_expires_at):
        flash('That code has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.otp_login'))

    if user.otp_attempts >= 5:
        flash('Too many incorrect attempts. Please request a new code.', 'danger')
        return redirect(url_for('auth.otp_login'))

    if not verify_otp(code, user.otp_code_hash):
        user.otp_attempts += 1
        db.session.commit()
        log_failed_login(identifier, 'invalid OTP', user_id=user.id)
        flash('Incorrect code. Please try again.', 'danger')
        return render_template('auth/otp_login.html', step='verify', identifier=identifier)

    user.otp_code_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.session.commit()
    _complete_login(user, method='otp')
    flash(f'Welcome back, {user.full_name}!', 'success')
    return redirect(url_for('dashboard.index'))


# ─────────────────────────────────────────────────────────────────
# OAuth: Google / GitHub sign-in
# ─────────────────────────────────────────────────────────────────

def _available_oauth_providers():
    """Only list a provider as available if it was actually registered
    (i.e. its client ID was configured) -- see the registration guard
    in app/__init__.py. Keeps the login page from showing a button
    that would error out on click."""
    providers = []
    if current_app.config.get('GOOGLE_CLIENT_ID'):
        providers.append('google')
    if current_app.config.get('GITHUB_CLIENT_ID'):
        providers.append('github')
    return providers


@auth_bp.route('/oauth/<provider>')
def oauth_login(provider):
    if provider not in ('google', 'github') or not current_app.config.get(f'{provider.upper()}_CLIENT_ID'):
        flash('That sign-in method is not available.', 'danger')
        return redirect(url_for('auth.login'))
    client = getattr(oauth, provider)
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)


@auth_bp.route('/oauth/<provider>/callback')
def oauth_callback(provider):
    if provider not in ('google', 'github') or not current_app.config.get(f'{provider.upper()}_CLIENT_ID'):
        flash('That sign-in method is not available.', 'danger')
        return redirect(url_for('auth.login'))

    client = getattr(oauth, provider)
    try:
        token = client.authorize_access_token()
    except Exception as e:
        current_app.logger.error(f"OAuth callback failed for {provider}: {e}")
        flash('Sign-in was cancelled or failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    if provider == 'google':
        profile = token.get('userinfo') or client.userinfo()
        provider_id = profile.get('sub')
        email = profile.get('email')
        name = profile.get('name', '')
        email_verified = bool(profile.get('email_verified', True))
    else:  # github
        profile = client.get('user').json()
        provider_id = str(profile.get('id'))
        email = profile.get('email')
        if not email:
            # GitHub only returns a public email if the user set one;
            # otherwise fetch their verified primary email explicitly.
            emails_resp = client.get('user/emails').json()
            primary = next((e for e in emails_resp if e.get('primary') and e.get('verified')), None)
            email = primary['email'] if primary else None
        name = profile.get('name') or profile.get('login', '')
        email_verified = True  # GitHub only returns verified emails via the emails API

    if not email:
        flash(f"Couldn't get an email address from {provider.title()}. Please make sure your account has a public/verified email.", 'danger')
        return redirect(url_for('auth.login'))

    user = _find_or_create_oauth_user(provider, provider_id, email, name, email_verified)
    _complete_login(user, method=provider)
    flash(f'Welcome, {user.full_name}!', 'success')
    return redirect(url_for('dashboard.index'))


def _find_or_create_oauth_user(provider, provider_id, email, name, email_verified):
    id_field = f'{provider}_id'
    user = User.query.filter_by(**{id_field: provider_id}).first()
    if user:
        return user

    # Not linked yet by provider ID -- check if an account with this
    # email already exists (e.g. originally registered with a
    # password) and link this OAuth provider to it, rather than
    # creating a confusing second account with the same email.
    user = User.query.filter_by(email=email).first()
    if user:
        setattr(user, id_field, provider_id)
        db.session.commit()
        return user

    base_username = (name or email.split('@')[0]).lower().replace(' ', '_')
    username = base_username
    suffix = 1
    while User.query.filter_by(username=username).first():
        suffix += 1
        username = f"{base_username}{suffix}"

    name_parts = (name or '').split(' ', 1)
    user = User(
        username=username,
        email=email,
        first_name=name_parts[0] if name_parts else '',
        last_name=name_parts[1] if len(name_parts) > 1 else '',
        role='user',
        email_verified=email_verified,  # Google/GitHub already verified this email
    )
    setattr(user, id_field, provider_id)
    db.session.add(user)
    db.session.commit()
    return user


# ─────────────────────────────────────────────────────────────────
# Profile: info, picture, notifications, sessions, delete account
# ─────────────────────────────────────────────────────────────────

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        new_email = request.form.get('email', '').strip()
        if new_email != current_user.email:
            current_user.email = new_email
            current_user.email_verified = False
            _send_verification_email_for(current_user)
            flash('Email updated — please verify your new address.', 'info')

        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('auth/profile.html')
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully.', 'success')

    return render_template('auth/profile.html')


def _allowed_picture_extension(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config.get('PROFILE_PICTURE_ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png', 'webp'})


@auth_bp.route('/profile/picture', methods=['POST'])
@login_required
def upload_profile_picture():
    file = request.files.get('picture')
    if not file or file.filename == '':
        flash('Please choose an image file.', 'danger')
        return redirect(url_for('auth.profile'))

    if not _allowed_picture_extension(file.filename):
        flash('Only JPG, PNG, and WEBP images are allowed.', 'danger')
        return redirect(url_for('auth.profile'))

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_bytes = current_app.config.get('PROFILE_PICTURE_MAX_BYTES', 5 * 1024 * 1024)
    if size > max_bytes:
        flash(f'Image must be under {max_bytes // (1024 * 1024)}MB.', 'danger')
        return redirect(url_for('auth.profile'))

    # Validate it's actually a real image (not just a renamed file with
    # an image extension) by opening it with Pillow before saving.
    try:
        from PIL import Image
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        flash('That file does not appear to be a valid image.', 'danger')
        return redirect(url_for('auth.profile'))

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'profile_pictures')
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = secure_filename(f"user_{current_user.id}_{generate_token()[:12]}.{ext}")
    file.save(os.path.join(upload_dir, filename))

    # Remove the old picture file if there was one, so uploads don't
    # accumulate forever in that directory.
    if current_user.profile_picture_path:
        old_path = os.path.join(current_app.static_folder, current_user.profile_picture_path)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    current_user.profile_picture_path = f'uploads/profile_pictures/{filename}'
    db.session.commit()
    flash('Profile picture updated.', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/notifications', methods=['POST'])
@login_required
def update_notification_preferences():
    current_user.email_notifications_enabled = 'email_notifications_enabled' in request.form
    current_user.security_alert_emails_enabled = 'security_alert_emails_enabled' in request.form
    db.session.commit()
    flash('Notification preferences updated.', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/sessions')
@login_required
def sessions_page():
    return render_template('auth/sessions.html')


@auth_bp.route('/api/sessions', methods=['GET'])
@login_required
def list_sessions():
    current_token = flask_session.get('session_token')
    sessions = UserSession.query.filter_by(user_id=current_user.id, revoked_at=None) \
        .order_by(UserSession.last_active_at.desc()).all()
    return jsonify({'sessions': [s.to_dict(current_token) for s in sessions]})


@auth_bp.route('/api/sessions/<int:session_id>/revoke', methods=['POST'])
@login_required
def revoke_session_endpoint(session_id):
    current_token = flask_session.get('session_token')
    target = UserSession.query.get(session_id)
    if target and target.session_token == current_token:
        return jsonify({'error': "Use Logout to end your current session, not Revoke."}), 400

    success = revoke_session(session_id, current_user.id)
    if not success:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify({'revoked': True})


@auth_bp.route('/api/login-history', methods=['GET'])
@login_required
def login_history():
    history = LoginHistory.query.filter_by(user_id=current_user.id) \
        .order_by(LoginHistory.created_at.desc()).limit(50).all()
    return jsonify({'history': [h.to_dict() for h in history]})


@auth_bp.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Right-to-be-forgotten account deletion. Requires the user's
    current password as confirmation (skipped for OAuth-only accounts
    with no password -- they confirm by re-typing their username
    instead, checked below). Deletes clearly-personal data outright;
    anonymizes (rather than deletes) community reports since that data
    remains genuinely useful to other users once attribution is
    removed -- see docs/MEMORY.md for the full reasoning.
    """
    if current_user.has_password:
        password = request.form.get('password', '')
        if not current_user.check_password(password):
            flash('Incorrect password.', 'danger')
            return redirect(url_for('auth.profile'))
    else:
        confirm_username = request.form.get('confirm_username', '')
        if confirm_username != current_user.username:
            flash('Please type your username exactly to confirm.', 'danger')
            return redirect(url_for('auth.profile'))

    from ..models.prediction import Prediction, TripSimulation, CommunityRangeReport
    from ..models.battery_health import BatteryHealthRecord
    from ..models.alert_subscription import AlertSubscription

    user_id = current_user.id

    CommunityRangeReport.query.filter_by(user_id=user_id).update({'user_id': None})
    Prediction.query.filter_by(user_id=user_id).delete()
    TripSimulation.query.filter_by(user_id=user_id).delete()
    BatteryHealthRecord.query.filter_by(user_id=user_id).delete()
    AlertSubscription.query.filter_by(user_id=user_id).delete()
    UserSession.query.filter_by(user_id=user_id).delete()
    LoginHistory.query.filter_by(user_id=user_id).update({'user_id': None})

    user = User.query.get(user_id)
    logout_user()
    db.session.delete(user)
    db.session.commit()

    flash('Your account and personal data have been deleted.', 'info')
    return redirect(url_for('auth.login'))
