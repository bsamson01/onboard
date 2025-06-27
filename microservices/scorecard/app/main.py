"""
Scorecard Microservice - Main Application

This service provides credit scoring and risk assessment functionality
for the microfinance platform.
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Optional

from .models import ScoringRequest, ScoringResponse, HealthResponse
from .scoring_engine import ScoringEngine
from .auth import verify_api_key


# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Scorecard microservice starting up...")
    
    # Validate environment on startup
    required_env_vars = ["SCORECARD_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.warning(f"Environment variable {var} not set - using defaults")
    
    yield
    logger.info("Scorecard microservice shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Scorecard Microservice",
    description="Credit scoring and risk assessment service for microfinance platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information"""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error for {request.url}: {error_details}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": error_details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = str(uuid.uuid4())
    logger.error(f"Unexpected error (ID: {request_id}): {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and response times"""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    # Add request ID to logs
    logger.info(f"[{request_id}] {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"[{request_id}] {response.status_code} - {process_time:.3f}s")
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Error: {str(e)} - {process_time:.3f}s")
        raise

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
    response: Response,
    authorization: str = Header(..., description="Bearer token"),
    x_api_version: str = Header("v1", alias="X-API-Version"),
    content_type: str = Header("application/json", alias="Content-Type"),
    user_agent: Optional[str] = Header(None, alias="User-Agent")
):
    """
    Calculate credit score based on customer profile and financial data
    
    This endpoint processes customer information and returns:
    - Credit score (0-1000 scale)
    - Credit grade (AA, A, B, C, D)
    - Eligibility determination
    - Score breakdown and analysis
    - Recommendations for improvement
    
    **Security**: Requires valid API key in Authorization header
    **Rate Limits**: 10 failed auth attempts per 15 minutes per key
    **Timeout**: 30 seconds maximum processing time
    """
    start_time = time.time()
    request_id = request.request_metadata.request_id
    
    try:
        # Verify API key first
        await verify_api_key(authorization)
        
        # Validate API version
        if x_api_version not in ["v1", "1.0"]:
            logger.warning(f"Unsupported API version: {x_api_version}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {x_api_version}. Supported versions: v1, 1.0"
            )
        
        # Validate content type
        if content_type.lower() not in ["application/json", "application/json; charset=utf-8"]:
            raise HTTPException(
                status_code=415,
                detail="Content-Type must be application/json"
            )
        
        # Log the scoring request with context
        logger.info(
            f"Processing scoring request: ID={request_id}, "
            f"age={request.customer_profile.age}, "
            f"income={request.financial_profile.monthly_income}, "
            f"employment={request.financial_profile.employment_status}, "
            f"user_agent={user_agent}"
        )
        
        # Calculate score using scoring engine with timeout
        result = await scoring_engine.calculate_score(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Add response headers
        response.headers["X-Score-Version"] = "1.0"
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        
        logger.info(
            f"Score calculated successfully: score={result.score}, "
            f"grade={result.grade}, eligibility={result.eligibility}, "
            f"request_id={request_id}, time={processing_time:.3f}s"
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (auth errors, etc.)
        raise
    except ValueError as e:
        logger.warning(f"Validation error for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=422, 
            detail=f"Data validation failed: {str(e)}"
        )
    except TimeoutError:
        logger.error(f"Timeout error for request {request_id}")
        raise HTTPException(
            status_code=504,
            detail="Request timeout - scoring took too long"
        )
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            f"Unexpected error for request {request_id}: {str(e)} "
            f"(time: {processing_time:.3f}s)", 
            exc_info=True
        )
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