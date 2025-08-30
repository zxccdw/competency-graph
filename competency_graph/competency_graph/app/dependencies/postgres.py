import logging
import asyncpg
import orjson
from dependencies.config import Config


logger = logging.getLogger(__name__)


async def init_connection(conn: asyncpg.Connection):
    """Инициализация подключения к PostgreSQL"""
    await conn.set_type_codec(
        "json",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )


async def create_db_pool(config: Config):
    """Создание пула подключений к PostgreSQL"""
    async with asyncpg.create_pool(
        dsn=config.database.dsn,
        statement_cache_size=0,
        init=init_connection,
    ) as pool:
        logger.info("PostgreSQL connection pool created")
        yield pool
        pool.terminate()
    logger.info("PostgreSQL connection pool closed")
