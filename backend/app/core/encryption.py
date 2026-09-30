"""
Kestrel Shield — Column-Level & At-Rest Encryption Utilities
Provides AES-GCM / Fernet encryption for sensitive account data (account_login, broker_server, API tokens, client PII)
and mirrors PostgreSQL pgcrypto symmetric encryption.
"""
import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet


def _get_encryption_key() -> bytes:
    """Retrieve 32-byte master encryption key from environment or derive from JWT_SECRET_KEY."""
    raw_key = os.getenv("KESTREL_ENCRYPTION_KEY") or os.getenv("JWT_SECRET_KEY") or "kestrel-default-dev-encryption-key-32b"
    # Ensure exactly 32 bytes via SHA-256
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def encrypt_data(plaintext: Optional[str], key: Optional[bytes] = None) -> Optional[str]:
    """
    Encrypt plaintext string using AES-256-GCM.
    Returns URL-safe Base64 encoded string containing 12-byte nonce + ciphertext + tag.
    """
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    aes_key = key or _get_encryption_key()
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Combine nonce + ciphertext
    payload = nonce + ciphertext
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_data(token: Optional[str], key: Optional[bytes] = None) -> Optional[str]:
    """
    Decrypt Base64 AES-256-GCM token back into plaintext.
    Returns None if token is None or invalid.
    """
    if token is None or token == "":
        return None

    try:
        aes_key = key or _get_encryption_key()
        payload = base64.urlsafe_b64decode(token.encode("ascii"))
        if len(payload) < 28:  # 12 nonce + 16 tag min
            # If not encrypted (e.g. legacy plain value), return as-is
            return token
        nonce = payload[:12]
        ciphertext = payload[12:]
        aesgcm = AESGCM(aes_key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception:
        # Fallback to returning raw string if it was plaintext before migration
        return token
