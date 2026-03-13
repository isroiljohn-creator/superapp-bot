"""A/B testing service — simple user-based variant assignment."""
import logging
from typing import Optional

from sqlalchemy import select, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Base, User

logger = logging.getLogger("ab_test")


class ABTest(Base):
    """A/B test experiment definition."""
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, default="")
    variant_a_name = Column(String, default="A")
    variant_b_name = Column(String, default="B")
    variant_a_value = Column(String, default="")  # e.g. message text, image URL
    variant_b_value = Column(String, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ABTestService:
    """Manages A/B test experiments and variant assignment."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_test(self, name: str, description: str = "",
                          variant_a: str = "", variant_b: str = "",
                          a_name: str = "A", b_name: str = "B") -> ABTest:
        """Create a new A/B test."""
        test = ABTest(
            name=name,
            description=description,
            variant_a_name=a_name,
            variant_b_name=b_name,
            variant_a_value=variant_a,
            variant_b_value=variant_b,
        )
        self.session.add(test)
        await self.session.flush()
        return test

    async def get_all(self) -> list[ABTest]:
        """Get all A/B tests."""
        result = await self.session.execute(
            select(ABTest).order_by(ABTest.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_tests(self) -> list[ABTest]:
        """Get only active tests."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.is_active == True).order_by(ABTest.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_variant(self, test_name: str, user_id: int) -> Optional[str]:
        """Get the variant value for a user in a specific test.
        Uses user_id % 2 for deterministic assignment: 0=A, 1=B.
        """
        result = await self.session.execute(
            select(ABTest).where(ABTest.name == test_name, ABTest.is_active == True)
        )
        test = result.scalar_one_or_none()
        if not test:
            return None

        # Deterministic: user_id % 2
        variant = "a" if (user_id % 2 == 0) else "b"
        return test.variant_a_value if variant == "a" else test.variant_b_value

    async def get_variant_name(self, test_name: str, user_id: int) -> Optional[str]:
        """Get variant name (A/B) for analytics."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.name == test_name, ABTest.is_active == True)
        )
        test = result.scalar_one_or_none()
        if not test:
            return None
        return test.variant_a_name if (user_id % 2 == 0) else test.variant_b_name

    async def toggle_test(self, test_id: int) -> Optional[ABTest]:
        """Toggle test active/inactive."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = result.scalar_one_or_none()
        if test:
            test.is_active = not test.is_active
            await self.session.flush()
        return test

    async def get_stats(self, test_id: int) -> dict:
        """Get conversion stats for a test."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            return {}

        # Count users in each variant
        all_users = await self.session.execute(select(func.count(User.id)))
        total = all_users.scalar() or 0

        return {
            "test_name": test.name,
            "variant_a": test.variant_a_name,
            "variant_b": test.variant_b_name,
            "users_a": total // 2 + (total % 2),  # even IDs
            "users_b": total // 2,  # odd IDs
            "is_active": test.is_active,
        }
