from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Security
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional
import logging
from datetime import datetime
import uuid as uuid_lib
import os
from pathlib import Path

from app.database import get_async_db
from app.models.user import User, UserRole
from app.models.onboarding import Customer, Document, DocumentType, DocumentStatus
from app.core.auth import get_current_user
from app.schemas.profile import (
    ProfileStatusResponse, UserProfileResponse, ProfileUpdateRequest,
    DocumentResponse, DocumentUploadResponse, ProfileUpdateRequiredResponse
)
from app.services.user_state_service import UserStateService
from app.services.file_service import FileService
from app.services.audit_service import AuditService
from app.core.logging import log_audit_event, AuditEvent

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Initialize services
user_state_service = UserStateService()
file_service = FileService()
audit_service = AuditService()

# Security constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif'
}
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif'}


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    try:
        uuid_lib.UUID(uuid_string)
        return True
    except ValueError:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Remove path components and keep only the filename
    safe_filename = os.path.basename(filename)
    
    # Remove any remaining dangerous characters
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
    
    if not safe_filename:
        raise ValueError("Invalid filename")
    
    return safe_filename


def validate_file_security(file: UploadFile) -> None:
    """Validate file for security requirements."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"MIME type not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}")


async def get_customer_safely(user_id: str, session: AsyncSession) -> Optional[Customer]:
    """Safely retrieve customer with proper error handling."""
    try:
        if not validate_uuid(user_id):
            raise ValueError("Invalid user ID format")
        
        stmt = select(Customer).where(Customer.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving customer for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error retrieving customer data")
    except Exception as e:
        logger.error(f"Error retrieving customer for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving customer data")


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get complete user profile information."""
    try:
        # Validate user access
        if not current_user or not current_user.is_active:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get customer data safely
        customer = await get_customer_safely(str(current_user.id), session)
        customer_data = None
        documents_count = 0
        verified_documents_count = 0
        
        if customer:
            try:
                # Build customer data dictionary with safe access
                customer_data = {
                    "id": str(customer.id),
                    "customer_number": customer.customer_number,
                    "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                    "gender": customer.gender,
                    "marital_status": customer.marital_status,
                    "nationality": customer.nationality,
                    "id_number": customer.id_number,
                    "id_type": customer.id_type,
                    "address_line1": customer.address_line1,
                    "address_line2": customer.address_line2,
                    "city": customer.city,
                    "state_province": customer.state_province,
                    "postal_code": customer.postal_code,
                    "country": customer.country,
                    "emergency_contact_name": customer.emergency_contact_name,
                    "emergency_contact_phone": customer.emergency_contact_phone,
                    "emergency_contact_relationship": customer.emergency_contact_relationship,
                    "employment_status": customer.employment_status,
                    "employer_name": customer.employer_name,
                    "job_title": customer.job_title,
                    "monthly_income": float(customer.monthly_income) if customer.monthly_income else None,
                    "employment_duration_months": customer.employment_duration_months,
                    "bank_name": customer.bank_name,
                    "bank_account_number": customer.bank_account_number,
                    "bank_account_type": customer.bank_account_type,
                    "has_other_loans": customer.has_other_loans,
                    "other_loans_details": customer.other_loans_details,
                    "consent_data_processing": customer.consent_data_processing,
                    "consent_credit_check": customer.consent_credit_check,
                    "consent_marketing": customer.consent_marketing,
                    "preferred_communication": customer.preferred_communication,
                    "is_verified": customer.is_verified,
                    "verification_completed_at": customer.verification_completed_at.isoformat() if customer.verification_completed_at else None
                }
                
                # Get document counts safely
                try:
                    documents_count = await session.scalar(
                        select(func.count(Document.id)).where(Document.customer_id == customer.id)
                    ) or 0
                    
                    verified_documents_count = await session.scalar(
                        select(func.count(Document.id)).where(
                            and_(
                                Document.customer_id == customer.id,
                                Document.status == DocumentStatus.VERIFIED
                            )
                        )
                    ) or 0
                except SQLAlchemyError as e:
                    logger.warning(f"Failed to get document counts for user {current_user.id}: {str(e)}")
                    # Continue with 0 counts rather than failing
                    
            except Exception as e:
                logger.error(f"Error building customer data for user {current_user.id}: {str(e)}")
                # Continue without customer data rather than failing
        
        # Build response safely
        try:
            profile_response = UserProfileResponse(
                id=str(current_user.id),
                email=current_user.email,
                username=current_user.username,
                first_name=current_user.first_name or "",
                last_name=current_user.last_name or "",
                phone_number=current_user.phone_number,
                role=current_user.role,
                user_state=current_user.user_state,
                is_active=current_user.is_active,
                is_verified=current_user.is_verified,
                is_locked=current_user.is_locked,
                last_login=current_user.last_login,
                created_at=current_user.created_at,
                onboarding_completed_at=current_user.onboarding_completed_at,
                last_profile_update=current_user.last_profile_update,
                profile_expiry_date=current_user.profile_expiry_date,
                profile_completion_percentage=current_user.profile_completion_percentage,
                can_create_loans=current_user.can_create_loans,
                customer_data=customer_data,
                documents_count=documents_count,
                verified_documents_count=verified_documents_count
            )
            
            return profile_response
            
        except Exception as e:
            logger.error(f"Error building profile response for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error building profile response"
            )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting user profile for user {getattr(current_user, 'id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving profile"
        )
    except Exception as e:
        logger.error(f"Failed to get user profile for user {getattr(current_user, 'id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: ProfileUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Update user profile information."""
    try:
        # Update user basic information
        old_user_data = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number
        }
        
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        if profile_data.phone_number is not None:
            current_user.phone_number = profile_data.phone_number
        
        # Update profile timestamp
        current_user.last_profile_update = datetime.utcnow()
        
        # Get or create customer record
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer:
            # Create new customer record
            customer = Customer(
                user_id=current_user.id,
                customer_number=f"CUST{str(current_user.id)[:8].upper()}"
            )
            session.add(customer)
            await session.flush()  # Get the customer ID
        
        # Update customer data
        old_customer_data = {}
        if customer:
            old_customer_data = {
                "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                "gender": customer.gender,
                "marital_status": customer.marital_status,
                "nationality": customer.nationality,
                "id_number": customer.id_number,
                "id_type": customer.id_type,
                "employment_status": customer.employment_status,
                "employer_name": customer.employer_name,
                "job_title": customer.job_title,
                "monthly_income": float(customer.monthly_income) if customer.monthly_income else None
            }
            
            # Update customer fields
            if profile_data.date_of_birth is not None:
                from datetime import date
                customer.date_of_birth = date.fromisoformat(profile_data.date_of_birth) if profile_data.date_of_birth else None
            if profile_data.gender is not None:
                customer.gender = profile_data.gender
            if profile_data.marital_status is not None:
                customer.marital_status = profile_data.marital_status
            if profile_data.nationality is not None:
                customer.nationality = profile_data.nationality
            if profile_data.id_number is not None:
                customer.id_number = profile_data.id_number
            if profile_data.id_type is not None:
                customer.id_type = profile_data.id_type
            
            # Contact information
            if profile_data.address_line1 is not None:
                customer.address_line1 = profile_data.address_line1
            if profile_data.address_line2 is not None:
                customer.address_line2 = profile_data.address_line2
            if profile_data.city is not None:
                customer.city = profile_data.city
            if profile_data.state_province is not None:
                customer.state_province = profile_data.state_province
            if profile_data.postal_code is not None:
                customer.postal_code = profile_data.postal_code
            if profile_data.country is not None:
                customer.country = profile_data.country
            
            # Emergency contact
            if profile_data.emergency_contact_name is not None:
                customer.emergency_contact_name = profile_data.emergency_contact_name
            if profile_data.emergency_contact_phone is not None:
                customer.emergency_contact_phone = profile_data.emergency_contact_phone
            if profile_data.emergency_contact_relationship is not None:
                customer.emergency_contact_relationship = profile_data.emergency_contact_relationship
            
            # Employment information
            if profile_data.employment_status is not None:
                customer.employment_status = profile_data.employment_status
            if profile_data.employer_name is not None:
                customer.employer_name = profile_data.employer_name
            if profile_data.job_title is not None:
                customer.job_title = profile_data.job_title
            if profile_data.monthly_income is not None:
                customer.monthly_income = profile_data.monthly_income
            if profile_data.employment_duration_months is not None:
                customer.employment_duration_months = profile_data.employment_duration_months
            
            # Financial information
            if profile_data.bank_name is not None:
                customer.bank_name = profile_data.bank_name
            if profile_data.bank_account_number is not None:
                customer.bank_account_number = profile_data.bank_account_number
            if profile_data.bank_account_type is not None:
                customer.bank_account_type = profile_data.bank_account_type
            if profile_data.has_other_loans is not None:
                customer.has_other_loans = profile_data.has_other_loans
            if profile_data.other_loans_details is not None:
                customer.other_loans_details = profile_data.other_loans_details
            
            # Consent and preferences
            if profile_data.consent_data_processing is not None:
                customer.consent_data_processing = profile_data.consent_data_processing
            if profile_data.consent_credit_check is not None:
                customer.consent_credit_check = profile_data.consent_credit_check
            if profile_data.consent_marketing is not None:
                customer.consent_marketing = profile_data.consent_marketing
            if profile_data.preferred_communication is not None:
                customer.preferred_communication = profile_data.preferred_communication
        
        await session.commit()
        
        # Log the profile update
        await audit_service.log_onboarding_action(
            user_id=str(current_user.id),
            action="profile_updated",
            resource_type="user_profile",
            resource_id=str(current_user.id),
            old_values={**old_user_data, **old_customer_data},
            new_values=profile_data.dict(exclude_unset=True),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            additional_data={"profile_update_timestamp": datetime.utcnow().isoformat()}
        )
        
        log_audit_event(
            AuditEvent.PROFILE_UPDATED,
            user_id=str(current_user.id),
            details={"ip_address": request.client.host}
        )
        
        # Return updated profile
        return await get_user_profile(current_user, session)
        
    except Exception as e:
        logger.error(f"Failed to update user profile for user {current_user.id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/profile/status", response_model=ProfileStatusResponse)
async def get_profile_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get user profile status."""
    try:
        # Check current state
        current_state = await user_state_service.check_user_state(current_user, session)
        
        status_response = ProfileStatusResponse(
            user_state=current_state,
            completion_percentage=current_user.profile_completion_percentage,
            needs_profile_update=current_user.needs_profile_update,
            is_profile_outdated=current_user.is_profile_outdated,
            onboarding_completed_at=current_user.onboarding_completed_at,
            last_profile_update=current_user.last_profile_update,
            profile_expiry_date=current_user.profile_expiry_date,
            can_create_loans=current_user.can_create_loans
        )
        
        return status_response
        
    except Exception as e:
        logger.error(f"Failed to get profile status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile status"
        )


@router.get("/profile/documents", response_model=List[DocumentResponse])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Get user's uploaded documents."""
    try:
        # Get customer record
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer:
            return []
        
        # Get documents
        documents_stmt = select(Document).where(Document.customer_id == customer.id)
        documents_result = await session.execute(documents_stmt)
        documents = documents_result.scalars().all()
        
        document_responses = []
        for doc in documents:
            doc_response = DocumentResponse(
                id=str(doc.id),
                document_type=doc.document_type,
                document_name=doc.document_name,
                status=doc.status,
                is_required=doc.is_required,
                expires_at=doc.expires_at.isoformat() if doc.expires_at else None,
                is_expired=doc.is_expired,
                uploaded_at=doc.uploaded_at,
                verified_at=doc.verified_at,
                verification_notes=doc.verification_notes,
                file_size=doc.file_size,
                mime_type=doc.mime_type
            )
            document_responses.append(doc_response)
        
        return document_responses
        
    except Exception as e:
        logger.error(f"Failed to get documents for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.post("/profile/documents", response_model=DocumentUploadResponse)
async def upload_document(
    document_type: DocumentType,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Upload a document for the user."""
    try:
        # Validate user access
        if not current_user or not current_user.is_active:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if current_user.is_locked:
            raise HTTPException(status_code=423, detail="Account is locked")
        
        # Validate file security first
        validate_file_security(file)
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Get customer record safely
        customer = await get_customer_safely(str(current_user.id), session)
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found. Please complete your profile first."
            )
        
        # Check for existing document of same type (prevent duplicates without proper handling)
        try:
            existing_doc_stmt = select(Document).where(
                and_(
                    Document.customer_id == customer.id,
                    Document.document_type == document_type,
                    Document.status != DocumentStatus.REJECTED
                )
            )
            existing_doc_result = await session.execute(existing_doc_stmt)
            existing_doc = existing_doc_result.scalar()
            
            if existing_doc:
                logger.info(f"User {current_user.id} replacing existing document of type {document_type}")
                # Mark old document as replaced rather than deleting
                existing_doc.status = DocumentStatus.REJECTED
                existing_doc.verification_notes = "Replaced with new upload"
                
        except SQLAlchemyError as e:
            logger.warning(f"Failed to check existing documents for user {current_user.id}: {str(e)}")
            # Continue with upload even if check fails
        
        # Read file content safely (with size limit)
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        # Reset file pointer for service
        await file.seek(0)
        
        try:
            # Save file using service
            file_path = await file_service.save_document(file, str(customer.id), document_type.value)
        except Exception as e:
            logger.error(f"Failed to save file for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file"
            )
        
        # Create document record with transaction safety
        try:
            document = Document(
                customer_id=customer.id,
                document_type=document_type,
                document_name=safe_filename,
                file_path=file_path,
                file_size=len(file_content),
                mime_type=file.content_type,
                original_filename=safe_filename,
                status=DocumentStatus.UPLOADED,
                is_required=True
            )
            
            session.add(document)
            await session.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating document record for user {current_user.id}: {str(e)}")
            # Clean up uploaded file if database operation fails
            try:
                await file_service.delete_document(file_path)
            except:
                pass  # Log but don't fail on cleanup error
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document record"
            )
        
        # Log document upload (outside transaction)
        try:
            await audit_service.log_onboarding_action(
                user_id=str(current_user.id),
                action="document_uploaded",
                resource_type="document",
                resource_id=str(document.id),
                additional_data={
                    "document_type": document_type.value,
                    "file_name": safe_filename,
                    "file_size": len(file_content),
                    "mime_type": file.content_type,
                    "original_filename": file.filename
                }
            )
        except Exception as e:
            logger.error(f"Failed to log document upload for user {current_user.id}: {str(e)}")
            # Don't fail operation due to logging error
        
        response = DocumentUploadResponse(
            document_id=str(document.id),
            document_type=document_type,
            document_name=safe_filename,
            status=DocumentStatus.UPLOADED,
            file_size=len(file_content),
            mime_type=file.content_type,
            uploaded_at=document.uploaded_at
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document for user {getattr(current_user, 'id', 'unknown')}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.delete("/profile/documents/{document_id}")
async def delete_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Delete a user's document."""
    try:
        # Get customer record
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found"
            )
        
        # Get document
        document_stmt = select(Document).where(
            and_(
                Document.id == document_id,
                Document.customer_id == customer.id
            )
        )
        document_result = await session.execute(document_stmt)
        document = document_result.scalar()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if document can be deleted (not verified)
        if document.status == DocumentStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete verified documents"
            )
        
        # Delete file
        await file_service.delete_document(document.file_path)
        
        # Delete document record
        await session.delete(document)
        await session.commit()
        
        # Log document deletion
        await audit_service.log_onboarding_action(
            user_id=str(current_user.id),
            action="document_deleted",
            resource_type="document",
            resource_id=document_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            additional_data={
                "document_type": document.document_type.value,
                "document_name": document.document_name
            }
        )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id} for user {current_user.id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/profile/update-required", response_model=ProfileUpdateRequiredResponse)
async def check_update_requirements(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """Check if profile update is required and what needs to be updated."""
    try:
        # Check current state
        current_state = await user_state_service.check_user_state(current_user, session)
        
        # Determine if update is required
        update_required = False
        reason = None
        expired_fields = []
        missing_documents = []
        required_actions = []
        
        if current_state == UserState.OUTDATED:
            update_required = True
            reason = "Profile information is outdated and needs to be refreshed"
            expired_fields = ["profile_information", "document_verification"]
            required_actions = [
                "Update personal information",
                "Upload new documents",
                "Renew consent agreements"
            ]
        elif current_state == UserState.REGISTERED:
            update_required = True
            reason = "Profile is incomplete - onboarding required"
            required_actions = ["Complete onboarding process"]
        
        # Check for missing documents if customer exists
        customer_stmt = select(Customer).where(Customer.user_id == current_user.id)
        customer_result = await session.execute(customer_stmt)
        customer = customer_result.scalar()
        
        if customer:
            # Get existing documents
            documents_stmt = select(Document).where(Document.customer_id == customer.id)
            documents_result = await session.execute(documents_stmt)
            existing_docs = documents_result.scalars().all()
            
            existing_types = {doc.document_type for doc in existing_docs}
            required_types = {DocumentType.NATIONAL_ID, DocumentType.PROOF_OF_RESIDENCE, DocumentType.BANK_STATEMENT}
            
            missing_documents = list(required_types - existing_types)
            
            if missing_documents:
                update_required = True
                if not reason:
                    reason = "Missing required documents"
                required_actions.extend([f"Upload {doc_type.value.replace('_', ' ').title()}" for doc_type in missing_documents])
        
        response = ProfileUpdateRequiredResponse(
            update_required=update_required,
            reason=reason,
            expired_fields=expired_fields,
            missing_documents=missing_documents,
            required_actions=required_actions
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to check update requirements for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check update requirements"
        )