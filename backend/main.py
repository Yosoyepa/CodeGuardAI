"""
CodeGuard AI - Backend Entry Point
Multi-Agent Code Review System
"""
import uvicorn
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.core.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
