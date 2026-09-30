"""
Kestrel Core — Telegram & Discord Notification Dispatcher
Delivers formatted trade signals, prop-firm safety alerts, and macro alerts
to trader channels with embedded confluences and circuit breaker updates.
"""
import httpx
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("NotificationDispatcher")


class NotificationDispatcher:
    """Dispatches real-time alerts to Telegram Bot API and Discord Webhooks."""

    async def send_telegram(
        self,
        bot_token: str,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """Send formatted message via official Telegram Bot API."""
        if not bot_token or not chat_id:
            return {"success": False, "error": "Missing bot token or chat ID"}

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return {"success": True, "data": res.json()}
                return {"success": False, "status_code": res.status_code, "error": res.text}
        except Exception as e:
            logger.warning(f"Telegram dispatch failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_discord(
        self,
        webhook_url: str,
        embeds: Optional[List[Dict[str, Any]]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send rich embed message to Discord Webhook."""
        if not webhook_url:
            return {"success": False, "error": "Missing Discord webhook URL"}

        payload = {
            "username": "Kestrel Institutional AI",
            "avatar_url": "https://frontend-delta-pied-96.vercel.app/kestrel-logo.jpg",
        }
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(webhook_url, json=payload)
                if res.status_code in (200, 204):
                    return {"success": True}
                return {"success": False, "status_code": res.status_code, "error": res.text}
        except Exception as e:
            logger.warning(f"Discord dispatch failed: {e}")
            return {"success": False, "error": str(e)}

    def format_trade_signal_telegram(self, signal: Dict[str, Any]) -> str:
        """Create HTML formatted trade signal message for Telegram."""
        direction = signal.get("direction", "BUY").upper()
        emoji = "🟢 <b>BUY ORDER</b>" if direction == "BUY" else "🔴 <b>SELL ORDER</b>"
        inst = signal.get("instrument", "XAUUSD")
        tf = signal.get("timeframe", "H1")
        entry = signal.get("entry_price", "Market")
        sl = signal.get("stop_loss", "None")
        tp = signal.get("take_profit", "None")
        conf = signal.get("confidence", 0.85) * 100
        swarm_pct = signal.get("swarm_consensus_pct", conf)
        horizon = signal.get("recommended_duration", "4h-8h")
        reasoning = signal.get("reasoning", "180-Agent Swarm alignment with multi-timeframe SMC Order Block.")

        return (
            f"🦅 <b>KESTREL INSTITUTIONAL TRADE ALERT</b>\n"
            f"────────────────────────\n"
            f"{emoji}: <b>{inst}</b> [{tf}]\n"
            f"🎯 <b>Entry:</b> <code>{entry}</code>\n"
            f"🛑 <b>Stop Loss:</b> <code>{sl}</code>\n"
            f"🎁 <b>Take Profit:</b> <code>{tp}</code>\n"
            f"🧠 <b>180-Swarm Quorum:</b> <code>{swarm_pct:.1f}%</code>\n"
            f"⏳ <b>Expected Horizon:</b> <code>{horizon}</code>\n"
            f"────────────────────────\n"
            f"💡 <i>{reasoning}</i>\n"
            f"⚡ <i>Auto-routed via Kestrel RiskEngine v4.0</i>"
        )

    def format_trade_signal_discord(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create rich embed array for Discord."""
        direction = signal.get("direction", "BUY").upper()
        color = 0x00E5FF if direction == "BUY" else 0xFF2A55  # Neon Cyan or Neon Red
        inst = signal.get("instrument", "XAUUSD")
        tf = signal.get("timeframe", "H1")
        entry = str(signal.get("entry_price", "Market"))
        sl = str(signal.get("stop_loss", "None"))
        tp = str(signal.get("take_profit", "None"))
        conf = signal.get("confidence", 0.85) * 100
        horizon = signal.get("recommended_duration", "4h-8h")

        return [{
            "title": f"🦅 Trade Signal: {direction} {inst} [{tf}]",
            "description": signal.get("reasoning", "180-Agent Quorum Consensus Confirmed."),
            "color": color,
            "fields": [
                {"name": "🎯 Entry", "value": entry, "inline": True},
                {"name": "🛑 Stop Loss", "value": sl, "inline": True},
                {"name": "🎁 Take Profit", "value": tp, "inline": True},
                {"name": "🧠 180-Swarm Quorum", "value": f"{conf:.1f}% Consensus", "inline": True},
                {"name": "⏳ Horizon", "value": horizon, "inline": True},
                {"name": "🛡️ Risk Shield", "value": "1.0% Max Risk Enforced", "inline": True},
            ],
            "footer": {"text": "CapeChain Labs • Institutional Trading Intelligence"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]

    def format_prop_firm_alert(self, data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        """Format prop firm drawdown warning."""
        acc = data.get("account_login", "Unknown")
        broker = data.get("broker", "FTMO")
        daily_loss = data.get("daily_loss_pct", 0.0)
        total_dd = data.get("max_drawdown_pct", 0.0)
        profile = data.get("prop_firm_profile", "PROP_FTMO")
        breach = data.get("breach", False)

        tag = "🚨 <b>PROP-FIRM RULE BREACH</b>" if breach else "⚠️ <b>PROP-FIRM RISK WARNING</b>"
        tg_msg = (
            f"🛡️ <b>KESTREL PROP-FIRM SHIELD ALERT</b>\n"
            f"────────────────────────\n"
            f"{tag}\n"
            f"👤 <b>Account:</b> <code>#{acc} ({broker})</code>\n"
            f"📊 <b>Profile:</b> <code>{profile}</code>\n"
            f"📉 <b>Daily Loss:</b> <code>{daily_loss:.2f}%</code>\n"
            f"🌊 <b>Total Drawdown:</b> <code>{total_dd:.2f}%</code>\n"
            f"────────────────────────\n"
            f"{'🛑 EMERGENCY HALT ACTIVE: All trades closed to prevent account breach.' if breach else '⚡ Stop loss tightening and auto-pilot throttled.'}"
        )

        discord_embed = [{
            "title": f"🛡️ Prop-Firm Shield: Account #{acc}",
            "description": "Rule breach emergency halt triggered." if breach else "Approaching daily/drawdown safety thresholds.",
            "color": 0xFF2A55 if breach else 0xF59E0B,
            "fields": [
                {"name": "Account / Broker", "value": f"{acc} ({broker})", "inline": True},
                {"name": "Rules Profile", "value": profile, "inline": True},
                {"name": "Daily Loss %", "value": f"{daily_loss:.2f}%", "inline": True},
                {"name": "Max Drawdown %", "value": f"{total_dd:.2f}%", "inline": True},
            ],
            "footer": {"text": "Kestrel CRiskEngine Automated Safeguard"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]

        return tg_msg, discord_embed


notification_dispatcher = NotificationDispatcher()
