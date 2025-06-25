"""
Main FastAPI application for the Credit Scorecard Microservice.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.database import create_tables
from app.api.scorecard import router as scorecard_router
from app.api.evaluation import router as evaluation_router
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Credit Scorecard Microservice...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Credit Scorecard Microservice...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    Credit Scorecard Microservice for evaluating applicant data using 
    institution-specific scoring logic with versioning and audit capabilities.
    
    ## Features
    
    * **Scorecard Management**: Create and manage per-MFI scorecard configurations
    * **Version Control**: Support for scorecard versioning with rollback capabilities
    * **Safe Evaluation**: Secure expression evaluation without eval() risks
    * **Audit Logging**: Complete audit trail for all evaluations
    * **Flexible Rules**: Support for threshold, condition, and expression-based rules
    * **Integration Ready**: RESTful API for easy integration with other systems
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(scorecard_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Credit Scorecard Microservice",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "Credit Scorecard Microservice",
        "timestamp": time.time()
    }


# Metrics endpoint (basic)
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    return {
        "service": "Credit Scorecard Microservice",
        "uptime": "N/A",  # Could be implemented with startup time tracking
        "requests_total": "N/A",  # Could be implemented with middleware
        "errors_total": "N/A"  # Could be implemented with error tracking
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )