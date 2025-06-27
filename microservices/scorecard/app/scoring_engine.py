"""
Credit Scoring Engine

Implements the core credit scoring algorithm for the scorecard microservice.
"""

import logging
from typing import List, Tuple

try:
    from .models import (
        ScoringRequest, ScoringResponse, ScoreBreakdown, CreditGrade, 
        EligibilityStatus, EmploymentStatus, IncomeStability, 
        EmploymentStability, RiskLevel
    )
except ImportError:
    from models import (
        ScoringRequest, ScoringResponse, ScoreBreakdown, CreditGrade, 
        EligibilityStatus, EmploymentStatus, IncomeStability, 
        EmploymentStability, RiskLevel
    )

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Core credit scoring engine that calculates credit scores based on 
    customer profile, financial data, and risk factors.
    """
    
    # Score range definitions
    SCORE_RANGES = {
        CreditGrade.AA: (900, 1000),
        CreditGrade.A: (800, 899),
        CreditGrade.B: (700, 799),
        CreditGrade.C: (600, 699),
        CreditGrade.D: (0, 599)
    }
    
    # Minimum score for eligibility
    MINIMUM_ELIGIBLE_SCORE = 600
    AUTO_APPROVAL_SCORE = 800
    
    def __init__(self):
        """Initialize the scoring engine"""
        logger.info("Scoring engine initialized")
    
    async def calculate_score(self, request: ScoringRequest) -> ScoringResponse:
        """
        Calculate credit score based on customer data
        
        Args:
            request: ScoringRequest containing customer and financial data
            
        Returns:
            ScoringResponse with score, grade, eligibility, and recommendations
        """
        try:
            # Calculate base score
            base_score = self._calculate_base_score(request)
            
            # Apply income adjustments
            income_adjustment = self._calculate_income_adjustment(request)
            
            # Calculate final score
            final_score = min(1000, max(0, base_score + income_adjustment))
            
            # Determine grade and eligibility
            grade = self._determine_grade(final_score)
            eligibility = self._determine_eligibility(final_score)
            
            # Generate message
            message = self._generate_score_message(final_score, grade)
            
            # Create score breakdown
            breakdown = ScoreBreakdown(
                base_score=base_score,
                income_adjustment=income_adjustment,
                final_score=final_score,
                risk_factors=request.risk_factors
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(request, final_score)
            
            return ScoringResponse(
                score=final_score,
                grade=grade,
                eligibility=eligibility,
                message=message,
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            # Return fallback response
            return self._create_fallback_response(request)
    
    def _calculate_base_score(self, request: ScoringRequest) -> int:
        """
        Calculate the base credit score before adjustments
        
        Args:
            request: ScoringRequest containing customer data
            
        Returns:
            Base score (integer)
        """
        score = 500  # Starting base score
        
        # Age factor (optimal range 25-55)
        age = request.customer_profile.age
        if 25 <= age <= 55:
            score += 50
        elif 18 <= age < 25 or 55 < age <= 65:
            score += 25
        # No adjustment for ages outside these ranges
        
        # Employment status factor
        employment_status = request.financial_profile.employment_status
        if employment_status == EmploymentStatus.EMPLOYED:
            score += 100
        elif employment_status == EmploymentStatus.SELF_EMPLOYED:
            score += 75
        elif employment_status == EmploymentStatus.UNEMPLOYED:
            score -= 100
        
        # Employment duration factor
        duration_months = request.financial_profile.employment_duration_months
        if duration_months >= 24:
            score += 75
        elif duration_months >= 12:
            score += 50
        elif duration_months >= 6:
            score += 25
        # Penalty for very short employment
        elif duration_months < 3:
            score -= 50
        
        # Banking relationship factor
        if request.financial_profile.has_bank_account:
            score += 50
            if request.financial_profile.bank_account_type in ["checking", "both"]:
                score += 25
        
        # Existing loans factor
        if request.financial_profile.has_other_loans:
            # Penalty based on number of loans
            loan_count = request.financial_profile.other_loans_count
            if loan_count == 1:
                score -= 25
            elif loan_count == 2:
                score -= 50
            elif loan_count >= 3:
                score -= 100
        else:
            # Bonus for no existing loans
            score += 25
        
        # Risk factors impact
        score += self._calculate_risk_factor_impact(request.risk_factors)
        
        return max(0, min(1000, score))
    
    def _calculate_income_adjustment(self, request: ScoringRequest) -> int:
        """
        Calculate score adjustment based on income level
        
        Args:
            request: ScoringRequest containing financial data
            
        Returns:
            Income adjustment (can be positive or negative)
        """
        monthly_income = request.financial_profile.monthly_income
        
        # Income brackets with corresponding adjustments
        if monthly_income >= 10000:
            return 100
        elif monthly_income >= 7500:
            return 75
        elif monthly_income >= 5000:
            return 50
        elif monthly_income >= 3000:
            return 25
        elif monthly_income >= 2000:
            return 0
        elif monthly_income >= 1000:
            return -25
        else:
            return -50
    
    def _calculate_risk_factor_impact(self, risk_factors) -> int:
        """
        Calculate score impact based on risk factors
        
        Args:
            risk_factors: RiskFactors object
            
        Returns:
            Risk factor score adjustment
        """
        score_adjustment = 0
        
        # Income stability impact
        if risk_factors.income_stability == IncomeStability.HIGH:
            score_adjustment += 50
        elif risk_factors.income_stability == IncomeStability.MEDIUM:
            score_adjustment += 25
        elif risk_factors.income_stability == IncomeStability.LOW:
            score_adjustment -= 50
        
        # Debt-to-income ratio impact
        debt_ratio = risk_factors.debt_to_income_ratio
        if debt_ratio < 0.2:
            score_adjustment += 50
        elif debt_ratio < 0.3:
            score_adjustment += 25
        elif debt_ratio < 0.4:
            score_adjustment += 0
        elif debt_ratio < 0.5:
            score_adjustment -= 25
        else:
            score_adjustment -= 75
        
        # Employment stability impact
        if risk_factors.employment_stability == EmploymentStability.STABLE:
            score_adjustment += 50
        elif risk_factors.employment_stability == EmploymentStability.MODERATE:
            score_adjustment += 25
        elif risk_factors.employment_stability == EmploymentStability.UNSTABLE:
            score_adjustment -= 50
        
        return score_adjustment
    
    def _determine_grade(self, score: int) -> CreditGrade:
        """
        Determine credit grade based on score
        
        Args:
            score: Credit score
            
        Returns:
            CreditGrade enum value
        """
        for grade, (min_score, max_score) in self.SCORE_RANGES.items():
            if min_score <= score <= max_score:
                return grade
        return CreditGrade.D  # Default to lowest grade
    
    def _determine_eligibility(self, score: int) -> EligibilityStatus:
        """
        Determine loan eligibility based on score
        
        Args:
            score: Credit score
            
        Returns:
            EligibilityStatus enum value
        """
        if score >= self.AUTO_APPROVAL_SCORE:
            return EligibilityStatus.ELIGIBLE
        elif score >= self.MINIMUM_ELIGIBLE_SCORE:
            return EligibilityStatus.ELIGIBLE
        else:
            return EligibilityStatus.INELIGIBLE
    
    def _generate_score_message(self, score: int, grade: CreditGrade) -> str:
        """
        Generate human-readable score interpretation message
        
        Args:
            score: Credit score
            grade: Credit grade
            
        Returns:
            Formatted message string
        """
        grade_messages = {
            CreditGrade.AA: f"Excellent credit profile! Your score of {score} qualifies you for the best rates and terms.",
            CreditGrade.A: f"Very good credit profile! Your score of {score} qualifies you for competitive rates.",
            CreditGrade.B: f"Good credit profile! Your score of {score} qualifies you for standard loan products.",
            CreditGrade.C: f"Fair credit profile. Your score of {score} may qualify for basic loan products with higher rates.",
            CreditGrade.D: f"Credit profile needs improvement. Your score of {score} may require additional documentation or a co-signer."
        }
        
        return grade_messages.get(grade, f"Your credit score is {score}.")
    
    def _generate_recommendations(self, request: ScoringRequest, score: int) -> List[str]:
        """
        Generate personalized recommendations for credit improvement
        
        Args:
            request: ScoringRequest containing customer data
            score: Calculated credit score
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Income-based recommendations
        monthly_income = request.financial_profile.monthly_income
        if monthly_income < 3000:
            recommendations.append("Consider documenting additional income sources")
            recommendations.append("Explore opportunities to increase monthly income")
        
        # Employment-based recommendations
        duration_months = request.financial_profile.employment_duration_months
        if duration_months < 12:
            recommendations.append("Maintain consistent employment history")
            recommendations.append("Consider waiting until you have 12+ months employment history")
        
        # Banking recommendations
        if not request.financial_profile.has_bank_account:
            recommendations.append("Establish a banking relationship with a checking account")
        
        # Debt management recommendations
        debt_ratio = request.risk_factors.debt_to_income_ratio
        if debt_ratio > 0.3:
            recommendations.append("Work on reducing existing debt obligations")
            recommendations.append("Consider debt consolidation options")
        
        # Risk factor recommendations
        if request.risk_factors.income_stability == IncomeStability.LOW:
            recommendations.append("Focus on stabilizing your income source")
        
        if request.risk_factors.employment_stability == EmploymentStability.UNSTABLE:
            recommendations.append("Build a more stable employment history")
        
        # Score-specific recommendations
        if score < 600:
            recommendations.append("Focus on improving employment stability and reducing debt")
            recommendations.append("Consider applying with a co-signer")
        elif score < 700:
            recommendations.append("Continue building positive financial history")
            recommendations.append("Consider providing additional income documentation")
        else:
            recommendations.append("Maintain your excellent financial profile")
            recommendations.append("You qualify for our best loan products")
        
        # Remove duplicates and limit to reasonable number
        recommendations = list(dict.fromkeys(recommendations))
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _create_fallback_response(self, request: ScoringRequest) -> ScoringResponse:
        """
        Create a fallback response when scoring fails
        
        Args:
            request: Original scoring request
            
        Returns:
            Fallback ScoringResponse
        """
        logger.warning("Creating fallback response due to scoring error")
        
        return ScoringResponse(
            score=500,  # Neutral score
            grade=CreditGrade.C,
            eligibility=EligibilityStatus.PENDING,
            message="Score calculation is pending. Please try again later or contact support.",
            breakdown=ScoreBreakdown(
                base_score=500,
                income_adjustment=0,
                final_score=500,
                risk_factors=request.risk_factors
            ),
            recommendations=[
                "Please retry the scoring request",
                "Contact customer support if the issue persists",
                "Ensure all required information is provided"
            ]
        )