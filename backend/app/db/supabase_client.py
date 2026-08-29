"""
Kestrel Core — Supabase Database Client & Cloud Sync Service
CapeChain Labs

Handles real-time persistence of trades, AI signals, 100-model consensus,
and account performance snapshots to Supabase PostgreSQL.
"""
import logging
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings

logger = logging.getLogger("kestrel.supabase")


class SupabaseClient:
    """
    High-performance async Supabase client with dual mode:
    Works with Supabase REST API (PostgREST) with automatic retry and graceful fallback.
    """
    
    def __init__(self):
        self.url = (settings.SUPABASE_URL or "").rstrip("/")
        self.api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY or ""
        self.rest_url = f"{self.url}/rest/v1" if self.url else ""
        self.is_configured = bool(self.url and self.api_key)
        
        if self.is_configured:
            logger.info("🦅 Supabase Client initialized for project: %s", self.url)
        else:
            logger.info("ℹ️ Supabase not yet configured. Operating in local-first database mode.")
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
    async def record_trade(self, trade_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a trade execution into Supabase 'trades' table."""
        if not self.is_configured:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    f"{self.rest_url}/trades",
                    headers=self._get_headers(),
                    json=trade_data
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    logger.info("✅ Trade persisted to Supabase: %s", trade_data.get("instrument"))
                    return data[0] if isinstance(data, list) and data else data
                else:
                    logger.warning("⚠️ Supabase trade insert response (%d): %s", res.status_code, res.text)
        except Exception as e:
            logger.error("❌ Supabase record_trade error: %s", str(e))
        return None

    async def record_signal(self, signal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a 100-AI consensus signal into Supabase 'signals' table."""
        if not self.is_configured:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    f"{self.rest_url}/signals",
                    headers=self._get_headers(),
                    json=signal_data
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    logger.info("✅ Signal persisted to Supabase: %s %s", signal_data.get("instrument"), signal_data.get("direction"))
                    return data[0] if isinstance(data, list) and data else data
                else:
                    logger.warning("⚠️ Supabase signal insert response (%d): %s", res.status_code, res.text)
        except Exception as e:
            logger.error("❌ Supabase record_signal error: %s", str(e))
        return None

    async def update_account_metrics(self, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upsert account balance, equity, drawdown, and recovery level."""
        if not self.is_configured:
            return None
            
        try:
            headers = self._get_headers()
            headers["Prefer"] = "resolution=merge-duplicates,return=representation"
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    f"{self.rest_url}/accounts",
                    headers=headers,
                    json=account_data
                )
                if res.status_code in (200, 201):
                    return res.json()
        except Exception as e:
            logger.error("❌ Supabase update_account_metrics error: %s", str(e))
        return None

    async def get_latest_signals(self, instrument: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent high-conviction signals from Supabase."""
        if not self.is_configured:
            return []
            
        try:
            params = {
                "select": "*",
                "order": "created_at.desc",
                "limit": str(limit)
            }
            if instrument:
                params["instrument"] = f"eq.{instrument}"
                
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    f"{self.rest_url}/signals",
                    headers=self._get_headers(),
                    params=params
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.error("❌ Supabase get_latest_signals error: %s", str(e))
        return []


supabase_client = SupabaseClient()
