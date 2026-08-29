"""
Kestrel Core — Signal & Trade Schemas
Pydantic models for signal generation and trade management.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


# --- Signal Schemas ---

class SignalRequest(BaseModel):
    instrument: str = Field(..., description="Trading instrument (e.g., EURUSD)")
    timeframe: str = Field("H1", description="Timeframe (e.g., M5, H1, D1)")


class ModelVote(BaseModel):
    category: str
    direction: str
    confidence: float
    reasoning: Optional[str] = None


class SignalResponse(BaseModel):
    id: str
    instrument: str
    timeframe: str
    direction: str
    confidence: float
    regime: str
    model_votes: Dict[str, str]
    model_confidences: Dict[str, float]
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int


# --- Trade Schemas ---

class TradeCreate(BaseModel):
    instrument: str
    direction: str
    entry_price: float
    lot_size: float = 0.01
    signal_id: Optional[str] = None
    confidence_at_entry: Optional[float] = None
    model_votes_at_entry: Optional[Dict[str, str]] = None


class TradeUpdate(BaseModel):
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pips: Optional[float] = None
    status: Optional[str] = None


class TradeResponse(BaseModel):
    id: str
    instrument: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    lot_size: float
    pnl: float
    pnl_pips: float
    status: str
    confidence_at_entry: Optional[float]
    model_votes_at_entry: Optional[Dict[str, str]]
    opened_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    trades: List[TradeResponse]
    total: int


class TradeStats(BaseModel):
    total_trades: int
    open_trades: int
    closed_trades: int
    total_pnl: float
    win_rate: float
    avg_pnl: float
    best_trade: float
    worst_trade: float
    avg_confidence: float


# --- Dashboard Schemas ---

class DashboardSummary(BaseModel):
    total_pnl: float
    total_trades: int
    win_rate: float
    ai_accuracy: float
    open_trades: int
    today_pnl: float
    week_pnl: float
    month_pnl: float
    current_regime: str
    active_models: List[str]
    connection_status: str
    live_balance: Optional[float] = 0.0
    live_equity: Optional[float] = 0.0
    account_number: Optional[str] = "MT5-Offline"
    broker_name: Optional[str] = "MetaTrader 5"
    recovery_level: Optional[str] = "OPTIMAL"
    recovery_multiplier: Optional[float] = 1.0
    auto_trade_enabled: Optional[bool] = True


class DrawdownInfo(BaseModel):
    current_drawdown_pct: float
    current_drawdown_value: float
    max_drawdown_pct: float
    max_drawdown_value: float
    guard_threshold: float
    guard_active: bool
    guard_reason: Optional[str] = None
    risk_per_trade: float


class PLBreakdown(BaseModel):
    by_instrument: Dict[str, float]
    by_session: Dict[str, float]
    by_model_category: Dict[str, float]
    by_day_of_week: Dict[str, float]
