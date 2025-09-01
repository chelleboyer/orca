"""
API v1 endpoints
"""
from fastapi import APIRouter
from . import auth, dashboard, projects, invitations, objects

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(projects.router)
api_router.include_router(invitations.router)
api_router.include_router(objects.router)
