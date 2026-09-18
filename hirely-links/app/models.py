import datetime as dt
from typing import Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

SCHEMA = "hirely"

EVENT_TYPES = (
    "page_view",
    "unique_visitor",
    "session_start",
    "phone_click",
    "telegram_click",
    "external_job_click",
    "ad_impression",
    "ad_click",
)
CONTACT_EVENTS = ("phone_click", "telegram_click", "external_job_click")
CAMPAIGN_STATUSES = ("draft", "active", "paused", "archived")
TARGET_KINDS = ("channel", "category", "market")


class Base(DeclarativeBase):
    metadata = MetaData(
        schema=SCHEMA,
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )


TS = DateTime(timezone=True)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[Optional[str]] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    last_login_at: Mapped[Optional[dt.datetime]] = mapped_column(TS)


class Channel(Base):
    """A place jobs are distributed to (a Telegram channel today; other markets/platforms later)."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    prefix: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    market: Mapped[str] = mapped_column(String(40), server_default="uz")
    platform: Mapped[str] = mapped_column(String(40), server_default="telegram")
    external_ref: Mapped[Optional[str]] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("title IS NOT NULL OR internal_ref IS NOT NULL", name="has_label"),
        CheckConstraint(
            "phone IS NOT NULL OR telegram IS NOT NULL OR external_url IS NOT NULL", name="has_contact"
        ),
        Index("ix_jobs_created_at", "created_at"),
        Index("ix_jobs_category", "category"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    internal_ref: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(40))
    source: Mapped[Optional[str]] = mapped_column(String(40))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    telegram: Mapped[Optional[str]] = mapped_column(String(40))
    external_url: Mapped[Optional[str]] = mapped_column(String(2048))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())

    distributions: Mapped[list["Distribution"]] = relationship(back_populates="job")

    @property
    def label(self) -> str:
        return self.title or self.internal_ref or self.public_id


class Distribution(Base):
    """One publication of a job in one channel. Its slug is the public tracking URL."""

    __tablename__ = "distributions"
    __table_args__ = (Index("ix_distributions_job_id", "job_id"), Index("ix_distributions_channel_created", "channel_id", "created_at"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True)
    slug: Mapped[str] = mapped_column(String(12), unique=True)
    job_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.jobs.id", ondelete="RESTRICT"))
    channel_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.channels.id", ondelete="RESTRICT"))
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    request_hash: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="distributions")
    channel: Mapped[Channel] = relationship()


class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    anon_id: Mapped[str] = mapped_column(String(64), unique=True)
    first_seen_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    last_seen_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_visitor_id", "visitor_id"), Index("ix_sessions_started_at", "started_at"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_key: Mapped[str] = mapped_column(String(64), unique=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.visitors.id", ondelete="CASCADE"))
    distribution_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.distributions.id", ondelete="SET NULL"))
    started_at: Mapped[dt.datetime] = mapped_column(TS)
    last_seen_at: Mapped[dt.datetime] = mapped_column(TS)
    referrer_host: Mapped[Optional[str]] = mapped_column(String(120))
    traffic_source: Mapped[Optional[str]] = mapped_column(String(60))
    device_category: Mapped[Optional[str]] = mapped_column(String(12))
    browser: Mapped[Optional[str]] = mapped_column(String(24))
    os: Mapped[Optional[str]] = mapped_column(String(24))


class Advertiser(Base):
    __tablename__ = "advertisers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    contact: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"
    __table_args__ = (
        CheckConstraint("status IN ('draft','active','paused','archived')", name="status"),
        CheckConstraint("end_at IS NULL OR start_at IS NULL OR end_at > start_at", name="period"),
        Index("ix_ad_campaigns_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    advertiser_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.advertisers.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(12), server_default="draft")
    start_at: Mapped[Optional[dt.datetime]] = mapped_column(TS)
    end_at: Mapped[Optional[dt.datetime]] = mapped_column(TS)
    impression_limit: Mapped[Optional[int]] = mapped_column(BigInteger)
    click_limit: Mapped[Optional[int]] = mapped_column(BigInteger)
    impressions_count: Mapped[int] = mapped_column(BigInteger, server_default="0")
    clicks_count: Mapped[int] = mapped_column(BigInteger, server_default="0")
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now(), onupdate=func.now())

    advertiser: Mapped[Advertiser] = relationship()
    targets: Mapped[list["AdTarget"]] = relationship(cascade="all, delete-orphan")
    creatives: Mapped[list["AdCreative"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class AdTarget(Base):
    """No rows for a campaign = all traffic. Otherwise a distribution must match any row."""

    __tablename__ = "ad_targets"
    __table_args__ = (
        UniqueConstraint("campaign_id", "kind", "value", name="uq_ad_targets_campaign_kind_value"),
        CheckConstraint("kind IN ('channel','category','market')", name="kind"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_campaigns.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(12))
    value: Mapped[str] = mapped_column(String(40))


class AdCreative(Base):
    __tablename__ = "ad_creatives"
    __table_args__ = (
        CheckConstraint("weight BETWEEN 1 AND 100", name="weight"),
        Index("ix_ad_creatives_campaign_id", "campaign_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(String(300))
    cta_text: Mapped[str] = mapped_column(String(40))
    destination_url: Mapped[str] = mapped_column(String(2048))
    image_name: Mapped[Optional[str]] = mapped_column(String(64))
    image_w: Mapped[Optional[int]] = mapped_column(SmallInteger)
    image_h: Mapped[Optional[int]] = mapped_column(SmallInteger)
    weight: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())

    campaign: Mapped[AdCampaign] = relationship(back_populates="creatives")


class Event(Base):
    """Append-only analytics log. Dimensions are denormalised so any group-by is a single-table scan."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "type IN ('" + "','".join(EVENT_TYPES) + "')",
            name="type",
        ),
        Index("ix_events_occurred_at_brin", "occurred_at", postgresql_using="brin"),
        Index("ix_events_type_occurred", "type", "occurred_at"),
        Index("ix_events_job_type_occurred", "job_id", "type", "occurred_at"),
        Index("ix_events_channel_type_occurred", "channel_id", "type", "occurred_at"),
        Index("ix_events_creative_type_occurred", "ad_id", "type", "occurred_at", postgresql_where=text("ad_id IS NOT NULL")),
        Index("ix_events_campaign_type_occurred", "campaign_id", "type", "occurred_at", postgresql_where=text("campaign_id IS NOT NULL")),
        Index("ix_events_visitor_type", "visitor_id", "type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), unique=True)
    type: Mapped[str] = mapped_column(String(24))
    occurred_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.jobs.id", ondelete="SET NULL"))
    distribution_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.distributions.id", ondelete="SET NULL"))
    channel_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.channels.id", ondelete="SET NULL"))
    ad_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.ad_creatives.id", ondelete="SET NULL"))
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.ad_campaigns.id", ondelete="SET NULL"))
    visitor_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.visitors.id", ondelete="SET NULL"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.sessions.id", ondelete="SET NULL"))
    category: Mapped[Optional[str]] = mapped_column(String(40))
    job_source: Mapped[Optional[str]] = mapped_column(String(40))
    traffic_source: Mapped[Optional[str]] = mapped_column(String(60))
    referrer_host: Mapped[Optional[str]] = mapped_column(String(120))
    device_category: Mapped[Optional[str]] = mapped_column(String(12))
    browser: Mapped[Optional[str]] = mapped_column(String(24))
    os: Mapped[Optional[str]] = mapped_column(String(24))
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)


class AdImpression(Base):
    __tablename__ = "ad_impressions"
    __table_args__ = (
        Index("ix_ad_impressions_campaign_occurred", "campaign_id", "occurred_at"),
        Index("ix_ad_impressions_creative_visitor", "creative_id", "visitor_id"),
        Index("ix_ad_impressions_occurred_brin", "occurred_at", postgresql_using="brin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nonce: Mapped[str] = mapped_column(String(32), unique=True)
    occurred_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    creative_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_creatives.id", ondelete="CASCADE"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_campaigns.id", ondelete="CASCADE"))
    distribution_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.distributions.id", ondelete="SET NULL"))
    visitor_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.visitors.id", ondelete="SET NULL"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.sessions.id", ondelete="SET NULL"))
    device_category: Mapped[Optional[str]] = mapped_column(String(12))
    visible_ms: Mapped[Optional[int]] = mapped_column(Integer)


class AdClick(Base):
    __tablename__ = "ad_clicks"
    __table_args__ = (
        Index("ix_ad_clicks_campaign_occurred", "campaign_id", "occurred_at"),
        Index("ix_ad_clicks_creative_visitor", "creative_id", "visitor_id"),
        Index("ix_ad_clicks_occurred_brin", "occurred_at", postgresql_using="brin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), unique=True)
    occurred_at: Mapped[dt.datetime] = mapped_column(TS, server_default=func.now())
    creative_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_creatives.id", ondelete="CASCADE"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA}.ad_campaigns.id", ondelete="CASCADE"))
    distribution_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.distributions.id", ondelete="SET NULL"))
    visitor_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.visitors.id", ondelete="SET NULL"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{SCHEMA}.sessions.id", ondelete="SET NULL"))
    device_category: Mapped[Optional[str]] = mapped_column(String(12))
    impression_nonce: Mapped[Optional[str]] = mapped_column(String(32))
