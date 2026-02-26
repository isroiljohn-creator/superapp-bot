"""FastAPI application — REST API for Mini App."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import user, payment, referral, course

app = FastAPI(
    title="SuperApp Bot API",
    description="Backend API for Telegram Mini App — payments, course, referral",
    version="1.0.0",
)

# CORS for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(payment.router)
app.include_router(referral.router)
app.include_router(course.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    from db.database import init_db
    await init_db()
