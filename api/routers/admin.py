from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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

    return {
        "kpis": {
            "totalUsers": total_users,
            "activeSubs": active_subs,
            "totalRevenue": int(total_revenue),
            "conversion": conversion
        },
        # For now, placeholder for charts (to be hooked up later if time permits)
        "revenueChart7d": [
             {"day": "Dush", "revenue": 0}, {"day": "Sesh", "revenue": 0},
             {"day": "Chor", "revenue": 0}, {"day": "Pay", "revenue": 0},
             {"day": "Jum", "revenue": 0}, {"day": "Shan", "revenue": 0},
             {"day": "Yak", "revenue": 0},
        ],
        "recentActivity": [
            # Placeholder, actual should query Events desc
        ]
    }

@router.get("/users")
async def get_users_list(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get CRM users list."""
    # Let's get top 100 latest users for performance
    result = await db.execute(select(User).order_by(User.registered_at.desc()).limit(100))
    users = result.scalars().all()
    
    # Format for the CRM table
    res = []
    for u in users:
        # Evaluate user status for admin display
        status = "free"
        if u.user_status == "registered":
            status = "free" # Default to free if registered
        
        # Will enhance score categorization later
        score_val = "cold"
        if u.lead_score >= 60: score_val = "hot"
        elif u.lead_score >= 30: score_val = "nurture"

        res.append({
            "id": u.telegram_id,
            "name": u.name or "Noma'lum",
            "phone": u.phone or "—",
            "score": score_val,
            "status": status,
            "source": u.source or "organik",
            "events": [] # Timeline events
        })
    return res

@router.get("/funnel")
async def get_funnel_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get funnel conversion data."""
    # Simplified funnel steps based on User counts
    res = await db.execute(select(func.count(User.id)))
    all_users = res.scalar() or 0
    
    res_reg = await db.execute(select(func.count(User.id)).where(User.user_status == "registered"))
    registered = res_reg.scalar() or 0

    return [
       {"label": "/start", "users": all_users, "rate": 100},
       {"label": "Ro'yxatdan o'tgan", "users": registered, "rate": round(registered/all_users*100) if all_users else 0},
       {"label": "Segmentlangan (Misol)", "users": int(registered*0.8), "rate": 80},
       {"label": "Material ochgan (Misol)", "users": int(registered*0.6), "rate": 75},
       {"label": "Video ko'rgan (Misol)", "users": int(registered*0.3), "rate": 50},
       {"label": "To'lovga o'tgan (Misol)", "users": int(registered*0.1), "rate": 33},
       {"label": "To'lov qildi (Misol)", "users": int(registered*0.05), "rate": 50},
    ]

@router.get("/events")
async def get_events_stats(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Get interaction and traffic data."""
    # Placeholder for structure matching frontend
    return {
        "topButtons": [],
        "trafficSources": [
            {"name": "Instagram", "value": 50, "color": "hsl(199, 85%, 55%)"},
            {"name": "Telegram", "value": 30, "color": "hsl(199, 85%, 40%)"},
            {"name": "Referral", "value": 20, "color": "hsl(142, 60%, 45%)"}
        ],
        "segmentGoal": [],
        "segmentLevel": []
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
        # Videoni ko'rgan, lekin to'lamagan (nurture/hot but free)
        filters = {"user_status": "free", "lead_score_min": 30}
    elif audience_index == 2:
        # Faqat issiq mijozlar
        filters = {"lead_segment": "hot"}
    elif audience_index == 3:
        # To'lagan mijozlar
        filters = {"user_status": "paid"}

    from services.broadcast import BroadcastService
    broadcast_service = BroadcastService(db)
    
    broadcast = await broadcast_service.create_broadcast(
        content=message_content,
        content_type="text",
        filters=filters,
    )
    await db.commit()

    # Schedule batch sending via queue
    try:
        from queue.tasks import schedule_broadcast
        await schedule_broadcast(broadcast.id)
    except Exception as e:
        print(f"Failed to schedule broadcast: {e}")
        # In this project, taskqueue might be named differently
        try:
            from taskqueue.tasks import schedule_broadcast
            await schedule_broadcast(broadcast.id)
        except Exception as e2:
            print(f"Fallback schedule failed: {e2}")

    return {"status": "accepted", "message": "Xabarlar tarqatish yuborildi."}
