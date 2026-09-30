"""
Kestrel Core — Phase 5 Market Features Tests
Tests Telegram/Discord alert formatting, multi-broker PAMM configuration,
master trade scaling, emergency halt kill switch, portfolio expectancy math,
and Pearson pair correlation risk matrix.
"""
import pytest
from httpx import AsyncClient, ASGITransport
import uuid

from app.main import app
from app.db.database import init_db, close_db
from app.services.notifications.dispatcher import notification_dispatcher


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await close_db()


def test_notification_formatting_engine():
    """Verify rich HTML/markdown message formatting for Telegram and Discord."""
    signal = {
        "instrument": "XAUUSD",
        "direction": "BUY",
        "timeframe": "H1",
        "entry_price": 2650.50,
        "stop_loss": 2638.00,
        "take_profit": 2675.00,
        "confidence": 0.88,
        "swarm_consensus_pct": 89.2,
        "recommended_duration": "4h-8h",
        "reasoning": "H1 Bullish Order Block confluence with institutional liquidity sweep."
    }

    tg_text = notification_dispatcher.format_trade_signal_telegram(signal)
    assert "KESTREL INSTITUTIONAL TRADE ALERT" in tg_text
    assert "XAUUSD" in tg_text
    assert "2650.5" in tg_text
    assert "89.2%" in tg_text

    discord_embeds = notification_dispatcher.format_trade_signal_discord(signal)
    assert len(discord_embeds) == 1
    assert "BUY XAUUSD" in discord_embeds[0]["title"]
    assert discord_embeds[0]["color"] == 0x00E5FF  # Neon Cyan for Buy


def test_prop_firm_risk_alert_formatting():
    """Verify prop-firm daily loss warning and emergency halt message synthesis."""
    data = {
        "account_login": "10592812",
        "broker": "FTMO-Server",
        "daily_loss_pct": 4.65,
        "max_drawdown_pct": 8.90,
        "prop_firm_profile": "PROP_FTMO",
        "breach": True,
    }
    tg_text, embeds = notification_dispatcher.format_prop_firm_alert(data)
    assert "PROP-FIRM RULE BREACH" in tg_text
    assert "10592812" in tg_text
    assert "4.65%" in tg_text
    assert embeds[0]["color"] == 0xFF2A55  # Neon Red for Breach


@pytest.mark.asyncio
async def test_notification_config_crud():
    """Verify saving and retrieving Telegram and Discord webhook configuration."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        test_user = f"user_{uuid.uuid4().hex[:6]}"

        cfg_payload = {
            "telegram_enabled": True,
            "telegram_bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            "telegram_chat_id": "-1001234567890",
            "discord_enabled": True,
            "discord_webhook_url": "https://discord.com/api/webhooks/123/xyz",
            "alert_trade_signals": True,
            "alert_prop_firm_risk": True,
            "alert_circuit_breaker": True,
            "alert_high_impact_news": True,
        }

        # Save config
        save_res = await client.post(f"/api/v1/notifications/config?user_id={test_user}", json=cfg_payload)
        assert save_res.status_code == 200

        # Retrieve config
        get_res = await client.get(f"/api/v1/notifications/config?user_id={test_user}")
        assert get_res.status_code == 200
        retrieved = get_res.json()
        assert retrieved["telegram_enabled"] is True
        assert retrieved["telegram_chat_id"] == "-1001234567890"
        assert retrieved["discord_enabled"] is True


@pytest.mark.asyncio
async def test_copier_multi_broker_hub():
    """Verify broker presets, account onboarding, and risk multiplier scaling."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Broker presets
        brokers_res = await client.get("/api/v1/copier/brokers")
        assert brokers_res.status_code == 200
        broker_ids = [b["id"] for b in brokers_res.json()]
        assert "FTMO" in broker_ids
        assert "THE5ERS" in broker_ids
        assert "DERIV" in broker_ids
        assert "ICMARKETS" in broker_ids

        # 2. Configure Receiver Account with 1.5x Multiplier
        acc_payload = {
            "account_login": f"rec_{uuid.uuid4().hex[:6]}",
            "account_name": "FTMO 100k Challenge Receiver",
            "broker_profile": "FTMO",
            "role": "RECEIVER",
            "risk_multiplier": 1.50,
            "max_lot_cap": 3.00,
            "max_slippage_pips": 2.50,
            "is_enabled": True,
        }
        conf_res = await client.post("/api/v1/copier/accounts/configure", json=acc_payload)
        assert conf_res.status_code == 200
        saved_acc = conf_res.json()
        assert saved_acc["risk_multiplier"] == 1.50
        assert saved_acc["broker_profile"] == "FTMO"

        # 3. List accounts
        list_res = await client.get("/api/v1/copier/accounts")
        assert list_res.status_code == 200
        logins = [a["account_login"] for a in list_res.json()]
        assert acc_payload["account_login"] in logins


@pytest.mark.asyncio
async def test_copier_broadcast_and_emergency_halt():
    """Verify master trade distribution and emergency kill switch halt."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        master_acc = f"master_{uuid.uuid4().hex[:6]}"
        rec_acc = f"rec_{uuid.uuid4().hex[:6]}"

        # Onboard accounts
        await client.post("/api/v1/copier/accounts/configure", json={
            "account_login": master_acc,
            "account_name": "PAMM Master 1",
            "broker_profile": "ICMARKETS",
            "role": "MASTER",
            "risk_multiplier": 1.0,
            "max_lot_cap": 10.0,
            "is_enabled": True,
        })
        await client.post("/api/v1/copier/accounts/configure", json={
            "account_login": rec_acc,
            "account_name": "The5ers Receiver",
            "broker_profile": "THE5ERS",
            "role": "RECEIVER",
            "risk_multiplier": 0.50,  # 0.5x scaling
            "max_lot_cap": 2.0,
            "is_enabled": True,
        })

        # Broadcast 1.0 lots from master -> should scale to 0.50 lots on receiver
        broadcast_payload = {
            "master_account": master_acc,
            "master_ticket": 884102,
            "symbol": "XAUUSD",
            "direction": "BUY",
            "lots": 1.00,
            "stop_loss": 2640.0,
            "take_profit": 2680.0
        }
        b_res = await client.post("/api/v1/copier/broadcast", json=broadcast_payload)
        assert b_res.status_code == 200
        dispatched = b_res.json()["dispatched"]
        target = next((d for d in dispatched if d["account_login"] == rec_acc), None)
        assert target is not None
        assert target["lots"] == 0.50

        # Trigger Emergency Master Halt
        halt_res = await client.post("/api/v1/copier/emergency-halt", json={
            "reason": "Macro Black Swan High-Impact Event"
        })
        assert halt_res.status_code == 200
        assert halt_res.json()["status"] == "halted"


@pytest.mark.asyncio
async def test_deep_portfolio_analytics():
    """Verify trade expectancy, R-multiples, Sharpe, and Sortino calculations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/portfolio-metrics")
        assert res.status_code == 200
        data = res.json()

        assert data["total_trades"] > 0
        assert 0.0 <= data["win_rate_pct"] <= 100.0
        assert data["profit_factor"] >= 0.0
        assert "expectancy_usd" in data
        assert "average_r_multiple" in data
        assert "sharpe_ratio" in data
        assert "sortino_ratio" in data


@pytest.mark.asyncio
async def test_pair_correlation_matrix_and_guards():
    """Verify 5x5 pair correlation matrix and flags for |r| > 0.70."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/correlation-matrix")
        assert res.status_code == 200
        data = res.json()

        assert len(data["assets"]) == 5
        assert len(data["matrix"]) == 5
        assert data["high_correlation_alerts_count"] >= 1

        # Check EURUSD / GBPUSD correlation is flagged
        flagged_pairs = [tuple(a["pair"]) for a in data["alerts"]]
        assert ("EURUSD", "GBPUSD") in flagged_pairs or ("GBPUSD", "EURUSD") in flagged_pairs


@pytest.mark.asyncio
async def test_session_edge_and_monthly_calendar():
    """Verify session breakdown and monthly historical performance grid."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Session edge
        session_res = await client.get("/api/v1/analytics/session-edge")
        assert session_res.status_code == 200
        sessions = session_res.json()
        assert len(sessions) == 4
        overlap = next(s for s in sessions if "Overlap" in s["session"])
        assert overlap["profit_factor"] >= 3.0

        # Monthly calendar
        cal_res = await client.get("/api/v1/analytics/monthly-calendar")
        assert cal_res.status_code == 200
        months = cal_res.json()
        assert len(months) == 8
        assert all(m["pnl"] > 0 for m in months)
