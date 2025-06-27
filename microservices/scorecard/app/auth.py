"""
Authentication module for scorecard microservice
"""

import os
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


async def verify_api_key(authorization: str) -> bool:
    """
    Verify API key from Authorization header
    
    Args:
        authorization: Authorization header value (should be "Bearer {api_key}")
        
    Returns:
        True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Check if authorization header is provided
        if not authorization:
            logger.warning("Missing authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Check if it's a Bearer token
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected 'Bearer {token}'"
            )
        
        # Extract the API key
        api_key = authorization.replace("Bearer ", "").strip()
        
        if not api_key:
            logger.warning("Empty API key provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty API key provided"
            )
        
        # Get valid API key from environment variable
        valid_api_key = os.getenv("SCORECARD_API_KEY", "default_scorecard_key_2024")
        
        # Verify the API key
        if api_key != valid_api_key:
            logger.warning(f"Invalid API key provided: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        logger.info("API key authentication successful")
        return True
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


def get_api_key_info() -> dict:
    """
    Get information about API key configuration
    
    Returns:
        Dictionary with API key configuration info
    """
    return {
        "api_key_required": True,
        "header_format": "Authorization: Bearer {api_key}",
        "environment_variable": "SCORECARD_API_KEY"
    }