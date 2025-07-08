import enum
import logging
import os
import secrets
from functools import cached_property

from logos.libs.conf.base import ConfigClass, at

__all__ = ("Config",)

logger = logging.getLogger(__name__)


class EnvironmentEnum(enum.Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"


class DatabaseConfig(ConfigClass):
    dsn = at.Str()
    connections_amount = at.Int()


class GraphDBConfig(ConfigClass):
    url = at.Str()
    repository = at.Str()
    username = at.Str(None)
    password = at.Str(None)


class RedisConfig(ConfigClass):
    url = at.Str()
    password = at.Str(None)
    ttl = at.Dict({
        'access_token': at.Int(900),  # 15 минут
        'refresh_token': at.Int(2592000),  # 30 дней
        'session': at.Int(2592000)  # 30 дней
    })


class AuthConfig(ConfigClass):
    secret_key = at.Str()
    algorithm = at.Str("HS256")


class HealthCheckConfig(ConfigClass):
    interval = at.Int(30)  # секунды
    timeout = at.Int(3)    # секунды
    retries = at.Int(3)


class Config(ConfigClass):
    @cached_property
    def environment(self) -> EnvironmentEnum:
        is_dev = bool(os.getenv("DEV_VERSION", False))
        return EnvironmentEnum.DEVELOPMENT if is_dev else EnvironmentEnum.PRODUCTION

    @cached_property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            dsn=self._get_db_url(),
            connections_amount=int(os.getenv("DATABASE_CONNECTIONS_AMOUNT", 10)),
        )

    @cached_property
    def graphdb(self) -> GraphDBConfig:
        return GraphDBConfig(
            url=os.getenv("GRAPHDB_URL", "http://localhost:7200"),
            repository=os.getenv("GRAPHDB_REPOSITORY", "competencies"),
            username=os.getenv("GRAPHDB_USERNAME"),
            password=os.getenv("GRAPHDB_PASSWORD"),
        )

    @cached_property
    def redis(self) -> RedisConfig:
        return RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            password=os.getenv("REDIS_PASSWORD"),
        )

    @cached_property
    def auth(self) -> AuthConfig:
        secret_key = os.getenv("AUTH_SECRET_KEY")
        if not secret_key:
            if self.environment == EnvironmentEnum.PRODUCTION:
                raise ValueError("AUTH_SECRET_KEY must be set in production")
            secret_key = secrets.token_urlsafe(32)
            logger.warning(f"Using generated secret key: {secret_key}")

        return AuthConfig(
            secret_key=secret_key,
            algorithm=os.getenv("AUTH_ALGORITHM", "HS256"),
        )

    @cached_property
    def healthcheck(self) -> HealthCheckConfig:
        return HealthCheckConfig(
            interval=int(os.getenv("HEALTHCHECK_INTERVAL", 30)),
            timeout=int(os.getenv("HEALTHCHECK_TIMEOUT", 3)),
            retries=int(os.getenv("HEALTHCHECK_RETRIES", 3))
        )

    def _get_db_url(self) -> str:
        if self.environment == EnvironmentEnum.DEVELOPMENT:
            database_dsn = os.getenv("DATABASE_URL")
            if not database_dsn:
                raise ConnectionError("You must specify DATABASE_URL variable in development mode")
            return database_dsn

        # Production settings
        required_variables = (
            "POSTGRESQL_HOST",
            "POSTGRESQL_PORT",
            "POSTGRESQL_DB",
            "POSTGRESQL_USER",
            "POSTGRESQL_PASSWORD",
        )
        for variable in required_variables:
            if variable not in os.environ:
                logger.warning(f"Environment variable {variable} not set")

        host = os.getenv("POSTGRESQL_HOST")
        port = os.getenv("POSTGRESQL_PORT", "5432")
        dbname = os.getenv("POSTGRESQL_DB", "competency_graph")
        user = os.getenv("POSTGRESQL_USER", "postgres")
        password = os.getenv("POSTGRESQL_PASSWORD")

        if not all([host, password]):
            raise ConnectionError("Required database credentials not set")

        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
