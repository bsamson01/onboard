from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.database import get_async_db
from app.models.user import User
from app.models.onboarding import (
    Customer, OnboardingApplication, OnboardingStep, Document,
    OnboardingStatus, DocumentType, DocumentStatus
)
from app.schemas.onboarding import (
    OnboardingApplicationResponse, OnboardingApplicationCreate,
    OnboardingStepRequest, PersonalInfoRequest, ContactInfoRequest,
    FinancialProfileRequest, ConsentRequest, DocumentUploadResponse,
    OnboardingProgressResponse, OnboardingSubmissionResponse,
    EligibilityResult
)
from app.services.ocr_service import OCRService
from app.services.scorecard_service import ScorecardService
from app.services.file_service import FileService
from app.services.audit_service import AuditService
from app.core.auth import get_current_user

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Initialize services
ocr_service = OCRService()
scorecard_service = ScorecardService()
file_service = FileService()
audit_service = AuditService()

# Step configurations
ONBOARDING_STEPS = {
    1: {"name": "Personal Information", "required_fields": ["first_name", "last_name", "date_of_birth", "gender", "id_number"]},
    2: {"name": "Contact Information", "required_fields": ["phone_number", "email", "address_line1", "city", "country"]},
    3: {"name": "Financial Profile", "required_fields": ["employment_status", "monthly_income"]},
    4: {"name": "Document Upload", "required_fields": []},
    5: {"name": "Consent & Scoring", "required_fields": ["consent_data_processing", "consent_credit_check"]}
}


@router.post("/applications", response_model=OnboardingApplicationResponse)
async def create_onboarding_application(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Create a new onboarding application for the current user."""
    try:
        # Check if user already has an active application
        existing_app_stmt = select(OnboardingApplication).join(Customer).where(
            Customer.user_id == current_user.id,
            OnboardingApplication.status.in_([
                OnboardingStatus.DRAFT,
                OnboardingStatus.IN_PROGRESS,
                OnboardingStatus.PENDING_DOCUMENTS,
                OnboardingStatus.UNDER_REVIEW
            ])
        )
        existing_app = await session.execute(existing_app_stmt)
        if existing_app.scalar():
            raise HTTPException(
                status_code=400,
                detail="You already have an active onboarding application. Please complete it first."
            )
        
        # Create or get customer record
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer:
            # Create new customer record
            customer = Customer(
                user_id=current_user.id,
                customer_number=f"CUST{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
            )
            session.add(customer)
            await session.flush()  # Get the customer ID
        
        # Generate application number
        app_number = f"ONB{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Create onboarding application
        application = OnboardingApplication(
            customer_id=customer.id,
            application_number=app_number,
            status=OnboardingStatus.DRAFT,
            current_step=1,
            total_steps=5
        )
        session.add(application)
        await session.flush()
        
        # Create initial step records
        for step_num in range(1, 6):
            step = OnboardingStep(
                application_id=application.id,
                step_number=step_num,
                step_name=ONBOARDING_STEPS[step_num]["name"],
                step_data={},
                is_completed=False
            )
            session.add(step)
        
        await session.commit()
        
        # Log application creation
        await audit_service.log_application_created(
            user_id=str(current_user.id),
            application_id=str(application.id),
            application_data={"application_number": app_number, "status": application.status.value},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Return response
        steps_stmt = select(OnboardingStep).where(OnboardingStep.application_id == application.id)
        steps_result = await session.execute(steps_stmt)
        steps = steps_result.scalars().all()
        
        return OnboardingApplicationResponse(
            id=application.id,
            application_number=application.application_number,
            status=application.status,
            current_step=application.current_step,
            total_steps=application.total_steps,
            progress_percentage=application.progress_percentage,
            steps=[
                {
                    "id": step.id,
                    "step_number": step.step_number,
                    "step_name": step.step_name,
                    "is_completed": step.is_completed,
                    "completed_at": step.completed_at,
                    "step_data": step.step_data
                } for step in steps
            ],
            created_at=application.created_at,
            updated_at=application.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create onboarding application: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create onboarding application")


@router.get("/applications", response_model=List[OnboardingApplicationResponse])
async def get_user_onboarding_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get all onboarding applications for the current user."""
    try:
        # Get applications for the current user
        stmt = select(OnboardingApplication).join(Customer).where(
            Customer.user_id == current_user.id
        ).order_by(OnboardingApplication.created_at.desc())
        
        result = await session.execute(stmt)
        applications = result.scalars().all()
        
        response_data = []
        for app in applications:
            # Get steps for each application
            steps_stmt = select(OnboardingStep).where(OnboardingStep.application_id == app.id)
            steps_result = await session.execute(steps_stmt)
            steps = steps_result.scalars().all()
            
            response_data.append(OnboardingApplicationResponse(
                id=app.id,
                application_number=app.application_number,
                status=app.status,
                current_step=app.current_step,
                total_steps=app.total_steps,
                progress_percentage=app.progress_percentage,
                steps=[
                    {
                        "id": step.id,
                        "step_number": step.step_number,
                        "step_name": step.step_name,
                        "is_completed": step.is_completed,
                        "completed_at": step.completed_at,
                        "step_data": step.step_data
                    } for step in steps
                ],
                created_at=app.created_at,
                updated_at=app.updated_at,
                submitted_at=app.submitted_at,
                completed_at=app.completed_at
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to get onboarding applications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve onboarding applications")


@router.get("/applications/{application_id}", response_model=OnboardingApplicationResponse)
async def get_onboarding_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get a specific onboarding application."""
    try:
        # Get application and verify ownership
        stmt = select(OnboardingApplication).join(Customer).where(
            OnboardingApplication.id == application_id,
            Customer.user_id == current_user.id
        )
        
        result = await session.execute(stmt)
        application = result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Onboarding application not found")
        
        # Get steps
        steps_stmt = select(OnboardingStep).where(OnboardingStep.application_id == application.id)
        steps_result = await session.execute(steps_stmt)
        steps = steps_result.scalars().all()
        
        # Get eligibility result if available
        eligibility_result = None
        if application.initial_score and application.eligibility_result:
            eligibility_result = EligibilityResult(
                score=application.initial_score,
                grade=application.score_breakdown.get("grade", "D") if application.score_breakdown else "D",
                eligibility=application.eligibility_result,
                message=application.score_breakdown.get("message", "") if application.score_breakdown else "",
                breakdown=application.score_breakdown,
                recommendations=application.score_breakdown.get("recommendations", []) if application.score_breakdown else []
            )
        
        return OnboardingApplicationResponse(
            id=application.id,
            application_number=application.application_number,
            status=application.status,
            current_step=application.current_step,
            total_steps=application.total_steps,
            progress_percentage=application.progress_percentage,
            steps=[
                {
                    "id": step.id,
                    "step_number": step.step_number,
                    "step_name": step.step_name,
                    "is_completed": step.is_completed,
                    "completed_at": step.completed_at,
                    "step_data": step.step_data
                } for step in steps
            ],
            eligibility_result=eligibility_result,
            created_at=application.created_at,
            updated_at=application.updated_at,
            submitted_at=application.submitted_at,
            completed_at=application.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding application: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve onboarding application")


@router.post("/applications/{application_id}/steps/{step_number}")
async def complete_onboarding_step(
    application_id: str,
    step_number: int,
    step_request: OnboardingStepRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Complete a specific step in the onboarding process."""
    try:
        # Validate step number
        if step_number not in ONBOARDING_STEPS:
            raise HTTPException(status_code=400, detail="Invalid step number")
        
        # Get application and verify ownership
        app_stmt = select(OnboardingApplication).join(Customer).where(
            OnboardingApplication.id == application_id,
            Customer.user_id == current_user.id
        )
        app_result = await session.execute(app_stmt)
        application = app_result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Onboarding application not found")
        
        # Validate application can be modified
        if application.status not in [OnboardingStatus.DRAFT, OnboardingStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=400, 
                detail="Application cannot be modified in its current status. Please contact support if you need to make changes."
            )
        
        # Get the specific step
        step_stmt = select(OnboardingStep).where(
            OnboardingStep.application_id == application_id,
            OnboardingStep.step_number == step_number
        )
        step_result = await session.execute(step_stmt)
        step = step_result.scalar()
        
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        # Process step data based on step number
        processed_data = await _process_step_data(
            step_number, step_request.step_data, application_id, current_user, session
        )
        
        # Update step
        step.step_data = processed_data
        step.is_completed = True
        step.completed_at = datetime.utcnow()
        
        # Update application progress
        completed_steps = await session.execute(
            select(OnboardingStep).where(
                OnboardingStep.application_id == application_id,
                OnboardingStep.is_completed == True
            )
        )
        completed_count = len(completed_steps.scalars().all())
        
        # Update application current step and status
        if completed_count >= application.total_steps:
            application.current_step = application.total_steps
            application.status = OnboardingStatus.PENDING_DOCUMENTS if step_number < 4 else OnboardingStatus.UNDER_REVIEW
        else:
            application.current_step = min(max(application.current_step, step_number + 1), application.total_steps)
            application.status = OnboardingStatus.IN_PROGRESS
        
        await session.commit()
        
        # Log step completion
        await audit_service.log_step_completed(
            user_id=str(current_user.id),
            application_id=application_id,
            step_number=step_number,
            step_name=step.step_name,
            step_data=processed_data,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "message": f"Step {step_number} completed successfully",
            "step_data": processed_data,
            "current_step": application.current_step,
            "progress_percentage": application.progress_percentage,
            "status": application.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete step {step_number}: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete onboarding step")


async def _process_step_data(
    step_number: int, 
    step_data: dict, 
    application_id: str, 
    current_user: User, 
    session: AsyncSession
) -> dict:
    """Process and validate step data based on step number."""
    
    if step_number == 1:  # Personal Information
        return await _process_personal_info_step(step_data, application_id, current_user, session)
    elif step_number == 2:  # Contact Information
        return await _process_contact_info_step(step_data, application_id, current_user, session)
    elif step_number == 3:  # Financial Profile
        return await _process_financial_profile_step(step_data, application_id, current_user, session)
    elif step_number == 4:  # Document Upload (handled separately)
        # Check if at least one ID document has been uploaded
        customer_stmt = select(Customer).join(OnboardingApplication).where(
            OnboardingApplication.id == application_id
        )
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Check for uploaded ID documents
            docs_stmt = select(Document).where(
                Document.customer_id == customer.id,
                Document.document_type.in_([DocumentType.NATIONAL_ID, DocumentType.PASSPORT])
            )
            id_docs = await session.execute(docs_stmt)
            if not id_docs.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Please upload at least one ID document (Government ID or Passport) before proceeding"
                )
        
        return step_data
    elif step_number == 5:  # Consent & Scoring
        return await _process_consent_and_scoring_step(step_data, application_id, current_user, session)
    else:
        return step_data


async def _process_personal_info_step(step_data: dict, application_id: str, current_user: User, session: AsyncSession) -> dict:
    """Process personal information step and update customer record."""
    try:
        # Validate required fields
        required_fields = ONBOARDING_STEPS[1]["required_fields"]
        for field in required_fields:
            if field not in step_data or not step_data[field]:
                raise HTTPException(status_code=400, detail=f"Required field '{field}' is missing")
        
        # Get customer record
        customer_stmt = select(Customer).join(OnboardingApplication).where(
            OnboardingApplication.id == application_id
        )
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Convert date string to date object if provided
            date_of_birth = None
            if step_data.get('date_of_birth'):
                try:
                    from datetime import datetime
                    date_of_birth = datetime.strptime(step_data['date_of_birth'], '%Y-%m-%d').date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
            # Update customer with personal information
            customer.date_of_birth = date_of_birth
            customer.gender = step_data.get('gender')
            customer.marital_status = step_data.get('marital_status')
            customer.nationality = step_data.get('nationality')
            customer.id_number = step_data.get('id_number')
            customer.id_type = step_data.get('id_type', 'national_id')
            
            # Also update user record with names
            user_stmt = select(User).where(User.id == current_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar()
            if user:
                user.first_name = step_data.get('first_name', user.first_name)
                user.last_name = step_data.get('last_name', user.last_name)
        
        return step_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process personal info step: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process personal information")


async def _process_contact_info_step(step_data: dict, application_id: str, current_user: User, session: AsyncSession) -> dict:
    """Process contact information step and update customer record."""
    try:
        # Validate required fields
        required_fields = ONBOARDING_STEPS[2]["required_fields"]
        for field in required_fields:
            if field not in step_data or not step_data[field]:
                raise HTTPException(status_code=400, detail=f"Required field '{field}' is missing")
        
        # Get customer record
        customer_stmt = select(Customer).join(OnboardingApplication).where(
            OnboardingApplication.id == application_id
        )
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Update customer with contact information
            customer.address_line1 = step_data.get('address_line1')
            customer.address_line2 = step_data.get('address_line2')
            customer.city = step_data.get('city')
            customer.state_province = step_data.get('state_province')
            customer.postal_code = step_data.get('postal_code')
            customer.country = step_data.get('country')
            customer.emergency_contact_name = step_data.get('emergency_contact_name')
            customer.emergency_contact_phone = step_data.get('emergency_contact_phone')
            customer.emergency_contact_relationship = step_data.get('emergency_contact_relationship')
            
            # Update user phone and email
            user_stmt = select(User).where(User.id == current_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar()
            if user:
                user.phone_number = step_data.get('phone_number', user.phone_number)
                user.email = step_data.get('email', user.email)
        
        return step_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process contact info step: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process contact information")


async def _process_financial_profile_step(step_data: dict, application_id: str, current_user: User, session: AsyncSession) -> dict:
    """Process financial profile step and update customer record."""
    try:
        # Validate required fields
        required_fields = ONBOARDING_STEPS[3]["required_fields"]
        for field in required_fields:
            if field not in step_data or not step_data[field]:
                raise HTTPException(status_code=400, detail=f"Required field '{field}' is missing")
        
        # Conditional validation for bank details
        number_of_bank_accounts = step_data.get('number_of_bank_accounts', 0)
        if number_of_bank_accounts and number_of_bank_accounts > 0:
            # If user has bank accounts, bank details are required
            bank_required_fields = ['bank_name', 'bank_account_number']
            for field in bank_required_fields:
                if field not in step_data or not step_data[field]:
                    raise HTTPException(status_code=400, detail=f"Required field '{field}' is missing when you have bank accounts")
        
        # Get customer record
        customer_stmt = select(Customer).join(OnboardingApplication).where(
            OnboardingApplication.id == application_id
        )
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Update customer with financial information
            customer.employment_status = step_data.get('employment_status')
            customer.employer_name = step_data.get('employer_name')
            customer.job_title = step_data.get('job_title')
            customer.monthly_income = step_data.get('monthly_income')
            customer.employment_duration_months = step_data.get('employment_duration_months')
            
            # Only set bank details if user has bank accounts
            if number_of_bank_accounts and number_of_bank_accounts > 0:
                customer.bank_name = step_data.get('bank_name')
                customer.bank_account_number = step_data.get('bank_account_number')
                customer.bank_account_type = step_data.get('bank_account_type')
            else:
                # Clear bank details if no accounts
                customer.bank_name = None
                customer.bank_account_number = None
                customer.bank_account_type = None
            
            customer.has_other_loans = step_data.get('has_other_loans', False)
            customer.other_loans_details = step_data.get('other_loans_details', [])
        
        return step_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process financial profile step: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process financial profile")


async def _process_consent_and_scoring_step(step_data: dict, application_id: str, current_user: User, session: AsyncSession) -> dict:
    """Process consent and trigger credit scoring."""
    try:
        # Validate required consents
        required_consents = ['consent_data_processing', 'consent_credit_check']
        for field in required_consents:
            if field not in step_data or not step_data[field]:
                raise HTTPException(status_code=400, detail=f"Required consent '{field}' is missing")
        
        # Update customer consent preferences
        customer_stmt = select(Customer).join(OnboardingApplication).where(
            OnboardingApplication.id == application_id
        )
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            customer.consent_data_processing = step_data.get('consent_data_processing')
            customer.consent_credit_check = step_data.get('consent_credit_check')
            customer.consent_marketing = step_data.get('consent_marketing', False)
            customer.preferred_communication = step_data.get('preferred_communication', 'email')
        
        # Trigger credit scoring if consents are given
        if step_data.get('consent_data_processing') and step_data.get('consent_credit_check'):
            try:
                # Get all customer data for scoring
                personal_data = await _get_customer_personal_data(application_id, session)
                financial_data = await _get_customer_financial_data(application_id, session)
                
                # Calculate credit score
                eligibility_result = await scorecard_service.calculate_score(personal_data, financial_data)
                
                # Update application with scoring results
                app_stmt = select(OnboardingApplication).where(OnboardingApplication.id == application_id)
                app_result = await session.execute(app_stmt)
                application = app_result.scalar()
                
                if application:
                    application.initial_score = eligibility_result.score
                    application.eligibility_result = eligibility_result.eligibility
                    application.score_breakdown = {
                        "grade": eligibility_result.grade,
                        "message": eligibility_result.message,
                        "breakdown": eligibility_result.breakdown,
                        "recommendations": eligibility_result.recommendations
                    }
                
                # Add scoring results to step data
                step_data['scoring_results'] = {
                    "score": eligibility_result.score,
                    "grade": eligibility_result.grade,
                    "eligibility": eligibility_result.eligibility,
                    "message": eligibility_result.message
                }
                
            except Exception as e:
                logger.warning(f"Credit scoring failed for application {application_id}: {str(e)}")
                step_data['scoring_results'] = {
                    "status": "pending",
                    "message": "Credit assessment is being processed. You will be notified when complete."
                }
        
        return step_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process consent and scoring step: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process consent and scoring")


@router.post("/applications/{application_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    application_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Upload a document for the onboarding application."""
    try:
        # Verify application ownership
        app_stmt = select(OnboardingApplication).join(Customer).where(
            OnboardingApplication.id == application_id,
            Customer.user_id == current_user.id
        )
        app_result = await session.execute(app_stmt)
        application = app_result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Onboarding application not found")
        
        # Get customer
        customer_stmt = select(Customer).where(Customer.id == application.customer_id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        # Upload file using file service
        file_record = await file_service.upload_document(
            file=file,
            customer_id=str(customer.id),
            document_type=document_type.value,
            application_id=application_id
        )
        
        # Create document record in database
        document = Document(
            customer_id=customer.id,
            document_type=document_type,
            document_name=file_record['original_filename'],
            file_path=file_record['file_path'],
            file_size=file_record['file_size'],
            mime_type=file_record['mime_type'],
            original_filename=file_record['original_filename'],
            status=DocumentStatus.UPLOADED
        )
        session.add(document)
        await session.flush()
        
        # Process document with OCR if it's an ID document
        if document_type in [DocumentType.NATIONAL_ID, DocumentType.PASSPORT]:
            try:
                ocr_results = await ocr_service.process_document(
                    file_record['full_path'], 
                    document_type.value
                )
                
                # Update document with OCR results
                document.ocr_text = ocr_results.get('ocr_text', '')
                document.ocr_confidence = ocr_results.get('confidence', 0.0)
                document.extracted_data = ocr_results.get('extracted_data', {})
                
                if ocr_results.get('processing_status') == 'completed':
                    document.status = DocumentStatus.PROCESSING
                    document.processed_at = datetime.utcnow()
                    
                    # Auto-fill customer data if OCR extracted useful information
                    if document.extracted_data:
                        await _autofill_customer_data_from_ocr(
                            customer, document.extracted_data, session
                        )
                
                # Log OCR processing
                await audit_service.log_ocr_processed(
                    user_id=str(current_user.id),
                    document_id=str(document.id),
                    ocr_results=ocr_results,
                    ip_address=request.client.host if request else None
                )
                
            except Exception as e:
                logger.warning(f"OCR processing failed for document {document.id}: {str(e)}")
                # Don't fail the upload if OCR fails
        
        await session.commit()
        
        # Log document upload
        await audit_service.log_document_uploaded(
            user_id=str(current_user.id),
            application_id=application_id,
            document_id=str(document.id),
            document_type=document_type.value,
            file_info=file_record,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return DocumentUploadResponse(
            id=document.id,
            document_type=document.document_type,
            document_name=document.document_name,
            file_path=document.file_path,
            file_size=document.file_size,
            status=document.status,
            uploaded_at=document.uploaded_at,
            ocr_confidence=document.ocr_confidence,
            extracted_data=document.extracted_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.post("/applications/{application_id}/submit", response_model=OnboardingSubmissionResponse)
async def submit_onboarding_application(
    application_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Submit the completed onboarding application for review."""
    try:
        # Get application and verify ownership
        app_stmt = select(OnboardingApplication).join(Customer).where(
            OnboardingApplication.id == application_id,
            Customer.user_id == current_user.id
        )
        app_result = await session.execute(app_stmt)
        application = app_result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Onboarding application not found")
        
        # Validate all steps are completed
        steps_stmt = select(OnboardingStep).where(
            OnboardingStep.application_id == application_id,
            OnboardingStep.is_completed == False
        )
        incomplete_steps = await session.execute(steps_stmt)
        incomplete_steps_list = incomplete_steps.scalars().all()
        
        if incomplete_steps_list:
            incomplete_step_names = [step.step_name for step in incomplete_steps_list]
            raise HTTPException(
                status_code=400,
                detail=f"Please complete all steps before submitting. Incomplete steps: {', '.join(incomplete_step_names)}"
            )
        
        # Check if required documents are uploaded
        required_docs = await session.execute(
            select(Document).where(
                Document.customer_id == application.customer_id,
                Document.document_type.in_([DocumentType.NATIONAL_ID, DocumentType.PASSPORT])
            )
        )
        if not required_docs.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid ID document before submitting"
            )
        
        # Update application status
        application.status = OnboardingStatus.UNDER_REVIEW
        application.submitted_at = datetime.utcnow()
        
        await session.commit()
        
        # Log submission
        submission_data = {
            "application_number": application.application_number,
            "submitted_at": application.submitted_at.isoformat(),
            "eligibility_score": application.initial_score,
            "eligibility_result": application.eligibility_result
        }
        
        await audit_service.log_application_submitted(
            user_id=str(current_user.id),
            application_id=application_id,
            submission_data=submission_data,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Prepare eligibility result
        eligibility_result = None
        if application.initial_score and application.eligibility_result:
            eligibility_result = EligibilityResult(
                score=application.initial_score,
                grade=application.score_breakdown.get("grade", "D") if application.score_breakdown else "D",
                eligibility=application.eligibility_result,
                message=application.score_breakdown.get("message", "") if application.score_breakdown else "",
                breakdown=application.score_breakdown,
                recommendations=application.score_breakdown.get("recommendations", []) if application.score_breakdown else []
            )
        
        # Determine next actions
        next_actions = []
        if application.eligibility_result == "eligible":
            next_actions = [
                "Your application will be reviewed by our loan officers",
                "You may be contacted for additional information",
                "Loan terms will be finalized upon approval"
            ]
        elif application.eligibility_result == "ineligible":
            next_actions = [
                "Your application will be reviewed for alternative products",
                "You may be contacted with improvement suggestions",
                "Consider reapplying after addressing recommendations"
            ]
        else:
            next_actions = [
                "Your application is being processed",
                "Additional verification may be required",
                "You will be notified of the decision within 3-5 business days"
            ]
        
        return OnboardingSubmissionResponse(
            application_id=uuid.UUID(application_id),
            status=application.status,
            eligibility_result=eligibility_result,
            next_actions=next_actions,
            estimated_processing_time="3-5 business days",
            reference_number=application.application_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit application: {str(e)}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit onboarding application")


async def _get_customer_personal_data(application_id: str, session: AsyncSession) -> dict:
    """Get customer personal data for scoring."""
    stmt = select(Customer).join(OnboardingApplication).where(
        OnboardingApplication.id == application_id
    )
    result = await session.execute(stmt)
    customer = result.scalar()
    
    if not customer:
        return {}
    
    return {
        "date_of_birth": customer.date_of_birth,
        "gender": customer.gender,
        "marital_status": customer.marital_status,
        "nationality": customer.nationality,
        "city": customer.city,
        "state_province": customer.state_province,
        "country": customer.country
    }


async def _get_customer_financial_data(application_id: str, session: AsyncSession) -> dict:
    """Get customer financial data for scoring."""
    stmt = select(Customer).join(OnboardingApplication).where(
        OnboardingApplication.id == application_id
    )
    result = await session.execute(stmt)
    customer = result.scalar()
    
    if not customer:
        return {}
    
    return {
        "employment_status": customer.employment_status,
        "monthly_income": float(customer.monthly_income) if customer.monthly_income else 0.0,
        "employment_duration_months": customer.employment_duration_months,
        "bank_name": customer.bank_name,
        "bank_account_type": customer.bank_account_type,
        "has_other_loans": customer.has_other_loans,
        "other_loans_details": customer.other_loans_details or []
    }


async def _autofill_customer_data_from_ocr(customer: Customer, extracted_data: dict, session: AsyncSession):
    """Auto-fill customer data from OCR extracted information."""
    try:
        # Map OCR fields to customer fields
        if 'full_name' in extracted_data and not customer.user.first_name:
            name_parts = extracted_data['full_name'].split()
            if len(name_parts) >= 2:
                customer.user.first_name = name_parts[0]
                customer.user.last_name = ' '.join(name_parts[1:])
        
        if 'date_of_birth' in extracted_data and not customer.date_of_birth:
            try:
                from datetime import datetime
                customer.date_of_birth = datetime.strptime(extracted_data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass
        
        if 'id_number' in extracted_data and not customer.id_number:
            customer.id_number = extracted_data['id_number']
        
        if 'address' in extracted_data and not customer.address_line1:
            customer.address_line1 = extracted_data['address']
        
        if 'nationality' in extracted_data and not customer.nationality:
            customer.nationality = extracted_data['nationality']
            
    except Exception as e:
        logger.warning(f"Failed to auto-fill customer data from OCR: {str(e)}")


@router.get("/applications/{application_id}/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get detailed progress information for an onboarding application."""
    try:
        # Get application and verify ownership
        app_stmt = select(OnboardingApplication).join(Customer).where(
            OnboardingApplication.id == application_id,
            Customer.user_id == current_user.id
        )
        app_result = await session.execute(app_stmt)
        application = app_result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Onboarding application not found")
        
        # Get completed steps
        completed_steps_stmt = select(OnboardingStep).where(
            OnboardingStep.application_id == application_id,
            OnboardingStep.is_completed == True
        )
        completed_steps_result = await session.execute(completed_steps_stmt)
        completed_steps = completed_steps_result.scalars().all()
        
        steps_completed = [step.step_name for step in completed_steps]
        
        # Determine next step
        next_step = None
        if application.current_step <= application.total_steps:
            next_step = ONBOARDING_STEPS.get(application.current_step, {}).get("name")
        
        # Check if can proceed (all previous steps completed)
        can_proceed = len(completed_steps) >= (application.current_step - 1)
        
        return OnboardingProgressResponse(
            application_id=uuid.UUID(application_id),
            current_step=application.current_step,
            total_steps=application.total_steps,
            progress_percentage=application.progress_percentage,
            steps_completed=steps_completed,
            next_step=next_step,
            can_proceed=can_proceed,
            validation_errors=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress information")