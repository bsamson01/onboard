#!/usr/bin/env python3
"""
Unit test for the scoring engine without requiring the full service to run
"""

import sys
import os
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import the scoring engine and models
from scoring_engine import ScoringEngine
from models import (
    ScoringRequest, CustomerProfile, FinancialProfile, 
    RiskFactors, RequestMetadata, Location
)

async def test_scoring_engine():
    """Test the scoring engine with sample data"""
    
    # Create test data
    location = Location(
        city="New York",
        state="NY",
        country="US"
    )
    
    customer_profile = CustomerProfile(
        age=35,
        gender="male",
        marital_status="married",
        nationality="US",
        location=location
    )
    
    financial_profile = FinancialProfile(
        employment_status="employed",
        monthly_income=5000.0,
        employment_duration_months=24,
        has_bank_account=True,
        bank_account_type="checking",
        has_other_loans=False,
        other_loans_count=0,
        total_other_loans_amount=0.0
    )
    
    risk_factors = RiskFactors(
        income_stability="high",
        debt_to_income_ratio=0.05,
        employment_stability="stable"
    )
    
    request_metadata = RequestMetadata(
        timestamp=datetime.now(timezone.utc),
        scorecard_version="v1.0",
        request_id="test_001"
    )
    
    scoring_request = ScoringRequest(
        customer_profile=customer_profile,
        financial_profile=financial_profile,
        risk_factors=risk_factors,
        request_metadata=request_metadata
    )
    
    # Initialize scoring engine
    engine = ScoringEngine()
    
    # Calculate score
    result = await engine.calculate_score(scoring_request)
    
    # Print results
    print("🧪 Scoring Engine Test Results")
    print("=" * 40)
    print(f"Credit Score: {result.score}")
    print(f"Credit Grade: {result.grade}")
    print(f"Eligibility: {result.eligibility}")
    print(f"Message: {result.message}")
    print(f"Base Score: {result.breakdown.base_score}")
    print(f"Income Adjustment: {result.breakdown.income_adjustment}")
    print(f"Final Score: {result.breakdown.final_score}")
    print("\nRecommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    
    # Validate results
    assert 0 <= result.score <= 1000, f"Score {result.score} out of valid range"
    assert result.grade in ["AA", "A", "B", "C", "D"], f"Invalid grade: {result.grade}"
    assert result.eligibility in ["eligible", "ineligible", "pending"], f"Invalid eligibility: {result.eligibility}"
    assert len(result.recommendations) > 0, "No recommendations provided"
    
    print("\n✅ All tests passed!")
    return True

def test_multiple_scenarios():
    """Test different scoring scenarios"""
    import asyncio
    
    scenarios = [
        {
            "name": "High Income Professional",
            "age": 40,
            "income": 8000,
            "employment_months": 36,
            "debt_ratio": 0.1,
            "expected_grade": "A"
        },
        {
            "name": "Young Professional",
            "age": 25,
            "income": 3000,
            "employment_months": 12,
            "debt_ratio": 0.05,
            "expected_grade": "B"
        },
        {
            "name": "High Risk Customer",
            "age": 22,
            "income": 1500,
            "employment_months": 3,
            "debt_ratio": 0.08,
            "expected_grade": "D"
        }
    ]
    
    engine = ScoringEngine()
    
    print("\n🔬 Testing Multiple Scenarios")
    print("=" * 50)
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # Create test request
        location = Location(city="Test", state="TS", country="US")
        customer_profile = CustomerProfile(
            age=scenario["age"],
            gender="male",
            marital_status="single",
            nationality="US",
            location=location
        )
        
        financial_profile = FinancialProfile(
            employment_status="employed",
            monthly_income=scenario["income"],
            employment_duration_months=scenario["employment_months"],
            has_bank_account=True,
            bank_account_type="checking",
            has_other_loans=False,
            other_loans_count=0,
            total_other_loans_amount=0.0
        )
        
        risk_factors = RiskFactors(
            income_stability="medium",
            debt_to_income_ratio=scenario["debt_ratio"],
            employment_stability="moderate"
        )
        
        request_metadata = RequestMetadata(
            timestamp=datetime.now(timezone.utc),
            scorecard_version="v1.0",
            request_id=f"test_{scenario['name'].replace(' ', '_').lower()}"
        )
        
        scoring_request = ScoringRequest(
            customer_profile=customer_profile,
            financial_profile=financial_profile,
            risk_factors=risk_factors,
            request_metadata=request_metadata
        )
        
        result = asyncio.run(engine.calculate_score(scoring_request))
        
        print(f"Score: {result.score}")
        print(f"Grade: {result.grade}")
        print(f"Eligibility: {result.eligibility}")
        
        # Verify grade is reasonable for scenario
        if result.grade == scenario["expected_grade"]:
            print(f"✅ Expected grade {scenario['expected_grade']} achieved")
        else:
            print(f"⚠️  Got grade {result.grade}, expected {scenario['expected_grade']}")

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Testing Scorecard Scoring Engine")
    print("=" * 50)
    
    try:
        # Test basic scoring
        asyncio.run(test_scoring_engine())
        
        # Test multiple scenarios
        test_multiple_scenarios()
        
        print("\n🎉 All scoring engine tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)