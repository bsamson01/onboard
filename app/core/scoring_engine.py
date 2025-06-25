"""
Main scoring engine that orchestrates the complete credit evaluation process.
Combines expression evaluation, letter grading, and audit logging.
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import hashlib
import json
import logging
from datetime import datetime

from .expression_evaluator import SafeExpressionEvaluator
from .letter_grader import LetterGrader
from app.schemas.evaluation import FactorScore, ScoreBreakdown

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Main scoring engine for credit evaluation.
    Processes applicant data against scorecard configurations to generate scores.
    """
    
    def __init__(self):
        """Initialize the scoring engine."""
        self.expression_evaluator = SafeExpressionEvaluator()
        self.letter_grader = LetterGrader()
    
    def evaluate_applicant(self, 
                         scorecard_config: Dict[str, Any],
                         scoring_factors: List[Dict[str, Any]],
                         applicant_data: Dict[str, Any],
                         request_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate an applicant against a scorecard configuration.
        
        Args:
            scorecard_config: The scorecard configuration
            scoring_factors: List of scoring factors with rules
            applicant_data: The applicant's data
            request_context: Additional request context for logging
            
        Returns:
            Complete evaluation result with scores, grades, and audit information
        """
        start_time = time.time()
        
        try:
            # Initialize evaluation context
            evaluation_context = self._initialize_evaluation_context(
                scorecard_config, applicant_data, request_context
            )
            
            # Evaluate each scoring factor
            factor_results = []
            total_weighted_score = 0
            total_weighted_max = 0
            warnings = []
            
            for factor in scoring_factors:
                factor_result = self._evaluate_factor(factor, applicant_data)
                factor_results.append(factor_result)
                
                # Calculate weighted contribution
                weight = factor.get('weight', 1.0)
                total_weighted_score += factor_result['points'] * weight
                total_weighted_max += factor_result['max_points'] * weight
                
                # Collect warnings
                warnings.extend(factor_result.get('warnings', []))
            
            # Normalize score to scorecard range
            min_score = scorecard_config.get('min_score', 300)
            max_score = scorecard_config.get('max_score', 850)
            
            normalized_score = self._normalize_score(
                total_weighted_score, total_weighted_max, min_score, max_score
            )
            
            # Generate letter grade
            letter_grade = self.letter_grader.get_letter_grade(normalized_score)
            
            # Determine eligibility
            passing_score = scorecard_config.get('passing_score', 600)
            eligibility = normalized_score >= passing_score
            
            # Calculate data completeness
            data_completeness = self._calculate_data_completeness(
                scoring_factors, applicant_data
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                factor_results, data_completeness, warnings
            )
            
            # Create detailed breakdown
            breakdown = self._create_score_breakdown(
                normalized_score, max_score, letter_grade, eligibility,
                factor_results, scorecard_config, warnings
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create evaluation result
            result = {
                'total_score': normalized_score,
                'letter_grade': letter_grade,
                'eligibility': eligibility,
                'factor_scores': [self._format_factor_score(fr) for fr in factor_results],
                'breakdown': breakdown,
                'processing_time_ms': processing_time_ms,
                'data_completeness': data_completeness,
                'confidence_score': confidence_score,
                'evaluation_context': evaluation_context,
                'warnings': warnings
            }
            
            logger.info(f"Evaluation completed: score={normalized_score}, grade={letter_grade}, eligible={eligibility}")
            return result
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Evaluation failed: {e}")
            
            # Return error result
            return {
                'total_score': scorecard_config.get('min_score', 300),
                'letter_grade': 'D',
                'eligibility': False,
                'factor_scores': [],
                'breakdown': self._create_error_breakdown(str(e)),
                'processing_time_ms': processing_time_ms,
                'data_completeness': 0.0,
                'confidence_score': 0.0,
                'evaluation_context': {},
                'warnings': [f"Evaluation error: {e}"]
            }
    
    def _initialize_evaluation_context(self, 
                                     scorecard_config: Dict[str, Any],
                                     applicant_data: Dict[str, Any],
                                     request_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize evaluation context for audit and debugging."""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'scorecard_id': scorecard_config.get('id'),
            'scorecard_name': scorecard_config.get('name'),
            'data_hash': self._hash_data(applicant_data),
            'evaluation_steps': []
        }
        
        if request_context:
            context.update(request_context)
        
        return context
    
    def _evaluate_factor(self, factor: Dict[str, Any], applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single scoring factor."""
        factor_code = factor.get('code', 'unknown')
        factor_name = factor.get('name', factor_code)
        
        logger.debug(f"Evaluating factor: {factor_code}")
        
        try:
            # Get scoring rules
            rules = factor.get('rules', {})
            
            # Evaluate the rules
            rule_result = self.expression_evaluator.get_score_for_rules(rules, applicant_data)
            
            # Enhance with factor metadata
            result = {
                'factor_code': factor_code,
                'factor_name': factor_name,
                'category': factor.get('category', 'General'),
                'weight': factor.get('weight', 1.0),
                'points': rule_result['points'],
                'max_points': rule_result['max_points'],
                'reasoning': rule_result['reasoning'],
                'warnings': rule_result['warnings'],
                'data_type': factor.get('data_type', 'numeric'),
                'is_required': factor.get('is_required', True)
            }
            
            # Add actual value if available
            if factor_code in applicant_data:
                result['value'] = applicant_data[factor_code]
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating factor {factor_code}: {e}")
            return {
                'factor_code': factor_code,
                'factor_name': factor_name,
                'category': factor.get('category', 'General'),
                'weight': factor.get('weight', 1.0),
                'points': 0,
                'max_points': 100,
                'reasoning': [f"Evaluation failed: {e}"],
                'warnings': [f"Factor evaluation error: {e}"],
                'data_type': factor.get('data_type', 'numeric'),
                'is_required': factor.get('is_required', True)
            }
    
    def _normalize_score(self, weighted_score: float, weighted_max: float, 
                        min_score: int, max_score: int) -> int:
        """Normalize weighted score to scorecard range."""
        if weighted_max == 0:
            return min_score
        
        # Calculate percentage of maximum possible score
        percentage = weighted_score / weighted_max
        
        # Map to scorecard range
        score_range = max_score - min_score
        normalized = min_score + (percentage * score_range)
        
        # Clamp to valid range
        return max(min_score, min(max_score, int(normalized)))
    
    def _calculate_data_completeness(self, scoring_factors: List[Dict[str, Any]], 
                                   applicant_data: Dict[str, Any]) -> float:
        """Calculate percentage of required data that was provided."""
        required_fields = [
            factor.get('code') for factor in scoring_factors
            if factor.get('is_required', True)
        ]
        
        if not required_fields:
            return 1.0
        
        available_fields = [
            field for field in required_fields
            if field in applicant_data and applicant_data[field] is not None
        ]
        
        return len(available_fields) / len(required_fields)
    
    def _calculate_confidence_score(self, factor_results: List[Dict[str, Any]], 
                                  data_completeness: float, warnings: List[str]) -> float:
        """Calculate confidence in the evaluation result."""
        base_confidence = data_completeness
        
        # Reduce confidence for warnings
        warning_penalty = min(0.1 * len(warnings), 0.5)
        
        # Reduce confidence for factors with low data quality
        data_quality_penalty = 0
        for result in factor_results:
            if result.get('warnings'):
                data_quality_penalty += 0.05
        
        confidence = base_confidence - warning_penalty - data_quality_penalty
        return max(0.0, min(1.0, confidence))
    
    def _create_score_breakdown(self, total_score: int, max_score: int, 
                              letter_grade: str, eligibility: bool,
                              factor_results: List[Dict[str, Any]],
                              scorecard_config: Dict[str, Any],
                              warnings: List[str]) -> ScoreBreakdown:
        """Create detailed score breakdown."""
        factor_scores = []
        
        for result in factor_results:
            factor_score = FactorScore(
                factor_code=result['factor_code'],
                factor_name=result['factor_name'],
                points=result['points'],
                max_points=result['max_points'],
                value=result.get('value', 'N/A'),
                reasoning=' | '.join(result['reasoning']),
                weight=result['weight']
            )
            factor_scores.append(factor_score)
        
        # Generate summary
        summary = self._generate_summary(total_score, letter_grade, eligibility, scorecard_config)
        
        return ScoreBreakdown(
            total_score=total_score,
            max_possible_score=max_score,
            letter_grade=letter_grade,
            eligibility=eligibility,
            factor_scores=factor_scores,
            summary=summary,
            warnings=warnings
        )
    
    def _create_error_breakdown(self, error_message: str) -> ScoreBreakdown:
        """Create breakdown for error cases."""
        return ScoreBreakdown(
            total_score=0,
            max_possible_score=850,
            letter_grade='D',
            eligibility=False,
            factor_scores=[],
            summary=f"Evaluation failed: {error_message}",
            warnings=[error_message]
        )
    
    def _generate_summary(self, score: int, grade: str, eligibility: bool,
                         scorecard_config: Dict[str, Any]) -> str:
        """Generate human-readable summary of the evaluation."""
        scorecard_name = scorecard_config.get('name', 'Credit Scorecard')
        passing_score = scorecard_config.get('passing_score', 600)
        
        status = "eligible" if eligibility else "not eligible"
        
        summary = f"Credit evaluation using {scorecard_name}: "
        summary += f"Score {score} (Grade {grade}), applicant is {status} for credit. "
        
        if not eligibility:
            points_needed = passing_score - score
            summary += f"Needs {points_needed} more points to reach eligibility threshold of {passing_score}."
        
        return summary
    
    def _format_factor_score(self, factor_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format factor result for API response."""
        return {
            'code': factor_result['factor_code'],
            'name': factor_result['factor_name'],
            'category': factor_result.get('category', 'General'),
            'points': factor_result['points'],
            'max_points': factor_result['max_points'],
            'weight': factor_result['weight'],
            'value': factor_result.get('value'),
            'reasoning': factor_result['reasoning'],
            'warnings': factor_result.get('warnings', [])
        }
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of input data for audit purposes."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()