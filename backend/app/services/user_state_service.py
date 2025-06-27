from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio
from contextlib import asynccontextmanager

from app.models.user import User, UserState, UserRoleHistory
from app.models.onboarding import Customer, OnboardingApplication, OnboardingStatus
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserStateService:
    """Service for managing user states and profile expiry."""
    
    def __init__(self):
        self.audit_service = AuditService()
        self._max_retry_attempts = 3
        self._retry_delay = 1.0  # seconds
    
    @asynccontextmanager
    async def _safe_transaction(self, session: AsyncSession):
        """Context manager for safe database transactions with retry logic."""
        for attempt in range(self._max_retry_attempts):
            try:
                yield session
                return
            except (SQLAlchemyError, IntegrityError) as e:
                await session.rollback()
                if attempt == self._max_retry_attempts - 1:
                    logger.error(f"Database transaction failed after {self._max_retry_attempts} attempts: {str(e)}")
                    raise
                logger.warning(f"Database transaction failed (attempt {attempt + 1}), retrying: {str(e)}")
                await asyncio.sleep(self._retry_delay * (attempt + 1))
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error in transaction: {str(e)}")
                raise
    
    def _validate_user(self, user: User) -> None:
        """Validate user object before operations."""
        if not user:
            raise ValueError("User object is required")
        if not user.id:
            raise ValueError("User must have a valid ID")
        if not user.email:
            raise ValueError("User must have a valid email")
    
    def _validate_user_state(self, state: UserState) -> None:
        """Validate user state."""
        if not isinstance(state, UserState):
            raise ValueError("Invalid user state type")
        valid_states = [UserState.REGISTERED, UserState.ONBOARDED, UserState.OUTDATED]
        if state not in valid_states:
            raise ValueError(f"Invalid user state: {state}")
    
    async def check_user_state(self, user: User, session: AsyncSession) -> UserState:
        """Check and determine the correct user state for a user."""
        try:
            self._validate_user(user)
            
            # Check if user has completed onboarding
            if user.onboarding_completed_at is None:
                logger.debug(f"User {user.id} has not completed onboarding")
                return UserState.REGISTERED
            
            # Check if profile is outdated (more than 1 year old)
            if self._is_profile_outdated(user):
                logger.debug(f"User {user.id} profile is outdated")
                return UserState.OUTDATED
            
            logger.debug(f"User {user.id} is fully onboarded")
            return UserState.ONBOARDED
            
        except ValueError as e:
            logger.error(f"Validation error checking user state for user {getattr(user, 'id', 'unknown')}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to check user state for user {getattr(user, 'id', 'unknown')}: {str(e)}")
            # Return safe default state in case of error
            return UserState.REGISTERED
    
    async def update_user_state(
        self, 
        user: User, 
        new_state: UserState, 
        session: AsyncSession,
        reason: Optional[str] = None
    ) -> User:
        """Update user state and log the change."""
        try:
            self._validate_user(user)
            self._validate_user_state(new_state)
            
            if reason and len(reason.strip()) > 500:
                raise ValueError("Reason cannot exceed 500 characters")
            
            old_state = user.user_state
            
            # Validate state transition
            if old_state == new_state:
                logger.warning(f"User {user.id} state is already {new_state}")
                return user
            
            # Validate state transition logic
            self._validate_state_transition(old_state, new_state)
            
            async with self._safe_transaction(session):
                user.user_state = new_state
                
                # Update timestamps based on state
                current_time = datetime.utcnow()
                
                if new_state == UserState.ONBOARDED:
                    if not user.onboarding_completed_at:
                        user.onboarding_completed_at = current_time
                    user.last_profile_update = current_time
                    user.profile_expiry_date = current_time + timedelta(days=365)
                elif new_state == UserState.OUTDATED:
                    # Profile expiry should already be set, but ensure it's in the past
                    if not user.profile_expiry_date or user.profile_expiry_date > current_time:
                        user.profile_expiry_date = current_time - timedelta(days=1)
                elif new_state == UserState.REGISTERED:
                    # Reset onboarding timestamps if moving back to registered
                    user.onboarding_completed_at = None
                    user.profile_expiry_date = None
                
                await session.commit()
                
                # Log the state change (outside transaction to avoid rollback issues)
                try:
                    await self.audit_service.log_onboarding_action(
                        user_id=str(user.id),
                        action="user_state_changed",
                        resource_type="user",
                        resource_id=str(user.id),
                        old_values={"user_state": old_state.value if old_state else None},
                        new_values={"user_state": new_state.value},
                        additional_data={
                            "reason": reason or "State updated by system",
                            "old_state": old_state.value if old_state else None,
                            "new_state": new_state.value,
                            "timestamp": current_time.isoformat()
                        }
                    )
                except Exception as audit_error:
                    logger.error(f"Failed to log state change audit for user {user.id}: {str(audit_error)}")
                    # Don't fail the entire operation due to audit logging failure
                
                logger.info(f"Updated user state for user {user.id} from {old_state} to {new_state}")
                return user
            
        except ValueError as e:
            logger.error(f"Validation error updating user state for user {getattr(user, 'id', 'unknown')}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user state for user {getattr(user, 'id', 'unknown')}: {str(e)}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Failed to update user state for user {getattr(user, 'id', 'unknown')}: {str(e)}")
            await session.rollback()
            raise
    
    def _validate_state_transition(self, old_state: UserState, new_state: UserState) -> None:
        """Validate that the state transition is allowed."""
        # Define allowed transitions
        allowed_transitions = {
            UserState.REGISTERED: [UserState.ONBOARDED],
            UserState.ONBOARDED: [UserState.OUTDATED, UserState.REGISTERED],  # Allow reverting for admin actions
            UserState.OUTDATED: [UserState.ONBOARDED, UserState.REGISTERED]   # Allow updating or reverting
        }
        
        if old_state not in allowed_transitions:
            raise ValueError(f"No transitions defined for state {old_state}")
        
        if new_state not in allowed_transitions[old_state]:
            raise ValueError(f"Invalid state transition from {old_state} to {new_state}")
    
    async def check_profile_expiry(self, user: User) -> bool:
        """Check if user's profile has expired."""
        if not user.profile_expiry_date:
            return False
        return datetime.utcnow() > user.profile_expiry_date
    
    async def get_outdated_users(self, session: AsyncSession) -> List[User]:
        """Get all users with outdated profiles."""
        try:
            # Get users whose profiles have expired
            stmt = select(User).where(
                and_(
                    User.user_state == UserState.ONBOARDED,
                    User.profile_expiry_date < datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            outdated_users = result.scalars().all()
            
            # Update their state to OUTDATED
            for user in outdated_users:
                await self.update_user_state(
                    user, 
                    UserState.OUTDATED, 
                    session, 
                    "Profile expired automatically"
                )
            
            return outdated_users
            
        except Exception as e:
            logger.error(f"Failed to get outdated users: {str(e)}")
            return []
    
    async def send_expiry_reminders(self, session: AsyncSession) -> int:
        """Send reminders to users whose profiles are about to expire."""
        try:
            # Get users who need reminders (30 days before expiry)
            reminder_date = datetime.utcnow() + timedelta(days=30)
            
            stmt = select(User).where(
                and_(
                    User.user_state == UserState.ONBOARDED,
                    User.profile_expiry_date <= reminder_date,
                    User.profile_expiry_date > datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            users_to_remind = result.scalars().all()
            
            reminder_count = 0
            for user in users_to_remind:
                # In a real implementation, this would send an email/SMS
                # For now, we'll just log it
                logger.info(f"Profile expiry reminder needed for user {user.id}")
                
                # Log the reminder
                await self.audit_service.log_onboarding_action(
                    user_id=str(user.id),
                    action="profile_expiry_reminder_sent",
                    resource_type="user",
                    resource_id=str(user.id),
                    additional_data={
                        "expiry_date": user.profile_expiry_date.isoformat() if user.profile_expiry_date else None,
                        "days_until_expiry": (user.profile_expiry_date - datetime.utcnow()).days if user.profile_expiry_date else None
                    }
                )
                reminder_count += 1
            
            return reminder_count
            
        except Exception as e:
            logger.error(f"Failed to send expiry reminders: {str(e)}")
            return 0
    
    async def get_user_statistics(self, session: AsyncSession) -> dict:
        """Get user state statistics."""
        try:
            # Count users by state
            registered_count = await session.scalar(
                select(func.count(User.id)).where(User.user_state == UserState.REGISTERED)
            )
            onboarded_count = await session.scalar(
                select(func.count(User.id)).where(User.user_state == UserState.ONBOARDED)
            )
            outdated_count = await session.scalar(
                select(func.count(User.id)).where(User.user_state == UserState.OUTDATED)
            )
            
            # Count users needing reminders
            reminder_date = datetime.utcnow() + timedelta(days=30)
            needs_reminder_count = await session.scalar(
                select(func.count(User.id)).where(
                    and_(
                        User.user_state == UserState.ONBOARDED,
                        User.profile_expiry_date <= reminder_date,
                        User.profile_expiry_date > datetime.utcnow()
                    )
                )
            )
            
            return {
                "registered_users": registered_count or 0,
                "onboarded_users": onboarded_count or 0,
                "outdated_users": outdated_count or 0,
                "users_needing_reminder": needs_reminder_count or 0,
                "total_users": (registered_count or 0) + (onboarded_count or 0) + (outdated_count or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {str(e)}")
            return {
                "registered_users": 0,
                "onboarded_users": 0,
                "outdated_users": 0,
                "users_needing_reminder": 0,
                "total_users": 0
            }
    
    async def transition_user_to_onboarded(
        self, 
        user: User, 
        session: AsyncSession,
        ip_address: Optional[str] = None
    ) -> User:
        """Transition user from REGISTERED to ONBOARDED state."""
        try:
            # Check if user has completed onboarding
            customer_stmt = select(Customer).where(Customer.user_id == user.id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar()
            
            if not customer:
                raise ValueError("Cannot transition to ONBOARDED: No customer profile found")
            
            # Check if onboarding application exists and is approved
            app_stmt = select(OnboardingApplication).where(
                and_(
                    OnboardingApplication.customer_id == customer.id,
                    OnboardingApplication.status == OnboardingStatus.APPROVED
                )
            )
            app_result = await session.execute(app_stmt)
            application = app_result.scalar()
            
            if not application:
                raise ValueError("Cannot transition to ONBOARDED: No approved onboarding application found")
            
            # Transition to ONBOARDED
            await self.update_user_state(
                user, 
                UserState.ONBOARDED, 
                session, 
                "Onboarding completed successfully"
            )
            
            logger.info(f"Successfully transitioned user {user.id} to ONBOARDED state")
            return user
            
        except Exception as e:
            logger.error(f"Failed to transition user {user.id} to ONBOARDED: {str(e)}")
            raise
    
    def _is_profile_outdated(self, user: User) -> bool:
        """Check if user's profile is outdated (helper method)."""
        if not user.profile_expiry_date:
            # If no expiry date is set and user was onboarded, assume it's outdated if more than 1 year
            if user.onboarding_completed_at:
                one_year_ago = datetime.utcnow() - timedelta(days=365)
                return user.onboarding_completed_at < one_year_ago
            return False
        
        return datetime.utcnow() > user.profile_expiry_date
    
    async def refresh_user_states(self, session: AsyncSession) -> dict:
        """Refresh all user states (maintenance function)."""
        try:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            all_users = result.scalars().all()
            
            updated_count = 0
            errors = []
            
            for user in all_users:
                try:
                    expected_state = await self.check_user_state(user, session)
                    if user.user_state != expected_state:
                        await self.update_user_state(
                            user, 
                            expected_state, 
                            session, 
                            "State refreshed by maintenance"
                        )
                        updated_count += 1
                except Exception as e:
                    errors.append(f"Failed to refresh state for user {user.id}: {str(e)}")
                    logger.error(f"Failed to refresh state for user {user.id}: {str(e)}")
            
            return {
                "total_users": len(all_users),
                "updated_count": updated_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh user states: {str(e)}")
            raise