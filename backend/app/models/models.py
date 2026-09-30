"""
Kestrel Core — ORM Models
SQLAlchemy models for users, licenses, signals, trades, and audit logs.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, DateTime, Text, JSON,
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
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(64), nullable=True)
    token_version = Column(Integer, default=0, nullable=False)
    tenant_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    license = relationship("License", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    passkeys = relationship("PasskeyCredential", back_populates="user")
    terminals = relationship("MT5Terminal", back_populates="user")


class License(Base):
    __tablename__ = "licenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    tenant_id = Column(String(64), nullable=True, index=True)
    account_login = Column(String(64), nullable=True, index=True)
    terminal_hash = Column(String(128), nullable=True)
    tier = Column(String(32), default="starter", nullable=False)  # starter, pro, institutional
    status = Column(String(20), default="active", nullable=False)  # active, trial, suspended, expired
    max_risk_per_trade = Column(Float, default=1.0)
    max_daily_loss_pct = Column(Float, default=5.0)
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


class AutopilotConfig(Base):
    """Per-user Autopilot configuration and state tracking."""
    __tablename__ = "autopilot_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    mode = Column(String(20), default="paper")  # "paper", "live", "suggest_only"
    confidence_threshold = Column(Float, default=0.80)
    risk_per_trade_pct = Column(Float, default=1.0)
    daily_max_loss_pct = Column(Float, default=5.0)
    weekly_max_loss_pct = Column(Float, default=10.0)
    max_concurrent_positions = Column(Integer, default=3)
    scan_interval_seconds = Column(Integer, default=60)
    instruments = Column(JSON, default=lambda: ["Volatility 100 Index"])
    instrument_modes = Column(JSON, default=dict)  # per-instrument: "autonomous" or "suggest_only"
    news_blackout_enabled = Column(Boolean, default=True)
    paper_trade_count = Column(Integer, default=0)
    paper_trade_required = Column(Integer, default=50)
    performance_baseline_winrate = Column(Float, default=0.0)
    drift_threshold_pct = Column(Float, default=15.0)
    is_drift_paused = Column(Boolean, default=False)
    daily_loss_today = Column(Float, default=0.0)
    daily_loss_reset_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")


class Order(Base):
    """Orders table for tracking order lifecycle, pending/filled status, and idempotency."""
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String, nullable=True)
    account_number = Column(String(64), nullable=True)
    client_order_id = Column(String(64), unique=True, nullable=False, index=True)  # Idempotency key
    instrument = Column(String(32), nullable=False, index=True)
    order_type = Column(String(16), default="MARKET", nullable=False)  # MARKET, LIMIT, STOP
    direction = Column(String(8), nullable=False)  # BUY, SELL
    qty = Column(Float, default=0.01, nullable=False)
    price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, SUBMITTED, FILLED, REJECTED, CANCELLED
    filled_price = Column(Float, nullable=True)
    filled_qty = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    mt5_ticket = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="orders")


class AiLog(Base):
    """Audit log for multi-model AI orchestration queries, voting breakdown, and latencies."""
    __tablename__ = "ai_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    prompt_type = Column(String(64), nullable=False, index=True)  # "SIGNAL_ANALYSIS", "MARKET_INSIGHT", "CHAT"
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String(64), nullable=False)  # "ENSEMBLE_QUORUM", "OLLAMA_MISTRAL", "CLAUDE_3_5", "GPT_4O"
    consensus_score = Column(Float, default=0.0)
    models_queried = Column(JSON, default=list)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User")


class PasskeyCredential(Base):
    """Registered WebAuthn passkey credentials for biometric / security key MFA."""
    __tablename__ = "passkey_credentials"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    credential_id = Column(String(255), unique=True, nullable=False, index=True)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0)
    device_name = Column(String(100), default="Passkey")
    transports = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="passkeys")


class MT5Terminal(Base):
    """Hardware-bound MT5 client terminal reporting heartbeat, account state, and ping latency."""
    __tablename__ = "mt5_terminals"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    account_login = Column(String(64), nullable=False, index=True)
    terminal_hash = Column(String(128), nullable=False, index=True)
    broker = Column(String(128), nullable=True)
    server = Column(String(128), nullable=True)
    currency = Column(String(16), default="USD")
    leverage = Column(Integer, default=100)
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)
    margin_level = Column(Float, default=0.0)
    ping_latency_ms = Column(Integer, default=0)
    regime = Column(String(64), default="REGIME_HYBRID")
    ea_version = Column(String(32), default="4.00")
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="terminals")
    positions = relationship("LivePosition", back_populates="terminal", cascade="all, delete-orphan")
    risk_metric = relationship("RiskMetric", back_populates="terminal", uselist=False, cascade="all, delete-orphan")
    commands = relationship("RemoteCommand", back_populates="terminal", cascade="all, delete-orphan")


class LivePosition(Base):
    """Snapshot of open MT5 position with live floating PnL and ticket synchronization."""
    __tablename__ = "live_positions"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    terminal_id = Column(String, ForeignKey("mt5_terminals.id"), nullable=False, index=True)
    account_login = Column(String(64), nullable=False, index=True)
    ticket = Column(BigInteger, nullable=False, index=True)
    magic_number = Column(BigInteger, default=773571)
    symbol = Column(String(32), nullable=False, index=True)
    direction = Column(String(16), nullable=False)  # BUY or SELL
    lots = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    floating_pnl = Column(Float, default=0.0)
    pnl_pips = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    comment = Column(String(255), nullable=True)
    open_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    terminal = relationship("MT5Terminal", back_populates="positions")


class RiskMetric(Base):
    """Real-time account risk tracking, daily loss % and prop-firm drawdown circuit breakers."""
    __tablename__ = "risk_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    terminal_id = Column(String, ForeignKey("mt5_terminals.id"), unique=True, nullable=False, index=True)
    account_login = Column(String(64), nullable=False, index=True)
    starting_equity_day = Column(Float, default=0.0, nullable=False)
    peak_equity = Column(Float, default=0.0, nullable=False)
    current_equity = Column(Float, default=0.0, nullable=False)
    current_balance = Column(Float, default=0.0, nullable=False)
    daily_loss_pct = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    consecutive_losses = Column(Integer, default=0)
    circuit_breaker_tripped = Column(Boolean, default=False)
    prop_rule_breach = Column(Boolean, default=False)
    prop_firm_profile = Column(String(32), default="PROP_NONE")
    reset_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    terminal = relationship("MT5Terminal", back_populates="risk_metric")


class RemoteCommand(Base):
    """Web-to-MT5 command queue (BUY, SELL, CLOSE, CLOSE_ALL, EMERGENCY_HALT, MODIFY_STOPS)."""
    __tablename__ = "remote_commands"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    terminal_id = Column(String, ForeignKey("mt5_terminals.id"), nullable=False, index=True)
    account_login = Column(String(64), nullable=False, index=True)
    command_type = Column(String(32), nullable=False)  # BUY, SELL, CLOSE, CLOSE_ALL, EMERGENCY_HALT, MODIFY_STOPS
    symbol = Column(String(32), nullable=True)
    ticket = Column(BigInteger, nullable=True)
    lots = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String(20), default="PENDING", index=True)  # PENDING, DISPATCHED, EXECUTED, FAILED
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    terminal = relationship("MT5Terminal", back_populates="commands")


class CopyTrade(Base):
    """Multi-client PAMM broadcast log tracking receiver execution, latency, and slippage."""
    __tablename__ = "copy_trades"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    master_ticket = Column(BigInteger, nullable=False, index=True)
    master_symbol = Column(String(32), nullable=False)
    master_direction = Column(String(16), nullable=False)
    master_lots = Column(Float, nullable=False)
    receiver_terminal_id = Column(String, ForeignKey("mt5_terminals.id"), nullable=False, index=True)
    receiver_account = Column(String(64), nullable=False, index=True)
    receiver_ticket = Column(BigInteger, nullable=True)
    risk_multiplier = Column(Float, default=1.0)
    executed_lots = Column(Float, nullable=True)
    execution_price = Column(Float, nullable=True)
    slippage_pips = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(20), default="PENDING", index=True)  # PENDING, EXECUTED, REJECTED, SKIPPED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    receiver_terminal = relationship("MT5Terminal")


class NotificationConfig(Base):
    """User/Tenant notification dispatch configuration for Telegram & Discord webhooks."""
    __tablename__ = "notification_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    telegram_enabled = Column(Boolean, default=False)
    telegram_bot_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(128), nullable=True)
    discord_enabled = Column(Boolean, default=False)
    discord_webhook_url = Column(Text, nullable=True)
    alert_trade_signals = Column(Boolean, default=True)
    alert_prop_firm_risk = Column(Boolean, default=True)
    alert_circuit_breaker = Column(Boolean, default=True)
    alert_high_impact_news = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CopierAccount(Base):
    """Multi-broker PAMM receiver and master account configuration."""
    __tablename__ = "copier_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=True, index=True)
    account_login = Column(String(64), unique=True, nullable=False, index=True)
    account_name = Column(String(128), nullable=False)
    broker_profile = Column(String(64), nullable=False)  # FTMO, THE5ERS, FUNDING_PIPS, TOPSTEP, ICMARKETS, DERIV, PEPPERSTONE, EXNESS
    role = Column(String(20), default="RECEIVER", index=True)  # MASTER or RECEIVER
    risk_multiplier = Column(Float, default=1.0)
    max_lot_cap = Column(Float, default=5.0)
    max_slippage_pips = Column(Float, default=3.0)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

