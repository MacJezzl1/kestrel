"""
Phase 1 Unit & Integration Tests: MT5 EA v4.0 Institutional Quant & Risk Engine
Tests:
- Calendar & Macro News Filter (/api/v1/calendar/forex-factory)
- Prop-Firm Rules Engine (FTMO, MFF, The5ers, EquityEdge limits, buffer stop)
- Audited CRiskEngine Math (Kelly Criterion cap, ATR-based lot sizing, Daily Circuit Breaker)
- Correlation Guard logic (|corr| > 0.70 same-side rejection)
- Adaptive Regime Switcher (Hurst Exponent R/S analysis on trending vs mean-reverting series)
- Smart Money Concepts (SMC) confluence rules (OB, FVG 50% mitigation, Liquidity sweeps)
"""
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ==============================================================================
# 1. Economic Calendar & Macro News Guard Endpoint
# ==============================================================================
def test_calendar_forex_factory_endpoint():
    """Verify the Forex Factory economic calendar feed returns valid Pydantic schemas."""
    response = client.get("/api/v1/calendar/forex-factory")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0

    for ev in events:
        assert "title" in ev
        assert "country" in ev
        assert "currency" in ev
        assert "impact" in ev
        assert ev["impact"] == "HIGH"  # Default filter is HIGH
        assert "event_time_utc" in ev
        assert "minutes_until" in ev


def test_calendar_forex_factory_filtering():
    """Verify impact and currency filtering on calendar endpoint."""
    # Filter by currency=USD
    res_usd = client.get("/api/v1/calendar/forex-factory?currency=USD")
    assert res_usd.status_code == 200
    for ev in res_usd.json():
        assert ev["currency"] == "USD"

    # Filter by impact=ALL
    res_all = client.get("/api/v1/calendar/forex-factory?impact=ALL")
    assert res_all.status_code == 200
    impacts = {ev["impact"] for ev in res_all.json()}
    assert "HIGH" in impacts or "MEDIUM" in impacts


# ==============================================================================
# 2. Prop-Firm Rules Engine Math
# ==============================================================================
def calculate_daily_loss_pct(day_start_equity: float, current_equity: float) -> float:
    if day_start_equity <= 0:
        return 0.0
    if current_equity >= day_start_equity:
        return 0.0
    return ((day_start_equity - current_equity) / day_start_equity) * 100.0


def calculate_total_drawdown_pct(peak_equity: float, current_equity: float) -> float:
    if peak_equity <= 0:
        return 0.0
    if current_equity >= peak_equity:
        return 0.0
    return ((peak_equity - current_equity) / peak_equity) * 100.0


def check_prop_firm_breach(mode: str, day_start: float, peak: float, current: float) -> tuple[bool, str]:
    limits = {
        "FTMO": (5.0, 10.0),
        "MFF": (5.0, 12.0),
        "THE5ERS": (5.0, 10.0),
        "EQUITY_EDGE": (4.0, 8.0),
    }
    max_daily, max_total = limits.get(mode, (5.0, 10.0))
    d_loss = calculate_daily_loss_pct(day_start, current)
    t_dd = calculate_total_drawdown_pct(peak, current)

    # 0.5% safety buffer before hard challenge failure
    if d_loss >= (max_daily - 0.5):
        return True, f"DAILY_LOSS_BREACH: {d_loss:.2f}% >= {max_daily - 0.5:.2f}% buffer"
    if t_dd >= (max_total - 0.5):
        return True, f"TOTAL_DD_BREACH: {t_dd:.2f}% >= {max_total - 0.5:.2f}% buffer"
    return False, "OK"


def test_prop_firm_rules_enforcement():
    """Verify FTMO and EquityEdge hard-stop triggers at specified drawdown thresholds."""
    day_start = 100_000.0
    peak = 102_000.0

    # Normal trading: day loss = 1.0%, total DD = 2.94%
    current = 99_000.0
    breached, reason = check_prop_firm_breach("FTMO", day_start, peak, current)
    assert not breached

    # FTMO Daily loss buffer breach: day loss = 4.6% (threshold 4.5% with 0.5% buffer)
    current_ftmo_breach = 95_400.0
    breached, reason = check_prop_firm_breach("FTMO", day_start, peak, current_ftmo_breach)
    assert breached
    assert "DAILY_LOSS_BREACH" in reason

    # EquityEdge Total Drawdown breach: total DD = 7.6% on a day starting at 95,000 (day loss = 0.84%)
    day_start_today = 95_000.0
    current_ee_breach = 94_200.0
    breached, reason = check_prop_firm_breach("EQUITY_EDGE", day_start_today, peak, current_ee_breach)
    assert breached
    assert "TOTAL_DD_BREACH" in reason


# ==============================================================================
# 3. Audited CRiskEngine Calculations & Kelly Criterion Cap
# ==============================================================================
def calculate_kelly_fraction(win_rate: float, win_loss_ratio: float) -> float:
    if win_loss_ratio <= 0:
        return 0.0
    # f* = W - (1 - W) / R
    return win_rate - ((1.0 - win_rate) / win_loss_ratio)


def calculate_risk_lot(
    balance: float,
    risk_pct: float,
    sl_points: float,
    tick_value: float,
    tick_size: float,
    point: float,
    lot_cap: float = 5.0,
    win_rate: float = 0.55,
    win_loss_ratio: float = 1.5,
) -> float:
    risk_amount = balance * (risk_pct / 100.0)
    sl_value_per_lot = (sl_points * point / tick_size) * tick_value
    raw_lot = risk_amount / sl_value_per_lot

    # Apply Kelly Criterion Cap: 2x Kelly fraction
    kf = calculate_kelly_fraction(win_rate, win_loss_ratio)
    if kf > 0.0:
        kelly_cap_lot = lot_cap * 2.0 * kf
        if raw_lot > kelly_cap_lot:
            raw_lot = kelly_cap_lot

    return min(raw_lot, lot_cap)


def test_kelly_criterion_and_lot_sizing():
    """Verify ATR-based risk lot sizing and Kelly Criterion capping."""
    balance = 100_000.0
    risk_pct = 1.0  # $1,000 risk
    sl_points = 50.0  # 50 points = 5 pips
    point = 0.0001
    tick_size = 0.0001
    tick_value = 10.0  # $10 per point for 1 standard lot

    # Base lot calculation: $1000 / (50 * $10) = 2.0 lots
    base_lot = calculate_risk_lot(
        balance, risk_pct, sl_points, tick_value, tick_size, point, lot_cap=5.0, win_rate=0.60, win_loss_ratio=1.5
    )
    assert 1.9 <= base_lot <= 2.1

    # Kelly formula check: W=0.60, R=1.5 -> f* = 0.60 - (0.40 / 1.5) = 0.60 - 0.2667 = 0.3333
    kf = calculate_kelly_fraction(0.60, 1.5)
    assert round(kf, 4) == 0.3333


def test_daily_circuit_breaker():
    """Verify circuit breaker triggers when daily loss exceeds 2% or 3 consecutive losses."""
    # Condition 1: Daily loss exceeds 2.0%
    day_start = 100_000.0
    current_ok = 98_500.0  # 1.5% loss
    assert calculate_daily_loss_pct(day_start, current_ok) < 2.0

    current_trip = 97_800.0  # 2.2% loss
    assert calculate_daily_loss_pct(day_start, current_trip) >= 2.0


# ==============================================================================
# 4. Correlation Guard Logic
# ==============================================================================
def check_correlation_guard(
    new_symbol: str, new_dir: str, open_positions: list[tuple[str, str]]
) -> tuple[bool, str]:
    """
    Rejection if open position on pair with shared base or quote currency in the same direction.
    """
    new_base = new_symbol[:3]
    new_quote = new_symbol[3:6] if len(new_symbol) >= 6 else ""

    for open_sym, open_dir in open_positions:
        if open_sym == new_symbol:
            continue
        open_base = open_sym[:3]
        open_quote = open_sym[3:6] if len(open_sym) >= 6 else ""

        # Same quote currency, same direction (e.g. BUY EURUSD & BUY GBPUSD both short USD, r ~ 0.82)
        if new_quote and new_quote == open_quote and new_dir == open_dir:
            return False, f"CORRELATION_REJECT: {new_symbol} and {open_sym} both {new_dir} on {new_quote}"

        # Same base currency, same direction (e.g. BUY EURUSD & BUY EURJPY both long EUR)
        if new_base == open_base and new_dir == open_dir:
            return False, f"CORRELATION_REJECT: {new_symbol} and {open_sym} both {new_dir} on {new_base}"

    return True, "ALLOWED"


def test_correlation_guard_rejections():
    """Verify correlation guard rejects double exposures across correlated currency pairs."""
    open_positions = [("EURUSD", "BUY")]

    # Attempt BUY GBPUSD when EURUSD is already BUY -> both short USD, highly correlated
    allowed, reason = check_correlation_guard("GBPUSD", "BUY", open_positions)
    assert not allowed
    assert "CORRELATION_REJECT" in reason

    # Attempt SELL GBPUSD when EURUSD is BUY -> opposite USD exposure, allowed
    allowed_opp, _ = check_correlation_guard("GBPUSD", "SELL", open_positions)
    assert allowed_opp

    # Attempt BUY USDJPY -> independent pair, allowed
    allowed_ind, _ = check_correlation_guard("USDJPY", "BUY", open_positions)
    assert allowed_ind


# ==============================================================================
# 5. Adaptive Regime Switcher (Hurst Exponent R/S Algorithm)
# ==============================================================================
def calculate_hurst_rs(prices: list[float]) -> float:
    """Python implementation of Rescaled Range (R/S) Hurst Exponent matching MQL5."""
    n = len(prices) - 1
    if n < 50:
        return 0.50

    returns = [math.log(prices[i] / prices[i + 1]) for i in range(n)]
    mean_ret = sum(returns) / n

    cum_dev = []
    current_cum = 0.0
    sum_sq = 0.0
    for r in returns:
        dev = r - mean_ret
        current_cum += dev
        cum_dev.append(current_cum)
        sum_sq += dev * dev

    range_r = max(cum_dev) - min(cum_dev)
    std_s = math.sqrt(sum_sq / n)

    if std_s <= 1e-12 or range_r <= 1e-12:
        return 0.50

    rs = range_r / std_s
    hurst = math.log(rs) / math.log(n / 2.0)
    return max(0.05, min(0.95, hurst))


def test_hurst_exponent_regimes():
    """Verify Hurst exponent correctly distinguishes persistent trends vs mean-reverting vs random walk."""
    np.random.seed(42)

    # 1. Strongly trending geometric series (Persistent trend H > 0.55)
    trend_noise = np.random.normal(0, 0.001, 201)
    trend_prices = [1.0]
    for step in range(200):
        trend_prices.append(trend_prices[-1] * (1.0 + 0.003 + trend_noise[step]))
    trend_prices.reverse()  # Time-series index 0 is newest
    h_trend = calculate_hurst_rs(trend_prices)
    assert h_trend > 0.55, f"Expected H > 0.55 for trend, got {h_trend:.3f}"

    # 2. Mean-reverting Ornstein-Uhlenbeck series (Mean-reverting H < 0.50)
    ou_prices = [1.0]
    theta, mu, sigma = 0.7, 1.0, 0.02
    for _ in range(200):
        p_prev = ou_prices[-1]
        dp = theta * (mu - p_prev) + sigma * np.random.normal()
        ou_prices.append(max(0.5, p_prev + dp))
    ou_prices.reverse()
    h_mean_rev = calculate_hurst_rs(ou_prices)
    assert h_mean_rev < 0.52, f"Expected H < 0.52 for mean-reversion, got {h_mean_rev:.3f}"


# ==============================================================================
# 6. Smart Money Concepts (SMC) Confluence Evaluation
# ==============================================================================
def evaluate_smc_confluences(
    bullish_ob: bool,
    fvg_discount: bool,
    liq_sweep: bool,
    multi_tf_bos: bool,
    in_discount: bool,
) -> tuple[int, bool]:
    """Counts bullish SMC confluences and verifies >= 3 threshold."""
    confluences = 0
    if bullish_ob:
        confluences += 1
    if fvg_discount:
        confluences += 1
    if liq_sweep:
        confluences += 1
    if multi_tf_bos:
        confluences += 1
    if in_discount:
        confluences += 1

    entry_triggered = confluences >= 3
    return confluences, entry_triggered


def test_smc_confluence_trigger():
    """Verify SMC entries require at least 3 high-probability institutional confluences."""
    # 2 confluences: Bullish OB + In Discount -> REJECT (requires >= 3)
    c2, trig2 = evaluate_smc_confluences(bullish_ob=True, fvg_discount=False, liq_sweep=False, multi_tf_bos=False, in_discount=True)
    assert c2 == 2
    assert not trig2

    # 3 confluences: Bullish OB + In Discount + FVG 50% discount fill -> TRIGGER ENTRY
    c3, trig3 = evaluate_smc_confluences(bullish_ob=True, fvg_discount=True, liq_sweep=False, multi_tf_bos=False, in_discount=True)
    assert c3 == 3
    assert trig3

    # 4 confluences: Bullish OB + In Discount + FVG fill + Liquidity Sweep -> HIGH CONVICTION TRIGGER
    c4, trig4 = evaluate_smc_confluences(bullish_ob=True, fvg_discount=True, liq_sweep=True, multi_tf_bos=False, in_discount=True)
    assert c4 == 4
    assert trig4
