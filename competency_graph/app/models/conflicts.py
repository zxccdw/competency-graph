from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel


class CompetencyConflict(BaseModel):
    """Модель для конфликтов при обновлении"""
    node_id: str
    current_version: int
    attempted_version: int
    conflicting_fields: List[str]
    timestamp: datetime


class ConflictResolution(BaseModel):
    """Модель для разрешения конфликтов"""
    conflict_id: str
    resolved_fields: Dict[str, Any]  # Выбранные значения для конфликтующих полей
    resolver_id: str
    resolution_timestamp: datetime
    resolution_comment: str
