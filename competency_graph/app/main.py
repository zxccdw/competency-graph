from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.v1 import router as competencies_router
from dependencies import Container


def create_app() -> FastAPI:
    container = Container()
    container.wire(packages=["api.v1", "dao"])

    app = FastAPI(
        title="Competency Graph API",
        description="API для работы с графом компетенций",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        competencies_router,
        prefix="/api/v1",
        tags=["competencies"]
    )

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)