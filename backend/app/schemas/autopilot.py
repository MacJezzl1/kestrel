"""
Kestrel Autopilot — Pydantic Schemas
Request/response models for autopilot configuration, status, and trade logging.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


# ── Configuration ─────────────────────────────────────────────────────

class AutopilotConfigUpdate(BaseModel):
    """User-facing autopilot settings (for PUT /api/autopilot/config)."""
    confidence_threshold: Optional[float] = Field(None, ge=0.50, le=0.99, description="Min swarm consensus to fire (0.50–0.99)")
    risk_per_trade_pct: Optional[float] = Field(None, ge=0.1, le=5.0, description="Risk per trade as % of equity")
    daily_max_loss_pct: Optional[float] = Field(None, ge=1.0, le=20.0, description="Daily max loss % before auto-halt")
    weekly_max_loss_pct: Optional[float] = Field(None, ge=2.0, le=30.0, description="Weekly max loss % before auto-halt")
    max_concurrent_positions: Optional[int] = Field(None, ge=1, le=20, description="Max simultaneous open trades")
    scan_interval_seconds: Optional[int] = Field(None, ge=10, le=600, description="Seconds between autopilot scans")
    instruments: Optional[List[str]] = Field(None, description="Instruments in watchlist")
    instrument_modes: Optional[Dict[str, str]] = Field(None, description="Per-instrument mode: 'autonomous' or 'suggest_only'")
    news_blackout_enabled: Optional[bool] = Field(None, description="Pause around high-impact news")
    paper_trade_required: Optional[int] = Field(None, ge=10, le=500, description="Paper trades required before live unlock")
    drift_threshold_pct: Optional[float] = Field(None, ge=5.0, le=50.0, description="% performance drift before auto-pause")


class AutopilotConfigResponse(BaseModel):
    """Full autopilot config returned from GET /api/autopilot/config."""
    id: str
    user_id: str
    is_enabled: bool
    mode: str
    confidence_threshold: float
    risk_per_trade_pct: float
    daily_max_loss_pct: float
    weekly_max_loss_pct: float
    max_concurrent_positions: int
    scan_interval_seconds: int
    instruments: List[str]
    instrument_modes: Dict[str, str]
    news_blackout_enabled: bool
    paper_trade_count: int
    paper_trade_required: int
    performance_baseline_winrate: float
    drift_threshold_pct: float
    is_drift_paused: bool
    daily_loss_today: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Status ────────────────────────────────────────────────────────────

class CircuitBreakerStatus(BaseModel):
    """Current state of each circuit breaker."""
    daily_loss_breaker: bool = Field(description="True if daily loss limit has NOT been hit")
    weekly_loss_breaker: bool = Field(description="True if weekly loss limit has NOT been hit")
    max_positions: bool = Field(description="True if under max position cap")
    drawdown_guard: bool = Field(description="True if drawdown level permits trading")
    news_blackout: bool = Field(description="True if outside news blackout window")
    performance_drift: bool = Field(description="True if no performance drift detected")


class AutopilotStatusResponse(BaseModel):
    """Current autopilot state from GET /api/autopilot/status."""
    is_running: bool
    mode: str
    is_enabled: bool
    is_drift_paused: bool
    paper_trade_count: int
    paper_trade_required: int
    paper_progress_pct: float
    can_unlock_live: bool
    total_decisions: int
    recent_executed: int
    recent_skipped: int
    recent_paper: int
    last_decision: Optional[Dict[str, Any]] = None
    last_5_decisions: List[Dict[str, Any]] = []
    circuit_breakers: Optional[CircuitBreakerStatus] = None


# ── Trade Log ─────────────────────────────────────────────────────────

class AutopilotTradeLogEntry(BaseModel):
    """Individual autopilot decision record."""
    instrument: str
    timeframe: str
    direction: str
    confidence: float
    action: str  # "executed", "skipped", "paper_logged"
    reason: str
    gate_results: List[Dict[str, Any]]
    lot_size: float = 0.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: str


class AutopilotTradeLogResponse(BaseModel):
    """Paginated autopilot decision log."""
    decisions: List[AutopilotTradeLogEntry]
    total: int


# ── Performance ───────────────────────────────────────────────────────

class AutopilotPerformanceResponse(BaseModel):
    """Rolling performance metrics vs baseline."""
    live_winrate: float
    baseline_winrate: float
    drift_pct: float
    drift_threshold_pct: float
    is_drifted: bool
    total_paper_trades: int
    total_live_trades: int
    paper_profit: float
    live_profit: float
