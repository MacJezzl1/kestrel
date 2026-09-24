"""
Kestrel Autopilot — REST API Router
Endpoints for controlling and monitoring the autonomous trading engine.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.models import AutopilotConfig
from app.schemas.autopilot import (
    AutopilotConfigUpdate,
    AutopilotConfigResponse,
    AutopilotStatusResponse,
    AutopilotTradeLogResponse,
    AutopilotTradeLogEntry,
    AutopilotPerformanceResponse,
    CircuitBreakerStatus,
)
from app.core.security import get_current_user_id
from app.services.shield.audit import log_action
from app.services.autopilot.autopilot import autopilot_engine

router = APIRouter(prefix="/api/autopilot", tags=["Autopilot"])


# ── Helper: Get or Create Config ──────────────────────────────────────

async def _get_or_create_config(
    db: AsyncSession, user_id: str
) -> AutopilotConfig:
    """Fetch user's autopilot config, creating one with defaults if none exists."""
    result = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = AutopilotConfig(user_id=user_id)
        db.add(config)
        await db.flush()

    return config


# ── GET /api/autopilot/status ─────────────────────────────────────────

@router.get("/status", response_model=AutopilotStatusResponse)
async def get_autopilot_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current autopilot state, circuit breaker statuses, and recent decisions."""
    config = await _get_or_create_config(db, user_id)
    engine_status = autopilot_engine.get_status()

    paper_progress = (
        (config.paper_trade_count / config.paper_trade_required * 100)
        if config.paper_trade_required > 0 else 100.0
    )
    can_unlock = config.paper_trade_count >= config.paper_trade_required

    return AutopilotStatusResponse(
        is_running=engine_status["is_running"],
        mode=config.mode,
        is_enabled=config.is_enabled,
        is_drift_paused=config.is_drift_paused,
        paper_trade_count=config.paper_trade_count,
        paper_trade_required=config.paper_trade_required,
        paper_progress_pct=round(min(paper_progress, 100.0), 1),
        can_unlock_live=can_unlock,
        total_decisions=engine_status["total_decisions"],
        recent_executed=engine_status["recent_executed"],
        recent_skipped=engine_status["recent_skipped"],
        recent_paper=engine_status["recent_paper"],
        last_decision=engine_status["last_decision"],
        last_5_decisions=engine_status["last_5_decisions"],
        circuit_breakers=CircuitBreakerStatus(
            daily_loss_breaker=True,
            weekly_loss_breaker=True,
            max_positions=True,
            drawdown_guard=True,
            news_blackout=True,
            performance_drift=not config.is_drift_paused,
        ),
    )


# ── GET /api/autopilot/config ────────────────────────────────────────

@router.get("/config", response_model=AutopilotConfigResponse)
async def get_autopilot_config(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's autopilot configuration."""
    config = await _get_or_create_config(db, user_id)
    return AutopilotConfigResponse(
        id=config.id,
        user_id=config.user_id,
        is_enabled=config.is_enabled,
        mode=config.mode,
        confidence_threshold=config.confidence_threshold,
        risk_per_trade_pct=config.risk_per_trade_pct,
        daily_max_loss_pct=config.daily_max_loss_pct,
        weekly_max_loss_pct=config.weekly_max_loss_pct,
        max_concurrent_positions=config.max_concurrent_positions,
        scan_interval_seconds=config.scan_interval_seconds,
        instruments=config.instruments or ["Volatility 100 Index"],
        instrument_modes=config.instrument_modes or {},
        news_blackout_enabled=config.news_blackout_enabled,
        paper_trade_count=config.paper_trade_count,
        paper_trade_required=config.paper_trade_required,
        performance_baseline_winrate=config.performance_baseline_winrate,
        drift_threshold_pct=config.drift_threshold_pct,
        is_drift_paused=config.is_drift_paused,
        daily_loss_today=config.daily_loss_today,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ── PUT /api/autopilot/config ────────────────────────────────────────

@router.put("/config", response_model=AutopilotConfigResponse)
async def update_autopilot_config(
    data: AutopilotConfigUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update autopilot settings."""
    config = await _get_or_create_config(db, user_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, "autopilot_config_updated", user_id,
        {"fields_updated": list(update_data.keys())},
        ip_address=request.client.host if request.client else None,
    )

    return AutopilotConfigResponse(
        id=config.id,
        user_id=config.user_id,
        is_enabled=config.is_enabled,
        mode=config.mode,
        confidence_threshold=config.confidence_threshold,
        risk_per_trade_pct=config.risk_per_trade_pct,
        daily_max_loss_pct=config.daily_max_loss_pct,
        weekly_max_loss_pct=config.weekly_max_loss_pct,
        max_concurrent_positions=config.max_concurrent_positions,
        scan_interval_seconds=config.scan_interval_seconds,
        instruments=config.instruments or ["Volatility 100 Index"],
        instrument_modes=config.instrument_modes or {},
        news_blackout_enabled=config.news_blackout_enabled,
        paper_trade_count=config.paper_trade_count,
        paper_trade_required=config.paper_trade_required,
        performance_baseline_winrate=config.performance_baseline_winrate,
        drift_threshold_pct=config.drift_threshold_pct,
        is_drift_paused=config.is_drift_paused,
        daily_loss_today=config.daily_loss_today,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ── POST /api/autopilot/enable ───────────────────────────────────────

@router.post("/enable")
async def enable_autopilot(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate autopilot. Starts in paper mode first.
    The engine begins its background scan loop immediately.
    """
    config = await _get_or_create_config(db, user_id)
    config.is_enabled = True
    if config.mode not in ("paper", "live"):
        config.mode = "paper"
    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    if not autopilot_engine.is_running:
        await autopilot_engine.start()

    await log_action(
        db, "autopilot_enabled", user_id,
        {"mode": config.mode},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "status": "enabled",
        "mode": config.mode,
        "message": f"✈️ Autopilot activated in {config.mode.upper()} mode. Scanning {len(config.instruments or [])} instrument(s).",
    }


# ── POST /api/autopilot/disable ──────────────────────────────────────

@router.post("/disable")
async def disable_autopilot(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Kill switch — immediately stops all autopilot activity.
    Does NOT close existing positions (use /kill for that).
    """
    config = await _get_or_create_config(db, user_id)
    config.is_enabled = False
    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await autopilot_engine.stop()

    await log_action(
        db, "autopilot_disabled", user_id,
        {"reason": "user_disabled"},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "status": "disabled",
        "message": "🛑 Autopilot stopped. No new trades will be opened. Existing positions remain open.",
    }


# ── POST /api/autopilot/kill ─────────────────────────────────────────

@router.post("/kill")
async def kill_autopilot(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Emergency kill — stops autopilot AND sends CLOSE_ALL to MT5.
    This is the nuclear option.
    """
    config = await _get_or_create_config(db, user_id)
    config.is_enabled = False
    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await autopilot_engine.emergency_kill()

    await log_action(
        db, "autopilot_emergency_kill", user_id,
        {"reason": "emergency_kill_button"},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "status": "killed",
        "message": "🚨 EMERGENCY KILL — Autopilot stopped and CLOSE ALL command sent to MT5 broker.",
    }


# ── POST /api/autopilot/unlock-live ──────────────────────────────────

@router.post("/unlock-live")
async def unlock_live_mode(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upgrade from paper to live mode.
    Only succeeds if paper-trade threshold has been met.
    """
    config = await _get_or_create_config(db, user_id)

    if config.paper_trade_count < config.paper_trade_required:
        remaining = config.paper_trade_required - config.paper_trade_count
        raise HTTPException(
            status_code=403,
            detail=f"Cannot unlock live mode. {remaining} more paper trades required "
                   f"({config.paper_trade_count}/{config.paper_trade_required} completed)."
        )

    config.mode = "live"
    config.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, "autopilot_unlock_live", user_id,
        {"paper_trades_completed": config.paper_trade_count},
        ip_address=request.client.host if request.client else None,
    )

    return {
        "status": "live_unlocked",
        "message": f"🚀 Live mode unlocked! {config.paper_trade_count} paper trades completed. Autopilot will now execute real trades.",
    }


# ── GET /api/autopilot/trade-log ─────────────────────────────────────

@router.get("/trade-log", response_model=AutopilotTradeLogResponse)
async def get_autopilot_trade_log(
    limit: int = 50,
    action_filter: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """Get paginated log of all autopilot decisions."""
    decisions = autopilot_engine.recent_decisions

    if action_filter:
        decisions = [d for d in decisions if d.get("action") == action_filter]

    # Most recent first
    decisions = list(reversed(decisions))[:limit]

    entries = [
        AutopilotTradeLogEntry(
            instrument=d.get("instrument", ""),
            timeframe=d.get("timeframe", "H1"),
            direction=d.get("direction", "hold"),
            confidence=d.get("confidence", 0.0),
            action=d.get("action", "skipped"),
            reason=d.get("reason", ""),
            gate_results=d.get("gate_results", []),
            lot_size=d.get("lot_size", 0.0),
            entry_price=d.get("entry_price"),
            stop_loss=d.get("stop_loss"),
            take_profit=d.get("take_profit"),
            timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
        for d in decisions
    ]

    return AutopilotTradeLogResponse(
        decisions=entries,
        total=len(entries),
    )


# ── GET /api/autopilot/performance ───────────────────────────────────

@router.get("/performance", response_model=AutopilotPerformanceResponse)
async def get_autopilot_performance(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Rolling performance metrics vs baseline."""
    config = await _get_or_create_config(db, user_id)
    engine_status = autopilot_engine.get_status()

    baseline = config.performance_baseline_winrate
    live_wr = 0.0  # Will be calculated from actual trade results
    drift = baseline - live_wr if baseline > 0 else 0.0
    drift_pct = (drift / baseline * 100) if baseline > 0 else 0.0

    return AutopilotPerformanceResponse(
        live_winrate=live_wr,
        baseline_winrate=baseline,
        drift_pct=round(drift_pct, 1),
        drift_threshold_pct=config.drift_threshold_pct,
        is_drifted=config.is_drift_paused,
        total_paper_trades=engine_status.get("paper_trades_total", 0),
        total_live_trades=engine_status.get("live_trades_total", 0),
        paper_profit=0.0,
        live_profit=0.0,
    )
