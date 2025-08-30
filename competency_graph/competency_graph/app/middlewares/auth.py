from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.dependencies.request_context import RequestContext
from app.services.auth import TokenService


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации пользователей"""

    def __init__(
        self,
        token_service: TokenService,
        request_context: RequestContext
    ):
        self.token_service = token_service
        self.request_context = request_context

    async def dispatch(self, request: Request, call_next):
        # Пропускаем некоторые пути без аутентификации
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        try:
            # Получаем токен из заголовка
            token = self._extract_token(request)
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing authentication token"}
                )

            # Проверяем токен
            payload = await self.token_service.verify_token(token)
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"}
                )

            # Сохраняем данные в контекст
            try:
                self.request_context.access_token = token
                self.request_context.device_id = payload.get("device_id", "")
                self.request_context.user_ip = request.client.host
                self.request_context.user_agent = request.headers.get("user-agent", "")

                response = await call_next(request)
                return response

            finally:
                # Очищаем контекст только после успешной обработки
                self.request_context.clear()

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": str(e)}
            )

    def _should_skip_auth(self, path: str) -> bool:
        """Проверка путей, не требующих аутентификации"""
        skip_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh"
        }
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _extract_token(self, request: Request) -> Optional[str]:
        """Извлечение токена из заголовка Authorization"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]
