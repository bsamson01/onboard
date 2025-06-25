"""
Basic tests for the scoring engine functionality.
"""

import pytest
from app.core.scoring_engine import ScoringEngine
from app.core.expression_evaluator import SafeExpressionEvaluator
from app.core.letter_grader import LetterGrader


class TestSafeExpressionEvaluator:
    """Test the safe expression evaluator."""
    
    def test_basic_expression(self):
        """Test basic mathematical expressions."""
        evaluator = SafeExpressionEvaluator()
        
        # Test simple math
        result = evaluator.evaluate("10 + 5", {})
        assert result == 15
        
        # Test with variables
        result = evaluator.evaluate("income * 0.3", {"income": 1000})
        assert result == 300
        
        # Test functions
        result = evaluator.evaluate("max(10, 20)", {})
        assert result == 20
    
    def test_threshold_rules(self):
        """Test threshold-based scoring rules."""
        evaluator = SafeExpressionEvaluator()
        
        rules = {
            "thresholds": {
                "field": "income",
                "ranges": [
                    {"min": 1000, "max": 2000, "points": 80},
                    {"min": 500, "max": 999, "points": 60},
                    {"min": 0, "max": 499, "points": 30}
                ]
            }
        }
        
        # Test high income
        result = evaluator.get_score_for_rules(rules, {"income": 1500})
        assert result["points"] == 80
        
        # Test low income
        result = evaluator.get_score_for_rules(rules, {"income": 300})
        assert result["points"] == 30
    
    def test_condition_rules(self):
        """Test condition-based scoring rules."""
        evaluator = SafeExpressionEvaluator()
        
        rules = {
            "conditions": [
                {"condition": "employment == 'full_time'", "points": 100},
                {"condition": "age >= 25", "points": 50}
            ]
        }
        
        # Test all conditions met
        data = {"employment": "full_time", "age": 30}
        result = evaluator.get_score_for_rules(rules, data)
        assert result["points"] == 150
        
        # Test partial conditions met
        data = {"employment": "part_time", "age": 30}
        result = evaluator.get_score_for_rules(rules, data)
        assert result["points"] == 50
    
    def test_security(self):
        """Test security features."""
        evaluator = SafeExpressionEvaluator()
        
        # Test that dangerous expressions are rejected
        with pytest.raises(ValueError):
            evaluator.evaluate("__import__('os').system('ls')", {})
        
        with pytest.raises(ValueError):
            evaluator.evaluate("eval('1+1')", {})


class TestLetterGrader:
    """Test the letter grader functionality."""
    
    def test_default_grading_scale(self):
        """Test the default FICO-like grading scale."""
        grader = LetterGrader()
        
        assert grader.get_letter_grade(800) == "AA"
        assert grader.get_letter_grade(750) == "A+"
        assert grader.get_letter_grade(700) == "A"
        assert grader.get_letter_grade(650) == "B+"
        assert grader.get_letter_grade(600) == "B"
        assert grader.get_letter_grade(550) == "C+"
        assert grader.get_letter_grade(500) == "C"
        assert grader.get_letter_grade(400) == "D"
        assert grader.get_letter_grade(200) == "D"  # Below minimum
    
    def test_custom_grading_scale(self):
        """Test custom grading scales."""
        custom_scale = [
            (900, "Excellent"),
            (700, "Good"),
            (500, "Fair"),
            (0, "Poor")
        ]
        
        grader = LetterGrader(custom_scale)
        
        assert grader.get_letter_grade(950) == "Excellent"
        assert grader.get_letter_grade(750) == "Good"
        assert grader.get_letter_grade(600) == "Fair"
        assert grader.get_letter_grade(300) == "Poor"
    
    def test_grade_info(self):
        """Test detailed grade information."""
        grader = LetterGrader()
        
        info = grader.get_grade_info(720)
        assert info["letter_grade"] == "A"
        assert info["score"] == 720
        assert info["grade_range_min"] == 700
        assert info["next_grade_min"] == 750
        assert info["points_to_next_grade"] == 30


class TestScoringEngine:
    """Test the main scoring engine."""
    
    def test_basic_evaluation(self):
        """Test basic applicant evaluation."""
        engine = ScoringEngine()
        
        scorecard_config = {
            "id": 1,
            "name": "Test Scorecard",
            "min_score": 300,
            "max_score": 850,
            "passing_score": 600
        }
        
        scoring_factors = [
            {
                "name": "Income Factor",
                "code": "income",
                "weight": 1.0,
                "rules": {"expression": "income / 100"},
                "is_required": True
            },
            {
                "name": "Age Factor", 
                "code": "age",
                "weight": 0.5,
                "rules": {
                    "conditions": [
                        {"condition": "age >= 25 and age <= 65", "points": 100}
                    ]
                },
                "is_required": True
            }
        ]
        
        applicant_data = {
            "income": 5000,
            "age": 35
        }
        
        result = engine.evaluate_applicant(
            scorecard_config, scoring_factors, applicant_data
        )
        
        assert "total_score" in result
        assert "letter_grade" in result
        assert "eligibility" in result
        assert "factor_scores" in result
        assert "breakdown" in result
        assert result["total_score"] >= scorecard_config["min_score"]
        assert result["total_score"] <= scorecard_config["max_score"]
    
    def test_missing_data_handling(self):
        """Test handling of missing applicant data."""
        engine = ScoringEngine()
        
        scorecard_config = {
            "id": 1,
            "name": "Test Scorecard",
            "min_score": 300,
            "max_score": 850,
            "passing_score": 600
        }
        
        scoring_factors = [
            {
                "name": "Income Factor",
                "code": "income",
                "weight": 1.0,
                "rules": {"expression": "income / 100"},
                "is_required": True
            },
            {
                "name": "Optional Factor",
                "code": "optional_field",
                "weight": 0.5,
                "rules": {"expression": "optional_field * 2"},
                "is_required": False,
                "default_points": 50
            }
        ]
        
        # Missing required field should still work
        applicant_data = {"income": 3000}
        
        result = engine.evaluate_applicant(
            scorecard_config, scoring_factors, applicant_data
        )
        
        # Should handle missing optional data gracefully
        assert result is not None
        assert "warnings" in result


def test_integration_example():
    """Test a complete integration example."""
    engine = ScoringEngine()
    
    # Realistic scorecard configuration
    scorecard_config = {
        "id": 1,
        "name": "MFI Basic Scorecard",
        "min_score": 300,
        "max_score": 850,
        "passing_score": 600
    }
    
    scoring_factors = [
        {
            "name": "Monthly Income",
            "code": "monthly_income",
            "category": "Financial",
            "weight": 2.0,
            "rules": {
                "thresholds": {
                    "field": "monthly_income",
                    "ranges": [
                        {"min": 30000, "max": 999999, "points": 100},
                        {"min": 20000, "max": 29999, "points": 70},
                        {"min": 10000, "max": 19999, "points": 40},
                        {"min": 0, "max": 9999, "points": 20}
                    ]
                }
            },
            "is_required": True
        },
        {
            "name": "Employment Status",
            "code": "employment_status",
            "category": "Demographic",
            "weight": 1.5,
            "rules": {
                "conditions": [
                    {"condition": "employment_status == 'full_time'", "points": 100},
                    {"condition": "employment_status == 'part_time'", "points": 70},
                    {"condition": "employment_status == 'self_employed'", "points": 60}
                ]
            },
            "is_required": True
        },
        {
            "name": "Age",
            "code": "age",
            "category": "Demographic", 
            "weight": 0.8,
            "rules": {
                "conditions": [
                    {"condition": "age >= 25 and age <= 55", "points": 100},
                    {"condition": "age >= 18 and age < 25", "points": 80},
                    {"condition": "age > 55", "points": 70}
                ]
            },
            "is_required": True
        }
    ]
    
    # Good applicant data
    applicant_data = {
        "monthly_income": 35000,
        "employment_status": "full_time",
        "age": 32
    }
    
    result = engine.evaluate_applicant(
        scorecard_config, scoring_factors, applicant_data
    )
    
    # Verify result structure
    assert result["total_score"] > 0
    assert result["letter_grade"] in ["AA", "A+", "A", "B+", "B", "C+", "C", "D"]
    assert isinstance(result["eligibility"], bool)
    assert len(result["factor_scores"]) == len(scoring_factors)
    assert result["data_completeness"] == 1.0  # All required data provided
    assert result["confidence_score"] > 0.8     # High confidence
    
    # This should be a high-scoring applicant
    assert result["total_score"] >= scorecard_config["passing_score"]
    assert result["eligibility"] is True
    
    print(f"Integration test result: {result['total_score']} ({result['letter_grade']}) - {'Eligible' if result['eligibility'] else 'Not Eligible'}")


if __name__ == "__main__":
    # Run the integration example
    test_integration_example()
    print("All tests passed!")