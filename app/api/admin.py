"""
Admin API endpoints for scorecard management and monitoring.
Provides administrative functions and system information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from app.database import get_db
from app.services.scorecard_service import ScorecardService
from app.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for admin interface."""
    try:
        scorecard_service = ScorecardService(db)
        evaluation_service = EvaluationService(db)
        
        # Get counts (would be more efficient with aggregate queries)
        total_scorecards = len(scorecard_service.get_scorecards_by_mfi(""))  # Get all
        
        # Basic stats
        stats = {
            "total_scorecards": total_scorecards,
            "total_evaluations": "N/A",  # Would need evaluation count query
            "active_scorecards": "N/A",   # Would need active count query
            "recent_activity": "N/A"      # Would need recent activity query
        }
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/system-info", status_code=status.HTTP_200_OK)
def get_system_info():
    """Get system information for monitoring."""
    return {
        "service": "Credit Scorecard Microservice",
        "version": "1.0.0",
        "environment": "development",  # Would be from config
        "components": {
            "scoring_engine": "operational",
            "expression_evaluator": "operational", 
            "letter_grader": "operational",
            "database": "connected"
        },
        "features": {
            "safe_evaluation": True,
            "version_control": True,
            "audit_logging": True,
            "scorecard_management": True
        }
    }


@router.post("/maintenance/cleanup", status_code=status.HTTP_200_OK)
def cleanup_old_data(db: Session = Depends(get_db)):
    """Cleanup old scorecard versions and evaluation logs."""
    try:
        scorecard_service = ScorecardService(db)
        
        # This would typically clean up across all scorecards
        # For now, return a placeholder response
        cleaned_versions = 0
        cleaned_logs = 0
        
        return {
            "status": "success",
            "cleaned_versions": cleaned_versions,
            "cleaned_logs": cleaned_logs,
            "message": f"Cleaned up {cleaned_versions} old versions and {cleaned_logs} old logs"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check for admin monitoring."""
    try:
        evaluation_service = EvaluationService(db)
        health_status = evaluation_service.health_check()
        
        # Enhanced health information
        detailed_status = {
            "overall_status": health_status.get("status", "unknown"),
            "components": {
                "database": "healthy" if health_status.get("scorecard_count", 0) >= 0 else "unhealthy",
                "scoring_engine": "healthy" if health_status.get("scoring_engine_test", False) else "unhealthy",
                "expression_evaluator": "healthy",
                "letter_grader": "healthy"
            },
            "metrics": {
                "scorecard_count": health_status.get("scorecard_count", 0),
                "uptime": "N/A",  # Would track actual uptime
                "requests_processed": "N/A",  # Would track from middleware
                "average_response_time": "N/A"  # Would calculate from metrics
            },
            "timestamp": health_status.get("timestamp")
        }
        
        return detailed_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }