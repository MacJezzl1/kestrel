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
    """Get the most recent signals from Supabase cloud or local DB."""
    from app.db.supabase_client import supabase_client
    
    # 1. Try Supabase cloud signals
    try:
        sb_signals = await supabase_client.get_latest_signals(instrument=instrument, limit=limit)
        if sb_signals and len(sb_signals) > 0:
            sig_responses = []
            for s in sb_signals:
                created_str = s.get("created_at") or datetime.now(timezone.utc).isoformat()
                sig_responses.append(
                    SignalResponse(
                        id=str(s.get("id")),
                        instrument=str(s.get("instrument", "Volatility 100 Index")),
                        timeframe=str(s.get("timeframe", "H1")),
                        direction=str(s.get("direction", "BUY")).lower(),
                        confidence=float(s.get("confidence", 0.91)),
                        regime=str(s.get("regime", "Trending Bullish")),
                        model_votes={"trend_following": str(s.get("direction", "BUY")).lower(), "order_flow": str(s.get("direction", "BUY")).lower()},
                        model_confidences={"trend_following": float(s.get("confidence", 0.91)), "order_flow": float(s.get("confidence", 0.91))},
                        entry_price=float(s["entry_price"]) if s.get("entry_price") is not None else None,
                        stop_loss=float(s["stop_loss"]) if s.get("stop_loss") is not None else None,
                        take_profit=float(s["take_profit"]) if s.get("take_profit") is not None else None,
                        created_at=datetime.fromisoformat(created_str.replace("Z", "+00:00")),
                    )
                )
            if len(sig_responses) > 0:
                return SignalListResponse(signals=sig_responses, total=len(sig_responses))
    except Exception:
        pass

    # 2. Fallback to local SQLite database
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


@router.get("/ai/ollama-status")
async def get_ollama_status(user_id: str = Depends(get_current_user_id)):
    """Check local/cloud Ollama server connection and available models."""
    from app.services.ensemble.ollama_client import ollama_client
    return await ollama_client.check_status()


@router.post("/ai/deep-reasoning")
async def run_deep_reasoning(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
):
    """Run DeepSeek-R1 / Llama 3.3 quantitative market reasoning."""
    from app.services.ensemble.ollama_client import ollama_client
    instrument = payload.get("instrument", "EURUSD")
    timeframe = payload.get("timeframe", "H1")
    direction = payload.get("direction", "buy")
    confidence = float(payload.get("confidence", 0.88))
    regime = payload.get("regime", "trending")
    model = payload.get("model", "deepseek-r1:latest")

    return await ollama_client.reason_market_setup(
        instrument=instrument,
        timeframe=timeframe,
        direction=direction,
        confidence=confidence,
        regime=regime,
        model=model
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
