from typing import List
import re
from SPARQLWrapper import POST, JSON, POSTDIRECTLY 
from fastapi import Depends
from dependency_injector import wiring
from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions

import requests
from fastapi import HTTPException

from models.graph import OntologyNode, CompetencyEdge, GraphPart, NodeType
from dependencies.config import Config

from models.graph import GraphResponse


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


        #11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111

   

    @classmethod
    async def get_graph_from_db(
        cls,
        client: SPARQLWrapper = Depends(wiring.Provide["graphdb_client"]),
        config: Config = Depends(wiring.Provide["config"])
    ) -> dict:
        """
        Получает весь граф из GraphDB
        """
        prefixes = cls._prefix_str(config)
    
        query = f"""
        {prefixes}
        CONSTRUCT {{
            ?s ?p ?o .
        }}
        WHERE {{
            ?s ?p ?o .
        }}
        """
    
        client.setQuery(query)
        client.method = "GET"
        try:
            results = client.query().convert()
        except Exception as e:
            raise RuntimeError(f"Ошибка при получении графа: {str(e)}")
    
        # Преобразование в нужный формат
        nodes = []
        links = []
    
        for s, p, o in results:
            if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                nodes.append({
                    "id": str(s),
                    "type": str(o),
                    "label": str(s).split("#")[-1]  # Локальное имя как label
                })
            else:
                links.append({
                    "source": str(s),
                    "target": str(o),
                    "predicate": str(p)
                })
    
        return {
            "nodes": nodes,
            "links": links
        }

    @classmethod
    async def save_graph_to_db(
        cls,
        graph_data: dict,
        config: Config = Depends(wiring.Provide["config"])
    ) -> bool:
        """
        Сохраняет граф в GraphDB через прямой HTTP запрос
        """
        type_map = {
            "class": "http://www.w3.org/2000/01/rdf-schema#Class",
            "property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property"
        }

        # URL для GraphDB updates (добавь /statements к основному URL)
        #graphdb_url = f"{config.GRAPHDB_ENDPOINT}/statements"

        graphdb_url = "http://localhost:7200/repositories/competencies/statements"
        auth = ("admin", "root")  # стандартные учетные данные GraphDB
    
        # Данные авторизации
        #auth = (config.GRAPHDB_USER, config.GRAPHDB_PASSWORD)

        successful = 0
        total = 0

        # Обрабатываем узлы
        for node in graph_data.get("nodes", []):
            node_uri = node["id"]
            node_type = type_map.get(node["type"], node["type"])
            label = node["label"].replace('"', '\\"')
        
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            INSERT DATA {{ <{node_uri}> a <{node_type}>; rdfs:label "{label}". }}
            """
        
            try:
                response = requests.post(
                    graphdb_url,
                    data={"update": query},
                    auth=auth,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                successful += 1
            except Exception as e:
                print(f"Ошибка с узлом {node_uri}: {e}")
        
            total += 1

        # Обрабатываем связи
        for link in graph_data.get("links", []):
            query = f"""
            INSERT DATA {{ <{link['source']}> <{link['predicate']}> <{link['target']}>. }}
            """
        
            try:
                response = requests.post(
                    graphdb_url,
                    data={"update": query},
                    auth=auth,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                successful += 1
            except Exception as e:
                print(f"Ошибка с связью {link['source']} -> {link['target']}: {e}")
        
            total += 1

        print(f"Успешно: {successful}/{total}")
        return successful > 0
    #11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111
    

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
    ) -> dict:
        """
        Возвращает часть графа в формате:
        {
            "nodes": [
                {"id": "...", "label": "...", "type": "..."}
            ],
            "links": [
                {"source": "...", "target": "...", "predicate": "..."}
            ]
        }
        """
        prefixes = cls._prefix_str(config)
        repo = config.graphdb.repository

        # Обработка URI
        if start_from.startswith(("http://", "https://")):
            start_uri = f"<{start_from}>"
        else:
            start_uri = f"<http://example.org/{repo}#{start_from}>"

        query = f"""
        {prefixes}

        SELECT DISTINCT ?id ?label ?type ?source ?target ?predicate
        WHERE {{
            {{
                # Получаем узлы
                {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5){{0,{depth}}} ?id .
                OPTIONAL {{ ?id rdfs:label ?label . }}
            
                # Определяем тип узла
                BIND(
                    IF(EXISTS {{ ?id a rdfs:Class }}, "class",
                    IF(EXISTS {{ ?id a rdf:Property }}, "property",
                    "instance")) AS ?type)
            }}
            UNION
            {{
                # Получаем связи
                ?source (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5) ?target .
                BIND("http://example.org/hasSubCompetence" AS ?predicate)
            
                # Фильтруем по глубине
                {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5){{0,{depth}}} ?source .
                {start_uri} (:hasLevel1|:hasLevel2|:hasLevel3|:hasLevel4|:hasLevel5){{0,{depth}}} ?target .
            }}
        }}
        OFFSET {offset}
        LIMIT {limit}
        """

        data = await cls._execute_stmt(client, query)

        # Собираем результаты
        nodes = []
        links = []
        seen_nodes = set()

        for binding in data["results"]["bindings"]:
            # Обработка узлов
            if "id" in binding:
                node_id = binding["id"]["value"]
                if node_id not in seen_nodes:
                    seen_nodes.add(node_id)
                    nodes.append({
                        "id": node_id,
                        "label": binding.get("label", {}).get("value", node_id),
                        "type": binding.get("type", {}).get("value", "class")
                    })

            # Обработка связей
            if "source" in binding and "target" in binding:
                links.append({
                    "source": binding["source"]["value"],
                    "target": binding["target"]["value"],
                    "predicate": binding.get("predicate", {}).get("value", 
                        "http://example.org/hasSubCompetence")
                })

        return {
            "nodes": nodes,
            "links": links
        }

    @classmethod
    async def get_graph_part_from_json(
        cls,
        graph_data: dict,  # Принимаем готовый JSON
        start_from: str,    # Опционально: начальный узел для фильтрации
        depth: int = 2
    ) -> dict:
        """
        Фильтрует готовый граф в JSON-формате.
        Пример graph_data:
        {
          "nodes": [...],
          "links": [...]
        }
        """
        # 1. Фильтрация узлов
        nodes = [
            node for node in graph_data["nodes"] 
            if node["id"] == start_from  # Простая фильтрация (можно сложнее)
        ]
    
        # 2. Фильтрация связей
        links = [
            link for link in graph_data["links"]
            if link["source"] == start_from or link["target"] == start_from
        ]
    
        return {
            "nodes": nodes[:depth*10],  # Упрощённая "глубина"
            "links": links[:depth*10]
        }



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
            label = binding.get("label", {}).get("value", ancestor_uri)

            ancestors.append(
                OntologyNode(
                    id=ancestor_uri,
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
            label = binding.get("label", {}).get("value", descendant_uri)

            descendants.append(
                OntologyNode(
                    id=descendant_uri,
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
        VALUES (?start ?end) {{ ({start_uri} {end_uri}) }}

        ?start (:hasSubCompetence)+ ?end .

        ?node ( ^:hasSubCompetence* | :hasSubCompetence* ) ?end .

        OPTIONAL {{ ?node rdfs:label ?label . }}
        }}
        """

        data = await cls._execute_stmt(client, query)

        nodes = []
        seen = set()

        for binding in data["results"]["bindings"]:
            node_uri = binding["node"]["value"]
            label = binding.get("label", {}).get("value", node_uri)

            if node_uri not in seen:
                seen.add(node_uri)
                nodes.append(
                    OntologyNode(
                        id=node_uri,
                        label=label,
                        type=NodeType.CLASS
                    )
                )

        return nodes