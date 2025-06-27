"""
Authentication module for scorecard microservice
"""

import os
import logging
import time
import hashlib
from typing import Dict
from fastapi import HTTPException, status
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class RateLimiter:
    """Simple rate limiter for API key attempts"""
    
    def __init__(self):
        self.attempts: Dict[str, list] = {}
        self.max_attempts = 10
        self.window_minutes = 15
    
    def is_rate_limited(self, api_key_hash: str) -> bool:
        """Check if API key is rate limited"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.window_minutes)
        
        if api_key_hash not in self.attempts:
            self.attempts[api_key_hash] = []
        
        # Clean old attempts
        self.attempts[api_key_hash] = [
            attempt for attempt in self.attempts[api_key_hash] 
            if attempt > cutoff
        ]
        
        return len(self.attempts[api_key_hash]) >= self.max_attempts
    
    def record_attempt(self, api_key_hash: str):
        """Record a failed authentication attempt"""
        if api_key_hash not in self.attempts:
            self.attempts[api_key_hash] = []
        self.attempts[api_key_hash].append(datetime.utcnow())


# Global rate limiter instance
rate_limiter = RateLimiter()


async def verify_api_key(authorization: str) -> bool:
    """
    Verify API key from Authorization header with rate limiting and security
    
    Args:
        authorization: Authorization header value (should be "Bearer {api_key}")
        
    Returns:
        True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    start_time = time.time()
    api_key_hash = None
    
    try:
        # Basic input validation
        if not authorization or not isinstance(authorization, str):
            logger.warning("Missing or invalid authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate authorization header format
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected 'Bearer {token}'",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract and validate API key
        api_key = authorization.replace("Bearer ", "").strip()
        
        if not api_key:
            logger.warning("Empty API key provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty API key provided",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Additional API key format validation
        if len(api_key) < 10:
            logger.warning("API key too short")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if len(api_key) > 500:  # Prevent DoS attacks with massive keys
            logger.warning("API key too long")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create hash for rate limiting (don't log actual key)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        # Check rate limiting
        if rate_limiter.is_rate_limited(api_key_hash):
            logger.warning(f"Rate limit exceeded for API key hash: {api_key_hash}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts. Please try again later.",
                headers={"Retry-After": "900"}  # 15 minutes
            )
        
        # Get valid API keys from environment (support multiple keys)
        valid_api_keys = []
        
        # Primary API key
        primary_key = os.getenv("SCORECARD_API_KEY")
        if primary_key:
            valid_api_keys.append(primary_key)
        
        # Additional API keys (for key rotation)
        secondary_key = os.getenv("SCORECARD_API_KEY_SECONDARY")
        if secondary_key:
            valid_api_keys.append(secondary_key)
        
        # Fallback key for development
        if not valid_api_keys:
            valid_api_keys.append("default_scorecard_key_2024")
            logger.warning("Using default API key - not suitable for production")
        
        # Verify the API key using constant-time comparison
        api_key_valid = False
        for valid_key in valid_api_keys:
            if len(api_key) == len(valid_key):
                # Constant-time comparison to prevent timing attacks
                result = 0
                for x, y in zip(api_key.encode(), valid_key.encode()):
                    result |= x ^ y
                if result == 0:
                    api_key_valid = True
                    break
        
        if not api_key_valid:
            # Record failed attempt for rate limiting
            rate_limiter.record_attempt(api_key_hash)
            logger.warning(f"Invalid API key provided (hash: {api_key_hash})")
            
            # Add delay to slow down brute force attacks
            elapsed = time.time() - start_time
            if elapsed < 0.1:  # Minimum 100ms response time
                time.sleep(0.1 - elapsed)
                
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Successful authentication
        elapsed = time.time() - start_time
        logger.info(f"API key authentication successful (hash: {api_key_hash}, time: {elapsed:.3f}s)")
        return True
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        
        # Add delay for error cases too
        elapsed = time.time() - start_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
            
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