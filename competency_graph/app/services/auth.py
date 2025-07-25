from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dependency_injector.wiring import inject, Provider
import jwt
from aioredis import Redis

from app.dependencies.config import Config


class TokenService:
    @inject
    def __init__(
        self,
        redis: Provider[Redis],
        config: Provider[Config]
    ):
        self._redis = redis()
        self._config = config()

    async def create_access_token(self, user_id: str) -> str:
        """Создание access token"""
        expires_delta = timedelta(seconds=self._config.auth.access_token_expire)
        expires_at = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "exp": expires_at.timestamp(),
            "type": "access"
        }
        return jwt.encode(
            payload,
            self._config.auth.secret_key,
            algorithm=self._config.auth.algorithm
        )

    async def create_refresh_token(self, user_id: str, device_id: str) -> str:
        """Создание refresh token"""
        expires_delta = timedelta(seconds=self._config.auth.refresh_token_expire)
        expires_at = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "device_id": device_id,
            "exp": expires_at.timestamp(),
            "type": "refresh"
        }
        token = jwt.encode(
            payload,
            self._config.auth.secret_key,
            algorithm=self._config.auth.algorithm
        )

        # Сохраняем в Redis
        await self._redis.set(
            f"refresh_tokens:{user_id}:{device_id}",
            token,
            expire=int(expires_delta.total_seconds())
        )
        return token

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка токена"""
        try:
            payload = jwt.decode(
                token,
                self._config.auth.secret_key,
                algorithms=[self._config.auth.algorithm]
            )
            if payload["type"] == "refresh":
                # Для refresh токена проверяем наличие в Redis
                stored_token = await self._redis.get(
                    f"refresh_tokens:{payload['user_id']}:{payload['device_id']}"
                )
                if not stored_token or stored_token != token:
                    return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class SessionService:
    @inject
    def __init__(
        self,
        redis: Provider[Redis],
        config: Provider[Config]
    ):
        self._redis = redis()
        self._config = config()

    async def create_session(
        self,
        user_id: str,
        device_id: str,
        ip: str,
        user_agent: str
    ) -> None:
        """Создание сессии"""
        session_data = {
            "device_id": device_id,
            "ip": ip,
            "user_agent": user_agent,
            "last_activity": datetime.utcnow().timestamp()
        }

        # Сохраняем сессию
        await self._redis.hset(
            f"sessions:{user_id}",
            device_id,
            session_data
        )
        await self._redis.expire(
            f"sessions:{user_id}",
            self._config.redis.ttl['session']
        )

    async def get_sessions(self, user_id: str) -> Dict[str, Dict]:
        """Получение всех сессий пользователя"""
        return await self._redis.hgetall(f"sessions:{user_id}")

    async def remove_session(self, user_id: str, device_id: str) -> None:
        """Удаление сессии"""
        await self._redis.hdel(f"sessions:{user_id}", device_id)
        await self._redis.delete(f"refresh_tokens:{user_id}:{device_id}")

    async def remove_all_sessions(self, user_id: str) -> None:
        """Удаление всех сессий пользователя"""
        sessions = await self.get_sessions(user_id)
        for device_id in sessions:
            await self.remove_session(user_id, device_id)
