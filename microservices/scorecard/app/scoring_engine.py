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
    
    def _validate_input_data(self, request: ScoringRequest) -> None:
        """
        Validate input data for business logic consistency
        
        Args:
            request: ScoringRequest to validate
            
        Raises:
            ValueError: If data is inconsistent
        """
        # Validate employment consistency
        if (request.financial_profile.employment_status == EmploymentStatus.UNEMPLOYED 
            and request.financial_profile.employment_duration_months > 0):
            raise ValueError("Unemployed customer cannot have employment duration > 0")
            
        # Validate income vs employment status
        if (request.financial_profile.employment_status == EmploymentStatus.UNEMPLOYED 
            and request.financial_profile.monthly_income > 2000):
            raise ValueError("Unemployed customer cannot have high income without explanation")
            
        # Validate risk factors consistency with financial data
        if (request.risk_factors.employment_stability == EmploymentStability.STABLE 
            and request.financial_profile.employment_duration_months < 12):
            raise ValueError("Employment cannot be 'stable' with less than 12 months duration")
            
        # Validate debt ratio makes sense with loan data
        if (not request.financial_profile.has_other_loans 
            and request.risk_factors.debt_to_income_ratio > 0.1):
            raise ValueError("High debt ratio inconsistent with no existing loans")
    
    def _apply_score_bounds(self, raw_score: float) -> int:
        """
        Apply bounds checking to score with proper rounding
        
        Args:
            raw_score: Raw calculated score
            
        Returns:
            Bounded integer score
        """
        # Handle extreme cases
        if raw_score < 0:
            logger.warning(f"Score below minimum bound: {raw_score}, setting to 0")
            return 0
        elif raw_score > 1000:
            logger.warning(f"Score above maximum bound: {raw_score}, setting to 1000") 
            return 1000
        else:
            # Round to nearest integer
            return int(round(raw_score))
    
    async def calculate_score(self, request: ScoringRequest) -> ScoringResponse:
        """
        Calculate credit score based on customer data
        
        Args:
            request: ScoringRequest containing customer and financial data
            
        Returns:
            ScoringResponse with score, grade, eligibility, and recommendations
        """
        try:
            # Validate input data integrity
            self._validate_input_data(request)
            
            # Calculate base score
            base_score = self._calculate_base_score(request)
            
            # Apply income adjustments
            income_adjustment = self._calculate_income_adjustment(request)
            
            # Calculate final score with bounds checking
            final_score = self._apply_score_bounds(base_score + income_adjustment)
            
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
            
            # Validate output data
            response = ScoringResponse(
                score=final_score,
                grade=grade,
                eligibility=eligibility,
                message=message,
                breakdown=breakdown,
                recommendations=recommendations
            )
            
            logger.info(f"Score calculated successfully: {final_score} ({grade}) for request {request.request_metadata.request_id}")
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error for request {request.request_metadata.request_id}: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error calculating score for request {request.request_metadata.request_id}: {str(e)}")
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
        try:
            score = 500  # Starting base score
            
            # Age factor (optimal range 25-55)
            age = request.customer_profile.age
            age_adjustment = self._calculate_age_factor(age)
            score += age_adjustment
            
            # Employment status factor
            employment_adjustment = self._calculate_employment_factor(request.financial_profile)
            score += employment_adjustment
            
            # Banking relationship factor
            banking_adjustment = self._calculate_banking_factor(request.financial_profile)
            score += banking_adjustment
            
            # Existing loans factor
            loans_adjustment = self._calculate_loans_factor(request.financial_profile)
            score += loans_adjustment
            
            # Risk factors impact
            risk_adjustment = self._calculate_risk_factor_impact(request.risk_factors)
            score += risk_adjustment
            
            logger.debug(f"Base score breakdown: base=500, age={age_adjustment}, "
                        f"employment={employment_adjustment}, banking={banking_adjustment}, "
                        f"loans={loans_adjustment}, risk={risk_adjustment}, total={score}")
            
            return max(0, min(1000, score))
            
        except Exception as e:
            logger.error(f"Error in base score calculation: {str(e)}")
            # Return neutral score on calculation error
            return 500
    
    def _calculate_age_factor(self, age: int) -> int:
        """Calculate age-based score adjustment"""
        if 25 <= age <= 55:
            return 50
        elif 18 <= age < 25 or 55 < age <= 65:
            return 25
        elif 65 < age <= 75:
            return 0
        else:
            return -25  # Very young (impossible due to validation) or very old
    
    def _calculate_employment_factor(self, financial_profile) -> int:
        """Calculate employment-based score adjustment"""
        employment_status = financial_profile.employment_status
        duration_months = financial_profile.employment_duration_months
        
        base_employment_score = 0
        
        # Base employment status scoring
        if employment_status == EmploymentStatus.EMPLOYED:
            base_employment_score = 100
        elif employment_status == EmploymentStatus.SELF_EMPLOYED:
            base_employment_score = 75
        elif employment_status == EmploymentStatus.STUDENT:
            base_employment_score = -25
        elif employment_status == EmploymentStatus.RETIRED:
            base_employment_score = 25
        elif employment_status == EmploymentStatus.UNEMPLOYED:
            base_employment_score = -150
        
        # Duration-based adjustment (only for employed/self-employed)
        duration_adjustment = 0
        if employment_status in [EmploymentStatus.EMPLOYED, EmploymentStatus.SELF_EMPLOYED]:
            if duration_months >= 24:
                duration_adjustment = 75
            elif duration_months >= 12:
                duration_adjustment = 50
            elif duration_months >= 6:
                duration_adjustment = 25
            elif duration_months >= 3:
                duration_adjustment = 0
            else:
                duration_adjustment = -50
                
        return base_employment_score + duration_adjustment
    
    def _calculate_banking_factor(self, financial_profile) -> int:
        """Calculate banking relationship score adjustment"""
        if not financial_profile.has_bank_account:
            return -25  # Penalty for no banking relationship
            
        base_score = 50
        
        # Additional bonus for checking account
        if financial_profile.bank_account_type in ["checking", "both"]:
            base_score += 25
            
        return base_score
    
    def _calculate_loans_factor(self, financial_profile) -> int:
        """Calculate existing loans score adjustment"""
        if not financial_profile.has_other_loans:
            return 25  # Bonus for no existing loans
            
        loan_count = financial_profile.other_loans_count
        loan_amount = financial_profile.total_other_loans_amount
        
        # Base penalty for having loans
        count_penalty = min(loan_count * 25, 100)  # Cap at -100
        
        # Additional penalty for high loan amounts
        amount_penalty = 0
        if loan_amount > 100000:  # Very high debt
            amount_penalty = 50
        elif loan_amount > 50000:  # High debt
            amount_penalty = 25
            
        return -(count_penalty + amount_penalty)
    
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
        try:
            recommendations = []
            priority_recommendations = []
            secondary_recommendations = []
            
            # Critical issues (high priority)
            if not request.financial_profile.has_bank_account:
                priority_recommendations.append("Establish a banking relationship with a checking account")
            
            if request.financial_profile.employment_status == EmploymentStatus.UNEMPLOYED:
                priority_recommendations.append("Secure stable employment to improve creditworthiness")
            
            if request.risk_factors.debt_to_income_ratio > 0.5:
                priority_recommendations.append("Urgent: Reduce debt obligations to improve debt-to-income ratio")
            
            # Employment-based recommendations
            duration_months = request.financial_profile.employment_duration_months
            if duration_months < 6 and request.financial_profile.employment_status != EmploymentStatus.UNEMPLOYED:
                priority_recommendations.append("Build employment history - maintain current position for at least 6 months")
            elif duration_months < 12:
                secondary_recommendations.append("Continue building employment history (aim for 12+ months)")
            
            # Income-based recommendations
            monthly_income = request.financial_profile.monthly_income
            if monthly_income < 2000:
                priority_recommendations.append("Increase monthly income through additional income sources")
            elif monthly_income < 3000:
                secondary_recommendations.append("Consider documenting additional income sources")
            
            # Debt management recommendations
            debt_ratio = request.risk_factors.debt_to_income_ratio
            if 0.3 < debt_ratio <= 0.5:
                secondary_recommendations.append("Work on reducing existing debt obligations")
            elif debt_ratio > 0.1 and not request.financial_profile.has_other_loans:
                secondary_recommendations.append("Verify debt calculations - ensure accuracy")
            
            # Banking improvements
            if (request.financial_profile.has_bank_account and 
                request.financial_profile.bank_account_type not in ["checking", "both"]):
                secondary_recommendations.append("Consider opening a checking account for improved credit profile")
            
            # Risk factor recommendations
            if request.risk_factors.income_stability == IncomeStability.LOW:
                secondary_recommendations.append("Focus on stabilizing your primary income source")
            
            if request.risk_factors.employment_stability == EmploymentStability.UNSTABLE:
                secondary_recommendations.append("Demonstrate employment stability through consistent work history")
            
            # Score-specific recommendations
            if score < 500:
                priority_recommendations.append("Consider working with a financial counselor")
                priority_recommendations.append("Focus on fundamental financial stability before applying")
            elif score < 600:
                secondary_recommendations.append("Consider applying with a co-signer or collateral")
            elif score < 700:
                secondary_recommendations.append("Continue building positive financial history")
            elif score < 800:
                secondary_recommendations.append("You're close to premium rates - maintain current trajectory")
            else:
                secondary_recommendations.append("Excellent profile! You qualify for our best terms")
            
            # Loan-specific recommendations
            if request.financial_profile.has_other_loans:
                loan_count = request.financial_profile.other_loans_count
                if loan_count > 3:
                    priority_recommendations.append("Consider debt consolidation to reduce number of active loans")
                elif loan_count > 1:
                    secondary_recommendations.append("Monitor loan obligations to maintain good payment history")
            
            # Combine recommendations with priority order
            final_recommendations = priority_recommendations + secondary_recommendations
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in final_recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)
            
            # Ensure we always return at least one recommendation
            if not unique_recommendations:
                unique_recommendations.append("Continue maintaining your current financial profile")
            
            # Limit to maximum 6 recommendations, prioritizing the most important
            return unique_recommendations[:6]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Fallback recommendations
            return [
                "Continue building a positive financial history",
                "Maintain stable employment and income",
                "Consider consulting with a financial advisor"
            ]
    
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