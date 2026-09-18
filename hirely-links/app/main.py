import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

from .ads import AdSelector
from .config import get_settings
from .db import dispose, sessionmaker
from .models import Admin
from .ratelimit import RateLimiter
from .routers import admin, api, public
from .security import hash_password
from .tracking import EventWriter
from .web import BASE, templates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("hirely")

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        h = resp.headers
        h.setdefault("Content-Security-Policy", CSP)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.path.startswith(("/media/", "/static/")) and resp.status_code == 200:
            h.setdefault("Cache-Control", "public, max-age=31536000, immutable")  # hashed names / ?v=mtime
        return resp


async def bootstrap_admin() -> None:
    s = get_settings()
    if not (s.bootstrap_admin_email and s.bootstrap_admin_password):
        return
    if len(s.bootstrap_admin_password) < 10:
        log.error("HIRELY_BOOTSTRAP_ADMIN_PASSWORD must be at least 10 characters; no admin created")
        return
    async with sessionmaker()() as db:
        if (await db.execute(select(Admin.id).limit(1))).first():
            return
        db.add(Admin(email=s.bootstrap_admin_email.strip().lower(), password_hash=hash_password(s.bootstrap_admin_password), display_name="Admin"))
        try:
            await db.commit()
            log.info("bootstrap admin created: %s", s.bootstrap_admin_email)
        except IntegrityError:  # another worker won the race
            await db.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    maker = sessionmaker()
    app.state.writer = EventWriter(maker, s.event_queue_size)
    app.state.ads = AdSelector(maker)
    app.state.limiter = RateLimiter(s.redis_url)
    os.makedirs(s.media_dir, exist_ok=True)
    await bootstrap_admin()
    app.state.writer.start()
    yield
    await app.state.writer.stop()
    await app.state.limiter.close()
    await dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Hirely Links", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(SecurityHeaders)
    app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
    app.mount("/media", StaticFiles(directory=get_settings().media_dir, check_dir=False), name="media")
    app.include_router(public.router)
    app.include_router(api.router)
    app.include_router(admin.router)
    admin.install(app)

    @app.exception_handler(404)
    async def _404(request: Request, exc):
        if request.url.path.startswith(("/api/", "/admin/api/")):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        return templates.TemplateResponse(request, "notfound.html", status_code=404, headers={"Cache-Control": "no-store"})

    return app


app = create_app()
