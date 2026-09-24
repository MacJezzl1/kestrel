"""
Kestrel Autopilot — Risk Gates Module
Hard safety constraints that MUST pass before any autonomous trade fires.
These are non-overridable circuit breakers to protect capital.

CapeChain Labs — "See every market. Miss nothing."
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple


class RiskGateResult:
    """Result of a single risk gate evaluation."""

    def __init__(self, gate_name: str, passed: bool, reason: str = ""):
        self.gate_name = gate_name
        self.passed = passed
        self.reason = reason

    def to_dict(self) -> dict:
        return {
            "gate": self.gate_name,
            "passed": self.passed,
            "reason": self.reason,
        }


class RiskGates:
    """
    Evaluates all mandatory risk gates before an autonomous trade is executed.
    Every gate must pass (AND logic) — a single failure blocks the trade.
    """

    # ── Gate 1: Confidence Threshold ──────────────────────────────────
    @staticmethod
    def check_confidence(
        consensus_pct: float, threshold: float
    ) -> RiskGateResult:
        """Swarm consensus must exceed user-set confidence threshold."""
        passed = consensus_pct >= threshold
        if passed:
            return RiskGateResult(
                "confidence_threshold", True,
                f"Consensus {consensus_pct:.1f}% >= {threshold:.1f}% threshold"
            )
        return RiskGateResult(
            "confidence_threshold", False,
            f"Consensus {consensus_pct:.1f}% < {threshold:.1f}% threshold — signal too weak"
        )

    # ── Gate 2: Multi-Timeframe Confluence ────────────────────────────
    @staticmethod
    def check_multi_tf_confluence(
        primary_direction: str,
        confirming_directions: List[str],
    ) -> RiskGateResult:
        """
        Primary TF direction must be confirmed by at least one higher TF.
        Filters "confident but wrong" single-TF traps.
        """
        agreeing = [d for d in confirming_directions if d == primary_direction]
        passed = len(agreeing) >= 1
        if passed:
            return RiskGateResult(
                "multi_tf_confluence", True,
                f"Direction '{primary_direction}' confirmed by {len(agreeing)} higher TF(s)"
            )
        return RiskGateResult(
            "multi_tf_confluence", False,
            f"No higher-TF confirmation for '{primary_direction}' — single-TF trap filter"
        )

    # ── Gate 3: Dynamic Position Sizing ───────────────────────────────
    @staticmethod
    def calculate_lot_size(
        equity: float,
        risk_pct: float,
        sl_distance: float,
        pip_value: float = 1.0,
        min_lot: float = 0.01,
        max_lot: float = 10.0,
    ) -> Tuple[float, RiskGateResult]:
        """
        Calculate lot size as risk_pct * equity / (SL_distance * pip_value).
        Never a fixed lot — always proportional to account size and stop distance.
        """
        if sl_distance <= 0 or equity <= 0:
            return min_lot, RiskGateResult(
                "position_sizing", False,
                f"Invalid SL distance ({sl_distance}) or equity ({equity})"
            )

        risk_amount = equity * (risk_pct / 100.0)
        raw_lot = risk_amount / (sl_distance * pip_value)
        clamped_lot = round(max(min_lot, min(max_lot, raw_lot)), 2)

        return clamped_lot, RiskGateResult(
            "position_sizing", True,
            f"Lot {clamped_lot} = {risk_pct}% of ${equity:.2f} equity / {sl_distance:.2f} SL distance"
        )

    # ── Gate 4: Daily Max Loss Circuit Breaker ────────────────────────
    @staticmethod
    def check_daily_loss(
        daily_loss_today: float,
        equity: float,
        daily_max_loss_pct: float,
    ) -> RiskGateResult:
        """If cumulative loss today exceeds daily_max_loss_pct, halt for the day."""
        if equity <= 0:
            return RiskGateResult(
                "daily_loss_breaker", False, "Equity is zero or negative"
            )

        loss_pct = abs(daily_loss_today) / equity * 100 if daily_loss_today < 0 else 0
        passed = loss_pct < daily_max_loss_pct
        if passed:
            return RiskGateResult(
                "daily_loss_breaker", True,
                f"Daily loss {loss_pct:.2f}% < {daily_max_loss_pct}% limit"
            )
        return RiskGateResult(
            "daily_loss_breaker", False,
            f"CIRCUIT BREAKER: Daily loss {loss_pct:.2f}% >= {daily_max_loss_pct}% limit — halted for today"
        )

    # ── Gate 5: Weekly Max Loss Circuit Breaker ───────────────────────
    @staticmethod
    def check_weekly_loss(
        weekly_loss: float,
        equity: float,
        weekly_max_loss_pct: float,
    ) -> RiskGateResult:
        """If cumulative loss this week exceeds weekly_max_loss_pct, halt for the week."""
        if equity <= 0:
            return RiskGateResult(
                "weekly_loss_breaker", False, "Equity is zero or negative"
            )

        loss_pct = abs(weekly_loss) / equity * 100 if weekly_loss < 0 else 0
        passed = loss_pct < weekly_max_loss_pct
        if passed:
            return RiskGateResult(
                "weekly_loss_breaker", True,
                f"Weekly loss {loss_pct:.2f}% < {weekly_max_loss_pct}% limit"
            )
        return RiskGateResult(
            "weekly_loss_breaker", False,
            f"CIRCUIT BREAKER: Weekly loss {loss_pct:.2f}% >= {weekly_max_loss_pct}% limit — halted for week"
        )

    # ── Gate 6: Max Concurrent Positions ──────────────────────────────
    @staticmethod
    def check_max_positions(
        current_open: int,
        max_concurrent: int,
    ) -> RiskGateResult:
        """Cap on simultaneous open positions."""
        passed = current_open < max_concurrent
        if passed:
            return RiskGateResult(
                "max_positions", True,
                f"Open positions {current_open} < {max_concurrent} max"
            )
        return RiskGateResult(
            "max_positions", False,
            f"Max positions reached: {current_open}/{max_concurrent} — no new trades"
        )

    # ── Gate 7: News Blackout ─────────────────────────────────────────
    @staticmethod
    def check_news_blackout(
        news_blackout_enabled: bool,
        high_impact_events: Optional[List[Dict[str, Any]]] = None,
        blackout_minutes: int = 15,
    ) -> RiskGateResult:
        """Auto-pause around high-impact news events."""
        if not news_blackout_enabled:
            return RiskGateResult(
                "news_blackout", True, "News blackout disabled by user"
            )

        if not high_impact_events:
            return RiskGateResult(
                "news_blackout", True, "No high-impact news events detected"
            )

        now = datetime.now(timezone.utc)
        for event in high_impact_events:
            event_time = event.get("time")
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
                except ValueError:
                    continue
            if event_time is None:
                continue

            window_start = event_time - timedelta(minutes=blackout_minutes)
            window_end = event_time + timedelta(minutes=blackout_minutes)

            if window_start <= now <= window_end:
                event_name = event.get("name", "Unknown Event")
                return RiskGateResult(
                    "news_blackout", False,
                    f"NEWS BLACKOUT: Within {blackout_minutes}min window of '{event_name}' — trading paused"
                )

        return RiskGateResult(
            "news_blackout", True,
            "Outside all news blackout windows"
        )

    # ── Gate 8: Drawdown Guard Integration ────────────────────────────
    @staticmethod
    def check_drawdown_guard(
        recovery_level: str,
    ) -> RiskGateResult:
        """
        Hooks into existing recovery metrics.
        If in RECOVERY_SHIELD or AGGRESSIVE_RECOVERY, auto-pause.
        """
        blocked_levels = {"RECOVERY_SHIELD", "AGGRESSIVE_RECOVERY"}
        passed = recovery_level not in blocked_levels
        if passed:
            return RiskGateResult(
                "drawdown_guard", True,
                f"Recovery level '{recovery_level}' — trading permitted"
            )
        return RiskGateResult(
            "drawdown_guard", False,
            f"DRAWDOWN GUARD: Recovery level '{recovery_level}' — autopilot paused until drawdown recovers"
        )

    # ── Gate 9: Performance Drift Monitor ─────────────────────────────
    @staticmethod
    def check_performance_drift(
        live_winrate: float,
        baseline_winrate: float,
        drift_threshold_pct: float,
    ) -> RiskGateResult:
        """
        If live performance drifts materially from baseline expectations,
        auto-flag and revert to suggest-only.
        """
        if baseline_winrate <= 0:
            # No baseline established yet — pass through
            return RiskGateResult(
                "performance_drift", True,
                "No baseline established — drift check skipped"
            )

        drift = baseline_winrate - live_winrate
        drift_pct = (drift / baseline_winrate) * 100 if baseline_winrate > 0 else 0

        passed = drift_pct < drift_threshold_pct
        if passed:
            return RiskGateResult(
                "performance_drift", True,
                f"Live WR {live_winrate:.1f}% vs baseline {baseline_winrate:.1f}% — drift {drift_pct:.1f}% within {drift_threshold_pct}% tolerance"
            )
        return RiskGateResult(
            "performance_drift", False,
            f"DRIFT ALERT: Live WR {live_winrate:.1f}% vs baseline {baseline_winrate:.1f}% — drift {drift_pct:.1f}% exceeds {drift_threshold_pct}% — reverting to suggest-only"
        )

    # ── Run All Gates ─────────────────────────────────────────────────
    @classmethod
    def evaluate_all(
        cls,
        consensus_pct: float,
        confidence_threshold: float,
        primary_direction: str,
        confirming_directions: List[str],
        equity: float,
        risk_pct: float,
        sl_distance: float,
        daily_loss_today: float,
        daily_max_loss_pct: float,
        weekly_loss: float,
        weekly_max_loss_pct: float,
        current_open_positions: int,
        max_concurrent_positions: int,
        news_blackout_enabled: bool,
        recovery_level: str,
        live_winrate: float,
        baseline_winrate: float,
        drift_threshold_pct: float,
        high_impact_events: Optional[List[Dict[str, Any]]] = None,
        pip_value: float = 1.0,
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """
        Run all risk gates. Returns (all_passed, calculated_lot_size, gate_results).
        """
        results: List[RiskGateResult] = []

        results.append(cls.check_confidence(consensus_pct, confidence_threshold))
        results.append(cls.check_multi_tf_confluence(primary_direction, confirming_directions))

        lot_size, sizing_result = cls.calculate_lot_size(
            equity, risk_pct, sl_distance, pip_value
        )
        results.append(sizing_result)

        results.append(cls.check_daily_loss(daily_loss_today, equity, daily_max_loss_pct))
        results.append(cls.check_weekly_loss(weekly_loss, equity, weekly_max_loss_pct))
        results.append(cls.check_max_positions(current_open_positions, max_concurrent_positions))
        results.append(cls.check_news_blackout(news_blackout_enabled, high_impact_events))
        results.append(cls.check_drawdown_guard(recovery_level))
        results.append(cls.check_performance_drift(live_winrate, baseline_winrate, drift_threshold_pct))

        all_passed = all(r.passed for r in results)
        return all_passed, lot_size, [r.to_dict() for r in results]
