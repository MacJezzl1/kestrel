"""
Kestrel Shield — Security Router
Session management, password changes, API key CRUD, and audit log viewing.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.database import get_db
from app.models.models import User, AuditLog, ApiKey
from app.schemas.auth import (
    ChangePassword, ApiKeyCreate, ApiKeyCreated, ApiKeyResponse,
    SessionInfo, AuditLogEntry,
)
from app.core.security import (
    hash_password, verify_password, create_access_token,
    get_current_user_id, generate_api_key, hash_api_key, get_api_key_prefix,
)
from app.services.shield.audit import log_action

router = APIRouter(prefix="/api/security", tags=["Security"])


# --- Active Sessions ---

@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List recent login sessions (from audit log)."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id, AuditLog.action == "login")
        .order_by(desc(AuditLog.created_at))
        .limit(50)
    )
    sessions = result.scalars().all()
    return [
        SessionInfo(
            action=s.action,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke all active sessions by incrementing token_version.
    All existing JWTs with an older version will be rejected.
    Returns a fresh token so the current session stays alive.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.token_version += 1
    await db.flush()

    await log_action(db, "sessions_revoked", user_id, {"new_version": user.token_version},
                     ip_address=request.client.host if request.client else None)

    # Issue a fresh token with the new version
    from app.services.shield.license_manager import get_license
    license_obj = await get_license(db, user_id)
    tier = license_obj.tier if license_obj else "free"

    new_token = create_access_token({
        "sub": user.id, "email": user.email, "tier": tier, "tv": user.token_version
    })

    return {"message": "All sessions revoked", "access_token": new_token}


# --- Change Password ---

@router.post("/change-password")
async def change_password(
    data: ChangePassword,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password. Requires current password verification."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = hash_password(data.new_password)
    # Also bump token_version to force re-login on other devices
    user.token_version += 1
    await db.flush()

    await log_action(db, "password_changed", user_id, {},
                     ip_address=request.client.host if request.client else None)

    # Issue a fresh token
    from app.services.shield.license_manager import get_license
    license_obj = await get_license(db, user_id)
    tier = license_obj.tier if license_obj else "free"

    new_token = create_access_token({
        "sub": user.id, "email": user.email, "tier": tier, "tv": user.token_version
    })

    return {"message": "Password changed successfully", "access_token": new_token}


# --- API Keys ---

@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key for bridge integrations.
    The raw key is returned ONLY at creation time — store it securely.
    """
    # Limit to 10 keys per user
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
    )
    active_keys = result.scalars().all()
    if len(active_keys) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 active API keys allowed")

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    prefix = get_api_key_prefix(raw_key)

    api_key_obj = ApiKey(
        user_id=user_id,
        name=data.name,
        key_prefix=prefix,
        hashed_key=hashed,
        permissions=data.permissions,
    )
    db.add(api_key_obj)
    await db.flush()

    await log_action(db, "api_key_created", user_id,
                     {"key_name": data.name, "key_prefix": prefix},
                     ip_address=request.client.host if request.client else None)

    return ApiKeyCreated(
        id=api_key_obj.id,
        name=api_key_obj.name,
        raw_key=raw_key,
        key_prefix=prefix,
        permissions=api_key_obj.permissions,
        created_at=api_key_obj.created_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(desc(ApiKey.created_at))
    )
    return result.scalars().all()


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    )
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key_obj.is_active = False
    await db.flush()

    await log_action(db, "api_key_revoked", user_id,
                     {"key_name": api_key_obj.name, "key_prefix": api_key_obj.key_prefix},
                     ip_address=request.client.host if request.client else None)

    return {"message": f"API key '{api_key_obj.name}' revoked"}


# --- Audit Log ---

@router.get("/audit-log", response_model=list[AuditLogEntry])
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """View audit log entries for the current user."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(min(limit, 100))
    )
    return result.scalars().all()
