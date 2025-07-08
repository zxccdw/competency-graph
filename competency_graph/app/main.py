from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.competencies import router as competencies_router
from app.dependencies import Container
from app.middlewares.auth import AuthMiddleware


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI(
        title="Competency Graph API",
        description="API для работы с графом компетенций",
        version="1.0.0",
    )

    app.container = container

    # Добавляем middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Добавляем middleware для аутентификации
    app.add_middleware(
        AuthMiddleware,
        token_service=container.token_service(),
        request_context=container.request_context()
    )

    # Регистрируем роутеры
    app.include_router(
        competencies_router,
        prefix="/api/v1",
        tags=["competencies"]
    )

    @app.get("/health")
    async def health_check():
        """Эндпоинт для проверки здоровья сервиса"""
        try:
            # Проверяем подключение к базам
            await container.db_pool().execute("SELECT 1")
            await container.redis_client().ping()

            # Проверяем GraphDB
            container.graphdb_client().setQuery("ASK { ?s ?p ?o }")
            container.graphdb_client().query()

            return JSONResponse(
                status_code=200,
                content={"status": "healthy"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e)
                }
            )

    return app


app = create_app()
