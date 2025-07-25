from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Настройки GraphDB (RDF)
    GRAPHDB_URL: str = "http://localhost:7200"
    GRAPHDB_REPOSITORY: str = "competency_graph"
    GRAPHDB_USERNAME: str = "admin"
    GRAPHDB_PASSWORD: str = "root"

    # Настройки JWT
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


# Создаем экземпляр настроек
settings = Settings()
