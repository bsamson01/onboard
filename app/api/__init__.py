from .scorecard import router as scorecard_router
from .evaluation import router as evaluation_router
from .admin import router as admin_router

__all__ = [
    "scorecard_router",
    "evaluation_router",
    "admin_router"
]