from typing import List, Optional
from pydantic import BaseModel


class CompetencyNode(BaseModel):
    """Модель узла компетенции в графе"""
    id: str
    name: str
    level: int
    description: Optional[str] = None


class CompetencyEdge(BaseModel):
    """Модель связи между компетенциями"""
    source: str  # ID исходной компетенции
    target: str  # ID целевой компетенции


class GraphPart(BaseModel):
    """Часть графа компетенций"""
    nodes: List[CompetencyNode]
    edges: List[CompetencyEdge]
