from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, customers, onboarding, loans, alerts, admin, status

api_router = APIRouter()

# Authentication routes
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Authentication"]
)

# User management routes
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["Users"]
)

# Customer management routes
api_router.include_router(
    customers.router, 
    prefix="/customers", 
    tags=["Customers"]
)

# Onboarding routes
api_router.include_router(
    onboarding.router, 
    prefix="/onboarding", 
    tags=["Onboarding"]
)

# Loan application routes
api_router.include_router(
    loans.router, 
    prefix="/loans", 
    tags=["Loans"]
)

# Application status management routes
api_router.include_router(
    status.router, 
    prefix="/status", 
    tags=["Application Status"]
)

# Alert management routes
api_router.include_router(
    alerts.router, 
    prefix="/alerts", 
    tags=["Alerts"]
)

# Admin routes
api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["Admin"]
)