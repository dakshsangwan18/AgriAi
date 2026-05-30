
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Annotated, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.agent_service import smart_agent
from app.services.scheduler_service import scheduler_service
from app.models.agent_analysis import AgentAnalysis
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.logging_config import logger

router = APIRouter()


class AnalysisRequest(BaseModel):
    crop: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z_\- ]+$")
    city: Optional[str] = Field("Delhi", min_length=1, max_length=100, pattern=r"^[a-zA-Z_\- ]+$")
    days: Optional[int] = Field(7, ge=1, le=180)


def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


@router.post("/analyze")
async def analyze_crop(
    request: AnalysisRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    user_prefs = {
        'risk_tolerance': 'medium'
    }

    try:
        analysis = smart_agent.analyze_crop(
            crop=request.crop,
            city=request.city,
            user_preferences=user_prefs,
            days_ahead=request.days
        )
    except Exception as e:
        logger.error(f"Analysis failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze crop")

    if not isinstance(analysis, dict) or "decision" not in analysis:
        raise HTTPException(status_code=500, detail="Analysis produced invalid result")

    return analysis


@router.get("/status")
async def agent_status(
    db: Session = Depends(get_db),
    admin: Annotated[User, Depends(require_admin)]
):
    # Get total analyses count
    total_analyses = db.query(func.count(AgentAnalysis.id)).scalar() or 0
    
    # Get last analysis time
    last_analysis = db.query(AgentAnalysis).order_by(AgentAnalysis.created_at.desc()).first()
    last_run = last_analysis.created_at.isoformat() if last_analysis else None
    
    # Get next scheduled run from APScheduler
    next_scheduled_run = None
    if scheduler_service.is_running:
        daily_monitoring_job = scheduler_service.scheduler.get_job('daily_monitoring')
        if daily_monitoring_job and daily_monitoring_job.next_run_time:
            next_scheduled_run = daily_monitoring_job.next_run_time.isoformat()
    
    return {
        "is_running": scheduler_service.is_running,
        "last_run": last_run,
        "next_scheduled_run": next_scheduled_run,
        "total_analyses": total_analyses
    }


@router.post("/trigger-monitoring")
async def trigger_monitoring(
    admin: Annotated[User, Depends(require_admin)]
):
    scheduler_service.run_now('daily_monitoring')
    
    return {
        "message": "Daily monitoring triggered successfully",
        "note": "Check console for alerts generated"
    }


@router.get("/health")
async def health_check(
    admin: Annotated[User, Depends(require_admin)]
):
    return {
        "agent": "healthy",
        "scheduler": "running" if scheduler_service.is_running else "stopped",
        "timestamp": "2025-10-30T00:00:00"
    }


@router.get("/history")
async def get_analysis_history(
    limit: int = 10,
    crop: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Annotated[User, Depends(require_admin)]
):
    limit = min(limit, 100)  # Cap at 100
    
    query = db.query(AgentAnalysis).order_by(AgentAnalysis.created_at.desc())
    
    if crop:
        query = query.filter(AgentAnalysis.crop == crop)
    
    analyses = query.limit(limit).all()
    
    return {
        "total": len(analyses),
        "analyses": [a.to_dict() for a in analyses]
    }
