from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_alerts():
    return []

@router.post("/")
async def create_alert():
    return {}

@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    return {}