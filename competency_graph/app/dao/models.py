from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class CompetencyBase(BaseModel): # TODO: прописать applied routes
    name: str
    description: Optional[str] = None
    level: Optional[int] = Field(default=1, ge=1, le=5)

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

class CompetencyConflict(BaseModel):
    node_id: str
    current_version: int
    attempted_version: int
    conflicting_fields: List[str]
    timestamp: datetime

class ConflictResolution(BaseModel):
    conflict_id: str
    resolved_fields: Dict[str, Any]  # Выбранные значения для конфликтующих полей
    resolver_id: str
    resolution_timestamp: datetime
    resolution_comment: str

class CompetencyNode(BaseModel):
    id: str
    name: str
    level: int
    description: Optional[str] = None

class CompetencyEdge(BaseModel):
    source: str  # ID исходной компетенции
    target: str  # ID целевой компетенции

class GraphPart(BaseModel):
    nodes: List[CompetencyNode]
    edges: List[CompetencyEdge]

class CompetencyVersion(BaseModel):
    node_id: str
    version: int
    changes: Dict[str, Any]  # Изменения в формате {field: new_value}
    timestamp: datetime
    author_id: str

class VersionMetadata(BaseModel):
    previous_version: int
    change_type: str  # CREATE, UPDATE, DELETE
    change_reason: str  # Описание причины изменения
