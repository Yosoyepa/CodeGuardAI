"""
CodeGuard AI - Backend Entry Point
FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import init_db
from .routers import analysis

# Create FastAPI app
app = FastAPI(
    title="CodeGuard AI",
    description="Multi-Agent Code Review System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0", "service": "CodeGuard AI Backend"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CodeGuard AI - Multi-Agent Code Review System",
        "docs": "/docs",
        "health": "/health",
    }


@app.on_event("startup")
def on_startup():
    # ensure DB tables exist for local development
    init_db()
    # include routers


# Include routers at import time so endpoints exist when TestClient imports `app`
app.include_router(analysis.router)
from .routers import reviews as reviews_router

app.include_router(reviews_router.router)
# For local development and tests, ensure DB tables exist on import
try:
    init_db()
except Exception:
    # don't fail import if DB init cannot run in some environments
    pass
