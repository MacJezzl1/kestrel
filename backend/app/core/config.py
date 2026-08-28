"""
Kestrel Core — Configuration
Environment-based settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Kestrel"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database (defaults to /tmp/kestrel.db on Vercel Serverless where / is read-only)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:////tmp/kestrel.db" if os.getenv("VERCEL") else "sqlite+aiosqlite:///./kestrel.db"
    )
    
    # JWT / Auth
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "52BjeWCO2JJbzx4BOsyNUYeertBZ2R2xgYoZryLYIRVQ0CQ6t-yGhoEpVwjJxrfS")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://api.kestrel.local:8000",
    ]
    
    # Vision (defaults to /tmp/uploads on Vercel)
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        "/tmp/uploads" if os.getenv("VERCEL") else "./uploads"
    )
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Bridge
    MT5_ADAPTER_SECRET: str = os.getenv("MT5_ADAPTER_SECRET", "mt5-adapter-secret-change-me")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

# Ensure upload directory exists safely (don't crash if read-only filesystem on serverless)
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
