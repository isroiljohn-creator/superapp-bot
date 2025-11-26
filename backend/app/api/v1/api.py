from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, users, plans, payments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(plans.router, prefix="/ai", tags=["ai"])
api_router.include_router(payments.router, prefix="/pay", tags=["payments"])
