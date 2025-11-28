"""Recommender endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
import uuid
import pandas as pd
from backend.datasets import get_datasets
from backend.utils import split_manager_and_analysts, parse_analyst_reports, extract_final_rating
from src.recommender import run_multi_analyst_recommendation

router = APIRouter()

_jobs: Dict[str, Dict] = {}


class RecommenderRequest(BaseModel):
    rec_index: int
    news_window_days: int = 30
    ticker: str = "N/A"
    company: str = "N/A"


def run_recommender_task(
    job_id: str,
    rec_index: int,
    news_window_days: int,
    ticker: str,
    company: str,
):
    """Background task to run the recommender."""
    try:
        ibes, fund, news = get_datasets()
        
        rec = ibes.iloc[rec_index]
        cusip = rec.get("cusip")
        rec_date = rec.get("anndats")
        
        if pd.isna(cusip) or pd.isna(rec_date):
            raise ValueError("CUSIP or recommendation date is missing")
        
        reco_md = run_multi_analyst_recommendation(
            cusip=str(cusip),
            rec_date=rec_date,
            fund_df=fund,
            news_df=news,
            news_window_days=news_window_days,
            ticker=ticker,
            company=company,
        )
        
        manager_md, analysts_md = split_manager_and_analysts(reco_md)
        final_rating = extract_final_rating(manager_md or reco_md)
        
        result = {
            "manager_report": manager_md or reco_md,
            "analyst_reports": parse_analyst_reports(analysts_md) if analysts_md else {
                "fundamental": "",
                "technical": "",
                "news": "",
            },
            "full_markdown": reco_md,
            "final_rating": final_rating,
        }
        
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = result
        _jobs[job_id]["error"] = None
        
    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["result"] = None
        _jobs[job_id]["error"] = str(e)


@router.post("/run")
async def run_recommender(request: RecommenderRequest, background_tasks: BackgroundTasks):
    """Start the recommender analysis."""
    job_id = str(uuid.uuid4())
    
    _jobs[job_id] = {
        "status": "processing",
        "result": None,
        "error": None,
    }
    
    background_tasks.add_task(
        run_recommender_task,
        job_id=job_id,
        rec_index=request.rec_index,
        news_window_days=request.news_window_days,
        ticker=request.ticker,
        company=request.company,
    )
    
    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Recommender team is running...",
    }


@router.get("/status/{job_id}")
async def get_recommender_status(job_id: str):
    """Get the status of a recommender job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _jobs[job_id]
    return {
        "status": job["status"],
        "result": job["result"],
        "error": job["error"],
    }

