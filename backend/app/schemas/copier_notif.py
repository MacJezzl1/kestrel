"""
Kestrel Core — Multi-Broker Copier & Notification Schemas
Pydantic v2 validation models for copier accounts, broker routing, and Telegram/Discord alerts.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NotificationConfigSchema(BaseModel):
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_enabled: bool = False
    discord_webhook_url: Optional[str] = None
    alert_trade_signals: bool = True
    alert_prop_firm_risk: bool = True
    alert_circuit_breaker: bool = True
    alert_high_impact_news: bool = True


class TelegramSendRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message: str = Field(..., description="Message text (HTML allowed)")


class DiscordSendRequest(BaseModel):
    webhook_url: Optional[str] = None
    content: Optional[str] = None
    embeds: Optional[List[Dict[str, Any]]] = None


class BroadcastNotificationRequest(BaseModel):
    alert_type: str = Field(..., description="TRADE_SIGNAL, PROP_RISK, CIRCUIT_BREAKER, NEWS_WARNING")
    payload: Dict[str, Any] = Field(..., description="Alert payload data")


class CopierAccountConfig(BaseModel):
    account_login: str
    account_name: str
    broker_profile: str = Field(default="FTMO", description="FTMO, THE5ERS, FUNDING_PIPS, TOPSTEP, ICMARKETS, DERIV, PEPPERSTONE, EXNESS")
    role: str = Field(default="RECEIVER", description="MASTER or RECEIVER")
    risk_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    max_lot_cap: float = Field(default=5.0, ge=0.01, le=50.0)
    max_slippage_pips: float = Field(default=3.0, ge=0.1, le=20.0)
    is_enabled: bool = True


class CopierAccountResponse(BaseModel):
    id: str
    account_login: str
    account_name: str
    broker_profile: str
    role: str
    risk_multiplier: float
    max_lot_cap: float
    max_slippage_pips: float
    is_enabled: bool
    balance: float = 0.0
    equity: float = 0.0
    ping_latency_ms: int = 12
    is_online: bool = True


class EmergencyHaltRequest(BaseModel):
    reason: str = "Manual Master Emergency Halt Triggered"
