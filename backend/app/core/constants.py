"""
Kestrel Core — Constants
Shared constants used across the application.
"""

# License tiers
LICENSE_FREE = "free"
LICENSE_PRO = "pro"
LICENSE_ENTERPRISE = "enterprise"

LICENSE_TIERS = [LICENSE_FREE, LICENSE_PRO, LICENSE_ENTERPRISE]

# Signal limits per tier (per day)
SIGNAL_LIMITS = {
    LICENSE_FREE: 10,
    LICENSE_PRO: 100,
    LICENSE_ENTERPRISE: -1,  # unlimited
}

# Model categories
MODEL_CATEGORIES = [
    "trend_following",
    "mean_reversion",
    "volatility_regime",
    "sentiment",
    "order_flow",
    "cross_asset",
    "seasonality",
    "macro_calendar",
    "meta_model",
]

# Market regimes
REGIME_TRENDING = "trending"
REGIME_RANGING = "ranging"
REGIME_VOLATILE = "volatile"
REGIME_UNKNOWN = "unknown"

REGIMES = [REGIME_TRENDING, REGIME_RANGING, REGIME_VOLATILE, REGIME_UNKNOWN]

# Signal directions
SIGNAL_BUY = "buy"
SIGNAL_SELL = "sell"
SIGNAL_HOLD = "hold"

# Trade statuses
TRADE_OPEN = "open"
TRADE_CLOSED = "closed"
TRADE_CANCELLED = "cancelled"

# Timeframes
TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"]

# Instruments (default set)
DEFAULT_INSTRUMENTS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "NZDUSD", "USDCHF", "EURGBP", "EURJPY", "GBPJPY",
    "XAUUSD", "XAGUSD",  # Metals
    "US30", "US500", "NAS100", "GER40",  # Indices
    "BTCUSD", "ETHUSD",  # Crypto
]

# Audit log actions
AUDIT_SIGNAL_GENERATED = "signal_generated"
AUDIT_TRADE_OPENED = "trade_opened"
AUDIT_TRADE_CLOSED = "trade_closed"
AUDIT_LICENSE_CHECKED = "license_checked"
AUDIT_LOGIN = "login"
AUDIT_VISION_SCAN = "vision_scan"

# Autopilot modes
AUTOPILOT_MODE_PAPER = "paper"
AUTOPILOT_MODE_LIVE = "live"
AUTOPILOT_MODE_SUGGEST = "suggest_only"

# Autopilot defaults
AUTOPILOT_DEFAULT_CONFIDENCE_THRESHOLD = 0.80
AUTOPILOT_DEFAULT_RISK_PCT = 1.0
AUTOPILOT_DEFAULT_DAILY_MAX_LOSS_PCT = 5.0
AUTOPILOT_DEFAULT_WEEKLY_MAX_LOSS_PCT = 10.0
AUTOPILOT_DEFAULT_MAX_CONCURRENT_POSITIONS = 3
AUTOPILOT_DEFAULT_SCAN_INTERVAL = 60
AUTOPILOT_DEFAULT_PAPER_REQUIRED = 50
AUTOPILOT_DEFAULT_DRIFT_THRESHOLD = 15.0

# Autopilot audit actions
AUDIT_AUTOPILOT_ENABLED = "autopilot_enabled"
AUDIT_AUTOPILOT_DISABLED = "autopilot_disabled"
AUDIT_AUTOPILOT_KILL = "autopilot_emergency_kill"
AUDIT_AUTOPILOT_PAPER_TRADE = "autopilot_paper_trade"
AUDIT_AUTOPILOT_LIVE_TRADE = "autopilot_live_trade"
AUDIT_AUTOPILOT_SKIP = "autopilot_skip"
AUDIT_AUTOPILOT_DRIFT = "autopilot_drift_detected"
AUDIT_AUTOPILOT_UNLOCK_LIVE = "autopilot_unlock_live"
