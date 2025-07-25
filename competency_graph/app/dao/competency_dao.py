from typing import List
import re

from fastapi import Depends
from dependency_injector import wiring
from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions

from models.graph import OntologyNode, CompetencyEdge, GraphPart, NodeType
from dependencies.config import Config
class CompetencyDAO:
    @classmethod
    def _get_prefixes(cls, config: Config) -> dict[str, str]:
        return {
            "": f"<{config.graphdb.url}/repositories/{config.graphdb.repository}#>",
            "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "rdfs": "<http://www.w3.org/2000/01/rdf-schema#>",
            "owl": "<http://www.w3.org/2002/07/owl#>",
        }

    @classmethod
    def _prefix_str(cls, config: Config) -> str:
        prefixes = cls._get_prefixes(config)
        return "\n".join(f"PREFIX {k}: {v}" for k, v in prefixes.items())
    
    @classmethod
    async def _execute_stmt(cls, client: SPARQLWrapper, stmt: str) -> dict:
        client.setQuery(stmt)
        try:
            result = client.query().convert()
            return result
        except SPARQLExceptions.EndPointInternalError as e:
            raise RuntimeError(f"Ошибка GraphDB: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения SPARQL-запроса: {e}")
        
    @classmethod
    def _extract_local_name(cls, uri: str) -> str:
        """
        Вытаскивает локальное имя из URI: http://example.org/university#compML → compML
        """
        match = re.search(r'#(.+)$', uri)
        return match.group(1) if match else uri
    
    @classmethod
    @wiring.inject
    async def get_graph_part(
        cls,
        start_from: str,
        depth: int = 2,
        limit: int = 50,
        offset: int = 0,
        client: SPARQLWrapper = Depends(wiring.Provide["graphdb_client"]),
        config: Config = Depends(wiring.Provide["config"])
    ) -> GraphPart:
        """
        Возвращает часть графа начиная с узла `start_from` до заданной глубины,
        с учетом лимита и оффсета.
        """
        prefixes = cls._prefix_str(config)
        repo = config.graphdb.repository

        # Формируем полный URI start_from, если это не URI, а локальный ID
        if start_from.startswith("http://") or start_from.startswith("https://"):
            start_uri = f"<{start_from}>"
        else:
            start_uri = f"<http://example.org/{repo}#{start_from}>"

        query = f"""
        {prefixes}

        SELECT DISTINCT ?id ?label ?level ?parent
        WHERE {{
        {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5){{0,{depth}}} ?id .
        OPTIONAL {{ ?id rdfs:label ?label . }}
        OPTIONAL {{
            ?parent (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5) ?id .
        }}
        BIND(
            IF(EXISTS {{ {start_uri} :hasLevel1 ?id }}, 1,
            IF(EXISTS {{ {start_uri} (:hasLevel1|:hasLevel2) ?id }}, 2,
            IF(EXISTS {{ {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3) ?id }}, 3,
            IF(EXISTS {{ {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4) ?id }}, 4,
            IF(EXISTS {{ {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5) ?id }}, 5, 0
            ))))) AS ?level)
        }}
        OFFSET {offset}
        LIMIT {limit}
        """

        data = await cls._execute_stmt(client, query)

        nodes_map = {}
        edges: List[CompetencyEdge] = []

        for binding in data["results"]["bindings"]:
            id_uri = binding["id"]["value"]
            id_local = cls._extract_local_name(id_uri)

            label = binding.get("label", {}).get("value", id_local)

            nodes_map[id_local] = OntologyNode(
                id=id_local,
                label=label,
                type=NodeType.CLASS  # По умолчанию все узлы считаем классами
            )

            if "parent" in binding:
                parent_uri = binding["parent"]["value"]
                parent_local = cls._extract_local_name(parent_uri)
                edges.append(CompetencyEdge(source=parent_local, target=id_local))

        return GraphPart(
            nodes=list(nodes_map.values()),
            edges=edges
        )

    @classmethod
    @wiring.inject
    async def get_ancestors(
        cls,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
        client: SPARQLWrapper = Depends(wiring.Provide["graphdb_client"]),
        config: Config = Depends(wiring.Provide["config"])
    ) -> List[OntologyNode]:
        """
        Возвращает предков компетенции с идентификатором `competency_id`,
        с учетом лимита и смещения (offset).
        """
        prefixes = cls._prefix_str(config)

        # Формируем полный URI компетенции
        if competency_id.startswith("http://") or competency_id.startswith("https://"):
            comp_uri = f"<{competency_id}>"
        else:
            comp_uri = f"<http://example.org/{config.graphdb.repository}#{competency_id}>"

        query = f"""
        {prefixes}

        SELECT DISTINCT ?ancestor ?label ?level
        WHERE {{
        {comp_uri} (:hasSubCompetence)+ ?ancestor .
        OPTIONAL {{ ?ancestor rdfs:label ?label . }}
        OPTIONAL {{
            ?ancestor :hasLevel1 ?_ .
            BIND(1 AS ?level)
        }}
        OPTIONAL {{
            ?ancestor :hasLevel2 ?_ .
            BIND(2 AS ?level)
        }}
        OPTIONAL {{
            ?ancestor :hasLevel3 ?_ .
            BIND(3 AS ?level)
        }}
        OPTIONAL {{
            ?ancestor :hasLevel4 ?_ .
            BIND(4 AS ?level)
        }}
        OPTIONAL {{
            ?ancestor :hasLevel5 ?_ .
            BIND(5 AS ?level)
        }}
        }}
        OFFSET {offset}
        LIMIT {limit}
        """

        data = await cls._execute_stmt(client, query)

        ancestors = []
        for binding in data["results"]["bindings"]:
            ancestor_uri = binding["ancestor"]["value"]
            ancestor_id = cls._extract_local_name(ancestor_uri)
            label = binding.get("label", {}).get("value", ancestor_id)

            ancestors.append(
                OntologyNode(
                    id=ancestor_id,
                    label=label,
                    type=NodeType.CLASS
                )
            )

        return ancestors

    @classmethod
    @wiring.inject
    async def get_descendants(
        cls,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
        client: SPARQLWrapper = Depends(wiring.Provide["graphdb_client"]),
        config: Config = Depends(wiring.Provide["config"])
    ) -> List[OntologyNode]:
        """
        Возвращает потомков компетенции с идентификатором `competency_id`,
        с учетом лимита и смещения (offset).
        """
        prefixes = cls._prefix_str(config)

        # Формируем полный URI компетенции
        if competency_id.startswith("http://") or competency_id.startswith("https://"):
            comp_uri = f"<{competency_id}>"
        else:
            comp_uri = f"<http://example.org/{config.graphdb.repository}#{competency_id}>"

        query = f"""
        {prefixes}

        SELECT DISTINCT ?descendant ?label ?level
        WHERE {{
        {comp_uri} (:hasSubCompetence)+ ?descendant .
        OPTIONAL {{ ?descendant rdfs:label ?label . }}
        OPTIONAL {{
            ?descendant :hasLevel1 ?_ .
            BIND(1 AS ?level)
        }}
        OPTIONAL {{
            ?descendant :hasLevel2 ?_ .
            BIND(2 AS ?level)
        }}
        OPTIONAL {{
            ?descendant :hasLevel3 ?_ .
            BIND(3 AS ?level)
        }}
        OPTIONAL {{
            ?descendant :hasLevel4 ?_ .
            BIND(4 AS ?level)
        }}
        OPTIONAL {{
            ?descendant :hasLevel5 ?_ .
            BIND(5 AS ?level)
        }}
        }}
        OFFSET {offset}
        LIMIT {limit}
        """

        data = await cls._execute_stmt(client, query)

        descendants = []
        for binding in data["results"]["bindings"]:
            descendant_uri = binding["descendant"]["value"]
            descendant_id = cls._extract_local_name(descendant_uri)
            label = binding.get("label", {}).get("value", descendant_id)

            descendants.append(
                OntologyNode(
                    id=descendant_id,
                    label=label,
                    type=NodeType.CLASS
                )
            )

        return descendants

    @classmethod
    @wiring.inject
    async def find_path(
        cls,
        start_id: str,
        end_id: str,
        client: SPARQLWrapper = Depends(wiring.Provide["graphdb_client"]),
        config: Config = Depends(wiring.Provide["config"])
    ) -> List[OntologyNode]:
        """
        Находит путь от start_id до end_id по связям :hasSubCompetence.
        Возвращает список узлов на пути или пустой список, если путь не найден.
        """

        prefixes = cls._prefix_str(config)

        if start_id.startswith("http://") or start_id.startswith("https://"):
            start_uri = f"<{start_id}>"
        else:
            start_uri = f"<http://example.org/{config.graphdb.repository}#{start_id}>"

        if end_id.startswith("http://") or end_id.startswith("https://"):
            end_uri = f"<{end_id}>"
        else:
            end_uri = f"<http://example.org/{config.graphdb.repository}#{end_id}>"

        query = f"""
        {prefixes}

        SELECT ?node ?label
        WHERE {{
        # Путь от start до end по hasSubCompetence
        VALUES (?start ?end) {{ ({start_uri} {end_uri}) }}

        # Используем property path для поиска пути
        ?start (:hasSubCompetence)+ ?end .

        # Находим узлы на пути
        ?node ( ^:hasSubCompetence* | :hasSubCompetence* ) ?end .

        OPTIONAL {{ ?node rdfs:label ?label . }}
        }}
        """

        data = await cls._execute_stmt(client, query)

        # Чтобы упорядочить узлы по пути, можно усложнить запрос, но SPARQL
        # не всегда позволяет легко это сделать.
        # Для простоты вернем уникальные узлы без гарантии порядка.

        nodes = []
        seen = set()

        for binding in data["results"]["bindings"]:
            node_uri = binding["node"]["value"]
            node_id = cls._extract_local_name(node_uri)
            label = binding.get("label", {}).get("value", node_id)

            if node_id not in seen:
                seen.add(node_id)
                nodes.append(
                    OntologyNode(
                        id=node_id,
                        label=label,
                        type=NodeType.CLASS
                    )
                )

        return nodes


