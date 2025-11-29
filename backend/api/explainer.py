"""Explainer endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
import uuid
from backend.datasets import get_datasets
from backend.utils import split_manager_and_analysts, parse_analyst_reports
from src.explainer import run_multi_analyst_explainer

router = APIRouter()

# In-memory job storage (use Redis/database in production)
_jobs: Dict[str, Dict] = {}


class ExplainerRequest(BaseModel):
    rec_index: int
    fund_window_days: int = 90
    news_window_days: int = 30


def run_explainer_task(job_id: str, rec_index: int, fund_window_days: int, news_window_days: int):
    """Background task to run the explainer."""
    try:
        ibes, fund, news = get_datasets()
        
        explanation_md = run_multi_analyst_explainer(
            ibes_df=ibes,
            fund_df=fund,
            news_df=news,
            rec_index=rec_index,
            fund_window_days=fund_window_days,
            news_window_days=news_window_days,
        )
        
        # Parse the results
        manager_md, analysts_md = split_manager_and_analysts(explanation_md)
        
        # Debug logging
        print(f"\n[DEBUG] Full markdown length: {len(explanation_md)}")
        print(f"[DEBUG] Manager MD length: {len(manager_md) if manager_md else 0}")
        print(f"[DEBUG] Analysts MD length: {len(analysts_md) if analysts_md else 0}")
        
        analyst_reports = parse_analyst_reports(analysts_md) if analysts_md else {
            "fundamental": "",
            "technical": "",
            "news": "",
        }
        
        print(f"[DEBUG] Parsed reports - Fundamental: {len(analyst_reports['fundamental'])} chars")
        print(f"[DEBUG] Parsed reports - Technical: {len(analyst_reports['technical'])} chars")
        print(f"[DEBUG] Parsed reports - News: {len(analyst_reports['news'])} chars")
        
        result = {
            "manager_report": manager_md or explanation_md,
            "analyst_reports": analyst_reports,
            "full_markdown": explanation_md,
        }
        
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = result
        _jobs[job_id]["error"] = None
        
    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["result"] = None
        _jobs[job_id]["error"] = str(e)


@router.post("/run")
async def run_explainer(request: ExplainerRequest, background_tasks: BackgroundTasks):
    """Start the explainer analysis."""
    job_id = str(uuid.uuid4())
    
    _jobs[job_id] = {
        "status": "processing",
        "result": None,
        "error": None,
    }
    
    background_tasks.add_task(
        run_explainer_task,
        job_id=job_id,
        rec_index=request.rec_index,
        fund_window_days=request.fund_window_days,
        news_window_days=request.news_window_days,
    )
    
    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Explainer team is running...",
    }


@router.get("/status/{job_id}")
async def get_explainer_status(job_id: str):
    """Get the status of an explainer job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _jobs[job_id]
    return {
        "status": job["status"],
        "result": job["result"],
        "error": job["error"],
    }

