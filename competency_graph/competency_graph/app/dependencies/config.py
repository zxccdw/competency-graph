import enum
import logging
import os
from functools import cached_property
from typing import Optional
from pydantic import BaseModel

__all__ = ("Config",)

logger = logging.getLogger(__name__)


class EnvironmentEnum(enum.Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"

class DatabaseConfig(BaseModel):
    dsn: str
    connections_amount: int


class GraphDBConfig(BaseModel):
    url: str
    repository: str
    username: Optional[str]
    password: Optional[str]


class HealthCheckConfig(BaseModel):
    interval: int = 30  # секунды
    timeout: int = 3 # секунды
    retries: int = 3


class Config:
    @cached_property
    def environment(self) -> EnvironmentEnum:
        is_dev = bool(os.getenv("DEV_VERSION", False))
        return EnvironmentEnum.DEVELOPMENT if is_dev else EnvironmentEnum.PRODUCTION

    @cached_property
    def graphdb(self) -> GraphDBConfig:
        return GraphDBConfig(
            url=os.getenv("GRAPHDB_URL", "http://localhost:7200"),
            repository=os.getenv("GRAPHDB_REPOSITORY", "competencies"),
            username=os.getenv("GRAPHDB_USERNAME"),
            password=os.getenv("GRAPHDB_PASSWORD"),
        )

    @cached_property
    def healthcheck(self) -> HealthCheckConfig:
        return HealthCheckConfig(
            interval=int(os.getenv("HEALTHCHECK_INTERVAL", 30)),
            timeout=int(os.getenv("HEALTHCHECK_TIMEOUT", 3)),
            retries=int(os.getenv("HEALTHCHECK_RETRIES", 3))
        )

    @cached_property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/competency_graph"),
            connections_amount=int(os.getenv("DATABASE_CONNECTIONS_AMOUNT", 2))
        )