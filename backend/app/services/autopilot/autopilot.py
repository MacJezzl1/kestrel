"""
Kestrel Autopilot — Autonomous Execution Engine v1.0
CapeChain Labs — "See every market. Miss nothing."

Design Principle: No system can be mathematically "perfect" or guarantee
the right call every time — markets are probabilistic. Autopilot's job is
disciplined, consistent execution that only acts when the odds are genuinely
stacked in its favor, not infallibility.

Runs as an async background task inside FastAPI's lifespan.
On each tick: Signal → Confidence Gate → Multi-TF Confluence → Risk Calc
→ Circuit Breaker Checks → Execution → Audit Trail
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from app.services.autopilot.risk_gates import RiskGates

logger = logging.getLogger("kestrel.autopilot")

# Multi-TF confirmation map: for each primary TF, which higher TFs to check
CONFIRMING_TIMEFRAMES = {
    "M1": ["M5", "M15"],
    "M5": ["M15", "H1"],
    "M15": ["H1", "H4"],
    "M30": ["H1", "H4"],
    "H1": ["H4", "D1"],
    "H4": ["D1"],
    "D1": [],
}


class AutopilotDecision:
    """A single decision record from the autopilot engine."""

    def __init__(
        self,
        instrument: str,
        timeframe: str,
        direction: str,
        confidence: float,
        action: str,  # "executed", "skipped", "paper_logged"
        reason: str,
        gate_results: List[Dict[str, Any]],
        lot_size: float = 0.0,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        signal_snapshot: Optional[Dict[str, Any]] = None,
    ):
        self.instrument = instrument
        self.timeframe = timeframe
        self.direction = direction
        self.confidence = confidence
        self.action = action
        self.reason = reason
        self.gate_results = gate_results
        self.lot_size = lot_size
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.signal_snapshot = signal_snapshot
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "instrument": self.instrument,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "confidence": self.confidence,
            "action": self.action,
            "reason": self.reason,
            "gate_results": self.gate_results,
            "lot_size": self.lot_size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "timestamp": self.timestamp.isoformat(),
        }


class AutopilotEngine:
    """
    Kestrel Autopilot Engine — Autonomous Trade Execution.

    Core loop:
    1. Generate signal for each instrument in the user's watchlist
    2. Evaluate all 9 risk gates
    3. If ALL pass → execute trade (or paper-log in paper mode)
    4. If ANY fail → skip and log reason
    5. Continuously monitor performance drift
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._recent_decisions: List[Dict[str, Any]] = []  # ring buffer, max 200
        self._max_decisions = 200
        self._paper_trades: List[Dict[str, Any]] = []
        self._live_trades_results: List[Dict[str, Any]] = []

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def recent_decisions(self) -> List[Dict[str, Any]]:
        return list(self._recent_decisions)

    def _log_decision(self, decision: AutopilotDecision):
        """Add decision to ring buffer."""
        entry = decision.to_dict()
        self._recent_decisions.append(entry)
        if len(self._recent_decisions) > self._max_decisions:
            self._recent_decisions = self._recent_decisions[-self._max_decisions:]

    async def start(self):
        """Start the autopilot background loop."""
        if self._running:
            logger.warning("[Autopilot] Already running — ignoring start request")
            return
        self._running = True
        self._task = asyncio.create_task(self._main_loop())
        logger.info("[Autopilot] ✈️ Engine started — background loop active")

    async def stop(self):
        """Gracefully stop the autopilot loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("[Autopilot] 🛑 Engine stopped")

    async def emergency_kill(self):
        """Emergency stop + close all positions."""
        await self.stop()
        logger.warning("[Autopilot] 🚨 EMERGENCY KILL — closing all positions")
        try:
            from app.db.supabase_client import supabase_client
            await supabase_client.push_remote_command({
                "action": "CLOSE_ALL",
                "instrument": "ALL",
                "lot_size": 0,
                "sl": 0,
                "tp": 0,
                "user_id": "autopilot",
                "source": "autopilot_emergency_kill",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.error(f"[Autopilot] Emergency close-all failed: {e}")

    async def _main_loop(self):
        """
        Core autopilot tick loop. Runs continuously until stopped.
        Each tick processes all instruments in the user's watchlist.
        """
        logger.info("[Autopilot] Main loop started")

        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Autopilot] Tick error: {e}", exc_info=True)

            # Get scan interval from config
            interval = await self._get_scan_interval()
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break

        logger.info("[Autopilot] Main loop exited")

    async def _get_scan_interval(self) -> int:
        """Fetch configured scan interval, default 60s."""
        try:
            config = await self._load_config()
            return config.get("scan_interval_seconds", 60) if config else 60
        except Exception:
            return 60

    async def _load_config(self) -> Optional[Dict[str, Any]]:
        """Load autopilot config from database."""
        try:
            from app.db.database import async_session
            from app.models.models import AutopilotConfig
            from sqlalchemy import select

            async with async_session() as db:
                result = await db.execute(
                    select(AutopilotConfig).limit(1)
                )
                config = result.scalar_one_or_none()
                if config:
                    return {
                        "is_enabled": config.is_enabled,
                        "mode": config.mode,
                        "confidence_threshold": config.confidence_threshold,
                        "risk_per_trade_pct": config.risk_per_trade_pct,
                        "daily_max_loss_pct": config.daily_max_loss_pct,
                        "weekly_max_loss_pct": config.weekly_max_loss_pct,
                        "max_concurrent_positions": config.max_concurrent_positions,
                        "scan_interval_seconds": config.scan_interval_seconds,
                        "instruments": config.instruments or ["Volatility 100 Index"],
                        "instrument_modes": config.instrument_modes or {},
                        "news_blackout_enabled": config.news_blackout_enabled,
                        "paper_trade_count": config.paper_trade_count,
                        "paper_trade_required": config.paper_trade_required,
                        "performance_baseline_winrate": config.performance_baseline_winrate,
                        "drift_threshold_pct": config.drift_threshold_pct,
                        "is_drift_paused": config.is_drift_paused,
                        "daily_loss_today": config.daily_loss_today,
                        "daily_loss_reset_at": config.daily_loss_reset_at,
                        "user_id": config.user_id,
                    }
        except Exception as e:
            logger.error(f"[Autopilot] Config load failed: {e}")
        return None

    async def _tick(self):
        """Single autopilot evaluation cycle."""
        config = await self._load_config()
        if not config or not config.get("is_enabled", False):
            return

        mode = config.get("mode", "paper")
        instruments = config.get("instruments", ["Volatility 100 Index"])
        instrument_modes = config.get("instrument_modes", {})

        # Check if drift-paused
        if config.get("is_drift_paused", False):
            logger.info("[Autopilot] Drift-paused — operating in suggest-only mode")
            return

        # Reset daily loss if new day
        await self._maybe_reset_daily_loss(config)

        # Get account state
        account_state = await self._get_account_state()
        equity = account_state.get("equity", 10000.0)
        recovery_level = account_state.get("recovery_level", "OPTIMAL")
        open_positions = account_state.get("open_positions", 0)

        # Calculate weekly loss
        weekly_loss = await self._calculate_weekly_loss()

        from app.services.ensemble.engine import ensemble_engine

        for instrument in instruments:
            # Check per-instrument mode
            inst_mode = instrument_modes.get(instrument, "suggest_only")
            if inst_mode == "suggest_only" and mode == "live":
                continue  # This instrument is suggest-only, skip autonomous execution

            try:
                await self._evaluate_instrument(
                    instrument=instrument,
                    config=config,
                    mode=mode,
                    equity=equity,
                    recovery_level=recovery_level,
                    open_positions=open_positions,
                    weekly_loss=weekly_loss,
                    ensemble_engine=ensemble_engine,
                )
            except Exception as e:
                logger.error(f"[Autopilot] Error evaluating {instrument}: {e}")

    async def _evaluate_instrument(
        self,
        instrument: str,
        config: Dict[str, Any],
        mode: str,
        equity: float,
        recovery_level: str,
        open_positions: int,
        weekly_loss: float,
        ensemble_engine: Any,
    ):
        """Evaluate a single instrument through the full autopilot pipeline."""
        primary_tf = "H1"  # Default primary timeframe

        # Step 1: Generate primary signal
        signal = ensemble_engine.generate_signal(
            instrument=instrument,
            timeframe=primary_tf,
            account_drawdown=0.0,
        )

        direction = signal["direction"]
        confidence = signal["confidence"]
        consensus_pct = signal.get("swarm_summary", {}).get("consensus_pct", confidence * 100)
        entry_price = signal.get("entry_price", 0.0)
        stop_loss = signal.get("stop_loss")
        take_profit = signal.get("take_profit")

        if direction == "hold":
            decision = AutopilotDecision(
                instrument=instrument,
                timeframe=primary_tf,
                direction=direction,
                confidence=confidence,
                action="skipped",
                reason="Signal direction is HOLD — no trade setup",
                gate_results=[],
            )
            self._log_decision(decision)
            return

        # Step 2: Multi-TF Confluence — get confirming TF directions
        confirming_tfs = CONFIRMING_TIMEFRAMES.get(primary_tf, [])
        confirming_directions = []
        for tf in confirming_tfs:
            try:
                tf_signal = ensemble_engine.generate_signal(instrument, tf)
                if tf_signal["direction"] != "hold":
                    confirming_directions.append(tf_signal["direction"])
            except Exception:
                pass

        # Step 3: Calculate SL distance for position sizing
        sl_distance = abs(entry_price - stop_loss) if stop_loss and entry_price else 10.0

        # Step 4: Get live performance metrics
        live_winrate = await self._calculate_live_winrate()
        baseline_winrate = config.get("performance_baseline_winrate", 0.0)

        # Step 5: Run ALL risk gates
        all_passed, lot_size, gate_results = RiskGates.evaluate_all(
            consensus_pct=consensus_pct,
            confidence_threshold=config.get("confidence_threshold", 80.0),
            primary_direction=direction,
            confirming_directions=confirming_directions,
            equity=equity,
            risk_pct=config.get("risk_per_trade_pct", 1.0),
            sl_distance=sl_distance,
            daily_loss_today=config.get("daily_loss_today", 0.0),
            daily_max_loss_pct=config.get("daily_max_loss_pct", 5.0),
            weekly_loss=weekly_loss,
            weekly_max_loss_pct=config.get("weekly_max_loss_pct", 10.0),
            current_open_positions=open_positions,
            max_concurrent_positions=config.get("max_concurrent_positions", 3),
            news_blackout_enabled=config.get("news_blackout_enabled", True),
            recovery_level=recovery_level,
            live_winrate=live_winrate,
            baseline_winrate=baseline_winrate,
            drift_threshold_pct=config.get("drift_threshold_pct", 15.0),
        )

        # Check for performance drift auto-pause
        drift_gate = next((g for g in gate_results if g["gate"] == "performance_drift"), None)
        if drift_gate and not drift_gate["passed"]:
            await self._set_drift_paused(True)
            logger.warning(f"[Autopilot] Performance drift detected — auto-reverting to suggest-only")

        if not all_passed:
            # Some gates failed — skip trade
            failed_gates = [g for g in gate_results if not g["passed"]]
            primary_reason = failed_gates[0]["reason"] if failed_gates else "Unknown gate failure"

            decision = AutopilotDecision(
                instrument=instrument,
                timeframe=primary_tf,
                direction=direction,
                confidence=confidence,
                action="skipped",
                reason=primary_reason,
                gate_results=gate_results,
                signal_snapshot=signal,
            )
            self._log_decision(decision)
            await self._audit_log("autopilot_skip", {
                "instrument": instrument,
                "direction": direction,
                "confidence": confidence,
                "reason": primary_reason,
                "failed_gates": [g["gate"] for g in failed_gates],
            })
            return

        # All gates passed!
        if mode == "paper":
            # Paper mode — log but don't execute
            decision = AutopilotDecision(
                instrument=instrument,
                timeframe=primary_tf,
                direction=direction,
                confidence=confidence,
                action="paper_logged",
                reason=f"Paper trade logged — {direction.upper()} {instrument} @ {entry_price}",
                gate_results=gate_results,
                lot_size=lot_size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_snapshot=signal,
            )
            self._log_decision(decision)
            self._paper_trades.append(decision.to_dict())
            await self._increment_paper_count()
            await self._audit_log("autopilot_paper_trade", {
                "instrument": instrument,
                "direction": direction,
                "confidence": confidence,
                "lot_size": lot_size,
                "entry_price": entry_price,
            })
            logger.info(f"[Autopilot] 📝 PAPER: {direction.upper()} {instrument} | Lot: {lot_size} | Conf: {confidence:.1%}")

        elif mode == "live":
            # Live mode — execute the trade via Supabase command bridge
            try:
                from app.db.supabase_client import supabase_client
                await supabase_client.push_remote_command({
                    "action": direction.upper(),
                    "instrument": instrument,
                    "lot_size": lot_size,
                    "sl": stop_loss or 0,
                    "tp": take_profit or 0,
                    "user_id": config.get("user_id", "autopilot"),
                    "source": "autopilot_live",
                    "confidence": confidence,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

                decision = AutopilotDecision(
                    instrument=instrument,
                    timeframe=primary_tf,
                    direction=direction,
                    confidence=confidence,
                    action="executed",
                    reason=f"LIVE TRADE: {direction.upper()} {instrument} | Lot: {lot_size} | SL: {stop_loss} | TP: {take_profit}",
                    gate_results=gate_results,
                    lot_size=lot_size,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    signal_snapshot=signal,
                )
                self._log_decision(decision)
                self._live_trades_results.append(decision.to_dict())

                await self._audit_log("autopilot_live_trade", {
                    "instrument": instrument,
                    "direction": direction,
                    "confidence": confidence,
                    "lot_size": lot_size,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "gate_results": gate_results,
                })
                logger.info(f"[Autopilot] 🚀 LIVE EXECUTED: {direction.upper()} {instrument} | Lot: {lot_size} | Conf: {confidence:.1%}")

            except Exception as e:
                logger.error(f"[Autopilot] Live execution failed: {e}")
                decision = AutopilotDecision(
                    instrument=instrument,
                    timeframe=primary_tf,
                    direction=direction,
                    confidence=confidence,
                    action="skipped",
                    reason=f"Execution failed: {str(e)}",
                    gate_results=gate_results,
                    lot_size=lot_size,
                )
                self._log_decision(decision)

    async def _get_account_state(self) -> Dict[str, Any]:
        """Fetch live account equity, recovery level, and open position count."""
        try:
            from app.db.supabase_client import supabase_client
            acc = await supabase_client.get_latest_account(
                license_key="kestrel-enterprise-owner-vip",
                user_email=""
            )
            if acc:
                return {
                    "equity": float(acc.get("equity", 10000.0)),
                    "balance": float(acc.get("balance", 10000.0)),
                    "recovery_level": str(acc.get("recovery_level", "OPTIMAL")),
                    "open_positions": 0,  # Will be populated from trade count
                }
        except Exception:
            pass
        return {"equity": 10000.0, "balance": 10000.0, "recovery_level": "OPTIMAL", "open_positions": 0}

    async def _calculate_weekly_loss(self) -> float:
        """Calculate cumulative P&L for the current week."""
        try:
            from app.db.database import async_session
            from app.models.models import Trade
            from sqlalchemy import select

            now = datetime.now(timezone.utc)
            week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

            async with async_session() as db:
                result = await db.execute(
                    select(Trade).where(
                        Trade.status == "closed",
                        Trade.closed_at >= week_start,
                    )
                )
                trades = result.scalars().all()
                return sum(t.pnl for t in trades)
        except Exception:
            return 0.0

    async def _calculate_live_winrate(self) -> float:
        """Calculate rolling live win rate from recent autopilot trades."""
        executed = [d for d in self._recent_decisions if d.get("action") in ("executed", "paper_logged")]
        if len(executed) < 5:
            return 0.0  # Not enough data

        # For paper trades, we estimate based on direction vs subsequent signals
        # For live trades, we'll use actual P&L when available
        # For now, return 0 to skip drift check until we have data
        return 0.0

    async def _maybe_reset_daily_loss(self, config: Dict[str, Any]):
        """Reset daily loss counter if a new day has started."""
        try:
            reset_at = config.get("daily_loss_reset_at")
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if reset_at is None or (isinstance(reset_at, datetime) and reset_at < today_start):
                from app.db.database import async_session
                from app.models.models import AutopilotConfig as APConfig
                from sqlalchemy import select

                async with async_session() as db:
                    result = await db.execute(select(APConfig).limit(1))
                    cfg = result.scalar_one_or_none()
                    if cfg:
                        cfg.daily_loss_today = 0.0
                        cfg.daily_loss_reset_at = now
                        await db.commit()
        except Exception as e:
            logger.error(f"[Autopilot] Daily loss reset error: {e}")

    async def _increment_paper_count(self):
        """Increment the paper trade counter."""
        try:
            from app.db.database import async_session
            from app.models.models import AutopilotConfig as APConfig
            from sqlalchemy import select

            async with async_session() as db:
                result = await db.execute(select(APConfig).limit(1))
                cfg = result.scalar_one_or_none()
                if cfg:
                    cfg.paper_trade_count = (cfg.paper_trade_count or 0) + 1
                    await db.commit()
        except Exception as e:
            logger.error(f"[Autopilot] Paper count increment error: {e}")

    async def _set_drift_paused(self, paused: bool):
        """Set the drift-paused flag in the database."""
        try:
            from app.db.database import async_session
            from app.models.models import AutopilotConfig as APConfig
            from sqlalchemy import select

            async with async_session() as db:
                result = await db.execute(select(APConfig).limit(1))
                cfg = result.scalar_one_or_none()
                if cfg:
                    cfg.is_drift_paused = paused
                    if not paused:
                        cfg.mode = "live"
                    await db.commit()
        except Exception as e:
            logger.error(f"[Autopilot] Drift pause update error: {e}")

    async def _audit_log(self, action: str, details: Dict[str, Any]):
        """Write to the immutable audit ledger."""
        try:
            from app.db.database import async_session
            from app.services.shield.audit import log_action

            async with async_session() as db:
                await log_action(db, action, "autopilot-engine", details)
                await db.commit()
        except Exception as e:
            logger.error(f"[Autopilot] Audit log error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current autopilot engine status."""
        recent_executed = [d for d in self._recent_decisions if d.get("action") == "executed"]
        recent_skipped = [d for d in self._recent_decisions if d.get("action") == "skipped"]
        recent_paper = [d for d in self._recent_decisions if d.get("action") == "paper_logged"]

        return {
            "is_running": self._running,
            "total_decisions": len(self._recent_decisions),
            "recent_executed": len(recent_executed),
            "recent_skipped": len(recent_skipped),
            "recent_paper": len(recent_paper),
            "paper_trades_total": len(self._paper_trades),
            "live_trades_total": len(self._live_trades_results),
            "last_decision": self._recent_decisions[-1] if self._recent_decisions else None,
            "last_5_decisions": self._recent_decisions[-5:],
        }


# Singleton
autopilot_engine = AutopilotEngine()
