"""
Kestrel Core — Phase 3 Database & MT5 Synchronization Tests
Tests MT5 heartbeat ingestion, risk metrics calculation, prop-firm breach triggers,
position reconciliation, trade ledger archival, and remote command lifecycle.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
import uuid

from app.main import app
from app.db.database import init_db, close_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await close_db()


@pytest.mark.asyncio
async def test_heartbeat_lifecycle_and_risk_metrics():
    """Verify heartbeat registration, daily loss calculation, and circuit breaker trip."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        account_login = f"test_acc_{uuid.uuid4().hex[:6]}"
        terminal_hash = f"MT5_HASH_{uuid.uuid4().hex[:8]}"

        # 1. Initial Heartbeat
        hb1 = {
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "broker": "FTMO-Server",
            "server": "FTMO-Demo",
            "currency": "USD",
            "leverage": 100,
            "balance": 100000.0,
            "equity": 100000.0,
            "margin": 1000.0,
            "free_margin": 99000.0,
            "margin_level": 10000.0,
            "ping_latency_ms": 12,
            "regime": "REGIME_HYBRID",
            "ea_version": "4.00",
            "prop_firm_profile": "PROP_FTMO",
            "consecutive_losses": 0,
        }
        res1 = await client.post("/api/v1/sync/heartbeat", json=hb1)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "ok"
        assert data1["circuit_breaker_tripped"] is False
        assert data1["prop_rule_breach"] is False
        assert data1["daily_loss_pct"] == 0.0

        # 2. Heartbeat with 1.5% loss (Normal, no circuit breaker)
        hb2 = dict(hb1)
        hb2["equity"] = 98500.0  # 1.5% loss from 100k starting equity
        res2 = await client.post("/api/v1/sync/heartbeat", json=hb2)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["daily_loss_pct"] == 1.5
        assert data2["circuit_breaker_tripped"] is False
        assert data2["prop_rule_breach"] is False

        # 3. Heartbeat with 2.2% loss (Exceeds 2.0% daily circuit breaker)
        hb3 = dict(hb1)
        hb3["equity"] = 97800.0  # 2.2% loss
        res3 = await client.post("/api/v1/sync/heartbeat", json=hb3)
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["daily_loss_pct"] == 2.2
        assert data3["circuit_breaker_tripped"] is True
        assert data3["prop_rule_breach"] is False

        # 4. Heartbeat with 4.8% loss on FTMO profile (Exceeds 4.5% prop firm limit safety buffer)
        hb4 = dict(hb1)
        hb4["equity"] = 95200.0  # 4.8% loss
        res4 = await client.post("/api/v1/sync/heartbeat", json=hb4)
        assert res4.status_code == 200
        data4 = res4.json()
        assert data4["daily_loss_pct"] == 4.8
        assert data4["prop_rule_breach"] is True


@pytest.mark.asyncio
async def test_positions_sync_and_retrieval():
    """Verify batch open positions synchronization and dashboard querying."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        account_login = f"pos_acc_{uuid.uuid4().hex[:6]}"
        terminal_hash = f"MT5_HASH_{uuid.uuid4().hex[:8]}"

        # Initialize terminal via heartbeat
        hb = {
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "balance": 50000.0,
            "equity": 50450.0,
        }
        await client.post("/api/v1/sync/heartbeat", json=hb)

        # Sync 2 open positions
        positions_payload = {
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "positions": [
                {
                    "ticket": 1001,
                    "magic_number": 773571,
                    "symbol": "XAUUSD",
                    "direction": "BUY",
                    "lots": 0.50,
                    "open_price": 2650.50,
                    "current_price": 2655.00,
                    "stop_loss": 2642.00,
                    "take_profit": 2670.00,
                    "floating_pnl": 225.00,
                    "pnl_pips": 45.0,
                },
                {
                    "ticket": 1002,
                    "magic_number": 773571,
                    "symbol": "EURUSD",
                    "direction": "SELL",
                    "lots": 1.00,
                    "open_price": 1.08500,
                    "current_price": 1.08250,
                    "stop_loss": 1.08900,
                    "take_profit": 1.07800,
                    "floating_pnl": 250.00,
                    "pnl_pips": 25.0,
                }
            ]
        }
        sync_res = await client.post("/api/v1/sync/positions", json=positions_payload)
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["synced_count"] == 2
        assert sync_data["total_floating_pnl"] == 475.00

        # Query live positions from dashboard endpoint
        get_res = await client.get(f"/api/v1/sync/positions?account_login={account_login}")
        assert get_res.status_code == 200
        positions = get_res.json()
        assert len(positions) == 2
        tickets = [p["ticket"] for p in positions]
        assert 1001 in tickets
        assert 1002 in tickets


@pytest.mark.asyncio
async def test_trade_reporting_and_consecutive_losses():
    """Verify closed deal reporting updates consecutive losses and risk metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        account_login = f"trade_acc_{uuid.uuid4().hex[:6]}"
        terminal_hash = f"MT5_HASH_{uuid.uuid4().hex[:8]}"

        # Initialize terminal
        await client.post("/api/v1/sync/heartbeat", json={
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "balance": 10000.0,
            "equity": 10000.0,
        })

        base_ticket = int(uuid.uuid4().int % 10000000) + 100000

        # Report winning trade
        t1 = {
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "ticket": base_ticket,
            "symbol": "GBPUSD",
            "direction": "BUY",
            "lots": 0.20,
            "open_price": 1.29000,
            "close_price": 1.29500,
            "profit": 100.0,
            "pips": 50.0,
        }
        res1 = await client.post("/api/v1/sync/trades", json=t1)
        assert res1.status_code == 200
        assert res1.json()["logged"] is True
        assert res1.json()["circuit_breaker_active"] is False

        # Report 3 consecutive losses to trigger circuit breaker
        for i, ticket in enumerate([base_ticket + 1, base_ticket + 2, base_ticket + 3]):
            t_loss = {
                "account_login": account_login,
                "terminal_hash": terminal_hash,
                "ticket": ticket,
                "symbol": "USDCAD",
                "direction": "SELL",
                "lots": 0.10,
                "open_price": 1.35000,
                "close_price": 1.35300,
                "profit": -30.0,
                "pips": -30.0,
            }
            res_loss = await client.post("/api/v1/sync/trades", json=t_loss)
            assert res_loss.status_code == 200
            data_loss = res_loss.json()
            if i == 2:
                # 3rd consecutive loss must trip circuit breaker
                assert data_loss["circuit_breaker_active"] is True


@pytest.mark.asyncio
async def test_remote_command_lifecycle():
    """Verify queueing, dispatching, and acknowledgment of remote execution commands."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        account_login = f"cmd_acc_{uuid.uuid4().hex[:6]}"
        terminal_hash = f"MT5_HASH_{uuid.uuid4().hex[:8]}"

        # Initialize terminal
        await client.post("/api/v1/sync/heartbeat", json={
            "account_login": account_login,
            "terminal_hash": terminal_hash,
            "balance": 25000.0,
            "equity": 25000.0,
        })

        # 1. Queue remote BUY order from Web frontend
        order_cmd = {
            "account_login": account_login,
            "command_type": "BUY",
            "symbol": "XAUUSD",
            "lots": 0.15,
            "stop_loss": 2640.00,
            "take_profit": 2680.00,
        }
        queue_res = await client.post("/api/v1/sync/remote-order", json=order_cmd)
        assert queue_res.status_code == 200
        cmd_data = queue_res.json()
        cmd_id = cmd_data["id"]
        assert cmd_data["status"] == "PENDING"
        assert cmd_data["command_type"] == "BUY"

        # 2. MT5 polls for pending commands
        poll_res = await client.get(
            f"/api/v1/sync/commands?account_login={account_login}&terminal_hash={terminal_hash}"
        )
        assert poll_res.status_code == 200
        polled_cmds = poll_res.json()
        assert len(polled_cmds) == 1
        assert polled_cmds[0]["id"] == cmd_id
        assert polled_cmds[0]["status"] == "DISPATCHED"

        # 3. MT5 sends ACK after executing the trade
        ack_payload = {
            "status": "EXECUTED",
            "execution_price": 2652.10,
            "slippage_pips": 0.4,
            "ticket": 888201
        }
        ack_res = await client.post(f"/api/v1/sync/commands/{cmd_id}/ack", json=ack_payload)
        assert ack_res.status_code == 200
        assert ack_res.json()["execution_status"] == "EXECUTED"

        # 4. Subsequent poll has no pending commands
        poll_res_2 = await client.get(
            f"/api/v1/sync/commands?account_login={account_login}&terminal_hash={terminal_hash}"
        )
        assert poll_res_2.status_code == 200
        assert len(poll_res_2.json()) == 0


@pytest.mark.asyncio
async def test_pamm_trade_broadcaster():
    """Verify PAMM master trade replication across active receiver terminals."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        master_acc = f"master_{uuid.uuid4().hex[:6]}"
        receiver_1 = f"rec1_{uuid.uuid4().hex[:6]}"
        receiver_2 = f"rec2_{uuid.uuid4().hex[:6]}"

        # Initialize terminals
        await client.post("/api/v1/sync/heartbeat", json={
            "account_login": master_acc,
            "terminal_hash": f"MT5_{master_acc}",
            "balance": 100000.0,
            "equity": 100000.0,
        })
        await client.post("/api/v1/sync/heartbeat", json={
            "account_login": receiver_1,
            "terminal_hash": f"MT5_{receiver_1}",
            "balance": 10000.0,
            "equity": 10000.0,
        })
        await client.post("/api/v1/sync/heartbeat", json={
            "account_login": receiver_2,
            "terminal_hash": f"MT5_{receiver_2}",
            "balance": 25000.0,
            "equity": 25000.0,
        })

        # Broadcast master trade
        broadcast = {
            "master_account": master_acc,
            "master_ticket": 777100,
            "symbol": "EURUSD",
            "direction": "BUY",
            "lots": 1.0,
            "stop_loss": 1.0800,
            "take_profit": 1.0950
        }
        b_res = await client.post("/api/v1/sync/broadcast-trade", json=broadcast)
        assert b_res.status_code == 200
        b_data = b_res.json()
        assert b_data["status"] == "ok"
        # At least receiver_1 and receiver_2 must be dispatched
        assert b_data["receivers_count"] >= 2
