from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class CompetencyVersion(BaseModel):
    """Модель для версионирования компетенций"""
    node_id: str
    version: int
    changes: Dict[str, Any]  # Изменения в формате {field: new_value}
    timestamp: datetime
    author_id: str


class VersionMetadata(BaseModel):
    """Метаданные версии"""
    previous_version: int
    change_type: str  # CREATE, UPDATE, DELETE
    change_reason: str  # Описание причины изменения
