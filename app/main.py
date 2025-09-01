"""
OOUX ORCA Project Builder
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import engine, Base

# Import routers
from app.api.v1 import auth
from app.api.v1 import projects
# from app.api.v1 import objects, relationships, ctas, attributes, exports
# from app.api import websocket

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A collaborative web application for Object-Oriented UX methodology",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "version": settings.APP_VERSION}

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
# app.include_router(objects.router, prefix="/api/v1/objects", tags=["objects"])
# app.include_router(relationships.router, prefix="/api/v1/relationships", tags=["relationships"])
# app.include_router(ctas.router, prefix="/api/v1/ctas", tags=["ctas"])
# app.include_router(attributes.router, prefix="/api/v1/attributes", tags=["attributes"])
# app.include_router(exports.router, prefix="/api/v1/exports", tags=["exports"])
# app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    # Create database tables (in development)
    # In production, use Alembic migrations
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
