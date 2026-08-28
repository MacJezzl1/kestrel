"""
Kestrel Core — FastAPI Application Entry Point
Main application with CORS, router registration, and lifecycle management.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import init_db, close_db
from app.routers import auth, signals, trades, dashboard, vision, security


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    await init_db()
    print(f"[Kestrel] {settings.APP_VERSION} -- Engine online")
    print(f"   Models loaded: {_get_model_count()} across 5 categories")
    print(f"   Database: {settings.DATABASE_URL}")
    yield
    # Shutdown
    await close_db()
    print("[Kestrel] -- Engine offline")


def _get_model_count():
    from app.services.ensemble.engine import ensemble_engine
    return ensemble_engine.model_count


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

# Register routers
app.include_router(auth.router)
app.include_router(signals.router)
app.include_router(trades.router)
app.include_router(dashboard.router)
app.include_router(vision.router)
app.include_router(security.router)


@app.get("/", tags=["Health"])
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
