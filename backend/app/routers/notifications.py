"""
Kestrel Core — Telegram & Discord Notification Router
Production endpoints for configuring webhooks, testing channels, and broadcasting institutional alerts.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.db.database import get_db
from app.models.models import NotificationConfig
from app.schemas.copier_notif import (
    NotificationConfigSchema,
    TelegramSendRequest,
    DiscordSendRequest,
    BroadcastNotificationRequest,
)
from app.services.notifications.dispatcher import notification_dispatcher

router = APIRouter(prefix="/api/v1/notifications", tags=["Notification Webhooks"])


@router.get("/config", response_model=NotificationConfigSchema)
async def get_notification_config(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """Retrieve saved Telegram and Discord webhook configuration."""
    stmt = select(NotificationConfig).where(NotificationConfig.user_id == user_id)
    res = await db.execute(stmt)
    cfg = res.scalars().first()

    if not cfg:
        return NotificationConfigSchema()

    return NotificationConfigSchema(
        telegram_enabled=cfg.telegram_enabled,
        telegram_bot_token=cfg.telegram_bot_token,
        telegram_chat_id=cfg.telegram_chat_id,
        discord_enabled=cfg.discord_enabled,
        discord_webhook_url=cfg.discord_webhook_url,
        alert_trade_signals=cfg.alert_trade_signals,
        alert_prop_firm_risk=cfg.alert_prop_firm_risk,
        alert_circuit_breaker=cfg.alert_circuit_breaker,
        alert_high_impact_news=cfg.alert_high_impact_news,
    )


@router.post("/config", response_model=NotificationConfigSchema)
async def save_notification_config(
    payload: NotificationConfigSchema,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """Save or update Telegram bot tokens and Discord webhook destinations."""
    now = datetime.now(timezone.utc)
    stmt = select(NotificationConfig).where(NotificationConfig.user_id == user_id)
    res = await db.execute(stmt)
    cfg = res.scalars().first()

    if not cfg:
        cfg = NotificationConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            telegram_enabled=payload.telegram_enabled,
            telegram_bot_token=payload.telegram_bot_token,
            telegram_chat_id=payload.telegram_chat_id,
            discord_enabled=payload.discord_enabled,
            discord_webhook_url=payload.discord_webhook_url,
            alert_trade_signals=payload.alert_trade_signals,
            alert_prop_firm_risk=payload.alert_prop_firm_risk,
            alert_circuit_breaker=payload.alert_circuit_breaker,
            alert_high_impact_news=payload.alert_high_impact_news,
            created_at=now,
        )
        db.add(cfg)
    else:
        cfg.telegram_enabled = payload.telegram_enabled
        cfg.telegram_bot_token = payload.telegram_bot_token
        cfg.telegram_chat_id = payload.telegram_chat_id
        cfg.discord_enabled = payload.discord_enabled
        cfg.discord_webhook_url = payload.discord_webhook_url
        cfg.alert_trade_signals = payload.alert_trade_signals
        cfg.alert_prop_firm_risk = payload.alert_prop_firm_risk
        cfg.alert_circuit_breaker = payload.alert_circuit_breaker
        cfg.alert_high_impact_news = payload.alert_high_impact_news
        cfg.updated_at = now

    await db.flush()
    return payload


@router.post("/telegram/send")
async def send_telegram_alert(
    req: TelegramSendRequest,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """Test or dispatch a direct Telegram message."""
    bot_token = req.bot_token
    chat_id = req.chat_id

    # Fallback to database config if omitted in request
    if not bot_token or not chat_id:
        stmt = select(NotificationConfig).where(NotificationConfig.user_id == user_id)
        res = await db.execute(stmt)
        cfg = res.scalars().first()
        if cfg:
            bot_token = bot_token or cfg.telegram_bot_token
            chat_id = chat_id or cfg.telegram_chat_id

    res = await notification_dispatcher.send_telegram(
        bot_token=bot_token or "",
        chat_id=chat_id or "",
        message=req.message
    )
    return res


@router.post("/discord/send")
async def send_discord_alert(
    req: DiscordSendRequest,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """Test or dispatch a direct Discord webhook message."""
    webhook_url = req.webhook_url
    if not webhook_url:
        stmt = select(NotificationConfig).where(NotificationConfig.user_id == user_id)
        res = await db.execute(stmt)
        cfg = res.scalars().first()
        if cfg:
            webhook_url = cfg.discord_webhook_url

    res = await notification_dispatcher.send_discord(
        webhook_url=webhook_url or "",
        embeds=req.embeds,
        content=req.content
    )
    return res


@router.post("/broadcast")
async def broadcast_alert(
    req: BroadcastNotificationRequest,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Unified institutional alert broadcaster.
    Formats rich markdown/HTML and delivers to all active channels.
    """
    stmt = select(NotificationConfig).where(NotificationConfig.user_id == user_id)
    res = await db.execute(stmt)
    cfg = res.scalars().first()

    tg_delivered = False
    dc_delivered = False

    if req.alert_type == "TRADE_SIGNAL":
        tg_text = notification_dispatcher.format_trade_signal_telegram(req.payload)
        dc_embeds = notification_dispatcher.format_trade_signal_discord(req.payload)
    elif req.alert_type in ("PROP_RISK", "CIRCUIT_BREAKER"):
        tg_text, dc_embeds = notification_dispatcher.format_prop_firm_alert(req.payload)
    else:
        tg_text = f"🦅 <b>KESTREL ALERT [{req.alert_type}]</b>\n{str(req.payload)}"
        dc_embeds = [{
            "title": f"🦅 Kestrel Alert: {req.alert_type}",
            "description": str(req.payload),
            "color": 0x00E5FF
        }]

    if cfg and cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
        tg_res = await notification_dispatcher.send_telegram(
            bot_token=cfg.telegram_bot_token,
            chat_id=cfg.telegram_chat_id,
            message=tg_text
        )
        tg_delivered = tg_res.get("success", False)

    if cfg and cfg.discord_enabled and cfg.discord_webhook_url:
        dc_res = await notification_dispatcher.send_discord(
            webhook_url=cfg.discord_webhook_url,
            embeds=dc_embeds
        )
        dc_delivered = dc_res.get("success", False)

    return {
        "status": "ok",
        "alert_type": req.alert_type,
        "telegram_dispatched": tg_delivered,
        "discord_dispatched": dc_delivered,
    }
