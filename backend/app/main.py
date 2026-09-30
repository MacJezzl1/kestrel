"""
Kestrel Core — FastAPI Application Entry Point
Main application with CORS, router registration, and lifecycle management.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import init_db, close_db
from app.routers import auth, signals, trades, dashboard, vision, security, payments, clients, market, autopilot, orders, license, calendar, mt5_sync, ws_sync, ensemble, notifications, copier, analytics, metrics
from app.routers.metrics import increment_metric
from app.core.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Sentry SDK Error Tracking (Safe initialization)
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.2,
            profiles_sample_rate=0.1,
            environment=settings.APP_ENV,
            release=f"kestrel-core@{settings.APP_VERSION}"
        )
        print("[Kestrel] 🔭 Sentry APM & error tracing initialized")
    except Exception as e:
        print(f"[Kestrel] ⚠️ Sentry init skipped: {e}")




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    await init_db()
    print(f"[Kestrel] {settings.APP_VERSION} -- Engine online")
    print(f"   Database: {settings.DATABASE_URL}")

    # Start Autopilot background engine
    from app.services.autopilot.autopilot import autopilot_engine
    await autopilot_engine.start()
    print("[Kestrel] ✈️ Autopilot engine started (background loop active)")

    yield

    # Shutdown
    from app.services.autopilot.autopilot import autopilot_engine as ap_engine
    await ap_engine.stop()
    print("[Kestrel] 🛑 Autopilot engine stopped")
    await close_db()
    print("[Kestrel] -- Engine offline")


app = FastAPI(
    title="Kestrel API",
    description="AI Trading Intelligence Platform — CapeChain Labs. See every market. Miss nothing.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Observability Middleware: Tracks total HTTP request count
@app.middleware("http")
async def track_metrics_middleware(request: Request, call_next):
    increment_metric("http_requests_total", 1)
    response = await call_next(request)
    return response

# Register routers
app.include_router(auth.router)
app.include_router(license.router)
app.include_router(signals.router)
app.include_router(trades.router)
app.include_router(dashboard.router)
app.include_router(vision.router)
app.include_router(security.router)
app.include_router(payments.router)
app.include_router(clients.router)
app.include_router(market.router)
app.include_router(autopilot.router)
app.include_router(orders.router)
app.include_router(calendar.router)
app.include_router(mt5_sync.router)
app.include_router(ws_sync.router)
app.include_router(ensemble.router)
app.include_router(notifications.router)
app.include_router(copier.router)
app.include_router(analytics.router)
app.include_router(metrics.router)





@app.get("/", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "name": "Kestrel",
        "version": settings.APP_VERSION,
        "status": "online",
        "tagline": "See every market. Miss nothing.",
    }


@app.get("/api/status", tags=["Health"])
async def api_status():
    """Detailed API status."""
    from app.services.ensemble.engine import ensemble_engine
    return {
        "status": "online",
        "version": settings.APP_VERSION,
        "models": {
            "count": ensemble_engine.model_count,
            "categories": ensemble_engine.active_categories,
        },
        "features": {
            "signals": True,
            "vision": True,
            "bridge_mt5": True,
            "bridge_tradingview": True,
            "bridge_crypto": False,  # Phase 5
        }
    }
