"""Tests for app/services/auth_tokens.py -- token generation, OTP
hashing/verification, expiry checks, and device label parsing."""
from datetime import datetime, timedelta
from conftest import load_app_module

at = load_app_module('app.services.auth_tokens')


def test_generate_token_is_unique_and_long_enough():
    t1, t2 = at.generate_token(), at.generate_token()
    assert t1 != t2
    assert len(t1) >= 32


def test_generate_otp_is_six_digits():
    otp = at.generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_generate_otp_preserves_leading_zeros():
    # Regression-style check: an OTP like "003456" must stay a 6-char
    # string, not silently become "3456" if it were ever treated as an int.
    found_leading_zero = False
    for _ in range(200):
        otp = at.generate_otp()
        if otp.startswith('0'):
            found_leading_zero = True
            assert len(otp) == 6
    assert found_leading_zero, "expected at least one OTP with a leading zero in 200 tries"


def test_otp_hash_verify_roundtrip():
    otp = at.generate_otp()
    h = at.hash_otp(otp)
    assert at.verify_otp(otp, h) is True


def test_otp_verify_rejects_wrong_code():
    otp = at.generate_otp()
    h = at.hash_otp(otp)
    wrong = '000000' if otp != '000000' else '111111'
    assert at.verify_otp(wrong, h) is False


def test_otp_verify_rejects_none_inputs():
    assert at.verify_otp(None, 'somehash') is False
    assert at.verify_otp('123456', None) is False


def test_is_expired_for_past_datetime():
    assert at.is_expired(datetime.utcnow() - timedelta(minutes=1)) is True


def test_is_expired_for_future_datetime():
    assert at.is_expired(datetime.utcnow() + timedelta(minutes=5)) is False


def test_is_expired_for_none():
    assert at.is_expired(None) is True


def test_otp_expiry_returns_future_datetime():
    expiry = at.otp_expiry(minutes=5)
    assert expiry > datetime.utcnow()
    assert expiry < datetime.utcnow() + timedelta(minutes=6)


def test_device_label_windows_chrome():
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'
    assert at.parse_device_label(ua) == 'Chrome on Windows'


def test_device_label_iphone_not_misclassified_as_macos():
    # Regression test: iPhone/iPad user-agent strings contain the
    # literal substring "like Mac OS X" -- a naive check-order bug
    # classified every iPhone as a Mac. Caught and fixed during
    # development; this pins the fix.
    ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1'
    assert at.parse_device_label(ua) == 'Safari on iOS'


def test_device_label_ipad_not_misclassified_as_macos():
    ua = 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1'
    assert at.parse_device_label(ua) == 'Safari on iOS'


def test_device_label_real_mac_still_classified_correctly():
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15'
    assert at.parse_device_label(ua) == 'Safari on macOS'


def test_device_label_empty_string():
    assert at.parse_device_label('') == 'Unknown device'


def test_device_label_none():
    assert at.parse_device_label(None) == 'Unknown device'
