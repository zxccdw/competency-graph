from typing import List, Dict, Any, Optional
from dependency_injector.wiring import inject, Provider
from SPARQLWrapper import SPARQLWrapper

from app.dependencies.config import Config


class BaseDAO:
    """Базовый класс для работы с GraphDB"""

    @inject
    def __init__(
        self,
        graphdb_client: Provider[SPARQLWrapper],
        config: Provider[Config]
    ):
        self._client = graphdb_client()
        self._config = config()

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Выполнить SPARQL-запрос"""
        self._client.setQuery(query)
        results = self._client.query().convert()
        return results["results"]["bindings"]

    async def execute_update(self, update: str) -> None:
        """Выполнить SPARQL-update запрос"""
        self._client.setMethod("POST")
        self._client.setQuery(update)
        self._client.query()

    async def add_triple(self, subject: str, predicate: str, object_: str) -> None:
        """Добавить RDF-триплет"""
        update_query = f"""
        INSERT DATA {{
            {subject} {predicate} {object_} .
        }}
        """
        await self.execute_update(update_query)

    async def delete_triple(self, subject: str, predicate: str, object_: str) -> None:
        """Удалить RDF-триплет"""
        update_query = f"""
        DELETE DATA {{
            {subject} {predicate} {object_} .
        }}
        """
        await self.execute_update(update_query)

    async def get_node_data(self, node_uri: str) -> Optional[Dict[str, Any]]:
        """Получить все данные узла"""
        query = f"""
        SELECT ?predicate ?object
        WHERE {{
            {node_uri} ?predicate ?object .
        }}
        """
        results = await self.execute_query(query)
        if not results:
            return None

        return {
            result["predicate"]["value"]: result["object"]["value"]
            for result in results
        }
