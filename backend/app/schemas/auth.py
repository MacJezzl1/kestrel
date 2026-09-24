"""
Kestrel Shield — Auth & Security Schemas
Pydantic models for authentication, security, and API key request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    email: str
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit TOTP code if MFA enabled")



class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    license_tier: str = "free"
    license_status: str = "active"
    created_at: datetime

    model_config = {"from_attributes": True}


class LicenseInfo(BaseModel):
    tier: str
    status: str
    signals_used_today: int
    signals_limit: int
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Security schemas ---

class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="A label for this API key, e.g. 'MT5 EA'")
    permissions: list[str] = Field(default=["signals", "trades"], description="Scopes this key can access")


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: list[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreated(BaseModel):
    """Returned only once — the full raw key is shown only at creation time."""
    id: str
    name: str
    raw_key: str
    key_prefix: str
    permissions: list[str]
    created_at: datetime


class SessionInfo(BaseModel):
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogEntry(BaseModel):
    id: str
    action: str
    details: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# Resolve forward reference
TokenResponse.model_rebuild()


# --- MFA (TOTP) Schemas ---

class MfaSetupResponse(BaseModel):
    secret: str = Field(..., description="Base32 TOTP secret")
    otpauth_url: str = Field(..., description="otpauth:// URL for authenticator QR codes")
    issuer: str = "Kestrel Trading"


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit TOTP code")


class MfaStatusResponse(BaseModel):
    mfa_enabled: bool
    message: str


# --- OAuth2 PKCE (RFC 7636) Schemas ---

class OAuthAuthorizeRequest(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=128)
    redirect_uri: str = Field(..., min_length=1, max_length=512)
    response_type: str = Field(default="code", pattern=r"^code$")
    code_challenge: str = Field(..., min_length=43, max_length=128, description="Base64URL encoded SHA-256 challenge")
    code_challenge_method: str = Field(default="S256", pattern=r"^(S256|plain)$")
    state: Optional[str] = Field(None, max_length=256)
    scope: Optional[str] = Field("trading", max_length=128)


class OAuthTokenRequest(BaseModel):
    grant_type: str = Field(..., pattern=r"^authorization_code$")
    code: str = Field(..., min_length=16, max_length=128)
    redirect_uri: str = Field(..., min_length=1, max_length=512)
    client_id: str = Field(..., min_length=1, max_length=128)
    code_verifier: str = Field(..., min_length=43, max_length=128, description="Cryptographic code verifier")


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str = "trading"

