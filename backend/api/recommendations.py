"""Recommendation endpoints."""
from fastapi import APIRouter, Query, HTTPException
from backend.datasets import get_datasets
import pandas as pd

router = APIRouter()


@router.get("/recommendations")
async def get_recommendations(
    ticker: str = Query(..., description="Stock ticker"),
    mode: str = Query("explainer", description="explainer or recommender"),
):
    """Get recommendations for a specific ticker."""
    ibes, _, _ = get_datasets()
    
    # Filter by ticker
    filtered = ibes[
        (ibes["oftic"] == ticker) | (ibes["ticker"] == ticker)
    ].copy()
    
    if filtered.empty:
        return {"recommendations": []}
    
    recommendations = []
    for idx, row in filtered.iterrows():
        rec = {
            "index": int(idx),
            "date": row["anndats"].isoformat() if pd.notna(row["anndats"]) else None,
            "analyst": str(row.get("analyst", "N/A")),
            "ticker": str(row.get("ticker", "N/A")),
            "company": str(row.get("cname", "N/A")),
            "cusip": str(row.get("cusip", "N/A")),
        }
        
        # Only include rating for explainer mode
        if mode == "explainer":
            rec["rating"] = str(row.get("etext", "N/A"))
        else:
            rec["rating"] = None  # Hidden for recommender
        
        recommendations.append(rec)
    
    return {"recommendations": recommendations}

