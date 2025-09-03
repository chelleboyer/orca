"""
API v1 endpoints
"""
from fastapi import APIRouter
from . import auth, dashboard, projects, invitations, objects, relationships, roles, ctas, attributes, object_map, prioritization

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(projects.router)
api_router.include_router(invitations.router)
api_router.include_router(objects.router)
api_router.include_router(relationships.router)
api_router.include_router(roles.router)
api_router.include_router(ctas.router)
api_router.include_router(attributes.router)
api_router.include_router(object_map.router)
api_router.include_router(prioritization.router)
