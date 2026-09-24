"""
Kestrel Shield — RFC 6238 TOTP Engine
Pure Python standard library implementation of Time-Based One-Time Passwords (TOTP).
Compatible with Google Authenticator, Microsoft Authenticator, Authy, and 1Password.
No external pip dependencies required.
"""
import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
import urllib.parse


def generate_totp_secret(length: int = 32) -> str:
    """Generate a secure random Base32 secret string (RFC 3548 / RFC 4648)."""
    random_bytes = secrets.token_bytes((length * 5 + 7) // 8)
    secret = base64.b32encode(random_bytes).decode("utf-8").replace("=", "")
    return secret[:length]


def generate_totp_uri(secret: str, account_name: str, issuer: str = "Kestrel Trading") -> str:
    """Generate the standard otpauth:// URI for QR codes."""
    label = f"{issuer}:{account_name}"
    params = {
        "secret": secret,
        "issuer": issuer,
        "algorithm": "SHA1",
        "digits": "6",
        "period": "30",
    }
    encoded_label = urllib.parse.quote(label)
    encoded_params = urllib.parse.urlencode(params)
    return f"otpauth://totp/{encoded_label}?{encoded_params}"


def generate_totp_code(secret: str, for_time: float | None = None, interval: int = 30, digits: int = 6) -> str:
    """Compute the current 6-digit TOTP code for a given secret and timestamp."""
    if for_time is None:
        for_time = time.time()

    counter = int(for_time // interval)
    
    # Pad base32 secret with '=' if necessary
    padding_needed = (8 - len(secret) % 8) % 8
    padded_secret = secret.upper() + ("=" * padding_needed)
    key = base64.b32decode(padded_secret, casefold=True)

    # Counter to 8-byte big-endian
    msg = struct.pack(">Q", counter)

    # HMAC-SHA1
    hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()

    # Dynamic truncation (RFC 4226)
    offset = hmac_hash[-1] & 0x0F
    binary_code = struct.unpack(">I", hmac_hash[offset : offset + 4])[0] & 0x7FFFFFFF

    # Modulo to get desired digits
    otp = binary_code % (10**digits)
    return f"{otp:0{digits}d}"


def verify_totp_code(secret: str, code: str, window: int = 1, interval: int = 30) -> bool:
    """
    Verify a user-provided 6-digit TOTP code.
    Allows clock drift within `window` intervals (window=1 allows ±30 seconds).
    """
    if not secret or not code:
        return False

    code = str(code).strip()
    if len(code) != 6 or not code.isdigit():
        return False

    now = time.time()
    for offset in range(-window, window + 1):
        test_time = now + (offset * interval)
        expected = generate_totp_code(secret, for_time=test_time, interval=interval, digits=6)
        if hmac.compare_digest(code, expected):
            return True

    return False
