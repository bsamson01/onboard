from fastapi import APIRouter

router = APIRouter()

@router.get("/applications")
async def get_loan_applications():
    return []

@router.post("/applications")
async def create_loan_application():
    return {}

@router.get("/applications/{application_id}")
async def get_loan_application(application_id: str):
    return {}