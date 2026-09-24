"""
Kestrel Shield — Auth Router
Registration, login, profile, and license validation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import User, License
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, UserProfile, LicenseInfo,
    MfaSetupResponse, MfaVerifyRequest, MfaStatusResponse,
    OAuthAuthorizeRequest, OAuthTokenRequest, OAuthTokenResponse
)
from app.core.security import (
    hash_password, verify_password, create_access_token, get_current_user_id,
    verify_pkce
)
from app.core.totp import (
    generate_totp_secret, generate_totp_uri, verify_totp_code
)
from app.core.rate_limiter import rate_limiter, get_client_ip
from app.core.constants import SIGNAL_LIMITS
from app.services.shield.license_manager import create_license, get_license, validate_license
from app.services.shield.audit import log_action
import secrets
import time

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory store for OAuth2 authorization codes: code -> {client_id, user_id, code_challenge, code_challenge_method, expires_at}
_oauth_codes: dict[str, dict] = {}

from app.db.supabase_client import supabase_client


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new Kestrel account."""
    # Check if email already exists locally
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Also check Supabase
    supabase_user = await supabase_client.get_user_by_email(data.email)
    if supabase_user:
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
    
    # Sync User and License to Supabase Cloud
    try:
        await supabase_client.save_user({
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "license_tier": license_obj.tier,
            "license_status": license_obj.status,
            "token_version": user.token_version
        })
    except Exception:
        pass
    
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
    """Login to Kestrel account with brute-force rate limiting and TOTP MFA verification."""
    client_ip = get_client_ip(request)
    await rate_limiter.check_rate_limit(f"login:{client_ip}", max_requests=10, window_seconds=60, action_name="login")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # If not in local SQLite (e.g. serverless cold restart), check Supabase
    if not user:
        sb_u = await supabase_client.get_user_by_email(data.email)
        if sb_u:
            user = User(
                id=sb_u["id"],
                email=sb_u["email"],
                hashed_password=sb_u["hashed_password"],
                full_name=sb_u.get("full_name"),
                is_active=sb_u.get("is_active", True),
                mfa_enabled=sb_u.get("mfa_enabled", False),
                mfa_secret=sb_u.get("mfa_secret"),
                token_version=sb_u.get("token_version", 1)
            )
            db.add(user)
            await db.flush()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # MFA verification if enabled
    if user.mfa_enabled:
        if not data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA_REQUIRED",
                headers={"X-MFA-Required": "true"}
            )
        if not verify_totp_code(user.mfa_secret or "", data.mfa_code):
            raise HTTPException(status_code=401, detail="Invalid two-factor authentication code")

    license_obj = await get_license(db, user.id)
    tier = license_obj.tier if license_obj else "pro"
    l_status = license_obj.status if license_obj else "active"
    
    # Audit log
    await log_action(db, "login", user.id, {"email": data.email, "mfa_used": bool(user.mfa_enabled)},
                     ip_address=client_ip)
    
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
        sb_u = await supabase_client.get_user_by_id(user_id)
        if sb_u:
            user = User(
                id=sb_u["id"],
                email=sb_u["email"],
                hashed_password=sb_u["hashed_password"],
                full_name=sb_u.get("full_name"),
                is_active=sb_u.get("is_active", True),
                token_version=sb_u.get("token_version", 1)
            )
            db.add(user)
            await db.flush()
            
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    license_obj = await get_license(db, user.id)
    
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        license_tier=license_obj.tier if license_obj else "pro",
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


@router.post("/link-broker")
async def link_broker_account(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Save and link user's MT5 Broker Account (Login ID, Broker Name, Server).
    Directly persists to Supabase PostgreSQL accounts table scoped to this user.
    """
    account_number = str(payload.get("account_number", "")).strip()
    broker_name = str(payload.get("broker_name", "Deriv.com Limited")).strip()
    server = str(payload.get("server", "Deriv-Demo")).strip()
    balance = float(payload.get("balance", 0.0))
    currency = str(payload.get("currency", "USD")).strip()
    
    if not account_number:
        raise HTTPException(status_code=400, detail="Account Number / Login ID is required")
        
    # Get user email for isolation
    user_res = await db.execute(select(User).where(User.id == user_id))
    user_obj = user_res.scalar_one_or_none()
    user_email = user_obj.email if user_obj else "trader"
    is_owner = "mcjezz" in user_email.lower()
    
    license_key = "kestrel-enterprise-owner-vip" if is_owner else f"user-{user_email}"
    license_tier = "ENTERPRISE_MASTER" if is_owner else "PRO_CLIENT"
    
    account_data = {
        "account_number": account_number,
        "broker_name": broker_name,
        "license_key": license_key,
        "license_tier": license_tier,
        "balance": balance,
        "equity": balance,
        "currency": currency,
        "total_profit": 0.0,
        "today_profit": 0.0,
        "recovery_level": "OPTIMAL",
        "recovery_multiplier": 1.0,
        "auto_trade_enabled": True
    }
    
    await supabase_client.update_account_metrics(account_data)
    
    return {
        "status": "success",
        "message": f"MT5 Account #{account_number} ({broker_name} - {server}) linked and synchronized.",
        "account": account_data
    }


@router.get("/broker-info")
async def get_broker_info(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Fetch current user's linked MT5 broker account details."""
    user_res = await db.execute(select(User).where(User.id == user_id))
    user_obj = user_res.scalar_one_or_none()
    user_email = user_obj.email if user_obj else ""
    is_owner = "mcjezz" in user_email.lower()

    acc = await supabase_client.get_latest_account(
        license_key="kestrel-enterprise-owner-vip" if is_owner else f"user-{user_email}",
        user_email=user_email
    )
    if acc:
        return acc

    if is_owner:
        return {
            "account_number": "41230754",
            "broker_name": "Deriv.com Limited",
            "server": "Deriv-Demo",
            "balance": 10500.00,
            "equity": 10545.20,
            "currency": "USD"
        }
        
    return {
        "account_number": "",
        "broker_name": "Deriv.com Limited",
        "server": "Deriv-Demo",
        "balance": 0.00,
        "equity": 0.00,
        "currency": "USD"
    }


# ====================================================================
# MULTI-FACTOR AUTHENTICATION (TOTP / NIST SP 800-63B)
# ====================================================================

@router.get("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new TOTP secret and otpauth:// URI for Google Authenticator / Authy.
    Secret is temporarily held until confirmed via /mfa/enable.
    """
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = generate_totp_secret()
    otpauth_url = generate_totp_uri(secret=secret, account_name=user.email, issuer="Kestrel Trading")
    
    # Store secret temporarily on user model until verified
    user.mfa_secret = secret
    await db.commit()

    return MfaSetupResponse(
        secret=secret,
        otpauth_url=otpauth_url,
        issuer="Kestrel Trading"
    )


@router.post("/mfa/enable", response_model=MfaStatusResponse)
async def enable_mfa(
    payload: MfaVerifyRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Verify first TOTP code to permanently activate MFA on user account."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA setup has not been initiated. Call /mfa/setup first.")

    if not verify_totp_code(user.mfa_secret, payload.code):
        raise HTTPException(status_code=400, detail="Invalid verification code. Check your authenticator app.")

    user.mfa_enabled = True
    await db.commit()

    try:
        await supabase_client.save_user({
            "id": user.id,
            "mfa_enabled": True,
            "mfa_secret": user.mfa_secret
        })
    except Exception:
        pass

    return MfaStatusResponse(
        mfa_enabled=True,
        message="Two-factor authentication successfully enabled. Your account is now hardened."
    )


@router.post("/mfa/disable", response_model=MfaStatusResponse)
async def disable_mfa(
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Disable MFA after verifying current password."""
    password = payload.get("password", "")
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password. Cannot disable MFA.")

    user.mfa_enabled = False
    user.mfa_secret = None
    await db.commit()

    try:
        await supabase_client.save_user({
            "id": user.id,
            "mfa_enabled": False,
            "mfa_secret": None
        })
    except Exception:
        pass

    return MfaStatusResponse(
        mfa_enabled=False,
        message="Two-factor authentication has been disabled."
    )


@router.get("/mfa/status", response_model=MfaStatusResponse)
async def get_mfa_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Check current MFA status of the authenticated user."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    enabled = bool(user and user.mfa_enabled)
    return MfaStatusResponse(
        mfa_enabled=enabled,
        message="MFA is active" if enabled else "MFA is inactive"
    )


# ====================================================================
# OAUTH2 AUTHORIZATION CODE FLOW WITH PKCE (RFC 7636)
# ====================================================================

@router.post("/oauth/authorize")
async def oauth_authorize(
    req: OAuthAuthorizeRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Issue an OAuth2 Authorization Code bound to client_id and code_challenge.
    Recommended for single-page and mobile apps per OAuth 2.1 / RFC 7636.
    """
    auth_code = f"kestrel_code_{secrets.token_urlsafe(32)}"
    expires_at = time.time() + 300  # 5 minutes validity
    
    _oauth_codes[auth_code] = {
        "client_id": req.client_id,
        "redirect_uri": req.redirect_uri,
        "user_id": user_id,
        "code_challenge": req.code_challenge,
        "code_challenge_method": req.code_challenge_method,
        "scope": req.scope or "trading",
        "expires_at": expires_at
    }

    return {
        "code": auth_code,
        "state": req.state,
        "redirect_uri": req.redirect_uri,
        "expires_in": 300
    }


@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def oauth_token(
    req: OAuthTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchange authorization code + code_verifier for JWT access token.
    Validates PKCE challenge strictly to prevent authorization code interception attacks.
    """
    client_ip = get_client_ip(request)
    await rate_limiter.check_rate_limit(f"oauth_token:{client_ip}", max_requests=20, window_seconds=60, action_name="oauth_token")

    entry = _oauth_codes.pop(req.code, None)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired authorization code")

    if time.time() > entry["expires_at"]:
        raise HTTPException(status_code=400, detail="Authorization code has expired")

    if entry["client_id"] != req.client_id or entry["redirect_uri"] != req.redirect_uri:
        raise HTTPException(status_code=400, detail="Client ID or Redirect URI mismatch")

    # Verify PKCE S256 code challenge
    if not verify_pkce(req.code_verifier, entry["code_challenge"], entry.get("code_challenge_method", "S256")):
        raise HTTPException(status_code=400, detail="PKCE code_verifier challenge verification failed")

    # Fetch user
    user_id = entry["user_id"]
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    license_obj = await get_license(db, user.id)
    tier = license_obj.tier if license_obj else "pro"

    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "tier": tier,
        "scope": entry["scope"],
        "tv": user.token_version
    })

    return OAuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1440 * 60,
        scope=entry["scope"]
    )


