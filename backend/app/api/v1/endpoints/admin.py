from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
async def get_admin_dashboard():
    return {}

@router.get("/reports")
async def get_reports():
    return []

@router.get("/system-health")
async def get_system_health():
    return {"status": "healthy"}