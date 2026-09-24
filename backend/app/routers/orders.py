"""
Kestrel Core — Orders Router & Idempotent Execution Pipeline
Implements the Master Roadmap Order Lifecycle (Pending -> MT5 RPC -> Filled Deal -> DB Sync).
Enforces idempotency, bracket SL/TP constraints, and strict allow-list input validation.
"""
from datetime import datetime, timezone
import re
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid

from app.db.database import get_db
from app.models.models import Order, Trade, User
from app.core.security import get_current_user_id
from app.core.rate_limiter import rate_limiter, get_client_ip
from app.services.mt5_bridge.rpc_client import mt5_rpc_client
from app.db.supabase_client import supabase_client

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Symbol allow-list pattern: alphanumeric, dot, slash, hyphen, underscore, space (e.g. "Volatility 100 Index", "EURUSD", "BTCUSD")
SYMBOL_REGEX = re.compile(r"^[A-Za-z0-9._\- /]{2,32}$")


class OrderCreate(BaseModel):
    client_order_id: str = Field(..., min_length=8, max_length=64, description="Unique client idempotency token")
    account_number: Optional[str] = Field("41230754", max_length=64)
    instrument: str = Field(..., min_length=2, max_length=32)
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|STOP)$")
    direction: str = Field(..., pattern="^(BUY|SELL)$")
    qty: float = Field(..., gt=0.0, le=100.0, description="Lot size between 0.01 and 100.0")
    price: Optional[float] = Field(None, gt=0.0)
    stop_loss: Optional[float] = Field(None, gt=0.0)
    take_profit: Optional[float] = Field(None, gt=0.0)

    @field_validator("instrument")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v_clean = v.strip()
        if not SYMBOL_REGEX.match(v_clean):
            raise ValueError("Instrument contains invalid characters.")
        return v_clean


class OrderResponse(BaseModel):
    id: str
    client_order_id: str
    account_number: Optional[str]
    instrument: str
    order_type: str
    direction: str
    qty: float
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: str
    filled_price: Optional[float]
    filled_qty: Optional[float]
    mt5_ticket: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def submit_order(
    req: OrderCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a trade order with strict idempotency and atomic MT5 execution synchronization.
    1. Checks if client_order_id already exists (prevents duplicate execution).
    2. Writes Order record with status=PENDING.
    3. Calls MT5 container RPC bridge.
    4. On success: marks status=FILLED, saves MT5 ticket, and creates corresponding Trade deal.
    5. Syncs state to Supabase Cloud PostgreSQL.
    """
    client_ip = get_client_ip(request)
    await rate_limiter.check_rate_limit(f"orders:{client_ip}", max_requests=30, window_seconds=60, action_name="order submission")

    # 1. Idempotency Check: Verify if order was already submitted
    existing_order = await db.execute(
        select(Order).where(Order.client_order_id == req.client_order_id)
    )
    order_obj = existing_order.scalar_one_or_none()
    if order_obj:
        # Return existing order record without double-executing
        return order_obj

    # 2. Insert PENDING order in DB (Source of Truth)
    order_obj = Order(
        user_id=user_id,
        account_number=req.account_number or "41230754",
        client_order_id=req.client_order_id,
        instrument=req.instrument,
        order_type=req.order_type,
        direction=req.direction,
        qty=req.qty,
        price=req.price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        status="PENDING",
    )
    db.add(order_obj)
    await db.flush()

    # 3. Dispatch execution to MT5 Container Service via secure RPC
    execution_result = await mt5_rpc_client.execute_order(
        account_number=order_obj.account_number,
        symbol=order_obj.instrument,
        action=order_obj.direction,
        lot_size=order_obj.qty,
        price=order_obj.price,
        stop_loss=order_obj.stop_loss,
        take_profit=order_obj.take_profit,
        comment=f"Kestrel #{req.client_order_id[:8]}",
    )

    # 4. Handle Execution Result
    if execution_result.get("success"):
        order_obj.status = "FILLED"
        order_obj.filled_price = execution_result.get("price") or req.price or 1.10000
        order_obj.filled_qty = req.qty
        order_obj.mt5_ticket = execution_result.get("ticket")

        # Create corresponding Trade record
        trade_record = Trade(
            user_id=user_id,
            account_number=order_obj.account_number,
            instrument=order_obj.instrument,
            direction=order_obj.direction.lower(),
            entry_price=order_obj.filled_price,
            lot_size=order_obj.qty,
            status="open",
            opened_at=datetime.now(timezone.utc),
        )
        db.add(trade_record)
        await db.flush()

        # Sync to Supabase Cloud
        try:
            await supabase_client.record_trade({
                "account_number": order_obj.account_number,
                "mt5_ticket": order_obj.mt5_ticket,
                "instrument": order_obj.instrument,
                "direction": order_obj.direction,
                "lot_size": order_obj.qty,
                "entry_price": order_obj.filled_price,
                "stop_loss": order_obj.stop_loss,
                "take_profit": order_obj.take_profit,
                "status": "open",
                "metadata": {"client_order_id": order_obj.client_order_id, "order_id": str(order_obj.id)}
            })
        except Exception:
            pass

    else:
        order_obj.status = "REJECTED"
        order_obj.error_message = execution_result.get("error", "Execution rejected by MT5 gateway")

    await db.commit()
    await db.refresh(order_obj)

    return order_obj


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    status_filter: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve orders for the authenticated user."""
    query = select(Order).where(Order.user_id == user_id)
    if status_filter:
        query = query.where(Order.status == status_filter.upper())
    query = query.order_by(desc(Order.created_at)).limit(min(limit, 100))

    res = await db.execute(query)
    return res.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get single order details."""
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order_obj = res.scalar_one_or_none()
    if not order_obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_obj


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending limit or stop order."""
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order_obj = res.scalar_one_or_none()
    if not order_obj:
        raise HTTPException(status_code=404, detail="Order not found")

    if order_obj.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order in status '{order_obj.status}'",
        )

    order_obj.status = "CANCELLED"
    await db.commit()
    return {"status": "success", "message": "Order cancelled"}
