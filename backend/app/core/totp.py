"""
Kestrel Shield — RFC 6238 TOTP Engine with pyotp
Supports Google Authenticator, Microsoft Authenticator, Authy, and 1Password.
Provides secret generation, provisioning URI generation, and time-drift tolerant verification.
"""
import pyotp
import urllib.parse
from typing import Optional


def generate_totp_secret() -> str:
    """Generate a standard Base32 TOTP secret string."""
    return pyotp.random_base32()


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


def generate_totp_code(secret: str, for_time: Optional[float] = None, interval: int = 30, digits: int = 6) -> str:
    """Compute current 6-digit TOTP code for testing / verification."""
    totp = pyotp.TOTP(secret, interval=interval, digits=digits)
    if for_time is not None:
        return totp.at(for_time)
    return totp.now()


def verify_totp_code(secret: str, code: str, window: int = 1, valid_window: Optional[int] = None, interval: int = 30) -> bool:
    """
    Verify a user-provided 6-digit TOTP code.
    Allows clock drift within `window` intervals (window=1 allows ±30 seconds).
    Supports pyotp verification with backwards-compatible argument names.
    """
    if not secret or not code:
        return False
    code_clean = str(code).strip()
    if len(code_clean) != 6 or not code_clean.isdigit():
        return False

    w = valid_window if valid_window is not None else window
    totp = pyotp.TOTP(secret, interval=interval, digits=6)
    return bool(totp.verify(code_clean, valid_window=w))
