"""
Kestrel Core — Database Connection
Async SQLAlchemy engine and session management.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all database tables and run lightweight migrations."""
    from sqlalchemy import text
    import app.models.models  # Ensure all models are registered with Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Lightweight migrations for SQLite
        migration_statements = [
            "ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0",
            "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64)",
            "ALTER TABLE users ADD COLUMN tenant_id VARCHAR(64)",
            "ALTER TABLE licenses ADD COLUMN tenant_id VARCHAR(64)",
            "ALTER TABLE licenses ADD COLUMN account_login VARCHAR(64)",
            "ALTER TABLE licenses ADD COLUMN terminal_hash VARCHAR(128)",
            "ALTER TABLE licenses ADD COLUMN max_risk_per_trade FLOAT DEFAULT 1.0",
            "ALTER TABLE licenses ADD COLUMN max_daily_loss_pct FLOAT DEFAULT 5.0",
            "ALTER TABLE trades ADD COLUMN tenant_id VARCHAR(64)",
            "ALTER TABLE orders ADD COLUMN tenant_id VARCHAR(64)",
            "ALTER TABLE signals ADD COLUMN tenant_id VARCHAR(64)",
        ]

        for stmt in migration_statements:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # Column already exists or table handles it



async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
