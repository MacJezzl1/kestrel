"""
Kestrel Core — Trades Router
Trade logging, history, and statistics endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.models import Trade
from app.schemas.signal import TradeCreate, TradeUpdate, TradeResponse, TradeListResponse, TradeStats
from app.core.security import get_current_user_id
from app.services.shield.audit import log_action

router = APIRouter(prefix="/api/trades", tags=["Trades"])


@router.get("", response_model=TradeListResponse)
async def get_trades(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    instrument: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated trade history with optional filtering."""
    query = select(Trade).where(Trade.user_id == user_id).order_by(desc(Trade.opened_at))
    
    if status:
        query = query.where(Trade.status == status)
    if instrument:
        query = query.where(Trade.instrument == instrument)
    
    # Count total
    count_query = select(func.count(Trade.id)).where(Trade.user_id == user_id)
    if status:
        count_query = count_query.where(Trade.status == status)
    if instrument:
        count_query = count_query.where(Trade.instrument == instrument)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return TradeListResponse(
        trades=[
            TradeResponse(
                id=t.id, instrument=t.instrument, direction=t.direction,
                entry_price=t.entry_price, exit_price=t.exit_price,
                lot_size=t.lot_size, pnl=t.pnl, pnl_pips=t.pnl_pips,
                status=t.status, confidence_at_entry=t.confidence_at_entry,
                model_votes_at_entry=t.model_votes_at_entry,
                opened_at=t.opened_at, closed_at=t.closed_at,
            ) for t in trades
        ],
        total=total,
    )


@router.post("", response_model=TradeResponse, status_code=201)
async def create_trade(
    data: TradeCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log a new trade execution."""
    trade = Trade(
        user_id=user_id,
        signal_id=data.signal_id,
        instrument=data.instrument,
        direction=data.direction,
        entry_price=data.entry_price,
        lot_size=data.lot_size,
        confidence_at_entry=data.confidence_at_entry,
        model_votes_at_entry=data.model_votes_at_entry,
    )
    db.add(trade)
    await db.flush()
    
    # Cloud sync to Supabase
    try:
        from app.db.supabase_client import supabase_client
        await supabase_client.record_trade({
            "instrument": trade.instrument,
            "direction": trade.direction,
            "entry_price": trade.entry_price,
            "lot_size": trade.lot_size,
            "confidence_at_entry": trade.confidence_at_entry,
            "execution_status": trade.status.upper() if trade.status else "OPEN",
            "metadata": {"user_id": user_id, "signal_id": trade.signal_id}
        })
    except Exception:
        pass
    
    await log_action(
        db, "trade_opened", user_id,
        {"trade_id": trade.id, "instrument": data.instrument, "direction": data.direction},
        ip_address=request.client.host if request.client else None,
    )
    
    return TradeResponse(
        id=trade.id, instrument=trade.instrument, direction=trade.direction,
        entry_price=trade.entry_price, exit_price=trade.exit_price,
        lot_size=trade.lot_size, pnl=trade.pnl, pnl_pips=trade.pnl_pips,
        status=trade.status, confidence_at_entry=trade.confidence_at_entry,
        model_votes_at_entry=trade.model_votes_at_entry,
        opened_at=trade.opened_at, closed_at=trade.closed_at,
    )


@router.patch("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    data: TradeUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a trade (close, set exit price, etc.)."""
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user_id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if data.exit_price is not None:
        trade.exit_price = data.exit_price
    if data.pnl is not None:
        trade.pnl = data.pnl
    if data.pnl_pips is not None:
        trade.pnl_pips = data.pnl_pips
    if data.status is not None:
        trade.status = data.status
        if data.status == "closed":
            trade.closed_at = datetime.now(timezone.utc)
    
    await db.flush()
    
    if data.status == "closed":
        await log_action(
            db, "trade_closed", user_id,
            {"trade_id": trade.id, "pnl": trade.pnl},
            ip_address=request.client.host if request.client else None,
        )
    
    return TradeResponse(
        id=trade.id, instrument=trade.instrument, direction=trade.direction,
        entry_price=trade.entry_price, exit_price=trade.exit_price,
        lot_size=trade.lot_size, pnl=trade.pnl, pnl_pips=trade.pnl_pips,
        status=trade.status, confidence_at_entry=trade.confidence_at_entry,
        model_votes_at_entry=trade.model_votes_at_entry,
        opened_at=trade.opened_at, closed_at=trade.closed_at,
    )


@router.get("/stats", response_model=TradeStats)
async def get_trade_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate trade statistics."""
    result = await db.execute(select(Trade).where(Trade.user_id == user_id))
    trades = result.scalars().all()
    
    if not trades:
        return TradeStats(
            total_trades=0, open_trades=0, closed_trades=0,
            total_pnl=0.0, win_rate=0.0, avg_pnl=0.0,
            best_trade=0.0, worst_trade=0.0, avg_confidence=0.0,
        )
    
    closed = [t for t in trades if t.status == "closed"]
    wins = [t for t in closed if t.pnl > 0]
    
    pnls = [t.pnl for t in closed] if closed else [0.0]
    confidences = [t.confidence_at_entry for t in trades if t.confidence_at_entry is not None]
    
    return TradeStats(
        total_trades=len(trades),
        open_trades=len([t for t in trades if t.status == "open"]),
        closed_trades=len(closed),
        total_pnl=round(sum(pnls), 2),
        win_rate=round(len(wins) / len(closed) * 100, 1) if closed else 0.0,
        avg_pnl=round(sum(pnls) / len(pnls), 2),
        best_trade=round(max(pnls), 2),
        worst_trade=round(min(pnls), 2),
        avg_confidence=round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
    )
