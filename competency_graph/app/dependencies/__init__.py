from dependency_injector import containers, providers
from SPARQLWrapper import SPARQLWrapper
import aioredis
import asyncpg

from app.dependencies.config import Config
from app.dependencies.graphdb import create_graphdb_client
from app.dependencies.redis import create_redis_client
from app.dependencies.postgres import create_db_pool
from app.dependencies.request_context import RequestContext

from app.services.auth import TokenService, SessionService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app"],
    )

    # Конфигурация
    config: providers.Provider[Config] = providers.Singleton(Config)

    # Контекст запроса
    request_context: providers.Provider[RequestContext] = providers.Singleton(RequestContext)

    # Клиенты для внешних сервисов
    graphdb_client: providers.Provider[SPARQLWrapper] = providers.Resource(
        create_graphdb_client,
        config=config
    )

    db_pool: providers.Provider[asyncpg.Pool] = providers.Resource(
        create_db_pool,
        config=config
    )

    redis_client: providers.Provider[aioredis.Redis] = providers.Resource(
        create_redis_client,
        config=config
    )

    # Сервисы
    token_service: providers.Provider[TokenService] = providers.Factory(
        TokenService,
        redis=redis_client,
        config=config
    )

    session_service: providers.Provider[SessionService] = providers.Factory(
        SessionService,
        redis=redis_client,
        config=config
    )
