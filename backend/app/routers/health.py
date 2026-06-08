
from fastapi import APIRouter, status, Depends, HTTPException
from typing import Dict, Any
from app.database import get_pool_status
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.core.dependencies import verify_admin

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    
    return {
        "status": "healthy",
        "service": "AgriAI Platform API"
    }


@router.get("/health/db-pool")
async def database_pool_health(admin: User = Depends(verify_admin)):
    
    pool_status = get_pool_status()
    
    # Determine health based on pool type
    if pool_status.get("type") == "sqlite":
        return {
            "status": "healthy",
            "message": "SQLite database (no pooling)",
            "pool": pool_status
        }
    
    # Check pool utilization for pooled databases
    utilization = pool_status.get("utilization_percent", 0)
    checked_out = pool_status.get("checked_out", 0)
    total = pool_status.get("total_connections", 30)
    
    # Determine health status
    if utilization > 90:
        health_status = "critical"
        message = "Pool utilization critical - consider scaling"
    elif utilization > 75:
        health_status = "warning"
        message = "Pool utilization high"
    else:
        health_status = "healthy"
        message = "Pool operating normally"
    
    # Generate recommendations
    recommendations = []
    if utilization > 80:
        recommendations.append("Consider increasing pool_size or max_overflow")
    if pool_status.get("overflow", 0) >= pool_status.get("max_connections", 30) - pool_status.get("size", 10):
        recommendations.append("All overflow connections in use - increase max_overflow")
    if checked_out == 0:
        recommendations.append("No active connections - pool may be idle")
    
    return {
        "status": health_status,
        "message": message,
        "pool": pool_status,
        "recommendations": recommendations if recommendations else ["No optimization needed"]
    }


@router.get("/health/ready")
async def readiness_check():
    
    try:
        # Check if we can get pool status (implies DB is accessible)
        pool_status = get_pool_status()
        
        return {
            "status": "ready",
            "checks": {
                "database": "ok"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "checks": {
                "database": f"error: {str(e)}"
            }
        }


@router.get("/health/live")
async def liveness_check():
    
    return {
        "status": "alive"
    }
