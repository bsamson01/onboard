"""
Letter grader for converting numerical scores to letter grades.
Supports flexible grading scales and customization per scorecard.
"""

from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class LetterGrader:
    """
    Converts numerical scores to letter grades using configurable scales.
    """
    
    # Default FICO-like grading scale
    DEFAULT_SCALE = [
        (800, 'AA'),  # Excellent
        (750, 'A+'),  # Very Good
        (700, 'A'),   # Good
        (650, 'B+'),  # Fair
        (600, 'B'),   # Poor
        (550, 'C+'),  # Very Poor
        (500, 'C'),   # Bad
        (0, 'D')      # Very Bad
    ]
    
    def __init__(self, custom_scale: Optional[List[Tuple[int, str]]] = None):
        """
        Initialize the letter grader.
        
        Args:
            custom_scale: Custom grading scale as list of (min_score, grade) tuples
                         Should be sorted in descending order by score
        """
        self.scale = custom_scale or self.DEFAULT_SCALE
        self._validate_scale()
    
    def _validate_scale(self):
        """Validate the grading scale."""
        if not self.scale:
            raise ValueError("Grading scale cannot be empty")
        
        # Check that scale is sorted in descending order
        scores = [score for score, _ in self.scale]
        if scores != sorted(scores, reverse=True):
            raise ValueError("Grading scale must be sorted in descending order by score")
        
        # Check for duplicate grades
        grades = [grade for _, grade in self.scale]
        if len(grades) != len(set(grades)):
            raise ValueError("Grading scale cannot have duplicate grades")
    
    def get_letter_grade(self, score: int) -> str:
        """
        Get letter grade for a numerical score.
        
        Args:
            score: Numerical score
            
        Returns:
            Letter grade string
        """
        if not isinstance(score, (int, float)):
            raise ValueError("Score must be a number")
        
        score = int(score)  # Convert to integer for comparison
        
        for min_score, grade in self.scale:
            if score >= min_score:
                logger.debug(f"Score {score} assigned grade {grade}")
                return grade
        
        # Fallback to lowest grade if score is below all thresholds
        lowest_grade = self.scale[-1][1]
        logger.warning(f"Score {score} below all thresholds, assigned lowest grade {lowest_grade}")
        return lowest_grade
    
    def get_grade_info(self, score: int) -> Dict[str, Any]:
        """
        Get detailed grade information for a score.
        
        Args:
            score: Numerical score
            
        Returns:
            Dictionary with grade information
        """
        letter_grade = self.get_letter_grade(score)
        
        # Find the grade range
        current_min = None
        next_min = None
        
        for i, (min_score, grade) in enumerate(self.scale):
            if grade == letter_grade:
                current_min = min_score
                if i > 0:
                    next_min = self.scale[i - 1][0]
                break
        
        return {
            'score': score,
            'letter_grade': letter_grade,
            'grade_range_min': current_min,
            'next_grade_min': next_min,
            'points_to_next_grade': max(0, next_min - score) if next_min else 0,
            'grade_description': self._get_grade_description(letter_grade)
        }
    
    def _get_grade_description(self, grade: str) -> str:
        """Get human-readable description for a grade."""
        descriptions = {
            'AA': 'Excellent - Exceptionally strong creditworthiness',
            'A+': 'Very Good - Strong creditworthiness with minimal risk',
            'A':  'Good - Solid creditworthiness with low risk',
            'B+': 'Fair - Acceptable creditworthiness with moderate risk',
            'B':  'Poor - Below average creditworthiness with elevated risk',
            'C+': 'Very Poor - Weak creditworthiness with high risk',
            'C':  'Bad - Very weak creditworthiness with very high risk',
            'D':  'Very Bad - Extremely poor creditworthiness with maximum risk'
        }
        return descriptions.get(grade, f"Grade {grade}")
    
    def is_passing_grade(self, score: int, passing_score: int) -> bool:
        """
        Check if a score meets the passing threshold.
        
        Args:
            score: Numerical score to check
            passing_score: Minimum passing score
            
        Returns:
            True if score meets or exceeds passing threshold
        """
        return score >= passing_score
    
    @classmethod
    def create_custom_scale(cls, 
                          min_score: int = 300, 
                          max_score: int = 850, 
                          num_grades: int = 8) -> List[Tuple[int, str]]:
        """
        Create a custom grading scale.
        
        Args:
            min_score: Minimum possible score
            max_score: Maximum possible score
            num_grades: Number of grade levels
            
        Returns:
            List of (min_score, grade) tuples
        """
        grades = ['AA', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D'][:num_grades]
        
        if num_grades > len(grades):
            # Generate additional grades if needed
            for i in range(len(grades), num_grades):
                grades.append(f'Grade{i+1}')
        
        # Calculate score ranges
        score_range = max_score - min_score
        step = score_range // num_grades
        
        scale = []
        for i, grade in enumerate(grades):
            threshold = max_score - (i * step)
            if i == num_grades - 1:  # Last grade gets minimum score
                threshold = min_score
            scale.append((threshold, grade))
        
        return scale