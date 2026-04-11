import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bot.config import settings

logger = logging.getLogger("amocrm")

class AmoCRMService:
    def __init__(self):
        self.domain = settings.AMOCRM_DOMAIN
        self.token = settings.AMOCRM_ACCESS_TOKEN
        self.client = httpx.AsyncClient(timeout=15.0)

    def is_configured(self) -> bool:
        return bool(self.domain and self.token)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def get_users(self) -> List[Dict[str, Any]]:
        """Fetch all users (managers) from amoCRM."""
        if not self.is_configured():
            logger.warning("AmoCRM not configured. Returning empty users.")
            return []
            
        url = f"https://{self.domain}/api/v4/users"
        try:
            res = await self.client.get(url, headers=self._headers())
            res.raise_for_status()
            data = res.json()
            return data.get("_embedded", {}).get("users", [])
        except Exception as e:
            logger.error(f"Failed to fetch amocrm users: {e}")
            return []

    async def get_daily_calls_for_user(self, user_id: int, timestamp_start: int, timestamp_end: int) -> Dict[str, Any]:
        """
        Fetch call events for a specific user within a date range.
        Calculates total calls, answered/missed (if possible by duration), and total duration.
        Note: amoCRM events api allows filtering by created_at.
        """
        if not self.is_configured():
            return {"total_calls": 0, "duration": 0, "answered": 0, "missed": 0}

        # Event type 'call' or 'call_in' or 'call_out'. By default AMO handles 'call' entity type
        # amoCRM actually stores calls under /api/v4/calls but it depends on the telephony widget.
        # As a robust fallback, we query events typed as call_in / call_out if needed, or just let users log it.
        # This is a stub implementation until specific amoCRM structure is known.
        url = f"https://{self.domain}/api/v4/events"
        params = {
            "filter[created_at][from]": timestamp_start,
            "filter[created_at][to]": timestamp_end,
            "filter[created_by]": user_id,
            "limit": 100
        }
        try:
            res = await self.client.get(url, headers=self._headers(), params=params)
            if res.status_code == 204:
                return {"total_calls": 0, "duration": 0, "answered": 0, "missed": 0}
            res.raise_for_status()
            data = res.json()
            events = data.get("_embedded", {}).get("events", [])
            
            # Placeholder: amoCRM call events differ by telephony.
            # Usually events with type 'outgoing_call' or 'incoming_call'.
            calls = [e for e in events if "call" in e.get("type", "")]
            return {
                "total_calls": len(calls),
                "duration": sum(120 for _ in calls), # Example mock 2 mins per call
                "answered": len(calls), # Example mock
                "missed": 0
            }
        except Exception as e:
            logger.error(f"Failed to fetch calls for user {user_id}: {e}")
            return {"total_calls": 0, "duration": 0, "answered": 0, "missed": 0}

    async def get_daily_leads_for_user(self, user_id: int, timestamp_start: int, timestamp_end: int) -> Dict[str, Any]:
        """
        Fetch won/pre_payable leads updated by user today.
        """
        if not self.is_configured():
            return {"won": 0, "pre_payments": 0, "total_leads": 0}

        url = f"https://{self.domain}/api/v4/leads"
        # We can filter leads created by user, but usually it's 'responsible_user_id'
        params = {
            "filter[updated_at][from]": timestamp_start,
            "filter[updated_at][to]": timestamp_end,
            "filter[responsible_user_id]": user_id,
            "limit": 50
        }
        try:
            res = await self.client.get(url, headers=self._headers(), params=params)
            if res.status_code == 204:
                return {"won": 0, "pre_payments": 0, "total_leads": 0}
            res.raise_for_status()
            data = res.json()
            leads = data.get("_embedded", {}).get("leads", [])
            
            # Status IDs are pipeline-specific. We use mock aggregation here.
            # Muvaffaqiyatli sotildi (success = 142) is generic AMO ID for success, 143 for loss.
            won_leads = [l for l in leads if l.get("status_id") == 142]
            
            return {
                "total_leads": len(leads),
                "won": len(won_leads),
                "pre_payments": 0 # Requires custom fields analysis
            }
        except Exception as e:
            logger.error(f"Failed to fetch leads for user {user_id}: {e}")
            return {"won": 0, "pre_payments": 0, "total_leads": 0}

    async def close(self):
        await self.client.aclose()
