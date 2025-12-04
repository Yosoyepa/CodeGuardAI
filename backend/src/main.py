"""
CodeGuard AI - Backend Entry Point
FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.settings import settings
from src.routers.analysis import router as analysis_router
from src.routers.auth import router as auth_router
from src.routers.findings import router as findings_router


def get_allowed_origins() -> list[str]:
    """
    Parse ALLOWED_ORIGINS and expand wildcards for Vercel preview URLs.

    Supports:
    - Exact URLs: https://codeguard-unal.vercel.app
    - Wildcards: https://*.vercel.app (converted to regex pattern)
    """
    origins = settings.allowed_origins_list

    # For production, we return exact origins
    # Wildcard patterns like *.vercel.app need special handling
    expanded = []
    for origin in origins:
        if "*" not in origin:
            expanded.append(origin)
        # Note: CORSMiddleware doesn't support wildcards directly
        # For Vercel previews, add common patterns or use allow_origin_regex

    return expanded


# Create FastAPI app
app = FastAPI(
    title="CodeGuard AI",
    description="Multi-Agent Code Review System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration for Vercel + Local Development
# Build allow_origin_regex for Vercel preview deployments
vercel_regex = r"https://.*\.vercel\.app"
localhost_regex = r"http://localhost:\d+"

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=f"({vercel_regex}|{localhost_regex})",
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
