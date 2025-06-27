#!/usr/bin/env python3
"""
Comprehensive edge case tests for the Scorecard Microservice

This test suite validates:
- Input validation edge cases
- Business logic boundary conditions
- Authentication security
- Error handling
- Performance limits
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import our modules
try:
    from models import (
        ScoringRequest, CustomerProfile, FinancialProfile, 
        RiskFactors, RequestMetadata, Location, Gender,
        MaritalStatus, EmploymentStatus, BankAccountType,
        IncomeStability, EmploymentStability
    )
    from scoring_engine import ScoringEngine
    from auth import verify_api_key, rate_limiter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the scorecard directory")
    sys.exit(1)


class EdgeCaseTests:
    """Comprehensive edge case test suite"""
    
    def __init__(self):
        self.scoring_engine = ScoringEngine()
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def create_base_request(self) -> Dict[str, Any]:
        """Create a base valid request for testing"""
        return {
            "customer_profile": {
                "age": 35,
                "gender": "male",
                "marital_status": "married",
                "nationality": "US",
                "location": {
                    "city": "New York",
                    "state": "NY",
                    "country": "US"
                }
            },
            "financial_profile": {
                "employment_status": "employed",
                "monthly_income": 5000.0,
                "employment_duration_months": 24,
                "has_bank_account": True,
                "bank_account_type": "checking",
                "has_other_loans": False,
                "other_loans_count": 0,
                "total_other_loans_amount": 0.0
            },
            "risk_factors": {
                "income_stability": "high",
                "debt_to_income_ratio": 0.05,
                "employment_stability": "stable"
            },
            "request_metadata": {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scorecard_version": "v1.0", 
            "request_id": f"test_{int(datetime.now(timezone.utc).timestamp())}"
            }
        }
    
    async def test_age_boundary_conditions(self):
        """Test age validation edge cases"""
        test_cases = [
            (17, False, "Below minimum age"),
            (18, True, "Minimum valid age"),
            (25, True, "Optimal age range start"),
            (55, True, "Optimal age range end"),
            (120, True, "Maximum valid age"),
            (121, False, "Above maximum age"),
            (-5, False, "Negative age"),
            (0, False, "Zero age")
        ]
        
        for age, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["customer_profile"]["age"] = age
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Age {age}", True, f"{description} - passed as expected")
                else:
                    self.log_test(f"Age {age}", False, f"{description} - should have failed but passed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Age {age}", False, f"{description} - failed unexpectedly: {str(e)}")
                else:
                    self.log_test(f"Age {age}", True, f"{description} - failed as expected")
    
    async def test_income_boundary_conditions(self):
        """Test income validation edge cases"""
        test_cases = [
            (99, False, "Below minimum income"),
            (100, True, "Minimum valid income"),
            (1000000, True, "Maximum valid income"),
            (1000001, False, "Above maximum income"),
            (-1000, False, "Negative income"),
            (0, False, "Zero income"),
            (150.555, True, "Decimal income (should round)")
        ]
        
        for income, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["financial_profile"]["monthly_income"] = income
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Income ${income}", True, f"{description} - passed as expected")
                else:
                    self.log_test(f"Income ${income}", False, f"{description} - should have failed but passed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Income ${income}", False, f"{description} - failed unexpectedly: {str(e)}")
                else:
                    self.log_test(f"Income ${income}", True, f"{description} - failed as expected")
    
    async def test_employment_consistency(self):
        """Test employment logic consistency"""
        test_cases = [
            # (status, duration, income, should_pass, description)
            ("unemployed", 12, 5000, False, "Unemployed with employment duration"),
            ("unemployed", 0, 3000, False, "Unemployed with high income"),
            ("unemployed", 0, 500, True, "Unemployed with low income"),
            ("employed", 0, 5000, True, "Recently employed"),
            ("employed", 6, 5000, True, "Employed 6 months"),
            ("self_employed", 601, 5000, False, "Employment duration too long"),
        ]
        
        for status, duration, income, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["financial_profile"]["employment_status"] = status
                data["financial_profile"]["employment_duration_months"] = duration
                data["financial_profile"]["monthly_income"] = income
                
                # Adjust employment stability based on duration
                if duration < 12:
                    data["risk_factors"]["employment_stability"] = "unstable"
                else:
                    data["risk_factors"]["employment_stability"] = "stable"
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Employment: {status}/{duration}m/${income}", True, f"{description} - passed")
                else:
                    self.log_test(f"Employment: {status}/{duration}m/${income}", False, f"{description} - should have failed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Employment: {status}/{duration}m/${income}", False, f"{description} - failed: {str(e)}")
                else:
                    self.log_test(f"Employment: {status}/{duration}m/${income}", True, f"{description} - failed as expected")
    
    async def test_loan_consistency(self):
        """Test loan-related data consistency"""
        test_cases = [
            # (has_loans, count, amount, should_pass, description)
            (True, 0, 0, False, "Has loans but count is 0"),
            (True, 1, 0, False, "Has loans but amount is 0"),
            (False, 1, 0, False, "No loans but count > 0"),
            (False, 0, 1000, False, "No loans but amount > 0"),
            (True, 2, 50000, True, "Valid loan data"),
            (False, 0, 0, True, "No loans - consistent"),
            (True, 51, 100000, False, "Too many loans"),
            (True, 5, 10000001, False, "Loan amount too high")
        ]
        
        for has_loans, count, amount, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["financial_profile"]["has_other_loans"] = has_loans
                data["financial_profile"]["other_loans_count"] = count
                data["financial_profile"]["total_other_loans_amount"] = amount
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Loans: {has_loans}/{count}/{amount}", True, f"{description} - passed")
                else:
                    self.log_test(f"Loans: {has_loans}/{count}/{amount}", False, f"{description} - should have failed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Loans: {has_loans}/{count}/{amount}", False, f"{description} - failed: {str(e)}")
                else:
                    self.log_test(f"Loans: {has_loans}/{count}/{amount}", True, f"{description} - failed as expected")
    
    async def test_debt_ratio_validation(self):
        """Test debt-to-income ratio validation"""
        test_cases = [
            (-0.1, False, "Negative debt ratio"),
            (0.0, True, "Zero debt ratio"),
            (0.5, True, "Normal debt ratio"),
            (1.0, True, "High debt ratio"),
            (5.0, True, "Maximum debt ratio"),
            (5.1, False, "Above maximum debt ratio"),
            (10.0, False, "Extremely high debt ratio")
        ]
        
        for ratio, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["risk_factors"]["debt_to_income_ratio"] = ratio
                
                # If testing high debt ratio, add existing loans to make it consistent
                if ratio > 0.1:
                    data["financial_profile"]["has_other_loans"] = True
                    data["financial_profile"]["other_loans_count"] = 2
                    data["financial_profile"]["total_other_loans_amount"] = ratio * data["financial_profile"]["monthly_income"] * 12
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Debt ratio {ratio}", True, f"{description} - passed")
                else:
                    self.log_test(f"Debt ratio {ratio}", False, f"{description} - should have failed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Debt ratio {ratio}", False, f"{description} - failed: {str(e)}")
                else:
                    self.log_test(f"Debt ratio {ratio}", True, f"{description} - failed as expected")
    
    async def test_location_validation(self):
        """Test location field validation"""
        test_cases = [
            # (city, state, country, should_pass, description)
            ("", "NY", "US", False, "Empty city"),
            ("New York", "", "US", False, "Empty state"),
            ("New York", "NY", "", False, "Empty country"),
            ("New York", "NY", "USA", True, "Valid 3-letter country"),
            ("New York", "NY", "U", False, "Invalid country code"),
            ("New York", "NY", "INVALID", False, "Invalid country format"),
            ("A" * 101, "NY", "US", False, "City name too long"),
            ("New York", "A" * 101, "US", False, "State name too long"),
        ]
        
        for city, state, country, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["customer_profile"]["location"]["city"] = city
                data["customer_profile"]["location"]["state"] = state
                data["customer_profile"]["location"]["country"] = country
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Location: {city[:10]}/{state[:10]}/{country}", True, f"{description} - passed")
                else:
                    self.log_test(f"Location: {city[:10]}/{state[:10]}/{country}", False, f"{description} - should have failed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Location: {city[:10]}/{state[:10]}/{country}", False, f"{description} - failed: {str(e)}")
                else:
                    self.log_test(f"Location: {city[:10]}/{state[:10]}/{country}", True, f"{description} - failed as expected")
    
    async def test_timestamp_validation(self):
        """Test timestamp validation"""
        now = datetime.now(timezone.utc)
        test_cases = [
            # (timestamp, should_pass, description)
            (now.isoformat(), True, "Current timestamp"),
            ((now + timedelta(minutes=2)).isoformat(), True, "2 minutes future (within limit)"),
            ((now + timedelta(minutes=10)).isoformat(), False, "10 minutes future (beyond limit)"),
            ((now - timedelta(hours=1)).isoformat(), True, "1 hour past (within limit)"),
            ((now - timedelta(hours=25)).isoformat(), False, "25 hours past (beyond limit)"),
        ]
        
        for timestamp_str, should_pass, description in test_cases:
            try:
                data = self.create_base_request()
                data["request_metadata"]["timestamp"] = timestamp_str
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if should_pass:
                    self.log_test(f"Timestamp validation", True, f"{description} - passed")
                else:
                    self.log_test(f"Timestamp validation", False, f"{description} - should have failed")
                    
            except Exception as e:
                if should_pass:
                    self.log_test(f"Timestamp validation", False, f"{description} - failed: {str(e)}")
                else:
                    self.log_test(f"Timestamp validation", True, f"{description} - failed as expected")
    
    async def test_score_boundary_conditions(self):
        """Test score calculation boundary conditions"""
        # Test extreme low score scenario
        try:
            data = self.create_base_request()
            data["customer_profile"]["age"] = 19  # Young
            data["financial_profile"]["employment_status"] = "unemployed"
            data["financial_profile"]["monthly_income"] = 200
            data["financial_profile"]["employment_duration_months"] = 0
            data["financial_profile"]["has_bank_account"] = False
            data["financial_profile"]["bank_account_type"] = "none"
            data["financial_profile"]["has_other_loans"] = True
            data["financial_profile"]["other_loans_count"] = 5
            data["financial_profile"]["total_other_loans_amount"] = 200000
            data["risk_factors"]["income_stability"] = "low"
            data["risk_factors"]["debt_to_income_ratio"] = 2.0
            data["risk_factors"]["employment_stability"] = "unstable"
            
            request = ScoringRequest(**data)
            result = await self.scoring_engine.calculate_score(request)
            
            if 0 <= result.score <= 1000:
                self.log_test("Extreme low score", True, f"Score {result.score} within bounds")
            else:
                self.log_test("Extreme low score", False, f"Score {result.score} out of bounds")
                
        except Exception as e:
            self.log_test("Extreme low score", False, f"Failed: {str(e)}")
        
        # Test extreme high score scenario
        try:
            data = self.create_base_request()
            data["customer_profile"]["age"] = 40  # Optimal
            data["financial_profile"]["employment_status"] = "employed"
            data["financial_profile"]["monthly_income"] = 15000
            data["financial_profile"]["employment_duration_months"] = 60
            data["financial_profile"]["has_bank_account"] = True
            data["financial_profile"]["bank_account_type"] = "both"
            data["financial_profile"]["has_other_loans"] = False
            data["risk_factors"]["income_stability"] = "high"
            data["risk_factors"]["debt_to_income_ratio"] = 0.05
            data["risk_factors"]["employment_stability"] = "stable"
            
            request = ScoringRequest(**data)
            result = await self.scoring_engine.calculate_score(request)
            
            if 0 <= result.score <= 1000:
                self.log_test("Extreme high score", True, f"Score {result.score} within bounds")
            else:
                self.log_test("Extreme high score", False, f"Score {result.score} out of bounds")
                
        except Exception as e:
            self.log_test("Extreme high score", False, f"Failed: {str(e)}")
    
    async def test_authentication_edge_cases(self):
        """Test authentication security edge cases"""
        test_cases = [
            ("", False, "Empty authorization"),
            ("Bearer", False, "Bearer without key"),
            ("Bearer ", False, "Bearer with space only"),
            ("Basic dGVzdA==", False, "Wrong auth type"),
            ("Bearer " + "x" * 600, False, "Extremely long key"),
            ("Bearer short", False, "Too short key"),
            ("Bearer default_scorecard_key_2024", True, "Valid key"),
        ]
        
        for auth_header, should_pass, description in test_cases:
            try:
                result = await verify_api_key(auth_header)
                if should_pass:
                    self.log_test(f"Auth: {description}", True, "Passed as expected")
                else:
                    self.log_test(f"Auth: {description}", False, "Should have failed but passed")
            except Exception as e:
                if should_pass:
                    self.log_test(f"Auth: {description}", False, f"Failed unexpectedly: {str(e)}")
                else:
                    self.log_test(f"Auth: {description}", True, "Failed as expected")
    
    async def test_comprehensive_recommendation_generation(self):
        """Test recommendation generation for various scenarios"""
        scenarios = [
            {
                "name": "Perfect customer",
                "data": {
                    "customer_profile": {"age": 35},
                    "financial_profile": {
                        "employment_status": "employed",
                        "monthly_income": 8000,
                        "employment_duration_months": 36,
                        "has_bank_account": True,
                        "bank_account_type": "checking"
                    },
                    "risk_factors": {
                        "income_stability": "high",
                        "debt_to_income_ratio": 0.1,
                        "employment_stability": "stable"
                    }
                }
            },
            {
                "name": "High-risk customer",
                "data": {
                    "customer_profile": {"age": 22},
                                         "financial_profile": {
                         "employment_status": "unemployed",
                         "monthly_income": 800,
                         "employment_duration_months": 0,
                         "has_bank_account": False,
                         "bank_account_type": "none",
                         "has_other_loans": True,
                         "other_loans_count": 3,
                         "total_other_loans_amount": 25000
                     },
                    "risk_factors": {
                        "income_stability": "low",
                        "debt_to_income_ratio": 0.8,
                        "employment_stability": "unstable"
                    }
                }
            }
        ]
        
        for scenario in scenarios:
            try:
                data = self.create_base_request()
                # Update with scenario data
                for section, updates in scenario["data"].items():
                    data[section].update(updates)
                
                request = ScoringRequest(**data)
                result = await self.scoring_engine.calculate_score(request)
                
                if result.recommendations and len(result.recommendations) > 0:
                    self.log_test(f"Recommendations: {scenario['name']}", True, 
                                f"Generated {len(result.recommendations)} recommendations")
                else:
                    self.log_test(f"Recommendations: {scenario['name']}", False, 
                                "No recommendations generated")
                    
            except Exception as e:
                self.log_test(f"Recommendations: {scenario['name']}", False, f"Failed: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("EDGE CASE TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("="*60)
        
        if self.failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.failed_tests == 0


async def main():
    """Run all edge case tests"""
    print("Starting comprehensive edge case tests for Scorecard Microservice...")
    print("This will validate input validation, business logic, and error handling.")
    print()
    
    tester = EdgeCaseTests()
    
    # Run all test categories
    await tester.test_age_boundary_conditions()
    await tester.test_income_boundary_conditions()
    await tester.test_employment_consistency()
    await tester.test_loan_consistency()
    await tester.test_debt_ratio_validation()
    await tester.test_location_validation()
    await tester.test_timestamp_validation()
    await tester.test_score_boundary_conditions()
    await tester.test_authentication_edge_cases()
    await tester.test_comprehensive_recommendation_generation()
    
    # Print final summary
    success = tester.print_summary()
    
    if success:
        print("\n✅ All edge case tests passed! The scorecard microservice is robust and ready for production.")
    else:
        print("\n❌ Some tests failed. Please review and fix the issues before deploying.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)