"""
Kestrel Shield — Auth Schemas
Pydantic models for authentication request/response validation.
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


# Resolve forward reference
TokenResponse.model_rebuild()
