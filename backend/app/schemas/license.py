"""
Kestrel Shield — License & EA Binding Schemas
Pydantic schemas for MT5 EA terminal license activation, validation, and tier entitlements.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LicenseActivationRequest(BaseModel):
    account_login: str = Field(..., min_length=1, max_length=64, description="MT5 Account Number / Login")
    broker_server: str = Field(..., min_length=1, max_length=128, description="Broker Server Name, e.g. Deriv-Demo")
    terminal_id: str = Field(..., min_length=1, max_length=128, description="Terminal / Machine Hardware Fingerprint")
    hmac_signature: Optional[str] = Field(None, description="HMAC-SHA256 signature for request validation")


class LicenseActivationResponse(BaseModel):
    valid: bool
    status: str = Field(..., description="active, trial, expired, or invalid")
    tier: str = Field("starter", description="starter, pro, or institutional")
    account_login: str
    max_risk_per_trade: float = Field(1.0, description="Maximum risk percentage allowed per trade")
    max_daily_loss_pct: float = Field(5.0, description="Maximum daily loss percentage before circuit breaker")
    expires_at: Optional[datetime] = None
    is_trial: bool = False
    days_remaining: Optional[int] = None
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="Valid JWT refresh token")


class TokenWithRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
