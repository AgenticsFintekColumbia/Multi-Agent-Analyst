"""Health check endpoint."""
from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """Check API health."""
    return {
        "status": "healthy",
        "datasets_loaded": True,
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
    }

