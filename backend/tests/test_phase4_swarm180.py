"""
Kestrel Core — Phase 4 180-Agent Swarm Intelligence & Ensemble Tests
Tests 180-agent swarm quorum consensus, 6 specialized clusters (30 models each),
drift mechanics for synthetics, multi-model LLM orchestration, and institutional AiLog auditing.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import init_db, close_db
from app.services.ensemble.swarm_180 import swarm_engine, Swarm180Engine, Swarm100Engine, SWARM_CATEGORIES
from app.services.ensemble.multi_orchestrator import multi_orchestrator


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await close_db()


def test_swarm_180_model_counts_and_clusters():
    """Verify exactly 180 models distributed across 6 specialized clusters of 30 models each."""
    assert swarm_engine.total_models == 180
    assert len(SWARM_CATEGORIES) == 6
    for cluster_name, models in SWARM_CATEGORIES.items():
        assert len(models) == 30, f"Cluster {cluster_name} has {len(models)} models, expected 30"
    # Ensure backward-compatible alias exists
    assert Swarm100Engine is Swarm180Engine


def test_swarm_consensus_generation_xauusd():
    """Verify deterministic 180-agent consensus generation on Gold (XAUUSD)."""
    result = swarm_engine.generate_swarm_consensus("XAUUSD", "H1", account_drawdown=1.2)

    assert result["instrument"] == "XAUUSD"
    assert result["timeframe"] == "H1"
    assert result["direction"].upper() in ("BUY", "SELL", "HOLD")
    assert 0.50 <= result["confidence"] <= 1.0
    assert result["entry_price"] > 0
    assert result["stop_loss"] is not None
    assert result["take_profit"] is not None
    assert "8h-24h" in result["recommended_duration"] or "Swing" in result["holding_time_estimate"]

    summary = result["swarm_summary"]
    assert summary["total_models"] == 180
    assert (summary["buy_votes"] + summary["sell_votes"] + summary["hold_votes"]) == 180
    assert 50.0 <= summary["consensus_pct"] <= 100.0

    breakdowns = summary["breakdowns"]
    assert len(breakdowns) == 6
    for cluster_name, stats in breakdowns.items():
        assert stats["total"] == 30
        assert (stats["buy"] + stats["sell"] + stats["hold"]) == 30


def test_synthetic_indices_drift_mechanics():
    """Verify specialized Poisson spike arrival & drift bias for Crash & Boom indices."""
    crash_result = swarm_engine.generate_swarm_consensus("Crash 500 Index", "M15")
    boom_result = swarm_engine.generate_swarm_consensus("Boom 1000 Index", "M15")

    # Crash indices drift upward between spikes; Boom indices drift downward
    crash_deriv_cluster = crash_result["swarm_summary"]["breakdowns"]["SYNTHETIC_DERIV_QUANT"]
    boom_deriv_cluster = boom_result["swarm_summary"]["breakdowns"]["SYNTHETIC_DERIV_QUANT"]

    assert crash_deriv_cluster["buy"] > crash_deriv_cluster["sell"]
    assert boom_deriv_cluster["sell"] > boom_deriv_cluster["buy"]


def test_dynamic_recovery_shield_tiers():
    """Verify drawdown protection and dynamic multiplier adjustments."""
    m_opt = swarm_engine.calculate_recovery_metrics(1.0)
    assert m_opt["recovery_level"] == "OPTIMAL"
    assert m_opt["recovery_multiplier"] == 1.00
    assert m_opt["shield_active"] is False

    m_caut = swarm_engine.calculate_recovery_metrics(3.5)
    assert m_caut["recovery_level"] == "CAUTION"
    assert m_caut["recovery_multiplier"] == 0.85

    m_shield = swarm_engine.calculate_recovery_metrics(7.0)
    assert m_shield["recovery_level"] == "RECOVERY_SHIELD"
    assert m_shield["recovery_multiplier"] == 0.60
    assert m_shield["shield_active"] is True

    m_aggr = swarm_engine.calculate_recovery_metrics(12.5)
    assert m_aggr["recovery_level"] == "AGGRESSIVE_RECOVERY"
    assert m_aggr["recovery_multiplier"] == 0.35
    assert m_aggr["shield_active"] is True


@pytest.mark.asyncio
async def test_ensemble_api_directory_and_consensus():
    """Verify GET /api/v1/ensemble/swarm-180 and POST /api/v1/ensemble/consensus."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Directory
        dir_res = await client.get("/api/v1/ensemble/swarm-180")
        assert dir_res.status_code == 200
        dir_data = dir_res.json()
        assert dir_data["total_models"] == 180
        assert dir_data["categories_count"] == 6
        assert dir_data["models_per_category"] == 30
        assert dir_data["status"] == "ONLINE"

        # 2. Consensus Generation
        req = {
            "instrument": "EURUSD",
            "timeframe": "H4",
            "account_drawdown": 2.5
        }
        cons_res = await client.post("/api/v1/ensemble/consensus", json=req)
        assert cons_res.status_code == 200
        cons_data = cons_res.json()
        assert cons_data["instrument"] == "EURUSD"
        assert cons_data["swarm_summary"]["total_models"] == 180
        assert cons_data["recovery_metrics"]["recovery_level"] == "CAUTION"


@pytest.mark.asyncio
async def test_multi_model_orchestrator_and_ai_log():
    """Verify LLM quorum consensus synthesis and persistence into AiLog."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        query_payload = {
            "instrument": "XAUUSD",
            "timeframe": "H1",
            "current_price": 2655.40,
            "bias": "BULLISH"
        }
        res = await client.post("/api/v1/ensemble/orchestrator-query", json=query_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["instrument"] == "XAUUSD"
        assert data["consensus_direction"] in ("BUY", "SELL", "HOLD")
        assert len(data["models_queried"]) >= 3
        assert data["is_quorum_reached"] is True

        # Query recent ai-logs to confirm audit persistence
        logs_res = await client.get("/api/v1/ensemble/ai-logs?limit=5")
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert len(logs) >= 1
        assert logs[0]["model"] == "ENSEMBLE_MULTI_QUORUM"
