"""
Auth email sending -- verification, password reset, OTP codes, and
"new device signed in" security alerts. Reuses the Flask-Mail wiring
from FEAT-3 (services/alerts.py) rather than duplicating mail setup.

Same fail-soft-and-say-so pattern as FEAT-3: if MAIL_USERNAME/PASSWORD
aren't configured, these functions log what they would have sent
instead of silently doing nothing OR raising an error that would break
registration/login for every user just because email isn't set up yet.
"""


def _mail_configured(app_config):
    return bool(app_config.get('MAIL_USERNAME') and app_config.get('MAIL_PASSWORD'))


def _send_or_log(app_config, subject, recipient, body):
    from .. import mail
    from flask_mail import Message

    if not _mail_configured(app_config):
        print(f"[EMAIL-WOULD-SEND] (MAIL_USERNAME/PASSWORD not configured) "
              f"To: {recipient} | Subject: {subject}\n{body}")
        return False, 'mail not configured'
    try:
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail.send(msg)
        return True, None
    except Exception as e:
        print(f"[ERROR] Failed to send email to {recipient}: {e}")
        return False, str(e)


def send_verification_email(app_config, user, verify_url):
    subject = "Verify your email — Cold Weather EV Modeler"
    body = (
        f"Hi {user.username},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"If you didn't create this account, you can ignore this email."
    )
    return _send_or_log(app_config, subject, user.email, body)


def send_password_reset_email(app_config, user, reset_url):
    subject = "Reset your password — Cold Weather EV Modeler"
    body = (
        f"Hi {user.username},\n\n"
        f"Someone requested a password reset for this account. If this was "
        f"you, click the link below (valid for 1 hour):\n\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, you can safely ignore this email — "
        f"your password will not be changed."
    )
    return _send_or_log(app_config, subject, user.email, body)


def send_otp_email(app_config, user, otp_code):
    subject = "Your login code — Cold Weather EV Modeler"
    body = (
        f"Hi {user.username},\n\n"
        f"Your one-time login code is: {otp_code}\n\n"
        f"This code expires in 5 minutes. If you didn't request this, "
        f"you can ignore this email."
    )
    return _send_or_log(app_config, subject, user.email, body)


def send_new_device_alert(app_config, user, device_label, ip_address):
    if not user.security_alert_emails_enabled:
        return False, 'user disabled security alert emails'
    subject = "New sign-in to your account — Cold Weather EV Modeler"
    body = (
        f"Hi {user.username},\n\n"
        f"Your account was just signed into from a new device:\n\n"
        f"Device: {device_label}\nIP address: {ip_address}\n\n"
        f"If this was you, no action is needed. If you don't recognize this, "
        f"change your password immediately and review your active sessions."
    )
    return _send_or_log(app_config, subject, user.email, body)
