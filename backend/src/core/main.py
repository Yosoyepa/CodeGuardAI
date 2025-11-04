"""
FastAPI Application Factory
Clean Architecture Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.presentation.api import analysis_controller, review_controller

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="CodeGuard AI",
        description="Multi-Agent Code Review System with AI Explanations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(analysis_controller.router, prefix="/api/v1", tags=["analysis"])
    app.include_router(review_controller.router, prefix="/api/v1", tags=["reviews"])
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
    
    return app

app = create_app()
