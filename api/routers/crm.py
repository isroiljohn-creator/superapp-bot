"""CRM/ERP backend — sales pipeline, staff, applications, expenses, finance."""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin import check_admin, get_db
from db.models import Deal, DealNote, DealTask, Application, AdminUser, Expense, Purchase, Product, User

router = APIRouter(prefix="/api/admin/crm", tags=["crm"])
logger = logging.getLogger("api.crm")


# ──────────────────────────────────────────────
# Deals / pipeline
# ──────────────────────────────────────────────
class DealPatch(BaseModel):
    stage: Optional[str] = None
    assigned_to: Optional[int] = None
    amount: Optional[int] = None
    lost_reason: Optional[str] = None


@router.get("/deals")
async def list_deals(
    stage: str = "",
    assigned_to: Optional[int] = None,
    q: str = "",
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Deal, User).join(User, User.id == Deal.user_id)
    if stage:
        query = query.where(Deal.stage == stage)
    if assigned_to is not None:
        query = query.where(Deal.assigned_to == assigned_to)
    if q:
        q_clean = q.strip()
        if q_clean.isdigit():
            query = query.where((User.telegram_id == int(q_clean)) | (User.phone.contains(q_clean)))
        else:
            query = query.where(User.name.ilike(f"%{q_clean}%"))
    query = query.order_by(Deal.created_at.desc())

    result = await db.execute(query)
    rows = result.all()
    return {
        "deals": [
            {
                "id": deal.id,
                "user_id": deal.user_id,
                "user_name": user.name,
                "user_phone": user.phone,
                "telegram_id": user.telegram_id,
                "application_id": deal.application_id,
                "product_id": deal.product_id,
                "stage": deal.stage,
                "amount": deal.amount,
                "assigned_to": deal.assigned_to,
                "lost_reason": deal.lost_reason,
                "created_at": deal.created_at.isoformat() if deal.created_at else None,
                "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
                "closed_at": deal.closed_at.isoformat() if deal.closed_at else None,
            }
            for deal, user in rows
        ]
    }


@router.patch("/deals/{deal_id}")
async def update_deal(
    deal_id: int,
    patch: DealPatch,
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal topilmadi")

    if patch.stage is not None:
        valid_stages = {"new", "contacted", "offer", "won", "lost"}
        if patch.stage not in valid_stages:
            raise HTTPException(status_code=400, detail=f"Noto'g'ri stage. Ruxsat etilgan: {valid_stages}")
        deal.stage = patch.stage
        if patch.stage in ("won", "lost"):
            deal.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if patch.assigned_to is not None:
        deal.assigned_to = patch.assigned_to
    if patch.amount is not None:
        deal.amount = patch.amount
    if patch.lost_reason is not None:
        deal.lost_reason = patch.lost_reason

    await db.commit()
    return {"status": "ok"}


class NoteCreate(BaseModel):
    text: str
    admin_id: Optional[int] = None


@router.get("/deals/{deal_id}/notes")
async def list_deal_notes(deal_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealNote).where(DealNote.deal_id == deal_id).order_by(DealNote.created_at.desc()))
    notes = result.scalars().all()
    return {
        "notes": [
            {"id": n.id, "text": n.text, "admin_id": n.admin_id, "created_at": n.created_at.isoformat() if n.created_at else None}
            for n in notes
        ]
    }


@router.post("/deals/{deal_id}/notes")
async def create_deal_note(deal_id: int, body: NoteCreate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    note = DealNote(deal_id=deal_id, text=body.text, admin_id=body.admin_id)
    db.add(note)
    await db.commit()
    return {"status": "ok", "id": note.id}


class TaskCreateBody(BaseModel):
    title: str
    task_type: str = "task"
    due_at: Optional[str] = None
    admin_id: Optional[int] = None


class TaskPatch(BaseModel):
    status: Optional[str] = None
    outcome: Optional[str] = None


@router.post("/deals/{deal_id}/tasks")
async def create_deal_task(deal_id: int, body: TaskCreateBody, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    due_at = None
    if body.due_at:
        try:
            due_at = datetime.fromisoformat(body.due_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=400, detail="due_at ISO formatda bo'lishi kerak")

    task = DealTask(deal_id=deal_id, title=body.title, task_type=body.task_type, due_at=due_at, admin_id=body.admin_id)
    db.add(task)
    await db.commit()
    return {"status": "ok", "id": task.id}


@router.patch("/tasks/{task_id}")
async def update_task(task_id: int, patch: TaskPatch, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealTask).where(DealTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")

    if patch.status is not None:
        task.status = patch.status
        if patch.status == "done":
            task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if patch.outcome is not None:
        task.outcome = patch.outcome

    await db.commit()
    return {"status": "ok"}


@router.post("/deals/{deal_id}/send_invoice")
async def send_deal_invoice(deal_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    """Trigger the bot to send a full-course Telegram invoice to this deal's user."""
    result = await db.execute(select(Deal, User).join(User, User.id == Deal.user_id).where(Deal.id == deal_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Deal topilmadi")
    deal, user = row

    from bot.config import settings
    from aiogram import Bot
    from bot.handlers.deals import send_course_invoice

    bot = Bot(token=settings.BOT_TOKEN)
    try:
        await send_course_invoice(bot, user.telegram_id, deal_id, amount=deal.amount)
    except Exception as e:
        logger.error(f"Failed to send course invoice for deal {deal_id}: {e}")
        raise HTTPException(status_code=502, detail="Invoice yuborib bo'lmadi")
    finally:
        await bot.session.close()

    if deal.stage == "new":
        deal.stage = "offer"
        await db.commit()

    return {"status": "ok"}


# ──────────────────────────────────────────────
# Applications
# ──────────────────────────────────────────────
@router.get("/applications")
async def list_applications(
    tier: str = "",
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Application, User).join(User, User.id == Application.user_id)
    if tier:
        query = query.where(Application.tier == tier)
    query = query.order_by(Application.created_at.desc())

    result = await db.execute(query)
    rows = result.all()
    return {
        "applications": [
            {
                "id": app.id,
                "user_id": app.user_id,
                "user_name": user.name,
                "telegram_id": user.telegram_id,
                "answers": app.answers,
                "score": app.score,
                "tier": app.tier,
                "created_at": app.created_at.isoformat() if app.created_at else None,
            }
            for app, user in rows
        ]
    }


# ──────────────────────────────────────────────
# Staff (AdminUser CRUD)
# ──────────────────────────────────────────────
class StaffCreate(BaseModel):
    username: str
    password: str
    role: str = "sales"


class StaffPatch(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


VALID_ROLES = {"admin", "sales", "marketing"}


@router.get("/staff")
async def list_staff(admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
    staff = result.scalars().all()
    return {
        "staff": [
            {"id": s.id, "username": s.username, "role": s.role, "is_active": s.is_active}
            for s in staff
        ]
    }


@router.post("/staff")
async def create_staff(body: StaffCreate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    import bcrypt

    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri rol. Ruxsat etilgan: {VALID_ROLES}")

    existing = await db.execute(select(AdminUser).where(AdminUser.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu username allaqachon band")

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    staff = AdminUser(username=body.username, password_hash=password_hash, role=body.role, is_active=True)
    db.add(staff)
    await db.commit()
    return {"status": "ok", "id": staff.id}


@router.patch("/staff/{staff_id}")
async def update_staff(staff_id: int, patch: StaffPatch, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    import bcrypt

    result = await db.execute(select(AdminUser).where(AdminUser.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    if patch.role is not None:
        if patch.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Noto'g'ri rol. Ruxsat etilgan: {VALID_ROLES}")
        staff.role = patch.role
    if patch.is_active is not None:
        staff.is_active = patch.is_active
    if patch.password:
        staff.password_hash = bcrypt.hashpw(patch.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    await db.commit()
    return {"status": "ok"}


@router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
    await db.delete(staff)
    await db.commit()
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Expenses
# ──────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    category: str
    amount: int
    description: Optional[str] = None
    expense_date: str  # ISO date
    admin_id: Optional[int] = None


@router.get("/expenses")
async def list_expenses(
    date_from: str = "",
    date_to: str = "",
    category: str = "",
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Expense)
    if category:
        query = query.where(Expense.category == category)
    if date_from:
        query = query.where(Expense.expense_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Expense.expense_date <= datetime.fromisoformat(date_to))
    query = query.order_by(Expense.expense_date.desc())

    result = await db.execute(query)
    expenses = result.scalars().all()
    return {
        "expenses": [
            {
                "id": e.id, "category": e.category, "amount": e.amount,
                "description": e.description, "expense_date": e.expense_date.isoformat() if e.expense_date else None,
            }
            for e in expenses
        ]
    }


@router.post("/expenses")
async def create_expense(body: ExpenseCreate, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    try:
        expense_date = datetime.fromisoformat(body.expense_date.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="expense_date ISO formatda bo'lishi kerak")

    expense = Expense(
        category=body.category, amount=body.amount, description=body.description,
        expense_date=expense_date, admin_id=body.admin_id,
    )
    db.add(expense)
    await db.commit()
    return {"status": "ok", "id": expense.id}


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, admin_id: int = Depends(check_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Xarajat topilmadi")
    await db.delete(expense)
    await db.commit()
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Finance summary
# ──────────────────────────────────────────────
@router.get("/finance/summary")
async def finance_summary(
    date_from: str = "",
    date_to: str = "",
    admin_id: int = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revenue (from Purchase — NOT Payment) minus expenses, by product and day."""
    revenue_q = select(Purchase.product_id, Product.code, func.sum(Purchase.amount), func.count(Purchase.id)).join(
        Product, Product.id == Purchase.product_id
    ).where(Purchase.status == "success")
    if date_from:
        revenue_q = revenue_q.where(Purchase.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        revenue_q = revenue_q.where(Purchase.created_at <= datetime.fromisoformat(date_to))
    revenue_q = revenue_q.group_by(Purchase.product_id, Product.code)

    revenue_result = await db.execute(revenue_q)
    by_product = [
        {"product_id": pid, "product_code": code, "revenue": total or 0, "count": count}
        for pid, code, total, count in revenue_result.all()
    ]
    total_revenue = sum(r["revenue"] for r in by_product)

    expense_q = select(func.sum(Expense.amount))
    if date_from:
        expense_q = expense_q.where(Expense.expense_date >= datetime.fromisoformat(date_from))
    if date_to:
        expense_q = expense_q.where(Expense.expense_date <= datetime.fromisoformat(date_to))
    expense_result = await db.execute(expense_q)
    total_expense = expense_result.scalar() or 0

    daily_q = select(func.date(Purchase.created_at).label("day"), func.sum(Purchase.amount)).where(
        Purchase.status == "success"
    )
    if date_from:
        daily_q = daily_q.where(Purchase.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        daily_q = daily_q.where(Purchase.created_at <= datetime.fromisoformat(date_to))
    daily_q = daily_q.group_by(func.date(Purchase.created_at)).order_by(func.date(Purchase.created_at))
    daily_result = await db.execute(daily_q)
    daily_revenue = [{"day": str(day), "revenue": total or 0} for day, total in daily_result.all()]

    return {
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "profit": total_revenue - total_expense,
        "by_product": by_product,
        "daily_revenue": daily_revenue,
    }
