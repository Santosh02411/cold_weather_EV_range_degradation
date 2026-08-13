"""
Pure helper functions for the auth features below -- token generation,
OTP hashing/verification, and user-agent-to-device-label parsing. Kept
free of Flask/DB imports so they're testable the same way as the rest
of this project's `ml/`/`services/` modules (see
docs/PROJECT_WORKFLOW.md's established pattern).
"""
import secrets
import hashlib
from datetime import datetime, timedelta


def generate_token():
    """A URL-safe random token for email verification / password reset
    links. 32 bytes -> 43 characters, matches the entropy used for
    Prediction.share_token and the SEC-3 generated passwords."""
    return secrets.token_urlsafe(32)


def generate_otp():
    """A 6-digit numeric OTP code, as a string (preserves leading
    zeros). Delivered by email in this project -- no SMS provider
    integration (see docs/MEMORY.md for why)."""
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(otp_code):
    """OTP codes are short-lived (minutes) and low-entropy (6 digits)
    compared to the long random tokens above, so they're hashed with a
    plain SHA-256 rather than werkzeug's slower password hash --
    appropriate for something that expires in minutes and is rate-
    limited on verification attempts, not a long-lived credential."""
    return hashlib.sha256(otp_code.encode()).hexdigest()


def verify_otp(otp_code, otp_hash):
    if not otp_code or not otp_hash:
        return False
    return hash_otp(otp_code) == otp_hash


def otp_expiry(minutes=5):
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_expired(expires_at):
    if expires_at is None:
        return True
    return datetime.utcnow() > expires_at


def parse_device_label(user_agent_string):
    """Turn a raw User-Agent string into a short human-readable label
    like "Chrome on Windows" for the session/device list. Deliberately
    simple substring matching, not a full UA-parsing library (adding a
    dependency for a cosmetic label isn't worth it) -- falls back to
    "Unknown device" rather than showing a raw, ugly UA string.
    """
    if not user_agent_string:
        return "Unknown device"
    ua = user_agent_string.lower()

    if 'edg/' in ua:
        browser = 'Edge'
    elif 'chrome/' in ua and 'edg/' not in ua:
        browser = 'Chrome'
    elif 'firefox/' in ua:
        browser = 'Firefox'
    elif 'safari/' in ua and 'chrome/' not in ua:
        browser = 'Safari'
    else:
        browser = 'Browser'

    # iOS devices must be checked BEFORE macOS: an iPhone/iPad user-agent
    # string contains the literal substring "like Mac OS X" (part of
    # how iOS UAs identify their WebKit lineage), so checking 'mac os'
    # first would misclassify every iPhone/iPad as a Mac. Caught by the
    # very first offline test run against a real iPhone UA string.
    if 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Unknown OS'

    return f"{browser} on {os_name}"
