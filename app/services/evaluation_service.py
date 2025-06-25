"""
Service layer for credit evaluation operations.
Orchestrates scoring, logging, and result storage.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import time
import logging
from datetime import datetime

from app.models.evaluation import ScoreResult, EvaluationLog
from app.models.scorecard import ScorecardConfig, ScorecardVersion
from app.schemas.evaluation import EvaluationRequest
from app.core.scoring_engine import ScoringEngine
from app.services.scorecard_service import ScorecardService

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for credit evaluation operations."""
    
    def __init__(self, db: Session):
        """Initialize the service with database session."""
        self.db = db
        self.scoring_engine = ScoringEngine()
        self.scorecard_service = ScorecardService(db)
    
    def evaluate_applicant(self, request: EvaluationRequest) -> Dict[str, Any]:
        """
        Evaluate an applicant against a scorecard.
        
        Args:
            request: Evaluation request with applicant data and scorecard info
            
        Returns:
            Evaluation result with scores, grades, and audit information
        """
        start_time = time.time()
        
        try:
            # Get the scorecard
            scorecard = self.scorecard_service.get_scorecard_by_uuid(request.scorecard_uuid)
            if not scorecard:
                raise ValueError(f"Scorecard not found: {request.scorecard_uuid}")
            
            if not scorecard.is_active:
                raise ValueError(f"Scorecard is not active: {request.scorecard_uuid}")
            
            # Get the version to use
            if request.use_version:
                version = self.scorecard_service.get_version_by_id(request.use_version)
                if not version or version.scorecard_id != scorecard.id:
                    raise ValueError(f"Version not found or not associated with scorecard: {request.use_version}")
            else:
                version = self.scorecard_service.get_active_version(scorecard.id)
                if not version:
                    raise ValueError(f"No active version found for scorecard: {request.scorecard_uuid}")
            
            # Get scoring factors
            scoring_factors = self.scorecard_service.get_scoring_factors(version.id)
            
            if not scoring_factors:
                raise ValueError(f"No scoring factors found for version {version.id}")
            
            # Prepare scorecard configuration
            scorecard_config = {
                'id': scorecard.id,
                'name': scorecard.name,
                'min_score': scorecard.min_score,
                'max_score': scorecard.max_score,
                'passing_score': scorecard.passing_score
            }
            
            # Prepare scoring factors data
            factors_data = [
                {
                    'id': f.id,
                    'name': f.name,
                    'code': f.code,
                    'description': f.description,
                    'category': f.category,
                    'weight': f.weight,
                    'data_type': f.data_type,
                    'rules': f.rules,
                    'is_required': f.is_required,
                    'min_value': f.min_value,
                    'max_value': f.max_value,
                    'default_points': f.default_points
                }
                for f in scoring_factors
            ]
            
            # Prepare request context
            request_context = {
                'request_id': request.request_id,
                'user_id': request.user_id,
                'source_system': request.source_system,
                'applicant_id': request.applicant_id,
                'version_id': version.id,
                'version_number': version.version_number
            }
            
            # Perform the evaluation
            evaluation_result = self.scoring_engine.evaluate_applicant(
                scorecard_config, factors_data, request.applicant_data, request_context
            )
            
            # Store the result
            score_result = self._store_evaluation_result(
                scorecard, version, request, evaluation_result
            )
            
            # Log the evaluation
            self._log_evaluation(score_result, request, evaluation_result)
            
            # Prepare response
            response = {
                'id': score_result.id,
                'uuid': score_result.uuid,
                'scorecard_id': scorecard.id,
                'version_id': version.id,
                'applicant_id': request.applicant_id,
                'total_score': evaluation_result['total_score'],
                'letter_grade': evaluation_result['letter_grade'],
                'eligibility': evaluation_result['eligibility'],
                'factor_scores': evaluation_result['factor_scores'],
                'breakdown': evaluation_result['breakdown'],
                'processing_time_ms': evaluation_result['processing_time_ms'],
                'data_completeness': evaluation_result['data_completeness'],
                'confidence_score': evaluation_result['confidence_score'],
                'created_at': score_result.created_at
            }
            
            logger.info(f"Evaluation completed for applicant {request.applicant_id}: "
                       f"score={evaluation_result['total_score']}, "
                       f"grade={evaluation_result['letter_grade']}, "
                       f"eligible={evaluation_result['eligibility']}")
            
            return response
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Evaluation failed for applicant {request.applicant_id}: {e}")
            
                         # Store error result if we have enough information
             if 'scorecard' in locals() and 'version' in locals():
                 try:
                     error_result = {
                         'total_score': getattr(scorecard, 'min_score', 300),
                         'letter_grade': 'D',
                         'eligibility': False,
                         'factor_scores': [],
                         'breakdown': None,
                         'processing_time_ms': processing_time_ms,
                         'data_completeness': 0.0,
                         'confidence_score': 0.0,
                         'warnings': [f"Evaluation error: {str(e)}"]
                     }
                     
                     score_result = self._store_evaluation_result(
                         scorecard, version, request, error_result
                     )
                     
                     self._log_evaluation_error(score_result, request, str(e))
                     
                     return {
                         'id': score_result.id,
                         'uuid': score_result.uuid,
                         'scorecard_id': getattr(scorecard, 'id', 0),
                         'version_id': getattr(version, 'id', 0),
                         'applicant_id': request.applicant_id,
                         'total_score': error_result['total_score'],
                         'letter_grade': error_result['letter_grade'],
                         'eligibility': error_result['eligibility'],
                         'factor_scores': error_result['factor_scores'],
                         'breakdown': error_result['breakdown'],
                         'processing_time_ms': error_result['processing_time_ms'],
                         'data_completeness': error_result['data_completeness'],
                         'confidence_score': error_result['confidence_score'],
                         'created_at': datetime.utcnow()
                     }
                 except Exception as store_error:
                     logger.error(f"Failed to store error result: {store_error}")
            
            # Re-raise the original exception
            raise
    
    def _store_evaluation_result(self, scorecard: ScorecardConfig, 
                               version: ScorecardVersion,
                               request: EvaluationRequest,
                               evaluation_result: Dict[str, Any]) -> ScoreResult:
        """Store evaluation result in database."""
        try:
            # Convert breakdown to dict if it's a Pydantic model
            breakdown_dict = evaluation_result['breakdown']
            if hasattr(breakdown_dict, 'dict'):
                breakdown_dict = breakdown_dict.dict()
            
            score_result = ScoreResult(
                scorecard_id=scorecard.id,
                version_id=version.id,
                applicant_id=request.applicant_id,
                total_score=evaluation_result['total_score'],
                letter_grade=evaluation_result['letter_grade'],
                eligibility=evaluation_result['eligibility'],
                factor_scores=evaluation_result['factor_scores'],
                breakdown=breakdown_dict,
                processing_time_ms=evaluation_result['processing_time_ms'],
                data_completeness=evaluation_result['data_completeness'],
                confidence_score=evaluation_result['confidence_score']
            )
            
            self.db.add(score_result)
            self.db.commit()
            self.db.refresh(score_result)
            
            return score_result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing evaluation result: {e}")
            raise
    
    def _log_evaluation(self, score_result: ScoreResult,
                       request: EvaluationRequest,
                       evaluation_result: Dict[str, Any]):
        """Log evaluation details for audit trail."""
        try:
            evaluation_context = evaluation_result.get('evaluation_context', {})
            warnings = evaluation_result.get('warnings', [])
            
            eval_log = EvaluationLog(
                score_result_id=score_result.id,
                request_id=request.request_id,
                user_id=request.user_id,
                source_system=request.source_system,
                input_data_hash=evaluation_context.get('data_hash'),
                data_sources=['applicant_data'],  # Could be expanded
                evaluation_steps=evaluation_context.get('evaluation_steps', []),
                warnings=warnings,
                errors=[],
                processing_time_ms=evaluation_result['processing_time_ms'],
                memory_usage_mb=0.0  # Could be tracked if needed
            )
            
            self.db.add(eval_log)
            self.db.commit()
            
        except Exception as e:
            # Don't fail the evaluation if logging fails
            logger.error(f"Error logging evaluation: {e}")
    
    def _log_evaluation_error(self, score_result: ScoreResult,
                            request: EvaluationRequest,
                            error_message: str):
        """Log evaluation error for audit trail."""
        try:
            eval_log = EvaluationLog(
                score_result_id=score_result.id,
                request_id=request.request_id,
                user_id=request.user_id,
                source_system=request.source_system,
                input_data_hash=None,
                data_sources=['applicant_data'],
                evaluation_steps=[],
                warnings=[],
                errors=[error_message],
                processing_time_ms=score_result.processing_time_ms or 0,
                memory_usage_mb=0.0
            )
            
            self.db.add(eval_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging evaluation error: {e}")
    
    def get_evaluation_result(self, result_uuid: str) -> Optional[ScoreResult]:
        """Get evaluation result by UUID."""
        return self.db.query(ScoreResult).filter(
            ScoreResult.uuid == result_uuid
        ).first()
    
    def get_evaluation_results_by_applicant(self, applicant_id: str) -> list:
        """Get all evaluation results for an applicant."""
        return self.db.query(ScoreResult).filter(
            ScoreResult.applicant_id == applicant_id
        ).order_by(ScoreResult.created_at.desc()).all()
    
    def get_evaluation_logs(self, result_id: int) -> list:
        """Get evaluation logs for a result."""
        return self.db.query(EvaluationLog).filter(
            EvaluationLog.score_result_id == result_id
        ).all()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the evaluation service.
        
        Returns:
            Health status information
        """
        try:
            # Check database connectivity
            scorecard_count = self.db.query(ScorecardConfig).count()
            
            # Check scoring engine
            test_data = {'test_field': 100}
            test_config = {
                'id': 1,
                'name': 'Test',
                'min_score': 300,
                'max_score': 850,
                'passing_score': 600
            }
            test_factors = [{
                'name': 'Test Factor',
                'code': 'test_field',
                'weight': 1.0,
                'rules': {'expression': 'test_field'},
                'is_required': True
            }]
            
            test_result = self.scoring_engine.evaluate_applicant(
                test_config, test_factors, test_data
            )
            
            return {
                'status': 'healthy',
                'scorecard_count': scorecard_count,
                'scoring_engine_test': test_result.get('total_score', 0) > 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }