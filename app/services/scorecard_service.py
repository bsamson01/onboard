"""
Service layer for scorecard management operations.
Handles CRUD operations, versioning, and business logic.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging

from app.models.scorecard import ScorecardConfig, ScorecardVersion, ScoringFactor
from app.schemas.scorecard import (
    ScorecardConfigCreate, ScorecardConfigUpdate, ScorecardVersionCreate,
    ScoringFactorCreate
)
from config import settings

logger = logging.getLogger(__name__)


class ScorecardService:
    """Service for managing scorecard configurations and versions."""
    
    def __init__(self, db: Session):
        """Initialize the service with database session."""
        self.db = db
    
    def create_scorecard(self, scorecard_data: ScorecardConfigCreate, created_by: str) -> ScorecardConfig:
        """
        Create a new scorecard configuration.
        
        Args:
            scorecard_data: Scorecard creation data
            created_by: User creating the scorecard
            
        Returns:
            Created scorecard configuration
        """
        try:
            # Create the scorecard
            scorecard = ScorecardConfig(
                mfi_id=scorecard_data.mfi_id,
                name=scorecard_data.name,
                description=scorecard_data.description,
                min_score=scorecard_data.min_score,
                max_score=scorecard_data.max_score,
                passing_score=scorecard_data.passing_score,
                created_by=created_by
            )
            
            self.db.add(scorecard)
            self.db.commit()
            self.db.refresh(scorecard)
            
            logger.info(f"Created scorecard {scorecard.id} for MFI {scorecard.mfi_id}")
            return scorecard
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating scorecard: {e}")
            raise
    
    def get_scorecard_by_uuid(self, uuid: str) -> Optional[ScorecardConfig]:
        """Get scorecard by UUID."""
        return self.db.query(ScorecardConfig).filter(
            ScorecardConfig.uuid == uuid
        ).first()
    
    def get_scorecard_by_id(self, scorecard_id: int) -> Optional[ScorecardConfig]:
        """Get scorecard by ID."""
        return self.db.query(ScorecardConfig).filter(
            ScorecardConfig.id == scorecard_id
        ).first()
    
    def get_scorecards_by_mfi(self, mfi_id: str) -> List[ScorecardConfig]:
        """Get all scorecards for an MFI."""
        return self.db.query(ScorecardConfig).filter(
            ScorecardConfig.mfi_id == mfi_id
        ).order_by(desc(ScorecardConfig.created_at)).all()
    
    def update_scorecard(self, scorecard_id: int, 
                        update_data: ScorecardConfigUpdate) -> Optional[ScorecardConfig]:
        """
        Update scorecard configuration.
        
        Args:
            scorecard_id: ID of scorecard to update
            update_data: Update data
            
        Returns:
            Updated scorecard or None if not found
        """
        try:
            scorecard = self.get_scorecard_by_id(scorecard_id)
            if not scorecard:
                return None
            
            # Update fields that are provided
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(scorecard, field, value)
            
            self.db.commit()
            self.db.refresh(scorecard)
            
            logger.info(f"Updated scorecard {scorecard_id}")
            return scorecard
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating scorecard {scorecard_id}: {e}")
            raise
    
    def create_scorecard_version(self, scorecard_id: int, 
                               version_data: ScorecardVersionCreate,
                               created_by: str) -> Optional[ScorecardVersion]:
        """
        Create a new version of a scorecard.
        
        Args:
            scorecard_id: ID of the scorecard
            version_data: Version creation data
            created_by: User creating the version
            
        Returns:
            Created version or None if scorecard not found
        """
        try:
            scorecard = self.get_scorecard_by_id(scorecard_id)
            if not scorecard:
                return None
            
            # Get next version number
            latest_version = self.db.query(ScorecardVersion).filter(
                ScorecardVersion.scorecard_id == scorecard_id
            ).order_by(desc(ScorecardVersion.version_number)).first()
            
            next_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create the version
            version = ScorecardVersion(
                scorecard_id=scorecard_id,
                version_number=next_version_number,
                description=version_data.description,
                config_data=version_data.config_data,
                created_by=created_by
            )
            
            self.db.add(version)
            self.db.flush()  # Get the ID
            
            # Create scoring factors
            for factor_data in version_data.scoring_factors:
                factor = ScoringFactor(
                    version_id=version.id,
                    name=factor_data.name,
                    code=factor_data.code,
                    description=factor_data.description,
                    category=factor_data.category,
                    weight=factor_data.weight,
                    data_type=factor_data.data_type.value,
                    rules=factor_data.rules,
                    is_required=factor_data.is_required,
                    min_value=factor_data.min_value,
                    max_value=factor_data.max_value,
                    default_points=factor_data.default_points
                )
                self.db.add(factor)
            
            self.db.commit()
            self.db.refresh(version)
            
            logger.info(f"Created version {next_version_number} for scorecard {scorecard_id}")
            return version
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating scorecard version: {e}")
            raise
    
    def activate_version(self, scorecard_id: int, version_id: int) -> bool:
        """
        Activate a specific version of a scorecard.
        
        Args:
            scorecard_id: ID of the scorecard
            version_id: ID of the version to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify the version belongs to the scorecard
            version = self.db.query(ScorecardVersion).filter(
                and_(
                    ScorecardVersion.id == version_id,
                    ScorecardVersion.scorecard_id == scorecard_id
                )
            ).first()
            
            if not version:
                return False
            
            # Deactivate all other versions
            self.db.query(ScorecardVersion).filter(
                ScorecardVersion.scorecard_id == scorecard_id
            ).update({'is_active': False})
            
            # Activate the selected version
            version.is_active = True
            
            # Update the scorecard's current version
            scorecard = self.get_scorecard_by_id(scorecard_id)
            if scorecard:
                scorecard.current_version_id = version_id
            
            self.db.commit()
            
            logger.info(f"Activated version {version_id} for scorecard {scorecard_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error activating version {version_id}: {e}")
            raise
    
    def get_active_version(self, scorecard_id: int) -> Optional[ScorecardVersion]:
        """Get the active version of a scorecard."""
        return self.db.query(ScorecardVersion).filter(
            and_(
                ScorecardVersion.scorecard_id == scorecard_id,
                ScorecardVersion.is_active == True
            )
        ).first()
    
    def get_version_by_id(self, version_id: int) -> Optional[ScorecardVersion]:
        """Get version by ID."""
        return self.db.query(ScorecardVersion).filter(
            ScorecardVersion.id == version_id
        ).first()
    
    def get_scorecard_versions(self, scorecard_id: int) -> List[ScorecardVersion]:
        """Get all versions of a scorecard."""
        return self.db.query(ScorecardVersion).filter(
            ScorecardVersion.scorecard_id == scorecard_id
        ).order_by(desc(ScorecardVersion.version_number)).all()
    
    def get_scoring_factors(self, version_id: int) -> List[ScoringFactor]:
        """Get all scoring factors for a version."""
        return self.db.query(ScoringFactor).filter(
            ScoringFactor.version_id == version_id
        ).order_by(ScoringFactor.name).all()
    
    def clone_version(self, version_id: int, description: str, 
                     created_by: str) -> Optional[ScorecardVersion]:
        """
        Clone an existing version to create a new version.
        
        Args:
            version_id: ID of version to clone
            description: Description for the new version
            created_by: User creating the clone
            
        Returns:
            New cloned version or None if original not found
        """
        try:
            original_version = self.get_version_by_id(version_id)
            if not original_version:
                return None
            
            # Get the scoring factors
            factors = self.get_scoring_factors(version_id)
            
            # Create version data from original
            version_data = ScorecardVersionCreate(
                description=description,
                config_data=original_version.config_data,
                scoring_factors=[
                    ScoringFactorCreate(
                        name=f.name,
                        code=f.code,
                        description=f.description,
                        category=f.category,
                        weight=f.weight,
                        data_type=f.data_type,
                        rules=f.rules,
                        is_required=f.is_required,
                        min_value=f.min_value,
                        max_value=f.max_value,
                        default_points=f.default_points
                    ) for f in factors
                ]
            )
            
            # Create the new version
            return self.create_scorecard_version(
                original_version.scorecard_id, version_data, created_by
            )
            
        except Exception as e:
            logger.error(f"Error cloning version {version_id}: {e}")
            raise
    
    def delete_scorecard(self, scorecard_id: int) -> bool:
        """
        Soft delete a scorecard (mark as inactive).
        
        Args:
            scorecard_id: ID of scorecard to delete
            
        Returns:
            True if successful, False if not found
        """
        try:
            scorecard = self.get_scorecard_by_id(scorecard_id)
            if not scorecard:
                return False
            
            scorecard.is_active = False
            self.db.commit()
            
            logger.info(f"Soft deleted scorecard {scorecard_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting scorecard {scorecard_id}: {e}")
            raise
    
    def cleanup_old_versions(self, scorecard_id: int) -> int:
        """
        Clean up old versions, keeping only the most recent ones.
        
        Args:
            scorecard_id: ID of scorecard to clean up
            
        Returns:
            Number of versions deleted
        """
        try:
            versions = self.get_scorecard_versions(scorecard_id)
            
            if len(versions) <= settings.MAX_SCORECARD_VERSIONS:
                return 0
            
            # Keep the most recent versions and the active one
            active_version = self.get_active_version(scorecard_id)
            versions_to_keep = versions[:settings.MAX_SCORECARD_VERSIONS - 1]
            
            if active_version and active_version not in versions_to_keep:
                versions_to_keep.append(active_version)
            
            keep_ids = [v.id for v in versions_to_keep]
            
            # Delete old versions
            deleted_count = self.db.query(ScorecardVersion).filter(
                and_(
                    ScorecardVersion.scorecard_id == scorecard_id,
                    ~ScorecardVersion.id.in_(keep_ids)
                )
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old versions for scorecard {scorecard_id}")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up versions for scorecard {scorecard_id}: {e}")
            raise