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
