from fastapi import APIRouter
# from app.api.v1.users import router as users_router
from api.v1.competencies import router as competencies_router
from api.v1.comments import router as comments_router

router = APIRouter(prefix="/api/v1")

# router.include_router(users_router)
router.include_router(competencies_router)
router.include_router(comments_router)

__all__ = ["router"]
