"""
Scorecard Microservice - Main Application

This service provides credit scoring and risk assessment functionality
for the microfinance platform.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime
from typing import Optional

from .models import ScoringRequest, ScoringResponse, HealthResponse
from .scoring_engine import ScoringEngine
from .auth import verify_api_key


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Scorecard microservice starting up...")
    yield
    logger.info("Scorecard microservice shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Scorecard Microservice",
    description="Credit scoring and risk assessment service for microfinance platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scoring engine
scoring_engine = ScoringEngine()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for service monitoring
    """
    return HealthResponse(
        status="healthy",
        service="scorecard"
    )


@app.post("/api/v1/score", response_model=ScoringResponse)
async def calculate_score(
    request: ScoringRequest,
    authorization: str = Header(..., description="Bearer token"),
    x_api_version: str = Header("v1", alias="X-API-Version"),
    content_type: str = Header("application/json", alias="Content-Type")
):
    """
    Calculate credit score based on customer profile and financial data
    
    This endpoint processes customer information and returns:
    - Credit score (0-1000 scale)
    - Credit grade (AA, A, B, C, D)
    - Eligibility determination
    - Score breakdown and analysis
    - Recommendations for improvement
    """
    try:
        # Verify API key
        await verify_api_key(authorization)
        
        # Log the scoring request
        logger.info(
            f"Processing scoring request for request_id: {request.request_metadata.request_id}"
        )
        
        # Calculate score using scoring engine
        result = await scoring_engine.calculate_score(request)
        
        logger.info(
            f"Score calculated successfully: {result.score} for request_id: {request.request_metadata.request_id}"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error occurred during score calculation"
        )


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Scorecard Microservice",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "score": "/api/v1/score"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )