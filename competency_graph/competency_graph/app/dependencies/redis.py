from typing import AsyncGenerator
import aioredis
from app.dependencies.config import Config


async def create_redis_client(config: Config) -> AsyncGenerator[aioredis.Redis, None]:
    """Создание клиента Redis"""
    redis = await aioredis.create_redis_pool(
        config.redis.url,
        password=config.redis.password,
        minsize=config.redis.pool_min_size,
        maxsize=config.redis.pool_max_size,
        encoding='utf-8'
    )

    try:
        yield redis
    finally:
        redis.close()
        await redis.wait_closed()
