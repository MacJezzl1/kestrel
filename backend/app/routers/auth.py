"""
Kestrel Shield — Auth Router
Registration, login, profile, and license validation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import User, License
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserProfile, LicenseInfo
from app.core.security import hash_password, verify_password, create_access_token, get_current_user_id
from app.core.constants import SIGNAL_LIMITS
from app.services.shield.license_manager import create_license, get_license, validate_license
from app.services.shield.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new Kestrel account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    
    # Create free license
    license_obj = await create_license(db, user.id)
    
    # Audit log
    await log_action(db, "register", user.id, {"email": data.email}, 
                     ip_address=request.client.host if request.client else None)
    
    # Generate token
    token = create_access_token({"sub": user.id, "email": user.email, "tier": license_obj.tier, "tv": user.token_version})
    
    return TokenResponse(
        access_token=token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            license_tier=license_obj.tier,
            license_status=license_obj.status,
            created_at=user.created_at,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login to Kestrel account."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    license_obj = await get_license(db, user.id)
    tier = license_obj.tier if license_obj else "free"
    l_status = license_obj.status if license_obj else "active"
    
    # Audit log
    await log_action(db, "login", user.id, {"email": data.email},
                     ip_address=request.client.host if request.client else None)
    
    token = create_access_token({"sub": user.id, "email": user.email, "tier": tier, "tv": user.token_version})
    
    return TokenResponse(
        access_token=token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            license_tier=tier,
            license_status=l_status,
            created_at=user.created_at,
        )
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Get current user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    license_obj = await get_license(db, user.id)
    
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        license_tier=license_obj.tier if license_obj else "free",
        license_status=license_obj.status if license_obj else "active",
        created_at=user.created_at,
    )


@router.get("/license", response_model=LicenseInfo)
async def get_license_info(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Get current license status and usage."""
    license_obj = await get_license(db, user_id)
    if not license_obj:
        raise HTTPException(status_code=404, detail="No license found")
    
    limit = SIGNAL_LIMITS.get(license_obj.tier, 10)
    
    return LicenseInfo(
        tier=license_obj.tier,
        status=license_obj.status,
        signals_used_today=license_obj.signals_used_today,
        signals_limit=limit,
        expires_at=license_obj.expires_at,
    )
