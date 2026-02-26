from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import List, Dict

from api.auth import validate_init_data
from db.database import async_session
from db.models import User, Event, Subscription, Payment, ReferralBalance
from bot.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def get_db():
    async with async_session() as session:
        yield session

def check_admin(user_data: dict = Depends(validate_init_data)):
    """Check if the requesting Telegram user is an admin."""
    user_id = user_data["id"]
    admin_ids = [int(i.strip()) for i in settings.ADMIN_IDS_STR.split(",") if i.strip()]
    if user_id not in admin_ids:
        raise HTTPException(status_code=403, detail="Not authorized (Admins only)")
    return user_id


@router.get("/stats")
async def get_dashboard_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """High-level KPIs for Dashboard Home."""
    # Total Users
    total_users_q = await db.execute(select(func.count(User.id)))
    total_users = total_users_q.scalar() or 0

    # Active Subscriptions
    active_subs_q = await db.execute(select(func.count(Subscription.id)).where(Subscription.status == "active"))
    active_subs = active_subs_q.scalar() or 0

    # Total Revenue (sum of all successful payments)
    revenue_q = await db.execute(select(func.sum(Payment.amount)).where(Payment.status == "success"))
    total_revenue = revenue_q.scalar() or 0

    # Basic Conversion Rate (Paid / Total)
    conversion = round((active_subs / total_users * 100) if total_users > 0 else 0, 1)

    # Revenue chart for last 7 days
    today = datetime.utcnow().date()
    day_labels = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"]
    revenue_chart = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        rev_q = await db.execute(
            select(func.sum(Payment.amount)).where(
                Payment.status == "success",
                Payment.created_at >= day_start,
                Payment.created_at < day_end,
            )
        )
        rev_val = rev_q.scalar() or 0
        revenue_chart.append({"day": day_labels[day.weekday()], "revenue": int(rev_val)})

    # Recent activity from Events table (last 10)
    events_q = await db.execute(
        select(Event, User).join(User, Event.user_id == User.id)
        .order_by(Event.created_at.desc())
        .limit(10)
    )
    rows = events_q.all()
    recent_activity = []
    for ev, user in rows:
        recent_activity.append({
            "id": ev.id,
            "type": ev.event_type,
            "text": f"{user.name or 'Foydalanuvchi'} — {ev.event_type}",
            "time": _format_time(ev.created_at),
        })

    return {
        "kpis": {
            "totalUsers": total_users,
            "activeSubs": active_subs,
            "totalRevenue": int(total_revenue),
            "conversion": conversion
        },
        "revenueChart7d": revenue_chart,
        "recentActivity": recent_activity
    }


@router.get("/users")
async def get_users_list(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get CRM users list."""
    result = await db.execute(
        select(User, Subscription)
        .outerjoin(Subscription, Subscription.user_id == User.id)
        .order_by(User.created_at.desc())
        .limit(200)
    )
    rows = result.all()

    res = []
    for user, sub in rows:
        # Derive status
        if sub and sub.status == "active":
            status = "paid"
        elif user.user_status == "registered":
            status = "free"
        else:
            status = "free"

        score_val = "cold"
        if user.lead_score >= 60:
            score_val = "hot"
        elif user.lead_score >= 30:
            score_val = "nurture"

        res.append({
            "id": user.telegram_id,
            "name": user.name or "Noma'lum",
            "phone": user.phone or "—",
            "score": score_val,
            "status": status,
            "source": user.source or "organik",
            "events": []
        })
    return res


@router.get("/funnel")
async def get_funnel_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get funnel conversion data from real DB counts."""
    # All users who started
    all_q = await db.execute(select(func.count(User.id)))
    all_users = all_q.scalar() or 0

    # Registered (has phone)
    reg_q = await db.execute(select(func.count(User.id)).where(User.user_status == "registered"))
    registered = reg_q.scalar() or 0

    # Segmented (has goal_tag or level_tag set)
    seg_q = await db.execute(select(func.count(User.id)).where(User.goal_tag != None))
    segmented = seg_q.scalar() or 0

    # Lead magnet opened
    lm_q = await db.execute(select(func.count(User.id)).where(User.lead_magnet_opened == True))
    lm_opened = lm_q.scalar() or 0

    # VSL viewed (event_type = vsl_view)
    vsl_q = await db.execute(
        select(func.count(func.distinct(Event.user_id))).where(Event.event_type == "vsl_view")
    )
    vsl_viewed = vsl_q.scalar() or 0

    # Payment started (event_type = payment_open or checkout opened)
    pay_open_q = await db.execute(
        select(func.count(func.distinct(Event.user_id))).where(Event.event_type == "payment_open")
    )
    payment_opened = pay_open_q.scalar() or 0

    # Payment successful
    pay_q = await db.execute(select(func.count(Payment.id)).where(Payment.status == "success"))
    paid = pay_q.scalar() or 0

    def _rate(n, d):
        if d == 0: return 0
        return round(n / d * 100)

    return [
        {"label": "/start", "users": all_users, "rate": 100},
        {"label": "Ro'yxatdan o'tgan", "users": registered, "rate": _rate(registered, all_users)},
        {"label": "Segmentlangan", "users": segmented, "rate": _rate(segmented, registered)},
        {"label": "Material ochgan", "users": lm_opened, "rate": _rate(lm_opened, segmented)},
        {"label": "Video ko'rgan", "users": vsl_viewed, "rate": _rate(vsl_viewed, lm_opened)},
        {"label": "To'lovga o'tgan", "users": payment_opened, "rate": _rate(payment_opened, vsl_viewed)},
        {"label": "To'lov qildi", "users": paid, "rate": _rate(paid, payment_opened)},
    ]


@router.get("/events")
async def get_events_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get interaction and traffic data from real DB events."""

    # Top button clicks — aggregate event_type counts for click events
    click_Q = await db.execute(
        select(Event.event_type, func.count(Event.id).label("cnt"))
        .where(Event.event_type.like("%_click%"))
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .limit(5)
    )
    top_buttons = [
        {"name": row.event_type.replace("_click", "").replace("_", " ").title(), "clicks": row.cnt, "trend": "—"}
        for row in click_Q.all()
    ]

    # Traffic sources — count distinct users per source
    source_q = await db.execute(
        select(User.source, func.count(User.id).label("cnt"))
        .where(User.source != None)
        .group_by(User.source)
        .order_by(func.count(User.id).desc())
        .limit(5)
    )
    source_rows = source_q.all()
    total_with_source = sum(r.cnt for r in source_rows) or 1
    colors = ["hsl(199, 85%, 55%)", "hsl(199, 85%, 40%)", "hsl(142, 60%, 45%)", "hsl(38, 92%, 55%)", "hsl(280, 65%, 55%)"]
    traffic_sources = [
        {
            "name": (r.source or "Boshqa").title(),
            "value": round(r.cnt / total_with_source * 100),
            "color": colors[i % len(colors)]
        }
        for i, r in enumerate(source_rows)
    ]

    # Goal segment counts
    goal_q = await db.execute(
        select(User.goal_tag, func.count(User.id).label("cnt"))
        .where(User.goal_tag != None)
        .group_by(User.goal_tag)
        .order_by(func.count(User.id).desc())
    )
    goal_map = {
        "make_money": "Pul topish",
        "get_clients": "Mijoz olish",
        "automate_business": "Avtomatlashtirish",
    }
    segment_goal = [
        {"name": goal_map.get(r.goal_tag, r.goal_tag), "count": r.cnt}
        for r in goal_q.all()
    ]

    # Level segment counts
    level_q = await db.execute(
        select(User.level_tag, func.count(User.id).label("cnt"))
        .where(User.level_tag != None)
        .group_by(User.level_tag)
        .order_by(func.count(User.id).desc())
    )
    level_map = {
        "beginner": "Boshlang'ich",
        "freelancer": "Frilanser",
        "business": "Biznes egasi",
    }
    segment_level = [
        {"name": level_map.get(r.level_tag, r.level_tag), "count": r.cnt}
        for r in level_q.all()
    ]

    return {
        "topButtons": top_buttons,
        "trafficSources": traffic_sources,
        "segmentGoal": segment_goal,
        "segmentLevel": segment_level,
    }


@router.post("/broadcast")
async def send_broadcast(payload: dict, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Trigger a broadcast message."""
    audience_index = payload.get("audience", 0)
    message_content = payload.get("message", "").strip()

    if not message_content:
        raise HTTPException(status_code=400, detail="Xabar matni bo'sh bo'lishi mumkin emas.")

    filters = {}
    if audience_index == 1:
        filters = {"user_status": "free", "lead_score_min": 30}
    elif audience_index == 2:
        filters = {"lead_segment": "hot"}
    elif audience_index == 3:
        filters = {"user_status": "paid"}

    from services.broadcast import BroadcastService
    broadcast_service = BroadcastService(db)

    broadcast = await broadcast_service.create_broadcast(
        content=message_content,
        content_type="text",
        filters=filters,
    )
    await db.commit()

    try:
        from taskqueue.tasks import schedule_broadcast
        await schedule_broadcast(broadcast.id)
    except Exception as e:
        print(f"Schedule broadcast failed: {e}")

    return {"status": "accepted", "message": "Xabarlar tarqatish yuborildi."}


# ── Helpers ───────────────────────────────────────
def _format_time(dt: datetime) -> str:
    """Format datetime to readable 'X daqiqa' or date string."""
    if not dt:
        return "—"
    diff = datetime.utcnow() - dt
    if diff.total_seconds() < 60:
        return "Hozirgina"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} daqiqa oldin"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} soat oldin"
    else:
        return dt.strftime("%d.%m.%Y")
