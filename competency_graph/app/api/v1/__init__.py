from fastapi import APIRouter
from app.api.v1.users import router as users_router
from app.api.v1.competencies import router as competencies_router

# Создаем основной роутер для API v1
router = APIRouter(prefix="/api/v1")

# Регистрируем все роутеры
router.include_router(users_router)
router.include_router(competencies_router)

__all__ = ["router"]
