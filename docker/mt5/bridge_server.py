"""
Kestrel MT5 Docker Bridge Server
Runs inside the Wine MT5 container (gmag11/MetaTrader5-Docker).
Connects to the local MetaTrader 5 terminal via python MetaTrader5 package
and exposes a secured, authenticated RPC interface on port 5001.
"""
import os
import sys
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MT5Bridge")

BRIDGE_SECRET_KEY = os.getenv("MT5_BRIDGE_SECRET", "kestrel-internal-rpc-secret-token")

app = FastAPI(title="Kestrel MT5 RPC Bridge", version="2.0.0")

# In production Wine container, MetaTrader5 package connects to terminal.exe
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 python library found.")
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 library not found - running in emulation mock mode.")


class OrderRequest(BaseModel):
    account_number: str
    symbol: str
    action: str = Field(..., pattern="^(BUY|SELL|CLOSE)$")
    lot_size: float = Field(..., gt=0)
    order_type: str = Field(default="MARKET")
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    magic: int = 120999
    comment: str = "Kestrel Quantum Order"


def verify_bridge_token(x_bridge_token: Optional[str] = Header(None)):
    if not x_bridge_token or x_bridge_token != BRIDGE_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized RPC bridge access")
    return True


@app.get("/health")
async def health_check():
    connected = False
    if MT5_AVAILABLE:
        try:
            connected = mt5.terminal_info() is not None
        except Exception:
            connected = False
    return {
        "status": "online",
        "mt5_connected": connected or not MT5_AVAILABLE,
        "mode": "live_mt5" if MT5_AVAILABLE else "emulation"
    }


@app.post("/execute", dependencies=[Depends(verify_bridge_token)])
async def execute_order(req: OrderRequest):
    """Execute order via MetaTrader 5 terminal."""
    logger.info(f"Received order: {req.action} {req.lot_size} {req.symbol} on #{req.account_number}")

    if not MT5_AVAILABLE:
        # Mock execution for container CI/CD testing
        import random, time
        simulated_ticket = random.randint(10000000, 99999999)
        simulated_fill = req.price or 1.10500
        return {
            "success": True,
            "ticket": simulated_ticket,
            "symbol": req.symbol,
            "action": req.action,
            "volume": req.lot_size,
            "price": simulated_fill,
            "comment": req.comment,
            "executed_at": time.time()
        }

    # MetaTrader5 live execution logic
    if not mt5.initialize():
        raise HTTPException(status_code=500, detail=f"MT5 terminal initialization failed: {mt5.last_error()}")

    action_type = mt5.ORDER_TYPE_BUY if req.action.upper() == "BUY" else mt5.ORDER_TYPE_SELL
    price = req.price or (mt5.symbol_info_tick(req.symbol).ask if action_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(req.symbol).bid)

    request_dict = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": req.symbol,
        "volume": req.lot_size,
        "type": action_type,
        "price": price,
        "sl": req.stop_loss or 0.0,
        "tp": req.take_profit or 0.0,
        "deviation": 20,
        "magic": req.magic,
        "comment": req.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request_dict)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"Order failed: {result.comment} (code {result.retcode})")
        raise HTTPException(status_code=400, detail=f"MT5 order failed: {result.comment}")

    return {
        "success": True,
        "ticket": result.order,
        "symbol": req.symbol,
        "volume": result.volume,
        "price": result.price,
        "deal": result.deal
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
