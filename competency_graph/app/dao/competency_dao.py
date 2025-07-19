from typing import List, Optional
import re

from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions

from models import *

class CompetencyDAO:

    def __init__(self, client: SPARQLWrapper, config: dict[str, str]):
        self._client = client
        self._config = config

        self._prefixes = {
            "": f"<http://{self._config['url']}/{self._config['repository']}#>",
            "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "rdfs": "<http://www.w3.org/2000/01/rdf-schema#>",
            "owl": "<http://www.w3.org/2002/07/owl#>",
        }

    def _prefix_str(self) -> str:
        return "\n".join(f"PREFIX {k}: {v}" for k, v in self._prefixes.items())
    
    async def _execute_stmt(self, stmt: str) -> dict:
        self._client.setQuery(stmt)
        try:
            result = self.client.query().convert()
            return result
        except SPARQLExceptions.EndPointInternalError as e:
            raise RuntimeError(f"Ошибка GraphDB: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения SPARQL-запроса: {e}")
        
    @staticmethod
    def _extract_local_name(uri: str) -> str:
        """
        Вытаскивает локальное имя из URI: http://example.org/university#compML → compML
        """
        match = re.search(r'#(.+)$', uri)
        return match.group(1) if match else uri
    
    async def get_graph_part(
        self,
        start_from: str,
        depth: int = 2,
        limit: int = 50,
        offset: int = 0,
    ) -> GraphPart:
        """
        Возвращает часть графа начиная с узла `start_from` до заданной глубины,
        с учетом лимита и оффсета.
        """
        prefixes = self._prefix_str()
        repo = self._config.repository

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

        data = await self._execute_stmt(query)

        nodes_map = {}
        edges: List[CompetencyEdge] = []

        for binding in data["results"]["bindings"]:
            id_uri = binding["id"]["value"]
            id_local = self._extract_local_name(id_uri)

            name = binding.get("label", {}).get("value", id_local)
            level = int(binding.get("level", {}).get("value", 0))
            description = None  # Если нужно, можно расширить и вытягивать описание

            nodes_map[id_local] = CompetencyNode(
                id=id_local,
                name=name,
                level=level,
                description=description
            )

            if "parent" in binding:
                parent_uri = binding["parent"]["value"]
                parent_local = self._extract_local_name(parent_uri)
                edges.append(CompetencyEdge(source=parent_local, target=id_local))

        return GraphPart(
            nodes=list(nodes_map.values()),
            edges=edges
        )

    async def get_ancestors(
        self,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompetencyNode]:
        """
        Возвращает предков компетенции с идентификатором `competency_id`,
        с учетом лимита и смещения (offset).
        """
        prefixes = self._prefix_str()

        # Формируем полный URI компетенции
        if competency_id.startswith("http://") or competency_id.startswith("https://"):
            comp_uri = f"<{competency_id}>"
        else:
            comp_uri = f"<http://example.org/{self._config.repository}#{competency_id}>"

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

        data = await self._execute_stmt(query)

        ancestors = []
        for binding in data["results"]["bindings"]:
            ancestor_uri = binding["ancestor"]["value"]
            ancestor_id = self._extract_local_name(ancestor_uri)
            label = binding.get("label", {}).get("value", ancestor_id)
            level = int(binding.get("level", {}).get("value", 0))

            ancestors.append(
                CompetencyNode(
                    id=ancestor_id,
                    name=label,
                    level=level,
                    description=None,
                )
            )

        return ancestors

    async def get_descendants(
        self,
        competency_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompetencyNode]:
        """
        Возвращает потомков компетенции с идентификатором `competency_id`,
        с учетом лимита и смещения (offset).
        """
        prefixes = self._prefix_str()

        # Формируем полный URI компетенции
        if competency_id.startswith("http://") or competency_id.startswith("https://"):
            comp_uri = f"<{competency_id}>"
        else:
            comp_uri = f"<http://example.org/{self._config.repository}#{competency_id}>"

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

        data = await self._execute_stmt(query)

        descendants = []
        for binding in data["results"]["bindings"]:
            descendant_uri = binding["descendant"]["value"]
            descendant_id = self._extract_local_name(descendant_uri)
            label = binding.get("label", {}).get("value", descendant_id)
            level = int(binding.get("level", {}).get("value", 0))

            descendants.append(
                CompetencyNode(
                    id=descendant_id,
                    name=label,
                    level=level,
                    description=None,
                )
            )

        return descendants

    async def find_path(
        self,
        start_id: str,
        end_id: str,
    ) -> List[CompetencyNode]:
        """
        Находит путь от start_id до end_id по связям :hasSubCompetence.
        Возвращает список узлов на пути или пустой список, если путь не найден.
        """

        prefixes = self._prefix_str()

        if start_id.startswith("http://") or start_id.startswith("https://"):
            start_uri = f"<{start_id}>"
        else:
            start_uri = f"<http://example.org/{self._config.repository}#{start_id}>"

        if end_id.startswith("http://") or end_id.startswith("https://"):
            end_uri = f"<{end_id}>"
        else:
            end_uri = f"<http://example.org/{self._config.repository}#{end_id}>"

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

        data = await self._execute_stmt(query)

        # Чтобы упорядочить узлы по пути, можно усложнить запрос, но SPARQL
        # не всегда позволяет легко это сделать.
        # Для простоты вернем уникальные узлы без гарантии порядка.

        nodes = []
        seen = set()

        for binding in data["results"]["bindings"]:
            node_uri = binding["node"]["value"]
            node_id = self._extract_local_name(node_uri)
            label = binding.get("label", {}).get("value", node_id)

            if node_id not in seen:
                seen.add(node_id)
                nodes.append(
                    CompetencyNode(
                        id=node_id,
                        name=label,
                        level=0,  # можно добавить логику для уровня, если нужно
                        description=None
                    )
                )

        return nodes



async def search_by_label(self, label: str, lang: str = "ru") -> list[dict]:
        """
        Ищет сущности по rdfs:label с заданным текстом и языком.

        :param label: Текст метки для поиска (частичное совпадение).
        :param lang: Язык метки (по умолчанию "ru").
        :return: Список словарей с URI и меткой.
        """
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?entity ?label
        WHERE {{
            ?entity rdfs:label ?label .
            FILTER (
                lang(?label) = "{lang}" &&
                CONTAINS(LCASE(STR(?label)), LCASE("{label}"))
            )
        }}
        """

        result = await self._execute_stmt(query)
        bindings = result.get("results", {}).get("bindings", [])

        return [
            {
                "uri": b["entity"]["value"],
                "label": b["label"]["value"]
            }
            for b in bindings
        ]
