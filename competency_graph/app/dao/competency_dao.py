import typing as tp
from datetime import datetime
import dependency_injector.wiring as wiring
from SPARQLWrapper import SPARQLWrapper
import asyncpg

from app.models.graph import CompetencyNode, CompetencyEdge, GraphPart
from app.dao.node_version import NodeVersionDAO


class CompetencyDAO:
    """Data Access Object для работы с компетенциями в GraphDB"""

    @classmethod
    async def create_competency(
        cls,
        competency: CompetencyNode,
        user_id: int,
        graphdb_client: SPARQLWrapper = wiring.Provide["graphdb_client"],
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> CompetencyNode:
        """Создать новую компетенцию"""
        # Создаем узел в GraphDB
        insert_query = f"""
        INSERT DATA {{
            <{competency.id}> a cg:Competency ;
                schema:name "{competency.name}" ;
                cg:level {competency.level} .
        }}
        """
        graphdb_client.setMethod("POST")
        graphdb_client.setQuery(insert_query)
        graphdb_client.query()

        # Записываем версию и историю изменений
        await NodeVersionDAO.add_change(
            node_uri=competency.id,
            user_id=user_id,
            change_type="CREATE",
            old_value=None,
            new_value=competency.dict(),
            version=1,
            db_pool=db_pool
        )

        return competency

    @classmethod
    async def get_graph_part(
        cls,
        start_from: str,
        depth: int = 2,
        limit: int = 50,
        offset: int = 0,
        graphdb_client: SPARQLWrapper = wiring.Provide["graphdb_client"],
    ) -> GraphPart:
        """
        Получить часть графа, начиная с указанного узла.

        Args:
            start_from: URI начального узла
            depth: Глубина обхода (количество уровней)
            limit: Максимальное количество узлов
            offset: Смещение для пагинации
        """
        # Получаем узлы с учетом глубины
        nodes_query = f"""
        SELECT DISTINCT ?id ?name ?level
        WHERE {{
            <{start_from}> (cg:hasChild|^cg:hasChild){{{depth}}} ?id .
            ?id schema:name ?name ;
                cg:level ?level .
        }}
        ORDER BY ?level ?name
        LIMIT {limit}
        OFFSET {offset}
        """
        graphdb_client.setQuery(nodes_query)
        nodes_result = graphdb_client.query().convert()

        nodes = [
            CompetencyNode(
                id=result["id"]["value"],
                name=result["name"]["value"],
                level=int(result["level"]["value"])
            )
            for result in nodes_result["results"]["bindings"]
        ]

        # Получаем связи между найденными узлами
        node_ids = [f"<{node.id}>" for node in nodes]
        nodes_filter = f"FILTER(?source IN ({', '.join(node_ids)}) && ?target IN ({', '.join(node_ids)}))"

        edges_query = f"""
        SELECT ?source ?target
        WHERE {{
            ?source cg:hasChild ?target .
            {nodes_filter}
        }}
        """
        graphdb_client.setQuery(edges_query)
        edges_result = graphdb_client.query().convert()

        edges = [
            CompetencyEdge(
                source=result["source"]["value"],
                target=result["target"]["value"]
            )
            for result in edges_result["results"]["bindings"]
        ]

        return GraphPart(nodes=nodes, edges=edges)

    @classmethod
    async def get_ancestors(
        cls,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
        graphdb_client: SPARQLWrapper = wiring.Provide["graphdb_client"],
    ) -> tp.List[CompetencyNode]:
        """Получить всех предков компетенции"""
        query = f"""
        SELECT DISTINCT ?id ?name ?level
        WHERE {{
            <{competency_id}> ^cg:hasChild+ ?id .
            ?id schema:name ?name ;
                cg:level ?level .
        }}
        ORDER BY ?level
        LIMIT {limit}
        OFFSET {offset}
        """
        graphdb_client.setQuery(query)
        results = graphdb_client.query().convert()

        return [
            CompetencyNode(
                id=result["id"]["value"],
                name=result["name"]["value"],
                level=int(result["level"]["value"])
            )
            for result in results["results"]["bindings"]
        ]

    @classmethod
    async def get_descendants(
        cls,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
        graphdb_client: SPARQLWrapper = wiring.Provide["graphdb_client"],
    ) -> tp.List[CompetencyNode]:
        """Получить всех потомков компетенции"""
        query = f"""
        SELECT DISTINCT ?id ?name ?level
        WHERE {{
            <{competency_id}> cg:hasChild+ ?id .
            ?id schema:name ?name ;
                cg:level ?level .
        }}
        ORDER BY ?level
        LIMIT {limit}
        OFFSET {offset}
        """
        graphdb_client.setQuery(query)
        results = graphdb_client.query().convert()

        return [
            CompetencyNode(
                id=result["id"]["value"],
                name=result["name"]["value"],
                level=int(result["level"]["value"])
            )
            for result in results["results"]["bindings"]
        ]

    @classmethod
    async def find_path(
        cls,
        start_id: str,
        end_id: str,
        graphdb_client: SPARQLWrapper = wiring.Provide["graphdb_client"],
    ) -> tp.List[CompetencyNode]:
        """Найти путь между двумя компетенциями"""
        query = f"""
        SELECT ?id ?name ?level
        WHERE {{
            <{start_id}> (cg:hasChild|^cg:hasChild)* ?id .
            ?id (cg:hasChild|^cg:hasChild)* <{end_id}> .
            ?id schema:name ?name ;
                cg:level ?level .
        }}
        ORDER BY ?level
        """
        graphdb_client.setQuery(query)
        results = graphdb_client.query().convert()

        return [
            CompetencyNode(
                id=result["id"]["value"],
                name=result["name"]["value"],
                level=int(result["level"]["value"])
            )
            for result in results["results"]["bindings"]
        ]
