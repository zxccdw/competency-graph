from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CompetencyBase(BaseModel):
    """Базовая модель компетенции"""
    name: str
    description: Optional[str] = None
    level: Optional[int] = Field(default=1, ge=1, le=5)


class TimestampMixin(BaseModel):
    """Миксин для добавления временных меток"""
    created_at: datetime
    updated_at: datetime
