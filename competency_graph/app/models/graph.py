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
