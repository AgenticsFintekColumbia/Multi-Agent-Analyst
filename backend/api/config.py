"""Configuration endpoint to expose default values."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/config")
async def get_config():
    """Get default configuration values."""
    return {
        "defaults": {
            "explainer": {
                "fund_window_days": 90,
                "news_window_days": 30,
                "technical_window_days": 90,  # Same as fund_window_days
            },
            "recommender": {
                "news_window_days": 30,
            },
        },
    }

