# Deploy Trigger: 2026-03-30T23:34:00
import os
import sys

# Ensure project root is in Python path (Railway deploys to /app)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import settings

from api.routers import user, payment, referral, course, admin, moderator_api

from typing import Optional

logger = logging.getLogger(__name__)

# Global bot and dispatcher
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

async def make_storage():
    """Create Redis FSM storage with fallback to MemoryStorage."""
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage.from_url(settings.get_redis_url)
        await storage.redis.ping()
        logger.info("✅ Redis FSM storage connected")
        return storage
    except Exception as e:
        logger.warning(f"⚠️ Redis FSM unavailable ({e}), falling back to MemoryStorage")
        from aiogram.fsm.storage.memory import MemoryStorage
        return MemoryStorage()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    from db.database import init_db, async_session
    await init_db()

    # One-time backfill: fix users with NULL created_at
    try:
        from sqlalchemy import update, select, func
        from db.models import User
        async with async_session() as session:
            null_count_q = await session.execute(
                select(func.count(User.id)).where(User.created_at.is_(None))
            )
            null_count = null_count_q.scalar() or 0
            if null_count > 0:
                logger.info(f"⏳ Backfilling created_at for {null_count} users...")
                # Use registered_at where available
                await session.execute(
                    update(User)
                    .where(User.created_at.is_(None), User.registered_at.isnot(None))
                    .values(created_at=User.registered_at)
                )
                # For remaining NULLs, use earliest known created_at or a fixed date
                earliest_q = await session.execute(
                    select(func.min(User.created_at))
                )
                earliest = earliest_q.scalar()
                if earliest:
                    await session.execute(
                        update(User)
                        .where(User.created_at.is_(None))
                        .values(created_at=earliest)
                    )
                else:
                    from datetime import datetime, timezone
                    await session.execute(
                        update(User)
                        .where(User.created_at.is_(None))
                        .values(created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
                    )
                await session.commit()
                logger.info(f"✅ Backfilled created_at for {null_count} users")
    except Exception as e:
        logger.warning(f"⚠️ created_at backfill failed: {e}")

    global bot, dp
    storage = await make_storage()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # Register bot routers
    from bot.handlers import registration, segmentation, lead_magnet, funnel, subscription, referral as bot_referral, admin as bot_admin, ai_workers, imagegen, copywriter, chatbot, moderation, menu, presentation, lyrics, lifecycle, jobs, superapp, moderator, moderator_group
    dp.include_routers(
        lifecycle.router,       # Bot block/unblock tracking — must be first
        moderator_group.router, # Group moderation — must be before menu
        registration.router,
        segmentation.router,
        lead_magnet.router,
        funnel.router,
        subscription.router,
        bot_referral.router,
        bot_admin.router,
        jobs.router,            # NUVI Jobs — vacancy posting
        superapp.router,        # Superapp menu
        moderator.router,       # Moderator settings (private chat)
        ai_workers.router,
        imagegen.router,
        copywriter.router,
        chatbot.router,
        presentation.router,
        lyrics.router,
        moderation.router,
        menu.router,
    )
    logger.info("✅ Barcha bot handlerlar ro'yxatdan o'tkazildi")

    # Set webhook if configured
    actual_webhook = settings.get_webhook_url
    if actual_webhook:
        webhook_url = f"{actual_webhook}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
            secret_token=settings.WEBHOOK_SECRET
        )
        logger.info(f"✅ Webhook o'rnatildi: {webhook_url}")
    else:
        logger.warning("⚠️ WEBHOOK_URL yo'q. Bot webhook orqali ishlamaydi (faqat polling)")

    # Start background services
    try:
        from taskqueue import start_scheduled_message_checker
        await start_scheduled_message_checker()
        logger.info("✅ Scheduled message checker started")
    except Exception as e:
        logger.warning(f"Scheduled message checker failed to start: {e}")

    yield

    # Shutdown
    if actual_webhook:
        try:
            # DO NOT delete webhook here, because in Railway blue-green deployments,
            # the old container shutting down will delete the webhook the new container just set!
            logger.info("✅ Webhook saqlab qolindi (zero-downtime)")
        except Exception as e:
            logger.error(f"❌ Webhook o'chirishda xatolik: {e}")
    if bot:
        await bot.session.close()


app = FastAPI(
    title="SuperApp Bot API",
    description="Backend API for Telegram Mini App — payments, course, referral",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Mini App — restrict to configured origin
_cors_origins = []
if settings.WEBAPP_URL:
    from urllib.parse import urlparse
    _parsed = urlparse(settings.WEBAPP_URL)
    _origin = f"{_parsed.scheme}://{_parsed.netloc}"
    _cors_origins = [_origin, settings.WEBAPP_URL]
elif settings.RAILWAY_PUBLIC_DOMAIN:
    _cors_origins = [f"https://{settings.RAILWAY_PUBLIC_DOMAIN}"]
else:
    # Local dev — allow all
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(payment.router)
app.include_router(referral.router)
app.include_router(course.router)
app.include_router(admin.router)
app.include_router(moderator_api.router)


@app.get("/health")
async def health():
    return {"status": "ok"}



@app.get("/")
async def root():
    """Serve GA4 tag at root for Google verification, then redirect to admin."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""<!doctype html>
<html lang="uz">
<head>
<meta charset="UTF-8"/>
<title>Nuvi Admin Dashboard</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ESZBV5JJCS"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-ESZBV5JJCS');
</script>
<meta http-equiv="refresh" content="1;url=/admin/">
</head>
<body><p>Redirecting to <a href="/admin/">Admin Dashboard</a>...</p></body>
</html>""")

@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Telegram webhook endpoint."""
    start_time = time.perf_counter()
    if settings.WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != settings.WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    update = types.Update(**data)
    if bot is None or dp is None:
        logger.warning("Webhook received before bot initialized — skipping")
        return {"ok": True}
    await dp.feed_update(bot=bot, update=update)
    
    elapsed = (time.perf_counter() - start_time) * 1000
    if elapsed > 1000:
        logger.warning(f"⚠️ WEBHOOK sekin ishladi! Vaqt: {elapsed:.2f} ms")
    else:
        logger.info(f"⚡️ Webhook tezligi: {elapsed:.2f} ms")
        
    return {"ok": True}


# Override static folder resolution safely
admin_dist = os.path.join(os.path.dirname(__file__), "static", "admin")
if os.path.exists(admin_dist):
    app.mount("/admin", StaticFiles(directory=admin_dist, html=True), name="admin_dashboard")
    app.mount("/panel", StaticFiles(directory=admin_dist, html=True), name="admin_dashboard_new")

mod_dist = os.path.join(os.path.dirname(__file__), "static", "moderator")
if os.path.exists(mod_dist):
    app.mount("/moderator", StaticFiles(directory=mod_dist, html=True), name="moderator_dashboard")

# No-cache middleware for admin HTML — defeats Telegram WebView caching
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/admin") or path.startswith("/panel") or path.startswith("/moderator"):
        # JS/CSS are hash-named (cache-safe), but HTML must never be cached
        if not path.endswith(".js") and not path.endswith(".css"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    return response
    
# Fallback for React Router (if a user refreshes a subpath)
@app.exception_handler(404)
async def custom_404_handler(request, __):
    # If the user is requesting an admin path, serve the React index file
    if (request.url.path.startswith("/admin/") or request.url.path.startswith("/panel/")) and os.path.exists(os.path.join(admin_dist, "index.html")):
        return FileResponse(os.path.join(admin_dist, "index.html"))
    # If requesting moderator path, serve moderator index
    if request.url.path.startswith("/moderator/") and os.path.exists(os.path.join(mod_dist, "index.html")):
        return FileResponse(os.path.join(mod_dist, "index.html"))
    # Otherwise, return a valid JSONResponse (Starlette stringently requires Response objects here)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
