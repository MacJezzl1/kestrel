"""
Kestrel Core — MT5 Synchronization & Remote Execution Router
Production API endpoints for MT5 terminal heartbeats, position reconciliation,
closed trade reporting, prop-firm risk monitoring, and remote order queueing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.models.models import (
    MT5Terminal, LivePosition, RiskMetric, RemoteCommand, CopyTrade, Trade, License
)
from app.schemas.sync import (
    HeartbeatPayload, HeartbeatResponse,
    PositionsSyncPayload, PositionsSyncResponse,
    TradeReportPayload, TradeReportResponse,
    RemoteCommandCreate, RemoteCommandResponse, RemoteCommandAck,
    BroadcastCopyTradePayload, PositionItem
)
from app.routers.ws_sync import ws_manager

router = APIRouter(prefix="/api/v1/sync", tags=["MT5 Synchronization"])


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def process_heartbeat(
    payload: HeartbeatPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest periodic heartbeat from MT5 EA.
    Tracks terminal connectivity, calculates drawdown and daily loss,
    enforces prop firm rules, and returns pending commands.
    """
    now = datetime.now(timezone.utc)

    # 1. Fetch or initialize MT5 Terminal
    stmt = select(MT5Terminal).where(
        MT5Terminal.account_login == payload.account_login,
        MT5Terminal.terminal_hash == payload.terminal_hash
    )
    result = await db.execute(stmt)
    terminal = result.scalars().first()

    if not terminal:
        terminal = MT5Terminal(
            id=str(uuid.uuid4()),
            account_login=payload.account_login,
            terminal_hash=payload.terminal_hash,
            broker=payload.broker,
            server=payload.server,
            currency=payload.currency,
            leverage=payload.leverage,
            balance=payload.balance,
            equity=payload.equity,
            margin=payload.margin,
            free_margin=payload.free_margin,
            margin_level=payload.margin_level,
            ping_latency_ms=payload.ping_latency_ms,
            regime=payload.regime,
            ea_version=payload.ea_version,
            is_active=True,
            last_heartbeat=now,
        )
        db.add(terminal)
        await db.flush()
    else:
        terminal.broker = payload.broker or terminal.broker
        terminal.server = payload.server or terminal.server
        terminal.balance = payload.balance
        terminal.equity = payload.equity
        terminal.margin = payload.margin
        terminal.free_margin = payload.free_margin
        terminal.margin_level = payload.margin_level
        terminal.ping_latency_ms = payload.ping_latency_ms
        terminal.regime = payload.regime
        terminal.ea_version = payload.ea_version
        terminal.is_active = True
        terminal.last_heartbeat = now
        terminal.updated_at = now

    # 2. Check License Tier
    lic_stmt = select(License).where(
        (License.account_login == payload.account_login) |
        (License.terminal_hash == payload.terminal_hash)
    )
    lic_res = await db.execute(lic_stmt)
    license_obj = lic_res.scalars().first()
    tier = license_obj.tier if license_obj else "starter"

    # 3. Update or Initialize Risk Metrics
    risk_stmt = select(RiskMetric).where(RiskMetric.terminal_id == terminal.id)
    risk_res = await db.execute(risk_stmt)
    risk_metric = risk_res.scalars().first()

    if not risk_metric:
        risk_metric = RiskMetric(
            id=str(uuid.uuid4()),
            terminal_id=terminal.id,
            account_login=payload.account_login,
            starting_equity_day=payload.equity,
            peak_equity=payload.equity,
            current_equity=payload.equity,
            current_balance=payload.balance,
            daily_loss_pct=0.0,
            max_drawdown_pct=0.0,
            consecutive_losses=payload.consecutive_losses,
            circuit_breaker_tripped=False,
            prop_rule_breach=False,
            prop_firm_profile=payload.prop_firm_profile or "PROP_NONE",
            reset_date=now,
        )
        db.add(risk_metric)
        await db.flush()
    else:
        # Check if day has reset (UTC midnight rollover)
        if risk_metric.reset_date.date() < now.date():
            risk_metric.starting_equity_day = payload.equity
            risk_metric.reset_date = now
            risk_metric.consecutive_losses = 0
            risk_metric.circuit_breaker_tripped = False

        if payload.equity > risk_metric.peak_equity:
            risk_metric.peak_equity = payload.equity

        risk_metric.current_equity = payload.equity
        risk_metric.current_balance = payload.balance
        risk_metric.consecutive_losses = payload.consecutive_losses

        # Math calculations
        start_eq = max(risk_metric.starting_equity_day, 1.0)
        peak_eq = max(risk_metric.peak_equity, 1.0)

        daily_loss = max(0.0, (start_eq - payload.equity) / start_eq * 100.0)
        total_dd = max(0.0, (peak_eq - payload.equity) / peak_eq * 100.0)

        risk_metric.daily_loss_pct = round(daily_loss, 2)
        risk_metric.max_drawdown_pct = round(total_dd, 2)
        risk_metric.updated_at = now

        # Circuit breaker trigger (daily loss >= 2.0% or 3 consecutive losses)
        if daily_loss >= 2.0 or payload.consecutive_losses >= 3:
            risk_metric.circuit_breaker_tripped = True

        # Prop Firm Rule Verification
        profile = payload.prop_firm_profile or risk_metric.prop_firm_profile
        breach = False
        if profile in ("PROP_FTMO", "PROP_THE5ERS") and (daily_loss >= 4.5 or total_dd >= 9.5):
            breach = True
        elif profile == "PROP_MFF" and (daily_loss >= 4.5 or total_dd >= 11.5):
            breach = True
        elif profile == "PROP_EQUITY_EDGE" and (daily_loss >= 3.5 or total_dd >= 7.5):
            breach = True

        risk_metric.prop_rule_breach = breach

    # 4. Count pending commands for this terminal
    cmd_stmt = select(RemoteCommand).where(
        RemoteCommand.terminal_id == terminal.id,
        RemoteCommand.status == "PENDING"
    )
    cmd_res = await db.execute(cmd_stmt)
    pending_count = len(cmd_res.scalars().all())

    # 5. Broadcast to realtime WebSockets
    await ws_manager.broadcast({
        "type": "TERMINAL_HEARTBEAT",
        "terminal_id": terminal.id,
        "account_login": payload.account_login,
        "equity": payload.equity,
        "balance": payload.balance,
        "daily_loss_pct": risk_metric.daily_loss_pct,
        "max_drawdown_pct": risk_metric.max_drawdown_pct,
        "ping_latency_ms": payload.ping_latency_ms,
        "regime": payload.regime,
        "server_time": now.isoformat(),
    })

    return HeartbeatResponse(
        status="ok",
        terminal_id=terminal.id,
        licensed=True,
        tier=tier,
        circuit_breaker_tripped=risk_metric.circuit_breaker_tripped,
        prop_rule_breach=risk_metric.prop_rule_breach,
        daily_loss_pct=risk_metric.daily_loss_pct,
        max_drawdown_pct=risk_metric.max_drawdown_pct,
        pending_commands_count=pending_count,
        server_time=now.isoformat(),
    )


@router.post("/positions", response_model=PositionsSyncResponse)
async def sync_positions(
    payload: PositionsSyncPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Reconciles open positions snapshot from MT5 terminal into the database.
    Overwrites previous live position cache for the terminal.
    """
    now = datetime.now(timezone.utc)

    # 1. Locate terminal
    t_stmt = select(MT5Terminal).where(
        MT5Terminal.account_login == payload.account_login,
        MT5Terminal.terminal_hash == payload.terminal_hash
    )
    t_res = await db.execute(t_stmt)
    terminal = t_res.scalars().first()

    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terminal not found for account {payload.account_login}"
        )

    # 2. Clear old live position snapshot for this terminal
    await db.execute(
        delete(LivePosition).where(LivePosition.terminal_id == terminal.id)
    )

    # 3. Insert incoming positions snapshot
    total_floating = 0.0
    for p in payload.positions:
        total_floating += p.floating_pnl
        open_dt = datetime.fromisoformat(p.open_time) if p.open_time else now

        pos = LivePosition(
            id=str(uuid.uuid4()),
            terminal_id=terminal.id,
            account_login=payload.account_login,
            ticket=p.ticket,
            magic_number=p.magic_number,
            symbol=p.symbol,
            direction=p.direction,
            lots=p.lots,
            open_price=p.open_price,
            current_price=p.current_price,
            stop_loss=p.stop_loss,
            take_profit=p.take_profit,
            floating_pnl=p.floating_pnl,
            pnl_pips=p.pnl_pips,
            swap=p.swap,
            commission=p.commission,
            comment=p.comment,
            open_time=open_dt,
            updated_at=now,
        )
        db.add(pos)

    await db.flush()

    # 4. Broadcast live positions to WebSocket subscribers
    await ws_manager.broadcast({
        "type": "POSITIONS_UPDATED",
        "account_login": payload.account_login,
        "count": len(payload.positions),
        "total_floating_pnl": round(total_floating, 2),
        "positions": [p.model_dump() for p in payload.positions],
        "timestamp": now.isoformat()
    })

    return PositionsSyncResponse(
        status="ok",
        synced_count=len(payload.positions),
        total_floating_pnl=round(total_floating, 2),
        updated_at=now.isoformat()
    )


@router.post("/trades", response_model=TradeReportResponse)
async def report_trade(
    payload: TradeReportPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Records closed MT5 trade deal into the institutional audit ledger.
    Updates consecutive win/loss counters and risk metric state.
    """
    now = datetime.now(timezone.utc)

    # Check for existing trade record with this ticket
    existing_stmt = select(Trade).where(Trade.id == str(payload.ticket))
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalars().first():
        return TradeReportResponse(
            status="ok",
            ticket=payload.ticket,
            logged=False,
            circuit_breaker_active=False,
            daily_loss_pct=0.0
        )

    # Locate terminal
    t_stmt = select(MT5Terminal).where(
        MT5Terminal.account_login == payload.account_login,
        MT5Terminal.terminal_hash == payload.terminal_hash
    )
    t_res = await db.execute(t_stmt)
    terminal = t_res.scalars().first()

    # Insert into trades ledger
    open_dt = datetime.fromisoformat(payload.opened_at) if payload.opened_at else now
    close_dt = datetime.fromisoformat(payload.closed_at) if payload.closed_at else now

    trade = Trade(
        id=str(payload.ticket),
        user_id=terminal.user_id if terminal and terminal.user_id else "system",
        instrument=payload.symbol,
        direction=payload.direction.lower(),
        entry_price=payload.open_price,
        exit_price=payload.close_price,
        lot_size=payload.lots,
        pnl=payload.profit,
        pnl_pips=payload.pips,
        status="closed",
        opened_at=open_dt,
        closed_at=close_dt,
    )
    db.add(trade)

    circuit_active = False
    daily_loss = 0.0

    # Update risk metrics if terminal exists
    if terminal:
        risk_stmt = select(RiskMetric).where(RiskMetric.terminal_id == terminal.id)
        risk_res = await db.execute(risk_stmt)
        risk_metric = risk_res.scalars().first()

        if risk_metric:
            if payload.profit < 0:
                risk_metric.consecutive_losses += 1
            else:
                risk_metric.consecutive_losses = 0

            if risk_metric.consecutive_losses >= 3:
                risk_metric.circuit_breaker_tripped = True

            circuit_active = risk_metric.circuit_breaker_tripped
            daily_loss = risk_metric.daily_loss_pct

    await db.flush()

    # Broadcast trade close to WebSocket subscribers
    await ws_manager.broadcast({
        "type": "TRADE_CLOSED",
        "ticket": payload.ticket,
        "symbol": payload.symbol,
        "direction": payload.direction,
        "profit": payload.profit,
        "pips": payload.pips,
        "timestamp": now.isoformat()
    })

    return TradeReportResponse(
        status="ok",
        ticket=payload.ticket,
        logged=True,
        circuit_breaker_active=circuit_active,
        daily_loss_pct=daily_loss
    )


@router.get("/commands", response_model=List[RemoteCommandResponse])
async def poll_remote_commands(
    account_login: str = Query(..., description="MT5 Account Login Number"),
    terminal_hash: str = Query(..., description="Hardware / Terminal fingerprint"),
    db: AsyncSession = Depends(get_db)
):
    """
    Polling endpoint used by MT5 EA to fetch pending execution commands.
    Automatically transitions retrieved commands to 'DISPATCHED' state.
    """
    t_stmt = select(MT5Terminal).where(
        MT5Terminal.account_login == account_login,
        MT5Terminal.terminal_hash == terminal_hash
    )
    t_res = await db.execute(t_stmt)
    terminal = t_res.scalars().first()

    if not terminal:
        return []

    cmd_stmt = select(RemoteCommand).where(
        RemoteCommand.terminal_id == terminal.id,
        RemoteCommand.status == "PENDING"
    ).order_by(RemoteCommand.created_at.asc())
    cmd_res = await db.execute(cmd_stmt)
    commands = cmd_res.scalars().all()

    response = []
    for cmd in commands:
        cmd.status = "DISPATCHED"
        response.append(RemoteCommandResponse(
            id=cmd.id,
            account_login=cmd.account_login,
            command_type=cmd.command_type,
            symbol=cmd.symbol,
            ticket=cmd.ticket,
            lots=cmd.lots,
            price=cmd.price,
            stop_loss=cmd.stop_loss,
            take_profit=cmd.take_profit,
            status="DISPATCHED",
            created_at=cmd.created_at.isoformat()
        ))

    await db.flush()
    return response


@router.post("/commands/{command_id}/ack")
async def acknowledge_command(
    command_id: str,
    ack: RemoteCommandAck,
    db: AsyncSession = Depends(get_db)
):
    """
    MT5 EA acknowledges completion of a remote command.
    Records fill price, slippage, and execution timestamp.
    """
    now = datetime.now(timezone.utc)
    cmd_stmt = select(RemoteCommand).where(RemoteCommand.id == command_id)
    cmd_res = await db.execute(cmd_stmt)
    cmd = cmd_res.scalars().first()

    if not cmd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command {command_id} not found"
        )

    cmd.status = ack.status
    cmd.result = ack.model_dump()
    cmd.executed_at = now

    await db.flush()

    # Broadcast command completion
    await ws_manager.broadcast({
        "type": "COMMAND_ACKNOWLEDGED",
        "command_id": command_id,
        "status": ack.status,
        "execution_price": ack.execution_price,
        "slippage_pips": ack.slippage_pips,
        "timestamp": now.isoformat()
    })

    return {"status": "ok", "command_id": command_id, "execution_status": ack.status}


@router.post("/remote-order", response_model=RemoteCommandResponse)
async def queue_remote_order(
    order: RemoteCommandCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Frontend or API trigger to queue a remote order for MT5 execution.
    Supports BUY, SELL, CLOSE, CLOSE_ALL, EMERGENCY_HALT.
    """
    now = datetime.now(timezone.utc)

    # Find terminal
    t_stmt = select(MT5Terminal).where(MT5Terminal.account_login == order.account_login)
    t_res = await db.execute(t_stmt)
    terminal = t_res.scalars().first()

    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No connected MT5 terminal found for account {order.account_login}"
        )

    cmd = RemoteCommand(
        id=str(uuid.uuid4()),
        terminal_id=terminal.id,
        account_login=order.account_login,
        command_type=order.command_type.upper(),
        symbol=order.symbol,
        ticket=order.ticket,
        lots=order.lots,
        price=order.price,
        stop_loss=order.stop_loss,
        take_profit=order.take_profit,
        status="PENDING",
        result={},
        created_at=now
    )
    db.add(cmd)
    await db.flush()

    # Notify subscribers
    await ws_manager.broadcast({
        "type": "REMOTE_ORDER_QUEUED",
        "command_id": cmd.id,
        "account_login": order.account_login,
        "command_type": cmd.command_type,
        "symbol": order.symbol,
        "lots": order.lots,
        "timestamp": now.isoformat()
    })

    return RemoteCommandResponse(
        id=cmd.id,
        account_login=cmd.account_login,
        command_type=cmd.command_type,
        symbol=cmd.symbol,
        ticket=cmd.ticket,
        lots=cmd.lots,
        price=cmd.price,
        stop_loss=cmd.stop_loss,
        take_profit=cmd.take_profit,
        status=cmd.status,
        created_at=cmd.created_at.isoformat()
    )


@router.post("/broadcast-trade")
async def broadcast_pamm_trade(
    broadcast: BroadcastCopyTradePayload,
    db: AsyncSession = Depends(get_db)
):
    """
    PAMM Master Trade Broadcaster.
    Dispatches mirrored trades to all active receiver terminals with risk weighting.
    """
    now = datetime.now(timezone.utc)

    # Fetch all active terminals except the master
    t_stmt = select(MT5Terminal).where(
        MT5Terminal.is_active == True,
        MT5Terminal.account_login != broadcast.master_account
    )
    t_res = await db.execute(t_stmt)
    receivers = t_res.scalars().all()

    dispatched = []
    for receiver in receivers:
        # Default multiplier = 1.0 (or proportional based on balance)
        multiplier = 1.0
        calculated_lots = max(0.01, round(broadcast.lots * multiplier, 2))

        # Create copy trade record
        copy_rec = CopyTrade(
            id=str(uuid.uuid4()),
            master_ticket=broadcast.master_ticket,
            master_symbol=broadcast.symbol,
            master_direction=broadcast.direction,
            master_lots=broadcast.lots,
            receiver_terminal_id=receiver.id,
            receiver_account=receiver.account_login,
            risk_multiplier=multiplier,
            executed_lots=calculated_lots,
            status="PENDING",
            created_at=now
        )
        db.add(copy_rec)

        # Queue remote command for the receiver terminal
        cmd = RemoteCommand(
            id=str(uuid.uuid4()),
            terminal_id=receiver.id,
            account_login=receiver.account_login,
            command_type=broadcast.direction.upper(),
            symbol=broadcast.symbol,
            lots=calculated_lots,
            stop_loss=broadcast.stop_loss,
            take_profit=broadcast.take_profit,
            status="PENDING",
            created_at=now
        )
        db.add(cmd)
        dispatched.append({
            "receiver_account": receiver.account_login,
            "lots": calculated_lots,
            "command_id": cmd.id
        })

    await db.flush()

    return {
        "status": "ok",
        "master_ticket": broadcast.master_ticket,
        "receivers_count": len(dispatched),
        "dispatched": dispatched
    }


@router.get("/terminals")
async def list_active_terminals(db: AsyncSession = Depends(get_db)):
    """Return list of all connected MT5 terminals for cockpit dashboard."""
    stmt = select(MT5Terminal).order_by(MT5Terminal.last_heartbeat.desc())
    res = await db.execute(stmt)
    terminals = res.scalars().all()

    now = datetime.now(timezone.utc)
    data = []
    for t in terminals:
        # Check if heartbeat within last 90 seconds
        is_online = (now - t.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() < 90
        data.append({
            "id": t.id,
            "account_login": t.account_login,
            "broker": t.broker,
            "server": t.server,
            "currency": t.currency,
            "balance": t.balance,
            "equity": t.equity,
            "margin_level": t.margin_level,
            "ping_latency_ms": t.ping_latency_ms,
            "regime": t.regime,
            "ea_version": t.ea_version,
            "is_online": is_online,
            "last_heartbeat": t.last_heartbeat.isoformat()
        })
    return data


@router.get("/positions")
async def get_live_positions(
    account_login: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Return current open positions across all active terminals or a specific account."""
    query = select(LivePosition)
    if account_login:
        query = query.where(LivePosition.account_login == account_login)
    query = query.order_by(LivePosition.open_time.desc())

    res = await db.execute(query)
    positions = res.scalars().all()

    return [
        {
            "id": p.id,
            "account_login": p.account_login,
            "ticket": p.ticket,
            "symbol": p.symbol,
            "direction": p.direction,
            "lots": p.lots,
            "open_price": p.open_price,
            "current_price": p.current_price,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit,
            "floating_pnl": p.floating_pnl,
            "pnl_pips": p.pnl_pips,
            "open_time": p.open_time.isoformat() if p.open_time else None
        }
        for p in positions
    ]
