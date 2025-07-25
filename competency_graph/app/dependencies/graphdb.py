from typing import AsyncGenerator
from SPARQLWrapper import SPARQLWrapper, JSON, POST

from dependencies.config import Config


async def create_graphdb_client(config: Config) -> AsyncGenerator[SPARQLWrapper, None]:
    """Создание клиента GraphDB"""
    endpoint = f"{config.graphdb.url}/repositories/{config.graphdb.repository}"
    client = SPARQLWrapper(endpoint)
    client.setReturnFormat(JSON)

    if config.graphdb.username and config.graphdb.password:
        client.setCredentials(config.graphdb.username, config.graphdb.password)

    try:
        yield client
    finally:
        # Здесь можно добавить cleanup код если потребуется
        pass
