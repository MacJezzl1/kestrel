"""
Kestrel Shield — WebAuthn / FIDO2 Passkey Engine
Provides challenge generation, credential registration, and assertion verification for passkeys.
"""
import os
import secrets
import base64
import time
import json
from typing import Optional, Dict, Any


def generate_challenge(length: int = 32) -> str:
    """Generate a cryptographically secure random base64url challenge string."""
    random_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")


def create_registration_options(
    user_id: str,
    email: str,
    display_name: Optional[str] = None,
    rp_name: str = "Kestrel Trading",
    rp_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate WebAuthn PublicKeyCredentialCreationOptions for passkey registration.
    """
    challenge = generate_challenge()
    user_handle = base64.urlsafe_b64encode(user_id.encode("utf-8")).decode("ascii").rstrip("=")
    
    options = {
        "challenge": challenge,
        "rp": {
            "name": rp_name,
            "id": rp_id or os.getenv("WEBAUTHN_RP_ID", "localhost"),
        },
        "user": {
            "id": user_handle,
            "name": email,
            "displayName": display_name or email.split("@")[0],
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},   # ES256
            {"type": "public-key", "alg": -257}, # RS256
        ],
        "timeout": 60000,
        "attestation": "none",
        "authenticatorSelection": {
            "residentKey": "preferred",
            "requireResidentKey": False,
            "userVerification": "preferred",
        },
    }
    return options


def create_authentication_options(
    registered_credential_ids: list[str],
    rp_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate WebAuthn PublicKeyCredentialRequestOptions for passkey sign-in / second-factor.
    """
    challenge = generate_challenge()
    allow_credentials = [
        {"type": "public-key", "id": cred_id, "transports": ["internal", "hybrid", "usb"]}
        for cred_id in registered_credential_ids
    ]
    return {
        "challenge": challenge,
        "timeout": 60000,
        "rpId": rp_id or os.getenv("WEBAUTHN_RP_ID", "localhost"),
        "allowCredentials": allow_credentials,
        "userVerification": "preferred",
    }


def verify_passkey_registration(
    client_data_json: str,
    expected_challenge: str,
    origin: str,
) -> bool:
    """
    Verify client data and challenge match for passkey registration.
    """
    try:
        data = json.loads(client_data_json)
        if data.get("type") != "webauthn.create":
            return False
        if data.get("challenge") != expected_challenge:
            return False
        return True
    except Exception:
        return False


def verify_passkey_assertion(
    client_data_json: str,
    expected_challenge: str,
    origin: str,
) -> bool:
    """
    Verify client data and challenge match for passkey assertion.
    """
    try:
        data = json.loads(client_data_json)
        if data.get("type") != "webauthn.get":
            return False
        if data.get("challenge") != expected_challenge:
            return False
        return True
    except Exception:
        return False
