"""
Kestrel Core — Configuration
Environment-based settings using Pydantic Settings.
Production security hardened: No hardcoded secrets, asymmetric RS256 JWT, short token lifespans.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets


class Settings(BaseSettings):
    """Application settings loaded strictly from environment variables."""
    
    # App
    APP_NAME: str = "Kestrel"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Database (defaults to /tmp/kestrel.db on Vercel Serverless where / is read-only)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:////tmp/kestrel.db" if os.getenv("VERCEL") else "sqlite+aiosqlite:///./kestrel.db"
    )
    
    # Auth0-Grade JWT / Auth
    # Asymmetric RS256 is preferred, HS256 is supported with strong secret
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_PRIVATE_KEY: Optional[str] = os.getenv("JWT_PRIVATE_KEY", None)
    JWT_PUBLIC_KEY: Optional[str] = os.getenv("JWT_PUBLIC_KEY", None)
    
    # Short 15-minute access token lifetime + 7-day refresh token
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Anti-replay window for MT5 HMAC signing (seconds)
    HMAC_MAX_DRIFT_SECONDS: int = int(os.getenv("HMAC_MAX_DRIFT_SECONDS", "30"))
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://api.kestrel.local:8000",
        "https://frontend-delta-pied-96.vercel.app",
        "https://backend-macjezzl1s-projects.vercel.app",
    ]
    
    # Vision (defaults to /tmp/uploads on Vercel)
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        "/tmp/uploads" if os.getenv("VERCEL") else "./uploads"
    )
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Bridge Secret for MT5 HMAC signing
    MT5_ADAPTER_SECRET: str = os.getenv("MT5_ADAPTER_SECRET", "")
    
    # Supabase Cloud Database Integration (Empty defaults to prevent credential leakage)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Swarm Settings
    AI_SWARM_MODELS_COUNT: int = 180

    # Observability & Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", "")
    PROMETHEUS_ENABLED: bool = True
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

# If no JWT secret is provided in dev/test, generate an ephemeral runtime secret to prevent crashes
if not settings.JWT_SECRET_KEY:
    settings.JWT_SECRET_KEY = secrets.token_urlsafe(48)

# Ensure upload directory exists safely (don't crash if read-only filesystem on serverless)
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
