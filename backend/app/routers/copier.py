"""
Kestrel Core — Multi-Broker PAMM Copier Hub Router
Manages receiver accounts, custom risk multipliers (0.1x - 5.0x), slippage guards,
and emergency master halt broadcasting across FTMO, The5ers, Deriv, and ICMarkets.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

from app.db.database import get_db
from app.models.models import CopierAccount, MT5Terminal, RemoteCommand, CopyTrade
from app.schemas.copier_notif import (
    CopierAccountConfig,
    CopierAccountResponse,
    EmergencyHaltRequest,
)
from app.schemas.sync import BroadcastCopyTradePayload
from app.routers.ws_sync import ws_manager

router = APIRouter(prefix="/api/v1/copier", tags=["Multi-Broker Copier Hub"])

BROKER_PRESETS = [
    {"id": "FTMO", "name": "FTMO Challenge / Funded", "default_leverage": 100, "max_dd": 10.0},
    {"id": "THE5ERS", "name": "The 5%ers Bootcamp / Hyper", "default_leverage": 100, "max_dd": 10.0},
    {"id": "FUNDING_PIPS", "name": "Funding Pips 2-Step", "default_leverage": 100, "max_dd": 10.0},
    {"id": "TOPSTEP", "name": "Topstep Futures / Forex", "default_leverage": 50, "max_dd": 8.0},
    {"id": "ICMARKETS", "name": "IC Markets Raw Spread", "default_leverage": 500, "max_dd": 0.0},
    {"id": "DERIV", "name": "Deriv Synthetic & Financial", "default_leverage": 1000, "max_dd": 0.0},
    {"id": "PEPPERSTONE", "name": "Pepperstone Razor", "default_leverage": 400, "max_dd": 0.0},
    {"id": "EXNESS", "name": "Exness Zero Spread", "default_leverage": 2000, "max_dd": 0.0},
]


@router.get("/brokers")
async def list_broker_presets():
    """Returns supported institutional broker profiles and default leverage settings."""
    return BROKER_PRESETS


@router.get("/accounts", response_model=List[CopierAccountResponse])
async def list_copier_accounts(db: AsyncSession = Depends(get_db)):
    """
    Returns all configured copier accounts enriched with real-time MT5 telemetry
    (live equity, closed balance, ping latency, and online connectivity).
    """
    stmt = select(CopierAccount)
    res = await db.execute(stmt)
    accounts = res.scalars().all()

    now = datetime.now(timezone.utc)
    enriched = []
    for acc in accounts:
        # Fetch matching MT5 terminal if active
        t_stmt = select(MT5Terminal).where(MT5Terminal.account_login == acc.account_login)
        t_res = await db.execute(t_stmt)
        terminal = t_res.scalars().first()

        balance = terminal.balance if terminal else 0.0
        equity = terminal.equity if terminal else 0.0
        ping = terminal.ping_latency_ms if terminal else 12
        is_online = bool(terminal and (now - terminal.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() < 90)

        enriched.append(CopierAccountResponse(
            id=acc.id,
            account_login=acc.account_login,
            account_name=acc.account_name,
            broker_profile=acc.broker_profile,
            role=acc.role,
            risk_multiplier=acc.risk_multiplier,
            max_lot_cap=acc.max_lot_cap,
            max_slippage_pips=acc.max_slippage_pips,
            is_enabled=acc.is_enabled,
            balance=balance,
            equity=equity,
            ping_latency_ms=ping,
            is_online=is_online,
        ))

    return enriched


@router.post("/accounts/configure", response_model=CopierAccountResponse)
async def configure_copier_account(
    config: CopierAccountConfig,
    db: AsyncSession = Depends(get_db)
):
    """Register or update a copier account profile, role, and custom risk multiplier."""
    now = datetime.now(timezone.utc)
    stmt = select(CopierAccount).where(CopierAccount.account_login == config.account_login)
    res = await db.execute(stmt)
    acc = res.scalars().first()

    if not acc:
        acc = CopierAccount(
            id=str(uuid.uuid4()),
            account_login=config.account_login,
            account_name=config.account_name,
            broker_profile=config.broker_profile,
            role=config.role.upper(),
            risk_multiplier=config.risk_multiplier,
            max_lot_cap=config.max_lot_cap,
            max_slippage_pips=config.max_slippage_pips,
            is_enabled=config.is_enabled,
            created_at=now,
        )
        db.add(acc)
    else:
        acc.account_name = config.account_name
        acc.broker_profile = config.broker_profile
        acc.role = config.role.upper()
        acc.risk_multiplier = config.risk_multiplier
        acc.max_lot_cap = config.max_lot_cap
        acc.max_slippage_pips = config.max_slippage_pips
        acc.is_enabled = config.is_enabled
        acc.updated_at = now

    await db.flush()

    return CopierAccountResponse(
        id=acc.id,
        account_login=acc.account_login,
        account_name=acc.account_name,
        broker_profile=acc.broker_profile,
        role=acc.role,
        risk_multiplier=acc.risk_multiplier,
        max_lot_cap=acc.max_lot_cap,
        max_slippage_pips=acc.max_slippage_pips,
        is_enabled=acc.is_enabled,
        balance=0.0,
        equity=0.0,
        ping_latency_ms=12,
        is_online=True,
    )


@router.post("/broadcast")
async def broadcast_trade(
    broadcast: BroadcastCopyTradePayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Distributes master trade execution to all active receiver accounts
    scaling lots by each receiver's risk multiplier and capping at max_lot_cap.
    """
    now = datetime.now(timezone.utc)

    # Fetch active receivers
    stmt = select(CopierAccount).where(
        CopierAccount.role == "RECEIVER",
        CopierAccount.is_enabled == True,
        CopierAccount.account_login != broadcast.master_account
    )
    res = await db.execute(stmt)
    receivers = res.scalars().all()

    dispatched = []
    for rec in receivers:
        # Calculate scaled lot size
        scaled_lots = round(broadcast.lots * rec.risk_multiplier, 2)
        final_lots = max(0.01, min(scaled_lots, rec.max_lot_cap))

        # Check for MT5 terminal connection
        t_stmt = select(MT5Terminal).where(MT5Terminal.account_login == rec.account_login)
        t_res = await db.execute(t_stmt)
        terminal = t_res.scalars().first()

        terminal_id = terminal.id if terminal else str(uuid.uuid4())

        # Create copy trade record
        copy_entry = CopyTrade(
            id=str(uuid.uuid4()),
            master_ticket=broadcast.master_ticket,
            master_symbol=broadcast.symbol,
            master_direction=broadcast.direction,
            master_lots=broadcast.lots,
            receiver_terminal_id=terminal_id,
            receiver_account=rec.account_login,
            risk_multiplier=rec.risk_multiplier,
            executed_lots=final_lots,
            status="PENDING",
            created_at=now,
        )
        db.add(copy_entry)

        # Queue remote command if terminal exists
        if terminal:
            cmd = RemoteCommand(
                id=str(uuid.uuid4()),
                terminal_id=terminal.id,
                account_login=rec.account_login,
                command_type=broadcast.direction.upper(),
                symbol=broadcast.symbol,
                lots=final_lots,
                stop_loss=broadcast.stop_loss,
                take_profit=broadcast.take_profit,
                status="PENDING",
                created_at=now,
            )
            db.add(cmd)

        dispatched.append({
            "account_login": rec.account_login,
            "account_name": rec.account_name,
            "broker": rec.broker_profile,
            "multiplier": rec.risk_multiplier,
            "lots": final_lots,
        })

    await db.flush()

    # Real-time WebSocket broadcast
    await ws_manager.broadcast({
        "type": "COPIER_TRADE_BROADCAST",
        "master_account": broadcast.master_account,
        "master_ticket": broadcast.master_ticket,
        "symbol": broadcast.symbol,
        "direction": broadcast.direction,
        "receivers_count": len(dispatched),
        "timestamp": now.isoformat(),
    })

    return {
        "status": "ok",
        "master_ticket": broadcast.master_ticket,
        "receivers_count": len(dispatched),
        "dispatched": dispatched,
    }


@router.post("/emergency-halt")
async def emergency_halt_all(
    halt: EmergencyHaltRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Master Kill Switch.
    Immediately dispatches CLOSE_ALL commands to all connected MT5 terminals
    and pauses all active receiver accounts.
    """
    now = datetime.now(timezone.utc)

    # 1. Dispatch CLOSE_ALL commands to all active MT5 terminals
    t_stmt = select(MT5Terminal).where(MT5Terminal.is_active == True)
    t_res = await db.execute(t_stmt)
    terminals = t_res.scalars().all()

    halted_terminals = []
    for t in terminals:
        cmd = RemoteCommand(
            id=str(uuid.uuid4()),
            terminal_id=t.id,
            account_login=t.account_login,
            command_type="CLOSE_ALL",
            status="PENDING",
            created_at=now,
        )
        db.add(cmd)
        halted_terminals.append(t.account_login)

    # 2. Disable all copier accounts
    await db.execute(
        update(CopierAccount).values(is_enabled=False, updated_at=now)
    )

    await db.flush()

    # 3. Broadcast emergency halt via WebSockets
    await ws_manager.broadcast({
        "type": "EMERGENCY_HALT_ACTIVATED",
        "reason": halt.reason,
        "halted_accounts": halted_terminals,
        "timestamp": now.isoformat(),
    })

    return {
        "status": "halted",
        "reason": halt.reason,
        "halted_accounts_count": len(halted_terminals),
        "halted_accounts": halted_terminals,
    }
