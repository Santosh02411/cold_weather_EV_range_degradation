"""Diagnoses why email isn't sending -- checks the actual config values
Flask loaded, opens a real SMTP connection, and (optionally) sends a
real test email, printing the exact failure at whichever step it
happens rather than leaving you to guess.

USAGE:
    cd backend
    python ../scripts/check_email_config.py                  # checks config + connection only
    python ../scripts/check_email_config.py you@example.com  # also sends a real test email to this address
"""
import sys
import os
import smtplib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app  # noqa: E402


def main():
    test_recipient = sys.argv[1] if len(sys.argv) > 1 else None

    app = create_app()

    print("=" * 60)
    print("1. Config values Flask actually loaded")
    print("=" * 60)
    server = app.config.get('MAIL_SERVER')
    port = app.config.get('MAIL_PORT')
    use_tls = app.config.get('MAIL_USE_TLS')
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    sender = app.config.get('MAIL_DEFAULT_SENDER')

    print(f"   MAIL_SERVER          = {server}")
    print(f"   MAIL_PORT            = {port}")
    print(f"   MAIL_USE_TLS         = {use_tls}")
    print(f"   MAIL_USERNAME        = {username or '(not set)'}")
    print(f"   MAIL_PASSWORD        = {'*' * len(password) + f' ({len(password)} chars)' if password else '(not set)'}")
    print(f"   MAIL_DEFAULT_SENDER  = {sender or '(not set)'}")

    if not username or not password:
        print()
        print("STOP: MAIL_USERNAME and/or MAIL_PASSWORD are not set.")
        print("This is why you're seeing [EMAIL-WOULD-SEND] in the console instead of a")
        print("real send -- the app is working as designed (fail-soft), it just isn't")
        print("configured yet. Set both in your .env file (project root, next to")
        print(".env.example) and re-run this script. See README 'Sending real emails'.")
        return

    if password.count(' ') == 0 and len(password) == 16 and password.isalnum():
        print()
        print("   Looks like a 16-character Gmail App Password with no spaces -- good,")
        print("   that's the expected format either with or without the spaces Google")
        print("   shows you when it's generated.")
    elif len(password) < 16 and server and 'gmail' in server:
        print()
        print("   WARNING: this is shorter than a Gmail App Password (16 characters).")
        print("   If this is your regular Gmail account password, STOP -- Gmail rejects")
        print("   that for SMTP unconditionally. Generate an App Password instead:")
        print("   https://myaccount.google.com/apppasswords (requires 2-Step Verification")
        print("   to be turned on first: https://myaccount.google.com/security)")

    print()
    print("=" * 60)
    print("2. Opening a real SMTP connection and logging in")
    print("=" * 60)
    try:
        smtp = smtplib.SMTP(server, port, timeout=15)
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        print("   SUCCESS: connected and authenticated.")
        smtp.quit()
    except smtplib.SMTPAuthenticationError as e:
        print(f"   FAILED (authentication rejected): {e}")
        print()
        print("   This means the connection worked but Gmail rejected the")
        print("   username/password combo. Most common causes:")
        print("   - Using your real Gmail password instead of an App Password")
        print("   - 2-Step Verification isn't turned on (required before App")
        print("     Passwords can be generated at all)")
        print("   - The App Password was copied with a missing/extra character")
        return
    except (smtplib.SMTPException, OSError) as e:
        print(f"   FAILED (connection problem): {e}")
        print()
        print("   This usually means outbound port 587 is being blocked -- by a")
        print("   firewall, antivirus, school/work network, or VPN. Try a different")
        print("   network (e.g. phone hotspot) to confirm, or check your firewall's")
        print("   outbound rules for python.exe / this port.")
        return

    if not test_recipient:
        print()
        print("Connection and login both work. Re-run with an email address as an")
        print("argument to send a real test email and confirm delivery end-to-end:")
        print("   python ../scripts/check_email_config.py you@example.com")
        return

    print()
    print("=" * 60)
    print(f"3. Sending a real test email to {test_recipient}")
    print("=" * 60)
    try:
        from app import mail
        from flask_mail import Message
        with app.app_context():
            msg = Message(
                subject="Cold Weather EV Modeler -- test email",
                recipients=[test_recipient],
                body="If you're reading this, your email configuration works correctly.",
            )
            mail.send(msg)
        print(f"   SUCCESS: sent. Check {test_recipient}'s inbox (and spam folder).")
    except Exception as e:
        print(f"   FAILED while sending: {e}")


if __name__ == '__main__':
    main()
