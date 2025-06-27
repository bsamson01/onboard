from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models.user import User, UserState, UserRoleHistory
from app.models.onboarding import Customer, OnboardingApplication, OnboardingStatus
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserStateService:
    """Service for managing user states and profile expiry."""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    async def check_user_state(self, user: User, session: AsyncSession) -> UserState:
        """Check and determine the correct user state for a user."""
        try:
            # Check if user has completed onboarding
            if user.onboarding_completed_at is None:
                return UserState.REGISTERED
            
            # Check if profile is outdated (more than 1 year old)
            if self._is_profile_outdated(user):
                return UserState.OUTDATED
                
            return UserState.ONBOARDED
            
        except Exception as e:
            logger.error(f"Failed to check user state for user {user.id}: {str(e)}")
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
            old_state = user.user_state
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
            
            await session.commit()
            
            # Log the state change
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
                    "new_state": new_state.value
                }
            )
            
            logger.info(f"Updated user state for user {user.id} from {old_state} to {new_state}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to update user state for user {user.id}: {str(e)}")
            await session.rollback()
            raise
    
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