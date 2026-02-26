"""FastAPI application — REST API for Mini App."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routers import user, payment, referral, course, admin

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
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    from db.database import init_db
    await init_db()

# Provide static files for the React apps
# We first check if the folder exists to avoid startup errors
admin_dist = os.path.join(os.path.dirname(__file__), "static", "admin")
if os.path.exists(admin_dist):
    app.mount("/admin", StaticFiles(directory=admin_dist, html=True), name="admin_dashboard")
    
# Fallback for React Router (if a user refreshes a subpath)
@app.exception_handler(404)
async def custom_404_handler(request, __):
    if request.url.path.startswith("/admin/") and os.path.exists(os.path.join(admin_dist, "index.html")):
        return FileResponse(os.path.join(admin_dist, "index.html"))
    return {"detail": "Not Found"}
