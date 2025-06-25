"""
API endpoints for credit evaluation.
Provides scoring and result retrieval functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.services.evaluation_service import EvaluationService
from app.schemas.evaluation import EvaluationRequest, ScoreResultResponse, EvaluationLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/evaluate", response_model=ScoreResultResponse, status_code=status.HTTP_200_OK)
def evaluate_applicant(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate an applicant against a scorecard.
    
    This is the main endpoint for credit scoring. It processes applicant data
    against a configured scorecard and returns scores, grades, and detailed breakdowns.
    """
    try:
        service = EvaluationService(db)
        result = service.evaluate_applicant(request)
        return result
    except ValueError as e:
        # Client errors (invalid input, scorecard not found, etc.)
        logger.warning(f"Evaluation request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Server errors
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal evaluation error occurred"
        )


@router.get("/results/{result_uuid}", response_model=ScoreResultResponse)
def get_evaluation_result(result_uuid: str, db: Session = Depends(get_db)):
    """Get evaluation result by UUID."""
    service = EvaluationService(db)
    result = service.get_evaluation_result(result_uuid)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation result not found: {result_uuid}"
        )
    
    return result


@router.get("/applicants/{applicant_id}/results", response_model=List[ScoreResultResponse])
def get_applicant_results(applicant_id: str, db: Session = Depends(get_db)):
    """Get all evaluation results for an applicant."""
    service = EvaluationService(db)
    results = service.get_evaluation_results_by_applicant(applicant_id)
    return results


@router.get("/results/{result_id}/logs", response_model=List[EvaluationLogResponse])
def get_evaluation_logs(result_id: int, db: Session = Depends(get_db)):
    """Get evaluation logs for a result (for audit purposes)."""
    service = EvaluationService(db)
    logs = service.get_evaluation_logs(result_id)
    return logs


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the evaluation service.
    
    This endpoint can be used by load balancers and monitoring systems
    to verify that the service is operational.
    """
    try:
        service = EvaluationService(db)
        health_status = service.health_check()
        
        if health_status.get('status') == 'healthy':
            return health_status
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )