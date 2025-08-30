from typing import Optional, List, Dict, Any
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from config.config import settings


class GraphDBClient:
    def __init__(self):
        self._endpoint = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"
        self._sparql = SPARQLWrapper(self._endpoint)
        self._sparql.setReturnFormat(JSON)

        # Настройка аутентификации
        if settings.GRAPHDB_USERNAME and settings.GRAPHDB_PASSWORD:
            self._sparql.setCredentials(settings.GRAPHDB_USERNAME, settings.GRAPHDB_PASSWORD)

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Выполнить SPARQL-запрос"""
        self._sparql.setQuery(query)
        results = self._sparql.query().convert()
        return results["results"]["bindings"]

    async def execute_update(self, update: str) -> None:
        """Выполнить SPARQL-update запрос"""
        self._sparql.setMethod(POST)
        self._sparql.setQuery(update)
        self._sparql.query()

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

    async def get_node_data(self, node_uri: str) -> Dict[str, Any]:
        """Получить все данные узла"""
        query = f"""
        SELECT ?predicate ?object
        WHERE {{
            {node_uri} ?predicate ?object .
        }}
        """
        return await self.execute_query(query)


# Создаем глобальный экземпляр клиента
db = GraphDBClient()
