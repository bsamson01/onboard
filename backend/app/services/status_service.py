from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException

from app.models.loan import LoanApplication, ApplicationStatus, ApplicationStatusHistory
from app.models.user import User, UserRole
from app.services.audit_service import AuditService


class StatusTransitionError(HTTPException):
    """Custom exception for invalid status transitions"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class StatusService:
    """Service for managing application status transitions and validation"""
    
    def __init__(self):
        self.audit_service = AuditService()
        
        # Define allowed status transitions and required roles
        self.allowed_transitions = {
            ApplicationStatus.IN_PROGRESS: {
                ApplicationStatus.SUBMITTED: ["customer"],  # Customer submits application
                ApplicationStatus.CANCELLED: ["customer"],  # Customer cancels
            },
            ApplicationStatus.SUBMITTED: {
                ApplicationStatus.UNDER_REVIEW: ["admin", "loan_officer", "risk_officer"],  # Staff starts review
                ApplicationStatus.CANCELLED: ["customer"],  # Customer can still cancel
                ApplicationStatus.REJECTED: ["admin", "loan_officer", "risk_officer"],     # Quick rejection
            },
            ApplicationStatus.UNDER_REVIEW: {
                ApplicationStatus.APPROVED: ["admin", "loan_officer", "risk_officer"],      # Approval
                ApplicationStatus.REJECTED: ["admin", "loan_officer", "risk_officer"],      # Rejection
                ApplicationStatus.AWAITING_DISBURSEMENT: ["admin", "loan_officer"],         # Direct to disbursement
            },
            ApplicationStatus.APPROVED: {
                ApplicationStatus.AWAITING_DISBURSEMENT: ["admin", "loan_officer"],         # Move to disbursement
                ApplicationStatus.REJECTED: ["admin"],  # Admin override (rare)
            },
            ApplicationStatus.AWAITING_DISBURSEMENT: {
                ApplicationStatus.DONE: ["admin", "loan_officer"],  # Funds disbursed
                ApplicationStatus.REJECTED: ["admin"],              # Admin override (rare)
            },
            ApplicationStatus.REJECTED: {},  # Terminal state
            ApplicationStatus.CANCELLED: {},  # Terminal state
            ApplicationStatus.DONE: {},      # Terminal state
        }
        
        # Statuses that require a reason
        self.statuses_requiring_reason = [
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED
        ]
    
    async def get_allowed_transitions(self, current_status: ApplicationStatus, user_role: str) -> List[ApplicationStatus]:
        """Get list of allowed status transitions for a user role"""
        if current_status not in self.allowed_transitions:
            return []
        
        allowed = []
        for status, roles in self.allowed_transitions[current_status].items():
            if user_role in roles:
                allowed.append(status)
        
        return allowed
    
    async def validate_transition(
        self, 
        current_status: ApplicationStatus, 
        new_status: ApplicationStatus, 
        user: User,
        reason: Optional[str] = None
    ) -> bool:
        """Validate if a status transition is allowed"""
        # Check if transition is defined
        if current_status not in self.allowed_transitions:
            raise StatusTransitionError(f"No transitions allowed from status: {current_status}")
        
        # Check if specific transition is allowed
        if new_status not in self.allowed_transitions[current_status]:
            raise StatusTransitionError(f"Transition from {current_status} to {new_status} is not allowed")
        
        # Check user role permissions
        allowed_roles = self.allowed_transitions[current_status][new_status]
        if user.role.value not in allowed_roles:
            raise StatusTransitionError(f"User role '{user.role.value}' cannot transition from {current_status} to {new_status}")
        
        # Check if reason is required
        if new_status in self.statuses_requiring_reason and not reason:
            raise StatusTransitionError(f"Reason is required for status: {new_status}")
        
        return True
    
    async def update_application_status(
        self,
        session: AsyncSession,
        application_id: str,
        new_status: ApplicationStatus,
        user: User,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoanApplication:
        """Update application status with validation and audit logging"""
        
        # Get the application
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Store current status
        current_status = application.status
        
        # Skip if status is the same
        if current_status == new_status:
            return application
        
        # Validate transition
        await self.validate_transition(current_status, new_status, user, reason)
        
        # Determine change type
        change_type = "user_action" if user.role == UserRole.CUSTOMER else "admin_action"
        
        # Update application status
        application.status = new_status
        
        # Update specific timestamp fields based on status
        now = datetime.utcnow()
        if new_status == ApplicationStatus.SUBMITTED:
            application.submitted_at = now
        elif new_status == ApplicationStatus.UNDER_REVIEW:
            application.reviewed_at = now
            application.assigned_officer_id = user.id if user.role != UserRole.CUSTOMER else application.assigned_officer_id
        elif new_status == ApplicationStatus.APPROVED:
            application.approved_at = now
            application.decision_made_by_id = user.id
            application.decision_date = now
        elif new_status == ApplicationStatus.REJECTED:
            application.rejected_at = now
            application.decision_made_by_id = user.id
            application.decision_date = now
            application.rejection_reason = reason
        elif new_status == ApplicationStatus.CANCELLED:
            application.cancelled_at = now
            application.cancellation_reason = reason
        elif new_status == ApplicationStatus.AWAITING_DISBURSEMENT:
            if not application.approved_at:
                application.approved_at = now
        elif new_status == ApplicationStatus.DONE:
            application.disbursed_at = now
            application.completed_at = now
        
        # Create status history record
        status_history = ApplicationStatusHistory(
            application_id=application.id,
            from_status=current_status,
            to_status=new_status,
            reason=reason,
            notes=notes,
            changed_by_id=user.id,
            change_type=change_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        session.add(status_history)
        await session.commit()
        await session.refresh(application)
        
        # Log to audit service
        await self.audit_service.log_status_change(
            user_id=str(user.id),
            application_id=str(application.id),
            from_status=current_status.value,
            to_status=new_status.value,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return application
    
    async def get_status_history(
        self,
        session: AsyncSession,
        application_id: str,
        user: User
    ) -> List[ApplicationStatusHistory]:
        """Get status change history for an application"""
        
        # Verify application exists and user has access
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Check access permissions
        if user.role == UserRole.CUSTOMER:
            # Customer can only see their own application
            if str(application.customer_id) != str(user.id):
                # Need to check if user is the customer via customer relationship
                customer_stmt = select(LoanApplication).join(LoanApplication.customer).where(
                    and_(
                        LoanApplication.id == application_id,
                        LoanApplication.customer.has(user_id=user.id)
                    )
                )
                customer_result = await session.execute(customer_stmt)
                if not customer_result.scalar():
                    raise HTTPException(status_code=403, detail="Access denied")
        
        # Get status history
        stmt = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(ApplicationStatusHistory.created_at.asc())
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def check_one_active_application_per_customer(
        self,
        session: AsyncSession,
        customer_id: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Check if customer has any active applications"""
        
        active_statuses = [
            ApplicationStatus.IN_PROGRESS,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.APPROVED,
            ApplicationStatus.AWAITING_DISBURSEMENT
        ]
        
        stmt = select(func.count(LoanApplication.id)).where(
            and_(
                LoanApplication.customer_id == customer_id,
                LoanApplication.status.in_(active_statuses)
            )
        )
        
        if exclude_application_id:
            stmt = stmt.where(LoanApplication.id != exclude_application_id)
        
        result = await session.execute(stmt)
        count = result.scalar()
        
        return count > 0
    
    async def cancel_application(
        self,
        session: AsyncSession,
        application_id: str,
        user: User,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoanApplication:
        """Cancel an application (customer action)"""
        
        # Get the application
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Check if user is the customer (via customer relationship)
        if user.role == UserRole.CUSTOMER:
            customer_stmt = select(LoanApplication).join(LoanApplication.customer).where(
                and_(
                    LoanApplication.id == application_id,
                    LoanApplication.customer.has(user_id=user.id)
                )
            )
            customer_result = await session.execute(customer_stmt)
            if not customer_result.scalar():
                raise HTTPException(status_code=403, detail="You can only cancel your own applications")
        
        # Check if application can be cancelled
        if not application.can_be_cancelled_by_customer:
            raise StatusTransitionError(f"Application in status '{application.status}' cannot be cancelled")
        
        return await self.update_application_status(
            session=session,
            application_id=application_id,
            new_status=ApplicationStatus.CANCELLED,
            user=user,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_status_display_info(self, status: ApplicationStatus) -> Dict[str, str]:
        """Get display information for a status"""
        status_info = {
            ApplicationStatus.IN_PROGRESS: {
                "label": "In Progress",
                "color": "blue",
                "description": "Application is being prepared"
            },
            ApplicationStatus.SUBMITTED: {
                "label": "Submitted",
                "color": "yellow",
                "description": "Application submitted, awaiting review"
            },
            ApplicationStatus.UNDER_REVIEW: {
                "label": "Under Review",
                "color": "orange",
                "description": "Application is being reviewed by our team"
            },
            ApplicationStatus.APPROVED: {
                "label": "Approved",
                "color": "green",
                "description": "Application has been approved"
            },
            ApplicationStatus.AWAITING_DISBURSEMENT: {
                "label": "Awaiting Disbursement",
                "color": "purple",
                "description": "Approved, preparing to disburse funds"
            },
            ApplicationStatus.DONE: {
                "label": "Completed",
                "color": "green",
                "description": "Funds disbursed successfully"
            },
            ApplicationStatus.REJECTED: {
                "label": "Rejected",
                "color": "red",
                "description": "Application has been rejected"
            },
            ApplicationStatus.CANCELLED: {
                "label": "Cancelled",
                "color": "gray",
                "description": "Application was cancelled"
            }
        }
        
        return status_info.get(status, {
            "label": str(status).title(),
            "color": "gray",
            "description": "Status information not available"
        })