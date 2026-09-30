"""
Kestrel Shield — License Activation & EA Binding Router
Endpoints for MT5 EA terminal license activation, hardware binding, and trial provisioning.
"""
from datetime import datetime, timedelta, timezone
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.models import License, User
from app.schemas.license import (
    LicenseActivationRequest,
    LicenseActivationResponse,
)

import secrets
from app.core.security import hash_password

router = APIRouter(tags=["License"])


@router.post("/api/v1/license/activate", response_model=LicenseActivationResponse)
@router.post("/api/license/activate", response_model=LicenseActivationResponse)
async def activate_license(
    req: LicenseActivationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    MT5 EA Terminal License Activation and Hardware Binding Endpoint.
    Validates account login, terminal fingerprint, tier limits, and trial status.
    """
    account_login = req.account_login.strip()
    terminal_id = req.terminal_id.strip()
    terminal_hash = hashlib.sha256(terminal_id.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    # 1. Look up existing license by account_login
    query = select(License).where(License.account_login == account_login)
    result = await db.execute(query)
    license_obj = result.scalar_one_or_none()

    # 2. If no license exists for this account, auto-provision a 7-day Trial
    if not license_obj:
        # Create a dedicated terminal user record for this account login to respect 1:1 user_id constraint
        terminal_email = f"terminal_{account_login}@kestrel.ai"
        user_res = await db.execute(select(User).where(User.email == terminal_email))
        terminal_user = user_res.scalar_one_or_none()
        if not terminal_user:
            terminal_user = User(
                email=terminal_email,
                hashed_password=hash_password(secrets.token_urlsafe(16)),
                full_name=f"MT5 Account {account_login}",
            )
            db.add(terminal_user)
            await db.flush()

        trial_expiry = now + timedelta(days=7)

        license_obj = License(
            user_id=terminal_user.id,
            account_login=account_login,
            terminal_hash=terminal_hash,
            tier="starter",
            status="trial",
            max_risk_per_trade=0.5,
            max_daily_loss_pct=3.0,
            expires_at=trial_expiry,
        )
        db.add(license_obj)
        await db.commit()
        await db.refresh(license_obj)


        return LicenseActivationResponse(
            valid=True,
            status="trial",
            tier="starter",
            account_login=account_login,
            max_risk_per_trade=0.5,
            max_daily_loss_pct=3.0,
            expires_at=trial_expiry,
            is_trial=True,
            days_remaining=7,
            message="7-Day Trial License Activated. Welcome to Kestrel Quantum Intelligence.",
        )

    # 3. Check if license has expired
    if license_obj.expires_at:
        # Handle timezone-aware vs naive comparison
        expires_at = license_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            license_obj.status = "expired"
            await db.commit()
            return LicenseActivationResponse(
                valid=False,
                status="expired",
                tier=license_obj.tier,
                account_login=account_login,
                max_risk_per_trade=0.0,
                max_daily_loss_pct=0.0,
                expires_at=expires_at,
                is_trial=(license_obj.status == "trial"),
                days_remaining=0,
                message="License Expired. Trading halted. Renew on Kestrel Dashboard.",
            )

        days_remaining = (expires_at - now).days
    else:
        days_remaining = None

    # 4. Check status
    if license_obj.status in ("suspended", "cancelled"):
        return LicenseActivationResponse(
            valid=False,
            status=license_obj.status,
            tier=license_obj.tier,
            account_login=account_login,
            max_risk_per_trade=0.0,
            max_daily_loss_pct=0.0,
            expires_at=license_obj.expires_at,
            message=f"License is {license_obj.status}. Contact Kestrel support.",
        )

    # 5. Bind terminal if not already bound
    if not license_obj.terminal_hash:
        license_obj.terminal_hash = terminal_hash
        await db.commit()

    # Tier entitlements mapping
    tier = (license_obj.tier or "starter").lower()
    if tier == "institutional":
        max_risk = getattr(license_obj, "max_risk_per_trade", 2.0) or 2.0
        max_daily_loss = getattr(license_obj, "max_daily_loss_pct", 10.0) or 10.0
    elif tier == "pro":
        max_risk = getattr(license_obj, "max_risk_per_trade", 1.5) or 1.5
        max_daily_loss = getattr(license_obj, "max_daily_loss_pct", 5.0) or 5.0
    else:
        max_risk = getattr(license_obj, "max_risk_per_trade", 0.5) or 0.5
        max_daily_loss = getattr(license_obj, "max_daily_loss_pct", 3.0) or 3.0

    return LicenseActivationResponse(
        valid=True,
        status=license_obj.status,
        tier=license_obj.tier,
        account_login=account_login,
        max_risk_per_trade=max_risk,
        max_daily_loss_pct=max_daily_loss,
        expires_at=license_obj.expires_at,
        is_trial=(license_obj.status == "trial"),
        days_remaining=days_remaining,
        message=f"License valid. Tier: {license_obj.tier.upper()}. Terminal authenticated.",
    )
