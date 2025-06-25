import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.config import settings
from app.schemas.onboarding import EligibilityResult

logger = logging.getLogger(__name__)


class ScorecardService:
    """Service for integrating with external scorecard microservice."""
    
    def __init__(self):
        """Initialize scorecard service with API configuration."""
        self.api_url = settings.SCORECARD_API_URL
        self.api_key = settings.SCORECARD_API_KEY
        self.timeout = 30.0  # 30 seconds timeout
        
        # Grade mappings
        self.grade_mappings = {
            (900, 1000): "AA",
            (800, 899): "A", 
            (700, 799): "B",
            (600, 699): "C",
            (0, 599): "D"
        }
        
        # Eligibility thresholds
        self.eligibility_threshold = 600  # Minimum score for eligibility
    
    async def calculate_score(self, customer_data: Dict[str, Any], financial_data: Dict[str, Any]) -> EligibilityResult:
        """
        Calculate credit score using external scorecard service.
        
        Args:
            customer_data: Customer personal and contact information
            financial_data: Customer financial profile data
            
        Returns:
            EligibilityResult with score, grade, and recommendations
        """
        try:
            # Prepare scorecard request payload
            payload = self._prepare_scorecard_payload(customer_data, financial_data)
            
            # Make API call to scorecard service
            score_response = await self._call_scorecard_api(payload)
            
            # Process response and generate eligibility result
            eligibility_result = self._process_scorecard_response(score_response)
            
            return eligibility_result
            
        except Exception as e:
            logger.error(f"Scorecard calculation failed: {str(e)}")
            # Return a default "pending" result in case of API failure
            return EligibilityResult(
                score=0,
                grade="D",
                eligibility="pending",
                message="Credit assessment is currently being processed. Please check back later.",
                breakdown=None,
                recommendations=["Complete document verification", "Provide additional financial information"]
            )
    
    def _prepare_scorecard_payload(self, customer_data: Dict[str, Any], financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for scorecard API request."""
        
        # Calculate age from date of birth
        age = None
        if customer_data.get('date_of_birth'):
            try:
                birth_date = datetime.strptime(str(customer_data['date_of_birth']), '%Y-%m-%d').date()
                today = datetime.now().date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = None
        
        # Prepare standardized payload
        payload = {
            "customer_profile": {
                "age": age,
                "gender": customer_data.get('gender'),
                "marital_status": customer_data.get('marital_status'),
                "nationality": customer_data.get('nationality'),
                "location": {
                    "city": customer_data.get('city'),
                    "state": customer_data.get('state_province'),
                    "country": customer_data.get('country')
                }
            },
            "financial_profile": {
                "employment_status": financial_data.get('employment_status'),
                "monthly_income": float(financial_data.get('monthly_income', 0)),
                "employment_duration_months": financial_data.get('employment_duration_months'),
                "has_bank_account": bool(financial_data.get('bank_name')),
                "bank_account_type": financial_data.get('bank_account_type'),
                "has_other_loans": financial_data.get('has_other_loans', False),
                "other_loans_count": len(financial_data.get('other_loans_details', [])),
                "total_other_loans_amount": self._calculate_total_loans(financial_data.get('other_loans_details', []))
            },
            "risk_factors": {
                "income_stability": self._assess_income_stability(financial_data),
                "debt_to_income_ratio": self._calculate_debt_to_income_ratio(financial_data),
                "employment_stability": self._assess_employment_stability(financial_data)
            },
            "request_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "scorecard_version": "v1.0",  # This could be configurable
                "request_id": f"score_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        return payload
    
    async def _call_scorecard_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to scorecard API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Version": "v1"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/v1/score",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 422:
                    # Validation error from scorecard API
                    error_detail = response.json()
                    logger.warning(f"Scorecard API validation error: {error_detail}")
                    raise ValueError(f"Invalid data provided to scorecard: {error_detail}")
                else:
                    # Other API errors
                    logger.error(f"Scorecard API error {response.status_code}: {response.text}")
                    raise Exception(f"Scorecard API returned {response.status_code}")
                    
            except httpx.TimeoutException:
                logger.error("Scorecard API timeout")
                raise Exception("Scorecard service is currently unavailable")
            except httpx.RequestError as e:
                logger.error(f"Scorecard API request failed: {str(e)}")
                raise Exception("Unable to connect to scorecard service")
    
    def _process_scorecard_response(self, response: Dict[str, Any]) -> EligibilityResult:
        """Process scorecard API response and create EligibilityResult."""
        
        # Extract score from response
        score = response.get('score', 0)
        score = max(0, min(1000, int(score)))  # Ensure score is between 0-1000
        
        # Determine grade based on score
        grade = self._determine_grade(score)
        
        # Determine eligibility
        eligibility = "eligible" if score >= self.eligibility_threshold else "ineligible"
        
        # Generate message based on score and eligibility
        message = self._generate_eligibility_message(score, grade, eligibility)
        
        # Extract breakdown if available
        breakdown = response.get('breakdown', {})
        
        # Generate recommendations
        recommendations = self._generate_recommendations(score, breakdown, response.get('recommendations', []))
        
        return EligibilityResult(
            score=score,
            grade=grade,
            eligibility=eligibility,
            message=message,
            breakdown=breakdown,
            recommendations=recommendations
        )
    
    def _determine_grade(self, score: int) -> str:
        """Determine credit grade based on score."""
        for (min_score, max_score), grade in self.grade_mappings.items():
            if min_score <= score <= max_score:
                return grade
        return "D"  # Default to lowest grade
    
    def _generate_eligibility_message(self, score: int, grade: str, eligibility: str) -> str:
        """Generate human-readable eligibility message."""
        if eligibility == "eligible":
            if grade == "AA":
                return f"Excellent credit profile! Your score of {score} qualifies you for our best rates and terms."
            elif grade == "A":
                return f"Very good credit profile! Your score of {score} qualifies you for competitive rates."
            elif grade == "B":
                return f"Good credit profile! Your score of {score} qualifies you for standard loan products."
            else:
                return f"Your score of {score} meets our minimum requirements. You may qualify for basic loan products."
        else:
            return f"Your current score of {score} does not meet our minimum requirements. Please review our recommendations to improve your eligibility."
    
    def _generate_recommendations(self, score: int, breakdown: Dict[str, Any], api_recommendations: list) -> list:
        """Generate recommendations based on score and breakdown."""
        recommendations = []
        
        # Use API recommendations if available
        if api_recommendations:
            recommendations.extend(api_recommendations)
        
        # Add standard recommendations based on score
        if score < 600:
            recommendations.extend([
                "Improve your monthly income documentation",
                "Reduce existing debt obligations",
                "Provide additional collateral or guarantor",
                "Consider a smaller loan amount initially"
            ])
        elif score < 700:
            recommendations.extend([
                "Maintain consistent employment history",
                "Consider providing additional income documentation",
                "Build a longer banking relationship"
            ])
        elif score < 800:
            recommendations.extend([
                "Continue maintaining your excellent financial profile",
                "Consider applying for higher loan amounts"
            ])
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def _calculate_total_loans(self, other_loans: list) -> float:
        """Calculate total amount of other loans."""
        total = 0.0
        for loan in other_loans:
            if isinstance(loan, dict) and 'amount' in loan:
                try:
                    total += float(loan['amount'])
                except (ValueError, TypeError):
                    continue
        return total
    
    def _assess_income_stability(self, financial_data: Dict[str, Any]) -> str:
        """Assess income stability based on employment information."""
        employment_status = financial_data.get('employment_status')
        employment_duration = financial_data.get('employment_duration_months', 0)
        
        if employment_status == 'employed':
            if employment_duration >= 24:
                return "high"
            elif employment_duration >= 12:
                return "medium"
            else:
                return "low"
        elif employment_status == 'self_employed':
            if employment_duration >= 36:
                return "medium"
            else:
                return "low"
        else:
            return "low"
    
    def _calculate_debt_to_income_ratio(self, financial_data: Dict[str, Any]) -> float:
        """Calculate debt-to-income ratio."""
        monthly_income = float(financial_data.get('monthly_income', 0))
        if monthly_income <= 0:
            return 1.0  # High risk if no income
        
        total_debt = self._calculate_total_loans(financial_data.get('other_loans_details', []))
        # Assume monthly debt payment is 1/12 of total debt (simplified)
        monthly_debt_payment = total_debt / 12 if total_debt > 0 else 0
        
        return monthly_debt_payment / monthly_income
    
    def _assess_employment_stability(self, financial_data: Dict[str, Any]) -> str:
        """Assess employment stability."""
        employment_status = financial_data.get('employment_status')
        employment_duration = financial_data.get('employment_duration_months', 0)
        
        if employment_status in ['employed', 'self_employed']:
            if employment_duration >= 24:
                return "stable"
            elif employment_duration >= 6:
                return "moderate"
            else:
                return "unstable"
        else:
            return "unstable"
    
    async def validate_scorecard_service(self) -> bool:
        """Validate that scorecard service is available and responding."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.api_url}/health",
                    headers=headers
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"Scorecard service validation failed: {str(e)}")
            return False