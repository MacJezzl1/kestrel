"""
Kestrel Core — MT5 Sync & Remote Execution Schemas
Pydantic v2 validation models for heartbeat, positions sync, trade reporting, and remote command queue.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HeartbeatPayload(BaseModel):
    """Payload received from MT5 EA heartbeat poll (every 10-30s)."""
    account_login: str = Field(..., description="MT5 Account Login Number")
    terminal_hash: str = Field(..., description="Hardware / Terminal fingerprint")
    broker: Optional[str] = Field(None, description="Broker server or company name")
    server: Optional[str] = Field(None, description="Connected MT5 trade server")
    currency: str = Field(default="USD", description="Account base currency")
    leverage: int = Field(default=100, description="Account leverage ratio")
    balance: float = Field(..., description="Account closed balance")
    equity: float = Field(..., description="Account live equity")
    margin: float = Field(default=0.0, description="Used margin")
    free_margin: float = Field(default=0.0, description="Available margin")
    margin_level: float = Field(default=0.0, description="Margin health level %")
    ping_latency_ms: int = Field(default=0, description="Ping latency to broker server in ms")
    regime: str = Field(default="REGIME_HYBRID", description="Active market regime")
    ea_version: str = Field(default="4.00", description="Installed EA version")
    prop_firm_profile: Optional[str] = Field(default="PROP_NONE", description="Active prop firm rules profile")
    consecutive_losses: int = Field(default=0, description="Current consecutive losses count")


class HeartbeatResponse(BaseModel):
    """Response returned to MT5 terminal after heartbeat validation."""
    status: str = "ok"
    terminal_id: str
    licensed: bool = True
    tier: str = "starter"
    circuit_breaker_tripped: bool = False
    prop_rule_breach: bool = False
    daily_loss_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    pending_commands_count: int = 0
    server_time: str


class PositionItem(BaseModel):
    """Individual open MT5 position snapshot."""
    ticket: int = Field(..., description="MT5 position order ticket")
    magic_number: int = Field(default=773571, description="EA Magic Number")
    symbol: str = Field(..., description="Instrument symbol (e.g. XAUUSD)")
    direction: str = Field(..., description="BUY or SELL")
    lots: float = Field(..., description="Position volume in lots")
    open_price: float = Field(..., description="Initial filled entry price")
    current_price: float = Field(..., description="Current live bid/ask price")
    stop_loss: Optional[float] = Field(None, description="Current Stop Loss level")
    take_profit: Optional[float] = Field(None, description="Current Take Profit level")
    floating_pnl: float = Field(default=0.0, description="Unrealized floating profit/loss")
    pnl_pips: float = Field(default=0.0, description="Floating profit in pips")
    swap: float = Field(default=0.0, description="Accumulated rollover swap")
    commission: float = Field(default=0.0, description="Broker execution commission")
    comment: Optional[str] = Field(None, description="Trade comment / confluence label")
    open_time: Optional[str] = Field(None, description="Open timestamp ISO8601")


class PositionsSyncPayload(BaseModel):
    """Batch snapshot of open positions transmitted by MT5 terminal."""
    account_login: str
    terminal_hash: str
    positions: List[PositionItem] = Field(default_factory=list)


class PositionsSyncResponse(BaseModel):
    """Response after positions table reconciliation."""
    status: str = "ok"
    synced_count: int
    total_floating_pnl: float
    updated_at: str


class TradeReportPayload(BaseModel):
    """Deal close report transmitted by MT5 upon position closure."""
    account_login: str
    terminal_hash: str
    ticket: int
    symbol: str
    direction: str
    lots: float
    open_price: float
    close_price: float
    profit: float
    pips: float = 0.0
    swap: float = 0.0
    commission: float = 0.0
    magic_number: int = 773571
    comment: Optional[str] = None
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None


class TradeReportResponse(BaseModel):
    """Response confirming trade archival and risk-engine updates."""
    status: str = "ok"
    ticket: int
    logged: bool
    circuit_breaker_active: bool
    daily_loss_pct: float


class RemoteCommandCreate(BaseModel):
    """Web or Copier request to queue a trade execution on MT5 terminal."""
    account_login: str = Field(..., description="Target MT5 account login")
    command_type: str = Field(..., description="BUY, SELL, CLOSE, CLOSE_ALL, EMERGENCY_HALT, MODIFY_STOPS")
    symbol: Optional[str] = Field(None, description="Target trading symbol")
    ticket: Optional[int] = Field(None, description="Target position ticket (for close/modify)")
    lots: Optional[float] = Field(None, description="Trade lot size")
    price: Optional[float] = Field(None, description="Order price if limit/stop")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")


class RemoteCommandResponse(BaseModel):
    """Remote command representation in queue."""
    id: str
    account_login: str
    command_type: str
    symbol: Optional[str] = None
    ticket: Optional[int] = None
    lots: Optional[float] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    created_at: str


class RemoteCommandAck(BaseModel):
    """Acknowledgment payload sent by MT5 EA after executing queued command."""
    status: str = Field(..., description="EXECUTED or FAILED")
    execution_price: Optional[float] = Field(None, description="Actual filled price")
    slippage_pips: Optional[float] = Field(default=0.0, description="Observed slippage in pips")
    error_message: Optional[str] = Field(None, description="Broker error string if rejected")
    ticket: Optional[int] = Field(None, description="Resulting position ticket")


class BroadcastCopyTradePayload(BaseModel):
    """Master account broadcast request to mirror trade to all active receivers."""
    master_account: str
    master_ticket: int
    symbol: str
    direction: str  # BUY or SELL
    lots: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
