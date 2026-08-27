"""
Kestrel Shield — Audit Service
Immutable audit logging for every signal, trade, and system action.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Create an immutable audit log entry.
    Every signal generated, trade executed, license check, and login is logged.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()
    return entry
