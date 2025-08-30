from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Тип узла в онтологии"""
    CLASS = 'class'
    PROPERTY = 'property'
    INSTANCE = 'instance'


class OntologyNode(BaseModel):
    """Модель узла в онтологии"""
    id: str
    label: str
    type: NodeType = Field(default=NodeType.CLASS)


class CompetencyEdge(BaseModel):
    """Модель связи между компетенциями"""
    source: str  # ID исходной компетенции
    target: str  # ID целевой компетенции


class GraphPart(BaseModel):
    """Часть графа онтологии"""
    nodes: List[OntologyNode]
    edges: List[CompetencyEdge]




# Новый вариант

class RDFNode(BaseModel):
    """Узел в формате RDF (с полным URI)"""
    id: str
    label: str
    type: str  # например: "class", "property", "instance"

class RDFLink(BaseModel):
    """Связь (триплет) между узлами"""
    source: str
    target: str
    predicate: str  # тоже URI

class GraphResponse(BaseModel):
    """Граф в формате, который принимает/отдаёт фронтенд"""
    nodes: List[RDFNode]
    links: List[RDFLink]

