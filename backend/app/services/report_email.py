"""Email Reports: send a generated report file as an email attachment.

Reuses the exact same Flask-Mail wiring and "fail-soft and log what
would have been sent" pattern as services/auth_email.py -- if
MAIL_USERNAME/MAIL_PASSWORD aren't configured, Scheduled Reports still
run (and still get logged in Report History) rather than silently
doing nothing or raising and breaking the whole scheduled job over one
user's report.
"""
from .report_generation import FORMAT_MIME_TYPES


def _mail_configured(app_config):
    return bool(app_config.get('MAIL_USERNAME') and app_config.get('MAIL_PASSWORD'))


def send_report_email(app_config, user, report_type, format, file_bytes, filename):
    """Returns (sent: bool, status: str) -- status is either 'sent',
    'mail not configured', or an error message, always suitable to
    store directly in ReportHistory.email_status.
    """
    from .. import mail
    from flask_mail import Message

    subject = f"Your {report_type.title()} Report ({format.upper()}) — Cold Weather EV Modeler"
    body = (
        f"Hi {user.username},\n\n"
        f"Attached is your requested {report_type} report in {format.upper()} format.\n\n"
        f"This report was generated automatically based on a schedule you set up. "
        f"You can manage your scheduled reports from the Reports page."
    )

    if not _mail_configured(app_config):
        print(f"[EMAIL-WOULD-SEND] (MAIL_USERNAME/PASSWORD not configured) "
              f"To: {user.email} | Subject: {subject} | Attachment: {filename} ({len(file_bytes)} bytes)")
        return False, 'mail not configured'

    try:
        msg = Message(subject=subject, recipients=[user.email], body=body)
        msg.attach(filename, FORMAT_MIME_TYPES.get(format, 'application/octet-stream'), file_bytes)
        mail.send(msg)
        return True, 'sent'
    except Exception as e:
        print(f"[ERROR] Failed to send report email to {user.email}: {e}")
        return False, str(e)
