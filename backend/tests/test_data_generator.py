"""
Test data generator for edge cases and simulation scenarios.
Generates realistic but extreme test cases for robustness testing.
"""

import random
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import uuid

class EdgeCaseDataGenerator:
    """Generate test data for edge cases and boundary conditions."""
    
    def __init__(self):
        self.countries = ["Kenya", "Nigeria", "Ghana", "Tanzania", "Uganda"]
        self.cities = ["Nairobi", "Lagos", "Accra", "Dar es Salaam", "Kampala"]
        self.banks = ["KCB", "Equity Bank", "ABSA", "Standard Chartered", "Barclays"]
        
    def generate_low_income_profile(self) -> Dict[str, Any]:
        """Generate customer profile with very low income."""
        return {
            "personal_info": {
                "first_name": f"LowIncome{random.randint(1000, 9999)}",
                "last_name": f"User{random.randint(100, 999)}",
                "date_of_birth": self._random_adult_birthdate(),
                "gender": random.choice(["male", "female"]),
                "id_number": f"ID{random.randint(10000000, 99999999)}",
                "marital_status": random.choice(["single", "married", "divorced"])
            },
            "contact_info": {
                "phone_number": f"+254{random.randint(700000000, 799999999)}",
                "email": f"lowincome{random.randint(1000, 9999)}@example.com",
                "address_line1": f"{random.randint(1, 999)} Low Income Street",
                "city": random.choice(self.cities),
                "country": random.choice(self.countries)
            },
            "financial_info": {
                "employment_status": random.choice(["employed", "self_employed", "casual_worker"]),
                "monthly_income": random.randint(50, 200),  # Very low income
                "employment_duration_months": random.randint(1, 6),  # Short employment
                "bank_name": random.choice(self.banks),
                "bank_account_number": f"{random.randint(1000000000, 9999999999)}",
                "bank_account_type": "savings",
                "has_other_loans": random.choice([True, False]),
                "other_loans_details": self._generate_loan_details(max_loans=3)
            }
        }
    
    def generate_missing_id_profile(self) -> Dict[str, Any]:
        """Generate customer profile with missing or invalid ID documentation."""
        return {
            "personal_info": {
                "first_name": f"MissingID{random.randint(1000, 9999)}",
                "last_name": f"User{random.randint(100, 999)}",
                "date_of_birth": self._random_adult_birthdate(),
                "gender": random.choice(["male", "female"]),
                "id_number": "",  # Missing ID number
                "marital_status": "single"
            },
            "contact_info": {
                "phone_number": f"+254{random.randint(700000000, 799999999)}",
                "email": f"missingid{random.randint(1000, 9999)}@example.com",
                "address_line1": "No Fixed Address",
                "city": random.choice(self.cities),
                "country": random.choice(self.countries)
            },
            "financial_info": {
                "employment_status": "unemployed",
                "monthly_income": 0,
                "employment_duration_months": 0,
                "bank_name": "",  # No bank account
                "bank_account_number": "",
                "bank_account_type": "",
                "has_other_loans": False,
                "other_loans_details": []
            },
            "documents": {
                "id_document_available": False,
                "alternative_documents": ["utility_bill", "employer_letter"]
            }
        }
    
    def generate_invalid_age_profile(self, age_type: str = "too_young") -> Dict[str, Any]:
        """Generate customer profile with invalid age."""
        if age_type == "too_young":
            birth_date = date.today() - timedelta(days=random.randint(365*10, 365*17))  # 10-17 years old
        elif age_type == "too_old":
            birth_date = date.today() - timedelta(days=random.randint(365*80, 365*95))  # 80-95 years old
        else:
            birth_date = self._random_adult_birthdate()
            
        return {
            "personal_info": {
                "first_name": f"InvalidAge{random.randint(1000, 9999)}",
                "last_name": f"User{random.randint(100, 999)}",
                "date_of_birth": birth_date.strftime("%Y-%m-%d"),
                "gender": random.choice(["male", "female"]),
                "id_number": f"ID{random.randint(10000000, 99999999)}",
                "marital_status": "single" if age_type == "too_young" else "married"
            },
            "contact_info": {
                "phone_number": f"+254{random.randint(700000000, 799999999)}",
                "email": f"invalidage{random.randint(1000, 9999)}@example.com",
                "address_line1": f"{random.randint(1, 999)} Age Test Street",
                "city": random.choice(self.cities),
                "country": random.choice(self.countries)
            },
            "financial_info": {
                "employment_status": "employed" if age_type == "too_old" else "student",
                "monthly_income": random.randint(200, 500),
                "employment_duration_months": random.randint(1, 12),
                "bank_name": random.choice(self.banks),
                "bank_account_number": f"{random.randint(1000000000, 9999999999)}",
                "bank_account_type": "savings",
                "has_other_loans": False,
                "other_loans_details": []
            }
        }
    
    def generate_high_debt_profile(self) -> Dict[str, Any]:
        """Generate customer profile with very high debt-to-income ratio."""
        monthly_income = random.randint(1000, 3000)
        total_debt = monthly_income * random.uniform(2.0, 5.0)  # 200-500% debt ratio
        
        return {
            "personal_info": {
                "first_name": f"HighDebt{random.randint(1000, 9999)}",
                "last_name": f"User{random.randint(100, 999)}",
                "date_of_birth": self._random_adult_birthdate(),
                "gender": random.choice(["male", "female"]),
                "id_number": f"ID{random.randint(10000000, 99999999)}",
                "marital_status": random.choice(["married", "divorced"])
            },
            "contact_info": {
                "phone_number": f"+254{random.randint(700000000, 799999999)}",
                "email": f"highdebt{random.randint(1000, 9999)}@example.com",
                "address_line1": f"{random.randint(1, 999)} Debt Street",
                "city": random.choice(self.cities),
                "country": random.choice(self.countries)
            },
            "financial_info": {
                "employment_status": "employed",
                "monthly_income": monthly_income,
                "employment_duration_months": random.randint(6, 24),
                "bank_name": random.choice(self.banks),
                "bank_account_number": f"{random.randint(1000000000, 9999999999)}",
                "bank_account_type": "current",
                "has_other_loans": True,
                "other_loans_details": self._generate_high_debt_loans(total_debt)
            }
        }
    
    def generate_perfect_profile(self) -> Dict[str, Any]:
        """Generate ideal customer profile for comparison."""
        return {
            "personal_info": {
                "first_name": f"Perfect{random.randint(1000, 9999)}",
                "last_name": f"Customer{random.randint(100, 999)}",
                "date_of_birth": self._random_adult_birthdate(min_age=25, max_age=45),
                "gender": random.choice(["male", "female"]),
                "id_number": f"ID{random.randint(10000000, 99999999)}",
                "marital_status": "married"
            },
            "contact_info": {
                "phone_number": f"+254{random.randint(700000000, 799999999)}",
                "email": f"perfect{random.randint(1000, 9999)}@example.com",
                "address_line1": f"{random.randint(1, 999)} Success Avenue",
                "city": random.choice(self.cities),
                "country": random.choice(self.countries)
            },
            "financial_info": {
                "employment_status": "employed",
                "monthly_income": random.randint(5000, 15000),  # High income
                "employment_duration_months": random.randint(24, 120),  # Stable employment
                "bank_name": random.choice(self.banks),
                "bank_account_number": f"{random.randint(1000000000, 9999999999)}",
                "bank_account_type": "current",
                "has_other_loans": False,  # No existing debt
                "other_loans_details": []
            }
        }
    
    def generate_malformed_ocr_scenarios(self) -> List[Dict[str, Any]]:
        """Generate scenarios for testing OCR failure handling."""
        return [
            {
                "scenario": "corrupted_image",
                "document_type": "national_id",
                "ocr_result": {
                    'ocr_text': '###CORRUPTED###',
                    'extracted_data': {},
                    'confidence': 0.0,
                    'processing_status': 'failed',
                    'error': 'Image corrupted or unreadable'
                }
            },
            {
                "scenario": "low_quality_scan",
                "document_type": "passport",
                "ocr_result": {
                    'ocr_text': 'blurry text partial data',
                    'extracted_data': {'partial_name': 'J**n D*e'},
                    'confidence': 15.0,
                    'processing_status': 'completed',
                    'warnings': ['Low image quality', 'Partial data extraction']
                }
            },
            {
                "scenario": "wrong_document_type",
                "document_type": "national_id",
                "ocr_result": {
                    'ocr_text': 'BIRTH CERTIFICATE',
                    'extracted_data': {},
                    'confidence': 85.0,
                    'processing_status': 'failed',
                    'error': 'Document type mismatch'
                }
            },
            {
                "scenario": "foreign_document",
                "document_type": "passport",
                "ocr_result": {
                    'ocr_text': 'ПАСПОРТ РОССИЙСКОЙ ФЕДЕРАЦИИ',
                    'extracted_data': {},
                    'confidence': 20.0,
                    'processing_status': 'failed',
                    'error': 'Language not supported'
                }
            }
        ]
    
    def _random_adult_birthdate(self, min_age: int = 18, max_age: int = 65) -> str:
        """Generate random birthdate for adult."""
        today = date.today()
        min_date = today - timedelta(days=max_age * 365)
        max_date = today - timedelta(days=min_age * 365)
        
        random_date = min_date + timedelta(
            days=random.randint(0, (max_date - min_date).days)
        )
        return random_date.strftime("%Y-%m-%d")
    
    def _generate_loan_details(self, max_loans: int = 2) -> List[Dict[str, Any]]:
        """Generate other loan details."""
        num_loans = random.randint(0, max_loans)
        loans = []
        
        for _ in range(num_loans):
            loans.append({
                "lender": random.choice(["MFI A", "Bank B", "SACCO C", "Mobile Money"]),
                "amount": random.randint(1000, 50000),
                "monthly_payment": random.randint(100, 2000),
                "remaining_balance": random.randint(500, 30000),
                "loan_type": random.choice(["personal", "business", "emergency"])
            })
        
        return loans
    
    def _generate_high_debt_loans(self, total_debt: float) -> List[Dict[str, Any]]:
        """Generate high debt loan details."""
        num_loans = random.randint(3, 7)  # Multiple loans
        loans = []
        remaining_debt = total_debt
        
        for i in range(num_loans):
            if i == num_loans - 1:
                # Last loan gets remaining debt
                amount = remaining_debt
            else:
                amount = remaining_debt * random.uniform(0.1, 0.4)
                remaining_debt -= amount
            
            loans.append({
                "lender": random.choice(["MFI A", "Bank B", "SACCO C", "Mobile Money", "Credit Card"]),
                "amount": int(amount),
                "monthly_payment": int(amount * random.uniform(0.05, 0.15)),
                "remaining_balance": int(amount * random.uniform(0.6, 0.9)),
                "loan_type": random.choice(["personal", "business", "emergency", "credit_card"])
            })
        
        return loans

# Convenience functions for test usage
def create_edge_case_dataset(num_samples: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Create a comprehensive dataset of edge cases."""
    generator = EdgeCaseDataGenerator()
    
    dataset = {
        "low_income_profiles": [],
        "missing_id_profiles": [],
        "invalid_age_profiles": [],
        "high_debt_profiles": [],
        "perfect_profiles": [],
        "ocr_scenarios": generator.generate_malformed_ocr_scenarios()
    }
    
    for _ in range(num_samples):
        dataset["low_income_profiles"].append(generator.generate_low_income_profile())
        dataset["missing_id_profiles"].append(generator.generate_missing_id_profile())
        dataset["invalid_age_profiles"].append(generator.generate_invalid_age_profile("too_young"))
        dataset["invalid_age_profiles"].append(generator.generate_invalid_age_profile("too_old"))
        dataset["high_debt_profiles"].append(generator.generate_high_debt_profile())
        dataset["perfect_profiles"].append(generator.generate_perfect_profile())
    
    return dataset

def save_test_dataset(filename: str = "edge_case_test_data.json"):
    """Save edge case dataset to JSON file."""
    import json
    
    dataset = create_edge_case_dataset(50)  # Generate 50 samples of each type
    
    with open(filename, 'w') as f:
        json.dump(dataset, f, indent=2, default=str)
    
    print(f"Test dataset saved to {filename}")
    return dataset