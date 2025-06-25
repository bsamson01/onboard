from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_customers():
    """Get customers list."""
    return []

@router.post("/")
async def create_customer():
    """Create new customer."""
    return {}

@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    """Get customer by ID."""
    return {}

@router.put("/{customer_id}")
async def update_customer(customer_id: str):
    """Update customer."""
    return {}