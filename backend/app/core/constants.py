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
