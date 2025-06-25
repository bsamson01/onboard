from fastapi import APIRouter

router = APIRouter()

@router.get("/applications")
async def get_onboarding_applications():
    return []

@router.post("/applications")
async def create_onboarding_application():
    return {}

@router.get("/applications/{application_id}")
async def get_onboarding_application(application_id: str):
    return {}