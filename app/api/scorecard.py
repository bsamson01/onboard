"""
API endpoints for scorecard management.
Provides CRUD operations and version management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.services.scorecard_service import ScorecardService
from app.schemas.scorecard import (
    ScorecardConfigCreate, ScorecardConfigUpdate, ScorecardConfigResponse,
    ScorecardVersionCreate, ScorecardVersionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scorecards", tags=["scorecards"])


@router.post("/", response_model=ScorecardConfigResponse, status_code=status.HTTP_201_CREATED)
def create_scorecard(
    scorecard_data: ScorecardConfigCreate,
    db: Session = Depends(get_db),
    created_by: str = "system"  # TODO: Get from authentication
):
    """Create a new scorecard configuration."""
    try:
        service = ScorecardService(db)
        scorecard = service.create_scorecard(scorecard_data, created_by)
        return scorecard
    except Exception as e:
        logger.error(f"Error creating scorecard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scorecard: {str(e)}"
        )


@router.get("/{uuid}", response_model=ScorecardConfigResponse)
def get_scorecard(uuid: str, db: Session = Depends(get_db)):
    """Get scorecard by UUID."""
    service = ScorecardService(db)
    scorecard = service.get_scorecard_by_uuid(uuid)
    
    if not scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scorecard not found: {uuid}"
        )
    
    return scorecard


@router.get("/mfi/{mfi_id}", response_model=List[ScorecardConfigResponse])
def get_scorecards_by_mfi(mfi_id: str, db: Session = Depends(get_db)):
    """Get all scorecards for an MFI."""
    service = ScorecardService(db)
    scorecards = service.get_scorecards_by_mfi(mfi_id)
    return scorecards


@router.put("/{scorecard_id}", response_model=ScorecardConfigResponse)
def update_scorecard(
    scorecard_id: int,
    update_data: ScorecardConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update scorecard configuration."""
    try:
        service = ScorecardService(db)
        scorecard = service.update_scorecard(scorecard_id, update_data)
        
        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scorecard not found: {scorecard_id}"
            )
        
        return scorecard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scorecard {scorecard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scorecard: {str(e)}"
        )


@router.delete("/{scorecard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scorecard(scorecard_id: int, db: Session = Depends(get_db)):
    """Soft delete a scorecard."""
    try:
        service = ScorecardService(db)
        success = service.delete_scorecard(scorecard_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scorecard not found: {scorecard_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scorecard {scorecard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scorecard: {str(e)}"
        )


# Version management endpoints

@router.post("/{scorecard_id}/versions", response_model=ScorecardVersionResponse, 
            status_code=status.HTTP_201_CREATED)
def create_scorecard_version(
    scorecard_id: int,
    version_data: ScorecardVersionCreate,
    db: Session = Depends(get_db),
    created_by: str = "system"  # TODO: Get from authentication
):
    """Create a new version of a scorecard."""
    try:
        service = ScorecardService(db)
        version = service.create_scorecard_version(scorecard_id, version_data, created_by)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scorecard not found: {scorecard_id}"
            )
        
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scorecard version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/{scorecard_id}/versions", response_model=List[ScorecardVersionResponse])
def get_scorecard_versions(scorecard_id: int, db: Session = Depends(get_db)):
    """Get all versions of a scorecard."""
    service = ScorecardService(db)
    versions = service.get_scorecard_versions(scorecard_id)
    return versions


@router.get("/{scorecard_id}/versions/{version_id}", response_model=ScorecardVersionResponse)
def get_scorecard_version(
    scorecard_id: int, 
    version_id: int, 
    db: Session = Depends(get_db)
):
    """Get a specific version of a scorecard."""
    service = ScorecardService(db)
    version = service.get_version_by_id(version_id)
    
    if not version or version.scorecard_id != scorecard_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version not found or not associated with scorecard"
        )
    
    return version


@router.post("/{scorecard_id}/versions/{version_id}/activate", 
            status_code=status.HTTP_200_OK)
def activate_version(
    scorecard_id: int, 
    version_id: int, 
    db: Session = Depends(get_db)
):
    """Activate a specific version of a scorecard."""
    try:
        service = ScorecardService(db)
        success = service.activate_version(scorecard_id, version_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version not found or not associated with scorecard"
            )
        
        return {"message": f"Version {version_id} activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating version {version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate version: {str(e)}"
        )


@router.post("/{scorecard_id}/versions/{version_id}/clone", 
            response_model=ScorecardVersionResponse,
            status_code=status.HTTP_201_CREATED)
def clone_version(
    scorecard_id: int,
    version_id: int,
    description: str,
    db: Session = Depends(get_db),
    created_by: str = "system"  # TODO: Get from authentication
):
    """Clone an existing version to create a new version."""
    try:
        service = ScorecardService(db)
        
        # Verify version belongs to scorecard
        original_version = service.get_version_by_id(version_id)
        if not original_version or original_version.scorecard_id != scorecard_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version not found or not associated with scorecard"
            )
        
        new_version = service.clone_version(version_id, description, created_by)
        
        if not new_version:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clone version"
            )
        
        return new_version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning version {version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone version: {str(e)}"
        )


@router.post("/{scorecard_id}/cleanup", status_code=status.HTTP_200_OK)
def cleanup_old_versions(scorecard_id: int, db: Session = Depends(get_db)):
    """Clean up old versions, keeping only the most recent ones."""
    try:
        service = ScorecardService(db)
        deleted_count = service.cleanup_old_versions(scorecard_id)
        return {"message": f"Cleaned up {deleted_count} old versions"}
    except Exception as e:
        logger.error(f"Error cleaning up versions for scorecard {scorecard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup versions: {str(e)}"
        )