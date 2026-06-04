from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_active_user
from app.core.logging_config import logger
from app.database import get_db
from app.models.agent_analysis import AgentAnalysis
from app.models.user import User
from app.services.agent_service import smart_agent
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/agent", tags=["Agent"])


class AnalysisRequest(BaseModel):
    crop: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z_\- ]+$"
    )

    city: Optional[str] = Field(
        default="Delhi",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z_\- ]+$"
    )

    days: Optional[int] = Field(
        default=7,
        ge=1,
        le=180
    )


def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    return current_user


@router.post("/analyze")
async def analyze_crop(
    request: AnalysisRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    user_prefs = {
        "risk_tolerance": "medium"
    }

    try:
        analysis = smart_agent.analyze_crop(
            crop=request.crop,
            city=request.city,
            user_preferences=user_prefs,
            days_ahead=request.days,
            user_id=current_user.id,
        )

    except Exception as e:
        logger.error(
            f"Analysis failed for user {current_user.id}: {e}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to analyze crop",
        )

    if not isinstance(analysis, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid analysis response",
        )

    if "decision" not in analysis:
        raise HTTPException(
            status_code=500,
            detail="Analysis missing decision field",
        )

    return analysis


@router.get("/status")
async def get_agent_status(
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    try:
        total_analyses = (
            db.query(func.count(AgentAnalysis.id)).scalar() or 0
        )

        last_analysis = (
            db.query(AgentAnalysis)
            .order_by(AgentAnalysis.created_at.desc())
            .first()
        )

        last_run = (
            last_analysis.created_at.isoformat()
            if last_analysis
            else None
        )

        next_scheduled_run = None

        if scheduler_service.is_running:
            daily_job = scheduler_service.scheduler.get_job(
                "daily_monitoring"
            )

            if daily_job and daily_job.next_run_time:
                next_scheduled_run = (
                    daily_job.next_run_time.isoformat()
                )

        return {
            "agent": "healthy",
            "scheduler_running": scheduler_service.is_running,
            "last_run": last_run,
            "next_scheduled_run": next_scheduled_run,
            "total_analyses": total_analyses,
        }

    except Exception as e:
        logger.error(
            f"Failed fetching status: {e}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch status",
        )


@router.post("/trigger-monitoring")
async def trigger_monitoring(
    admin: Annotated[User, Depends(require_admin)],
):
    try:
        scheduler_service.run_now("daily_monitoring")

        return {
            "message": "Daily monitoring triggered successfully",
            "note": "Check logs for generated alerts",
        }

    except Exception as e:
        logger.error(
            f"Failed triggering monitoring: {e}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to trigger monitoring",
        )


@router.get("/health")
async def health_check(
    admin: Annotated[User, Depends(require_admin)],
):
    return {
        "agent": "healthy",
        "scheduler": (
            "running"
            if scheduler_service.is_running
            else "stopped"
        ),
    }


@router.get("/history")
async def get_analysis_history(
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
    limit: int = 10,
    crop: Optional[str] = None,
):
    limit = min(limit, 100)

    query = (
        db.query(AgentAnalysis)
        .order_by(AgentAnalysis.created_at.desc())
    )

    if crop:
        query = query.filter(
            AgentAnalysis.crop == crop
        )

    analyses = query.limit(limit).all()

    return {
        "total": len(analyses),
        "analyses": [a.to_dict() for a in analyses],
    }
