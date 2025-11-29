"""
FastAPI backend for Agentic Recommendation Explainer & Recommender
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing functions
from src.explainer import run_multi_analyst_explainer
from src.recommender import run_multi_analyst_recommendation
from backend.datasets import initialize_datasets, clear_datasets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load datasets once at startup."""
    initialize_datasets(data_dir="data/")
    yield
    clear_datasets()


app = FastAPI(
    title="Agentic Recommendation API",
    description="API for multi-agent stock recommendation explainer and recommender",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:5174",
        "http://localhost:8080",   # Vite alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from backend.api import health, tickers, recommendations, explainer, recommender, config

app.include_router(health.router)
app.include_router(config.router, tags=["config"])
app.include_router(tickers.router, prefix="/api", tags=["tickers"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(explainer.router, prefix="/api/explainer", tags=["explainer"])
app.include_router(recommender.router, prefix="/api/recommender", tags=["recommender"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

