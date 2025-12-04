"""
CodeGuard AI - Backend Entry Point
FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.analysis import router as analysis_router
from src.routers.auth import router as auth_router
from src.routers.findings import router as findings_router

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

app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(findings_router)


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
