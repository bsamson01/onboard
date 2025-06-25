import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch

from app.models.onboarding import OnboardingStatus, DocumentType
from app.services.ocr_service import OCRService
from app.services.scorecard_service import ScorecardService

class TestOnboardingFlow:
    """Test complete onboarding workflow."""

    @pytest.mark.asyncio
    async def test_create_application(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test creating a new onboarding application."""
        # Create and login user first
        user_data = {
            "email": "onboard@example.com",
            "username": "onboarduser",
            "password": "password123",
            "first_name": "Onboard",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "onboard@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create application
        response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "in_progress"
        assert "application_number" in data

    @pytest.mark.asyncio
    async def test_complete_personal_info_step(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test completing personal information step."""
        # Setup user and application
        user_data = {
            "email": "personal@example.com",
            "username": "personaluser",
            "password": "password123",
            "first_name": "Personal",
            "last_name": "User"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "personal@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        app_response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
        app_id = app_response.json()["id"]
        
        # Complete step 1
        step_data = {
            "step_number": 1,
            "step_data": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "gender": "male",
                "id_number": "ID123456789"
            }
        }
        
        response = await async_client.post(
            f"/api/v1/onboarding/applications/{app_id}/steps/1",
            json=step_data,
            headers=headers
        )
        assert response.status_code == 200

class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_low_income_scenario(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test low income edge case."""
        # Setup complete application with low income
        user_data = {
            "email": "lowincome@example.com",
            "username": "lowincomeuser",
            "password": "password123",
            "first_name": "Low",
            "last_name": "Income"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "lowincome@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        app_response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
        app_id = app_response.json()["id"]
        
        # Complete financial step with very low income
        financial_data = {
            "step_number": 3,
            "step_data": {
                "employment_status": "employed",
                "monthly_income": 100,  # Very low income
                "bank_name": "Test Bank",
                "bank_account_number": "123456789"
            }
        }
        
        response = await async_client.post(
            f"/api/v1/onboarding/applications/{app_id}/steps/3",
            json=financial_data,
            headers=headers
        )
        
        # Should still accept but flag for review
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_age_scenario(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test invalid age (too young/old) scenario."""
        user_data = {
            "email": "invalidage@example.com",
            "username": "invalidageuser",
            "password": "password123",
            "first_name": "Invalid",
            "last_name": "Age"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": "invalidage@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        app_response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
        app_id = app_response.json()["id"]
        
        # Try with age under 18
        step_data = {
            "step_number": 1,
            "step_data": {
                "first_name": "Minor",
                "last_name": "User",
                "date_of_birth": "2010-01-15",  # Under 18
                "gender": "male",
                "id_number": "ID123456789"
            }
        }
        
        response = await async_client.post(
            f"/api/v1/onboarding/applications/{app_id}/steps/1",
            json=step_data,
            headers=headers
        )
        
        # Should reject or require special handling
        assert response.status_code in [400, 422]

class TestOCRValidation:
    """Test OCR processing and validation."""

    @pytest.mark.asyncio
    async def test_malformed_document_ocr(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test OCR handling of malformed documents."""
        with patch.object(OCRService, 'process_document') as mock_ocr:
            # Mock OCR failure
            mock_ocr.return_value = {
                'ocr_text': '',
                'extracted_data': {},
                'confidence': 0.0,
                'document_type': 'national_id',
                'processing_status': 'failed',
                'error': 'Unable to extract text from document'
            }
            
            # Setup user and upload document
            user_data = {
                "email": "ocrtest@example.com",
                "username": "ocrtestuser",
                "password": "password123",
                "first_name": "OCR",
                "last_name": "Test"
            }
            await async_client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await async_client.post("/api/v1/auth/login", data={
                "username": "ocrtest@example.com",
                "password": "password123"
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            app_response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
            app_id = app_response.json()["id"]
            
            # Mock file upload
            files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
            data = {"document_type": "national_id"}
            
            response = await async_client.post(
                f"/api/v1/onboarding/applications/{app_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            # Should handle OCR failure gracefully
            assert response.status_code == 200
            assert response.json()["ocr_confidence"] == 0.0

class TestScorecardIntegration:
    """Test scorecard service integration."""

    @pytest.mark.asyncio
    async def test_scorecard_service_unavailable(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test handling when scorecard service is unavailable."""
        with patch.object(ScorecardService, 'calculate_score') as mock_score:
            mock_score.side_effect = Exception("Scorecard service unavailable")
            
            # Setup complete application
            user_data = {
                "email": "scoretest@example.com",
                "username": "scoretestuser",
                "password": "password123",
                "first_name": "Score",
                "last_name": "Test"
            }
            await async_client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await async_client.post("/api/v1/auth/login", data={
                "username": "scoretest@example.com",
                "password": "password123"
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            app_response = await async_client.post("/api/v1/onboarding/applications", headers=headers)
            app_id = app_response.json()["id"]
            
            # Complete consent step (which triggers scoring)
            consent_data = {
                "step_number": 5,
                "step_data": {
                    "consent_data_processing": True,
                    "consent_credit_check": True
                }
            }
            
            response = await async_client.post(
                f"/api/v1/onboarding/applications/{app_id}/steps/5",
                json=consent_data,
                headers=headers
            )
            
            # Should handle scorecard failure gracefully
            assert response.status_code == 200
            assert "scoring_results" in response.json()["step_data"]
            assert response.json()["step_data"]["scoring_results"]["status"] == "pending"