"""
Kestrel Shield — License Manager
Account-bound licensing with tiered subscriptions and server-side validation.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import License, User
from app.core.constants import LICENSE_FREE, LICENSE_PRO, SIGNAL_LIMITS


async def create_license(db: AsyncSession, user_id: str, tier: str = LICENSE_FREE) -> License:
    """Create a new license for a user."""
    license_obj = License(
        user_id=user_id,
        tier=tier,
        status="active",
        signals_used_today=0,
        last_signal_reset=datetime.now(timezone.utc),
    )
    db.add(license_obj)
    await db.flush()
    return license_obj


async def get_license(db: AsyncSession, user_id: str) -> License | None:
    """Get a user's license."""
    result = await db.execute(select(License).where(License.user_id == user_id))
    return result.scalar_one_or_none()


async def validate_license(db: AsyncSession, user_id: str) -> dict:
    """
    Validate a user's license status.
    Returns validation result with remaining signal capacity.
    """
    license_obj = await get_license(db, user_id)
    
    if not license_obj:
        return {"valid": False, "reason": "No license found"}
    
    if license_obj.status != "active":
        return {"valid": False, "reason": f"License is {license_obj.status}"}
    
    if license_obj.expires_at and license_obj.expires_at < datetime.now(timezone.utc):
        license_obj.status = "expired"
        await db.flush()
        return {"valid": False, "reason": "License has expired"}
    
    # Reset daily signal counter if needed
    now = datetime.now(timezone.utc)
    if license_obj.last_signal_reset.date() < now.date():
        license_obj.signals_used_today = 0
        license_obj.last_signal_reset = now
        await db.flush()
    
    # Check signal limit
    limit = SIGNAL_LIMITS.get(license_obj.tier, 10)
    if limit != -1 and license_obj.signals_used_today >= limit:
        return {
            "valid": False,
            "reason": f"Daily signal limit reached ({limit}). Upgrade to Pro for more.",
        }
    
    return {
        "valid": True,
        "tier": license_obj.tier,
        "signals_remaining": limit - license_obj.signals_used_today if limit != -1 else -1,
        "signals_used": license_obj.signals_used_today,
    }


async def increment_signal_count(db: AsyncSession, user_id: str):
    """Increment the daily signal usage counter."""
    license_obj = await get_license(db, user_id)
    if license_obj:
        license_obj.signals_used_today += 1
        await db.flush()
