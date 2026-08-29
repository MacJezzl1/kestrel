"""
Kestrel Core — Signals Router
Signal generation and retrieval endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.database import get_db
from app.models.models import Signal
from app.schemas.signal import SignalRequest, SignalResponse, SignalListResponse
from app.core.security import get_current_user_id
from app.services.ensemble.engine import ensemble_engine
from app.services.shield.license_manager import validate_license, increment_signal_count
from app.services.shield.audit import log_action

router = APIRouter(prefix="/api/signals", tags=["Signals"])


@router.post("/generate", response_model=SignalResponse)
async def generate_signal(
    data: SignalRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI signal for the given instrument and timeframe."""
    # Validate license
    license_check = await validate_license(db, user_id)
    if not license_check["valid"]:
        raise HTTPException(status_code=403, detail=license_check["reason"])
    
    # Generate signal from ensemble
    signal_data = ensemble_engine.generate_signal(data.instrument, data.timeframe)
    
    # Persist signal locally
    signal = Signal(**{
        "instrument": signal_data["instrument"],
        "timeframe": signal_data["timeframe"],
        "direction": signal_data["direction"],
        "confidence": signal_data["confidence"],
        "regime": signal_data["regime"],
        "model_votes": signal_data["model_votes"],
        "model_confidences": signal_data["model_confidences"],
        "entry_price": signal_data["entry_price"],
        "stop_loss": signal_data["stop_loss"],
        "take_profit": signal_data["take_profit"],
    })
    db.add(signal)
    await db.flush()
    
    # Cloud sync to Supabase
    try:
        from app.db.supabase_client import supabase_client
        await supabase_client.record_signal({
            "instrument": signal.instrument,
            "timeframe": signal.timeframe,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "regime": signal.regime,
            "buy_votes": signal_data.get("swarm_summary", {}).get("buy_votes", 0),
            "sell_votes": signal_data.get("swarm_summary", {}).get("sell_votes", 0),
            "hold_votes": signal_data.get("swarm_summary", {}).get("hold_votes", 0),
            "total_models": 100,
            "consensus_percentage": signal_data.get("swarm_summary", {}).get("consensus_pct", signal.confidence * 100),
            "leading_swarm": signal_data.get("swarm_summary", {}).get("leading_swarm", "GENERAL_CONSENSUS"),
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "swarm_details": signal_data.get("swarm_summary", {})
        })
    except Exception:
        pass
    
    # Increment signal usage
    await increment_signal_count(db, user_id)
    
    # Audit log
    await log_action(
        db, "signal_generated", user_id,
        {
            "signal_id": signal.id,
            "instrument": data.instrument,
            "timeframe": data.timeframe,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "regime": signal.regime,
        },
        ip_address=request.client.host if request.client else None,
    )
    
    return SignalResponse(
        id=signal.id,
        instrument=signal.instrument,
        timeframe=signal.timeframe,
        direction=signal.direction,
        confidence=signal.confidence,
        regime=signal.regime,
        model_votes=signal.model_votes,
        model_confidences=signal.model_confidences,
        entry_price=signal.entry_price,
        stop_loss=signal.stop_loss,
        take_profit=signal.take_profit,
        created_at=signal.created_at,
    )


@router.get("/latest", response_model=SignalListResponse)
async def get_latest_signals(
    limit: int = 20,
    instrument: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent signals."""
    query = select(Signal).order_by(desc(Signal.created_at)).limit(limit)
    if instrument:
        query = query.where(Signal.instrument == instrument)
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    return SignalListResponse(
        signals=[
            SignalResponse(
                id=s.id, instrument=s.instrument, timeframe=s.timeframe,
                direction=s.direction, confidence=s.confidence, regime=s.regime,
                model_votes=s.model_votes, model_confidences=s.model_confidences,
                entry_price=s.entry_price, stop_loss=s.stop_loss,
                take_profit=s.take_profit, created_at=s.created_at,
            ) for s in signals
        ],
        total=len(signals),
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific signal with full model category breakdown."""
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return SignalResponse(
        id=signal.id, instrument=signal.instrument, timeframe=signal.timeframe,
        direction=signal.direction, confidence=signal.confidence, regime=signal.regime,
        model_votes=signal.model_votes, model_confidences=signal.model_confidences,
        entry_price=signal.entry_price, stop_loss=signal.stop_loss,
        take_profit=signal.take_profit, created_at=signal.created_at,
    )
