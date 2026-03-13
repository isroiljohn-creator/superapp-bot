"""Funnel service — manages the sales funnel flow."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LeadMagnet, VSLContent


class FunnelService:
    """Manages lead magnets and VSL content."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Lead magnets ─────────────────────────
    async def get_lead_magnet(self, campaign: str) -> Optional[LeadMagnet]:
        result = await self.session.execute(
            select(LeadMagnet).where(
                LeadMagnet.campaign == campaign,
                LeadMagnet.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create_lead_magnet(
        self,
        campaign: str,
        content_type: str,
        file_id: str = None,
        file_url: str = None,
        description: str = None,
    ) -> LeadMagnet:
        lm = LeadMagnet(
            campaign=campaign,
            content_type=content_type,
            file_id=file_id,
            file_url=file_url,
            description=description,
        )
        self.session.add(lm)
        await self.session.flush()
        return lm

    # ── VSL content ──────────────────────────
    async def get_vsl(self, level_tag: str, goal_tag: str = None) -> Optional[VSLContent]:
        q = select(VSLContent).where(
            VSLContent.level_tag == level_tag,
            VSLContent.is_active.is_(True),
        )
        if goal_tag:
            q = q.where(VSLContent.goal_tag == goal_tag)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()
