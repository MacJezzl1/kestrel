"""
Kestrel Core — ORM Models
SQLAlchemy models for users, licenses, signals, trades, and audit logs.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    license = relationship("License", back_populates="user", uselist=False)
    trades = relationship("Trade", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")


class License(Base):
    __tablename__ = "licenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    tier = Column(String(20), default="free", nullable=False)  # free, pro, enterprise
    status = Column(String(20), default="active", nullable=False)  # active, suspended, expired
    signals_used_today = Column(Integer, default=0)
    last_signal_reset = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    bound_devices = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="license")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=generate_uuid)
    instrument = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False)
    direction = Column(String(10), nullable=False)  # buy, sell, hold
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    regime = Column(String(20), nullable=False)  # trending, ranging, volatile
    model_votes = Column(JSON, nullable=False)  # {"trend_following": "buy", "mean_reversion": "hold", ...}
    model_confidences = Column(JSON, nullable=False)  # {"trend_following": 0.85, ...}
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    metadata_extra = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    trades = relationship("Trade", back_populates="signal")

    __table_args__ = (
        Index("ix_signals_instrument_time", "instrument", "created_at"),
    )


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    signal_id = Column(String, ForeignKey("signals.id"), nullable=True)
    instrument = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # buy, sell
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    lot_size = Column(Float, default=0.01)
    pnl = Column(Float, default=0.0)
    pnl_pips = Column(Float, default=0.0)
    status = Column(String(20), default="open")  # open, closed, cancelled
    confidence_at_entry = Column(Float, nullable=True)
    model_votes_at_entry = Column(JSON, nullable=True)
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")

    __table_args__ = (
        Index("ix_trades_user_time", "user_id", "opened_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class ApiKey(Base):
    """Long-lived API keys for bridge integrations (MT5 EA, TradingView, etc.)."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(8), nullable=False)  # First 8 chars shown for identification
    hashed_key = Column(String(255), nullable=False)
    permissions = Column(JSON, default=lambda: ["signals", "trades"])
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="api_keys")
