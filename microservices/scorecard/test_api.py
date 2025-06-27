#!/usr/bin/env python3
"""
Test script for the Scorecard Microservice API
"""

import requests
import json
from datetime import datetime


def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8001/health")
        print(f"Health Check Status: {response.status_code}")
        print(f"Health Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def test_scoring_endpoint():
    """Test the scoring endpoint with sample data"""
    url = "http://localhost:8001/api/v1/score"
    
    headers = {
        "Authorization": "Bearer default_scorecard_key_2024",
        "Content-Type": "application/json",
        "X-API-Version": "v1"
    }
    
    payload = {
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
            "debt_to_income_ratio": 0.15,
            "employment_stability": "stable"
        },
        "request_metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scorecard_version": "v1.0",
            "request_id": "test_request_001"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Scoring Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Credit Score: {result['score']}")
            print(f"Credit Grade: {result['grade']}")
            print(f"Eligibility: {result['eligibility']}")
            print(f"Message: {result['message']}")
            print(f"Recommendations: {result['recommendations']}")
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Scoring test failed: {e}")
        return False


def test_authentication_failure():
    """Test authentication with invalid API key"""
    url = "http://localhost:8001/api/v1/score"
    
    headers = {
        "Authorization": "Bearer invalid_key",
        "Content-Type": "application/json",
        "X-API-Version": "v1"
    }
    
    payload = {
        "customer_profile": {"age": 30, "gender": "male", "marital_status": "single", "nationality": "US", "location": {"city": "Test", "state": "TS", "country": "US"}},
        "financial_profile": {"employment_status": "employed", "monthly_income": 3000.0, "employment_duration_months": 12, "has_bank_account": True, "bank_account_type": "checking", "has_other_loans": False, "other_loans_count": 0, "total_other_loans_amount": 0.0},
        "risk_factors": {"income_stability": "medium", "debt_to_income_ratio": 0.25, "employment_stability": "moderate"},
        "request_metadata": {"timestamp": datetime.utcnow().isoformat() + "Z", "scorecard_version": "v1.0", "request_id": "test_auth_fail"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Auth Test Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Authentication properly rejected invalid API key")
            return True
        else:
            print(f"✗ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"Auth test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Scorecard Microservice API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Credit Scoring", test_scoring_endpoint),
        ("Authentication", test_authentication_failure)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))
        print(f"{test_name}: {'✓ PASSED' if result else '✗ FAILED'}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")