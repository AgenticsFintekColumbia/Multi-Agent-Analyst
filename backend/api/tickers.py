"""Ticker endpoints."""
from fastapi import APIRouter
from backend.datasets import get_datasets

router = APIRouter()


@router.get("/tickers")
async def get_tickers():
    """Get list of available tickers."""
    ibes, _, _ = get_datasets()
    
    # Use oftic when available, fallback to ticker
    ibes = ibes.copy()
    ibes["display_ticker"] = ibes["oftic"].fillna(ibes["ticker"])
    tickers = sorted(ibes["display_ticker"].dropna().unique().tolist())
    
    default = "AMZN" if "AMZN" in tickers else (tickers[0] if tickers else None)
    
    return {
        "tickers": tickers,
        "default": default,
    }

