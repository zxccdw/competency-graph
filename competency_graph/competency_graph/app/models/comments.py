from datetime import datetime
from pydantic import BaseModel, Field

class Comment(BaseModel):
    id: int | None = None
    filename: str
    start_index: int = Field(alias="startIndex")
    end_index: int = Field(alias="endIndex")
    subject: str
    predicate: str
    object: str
    author: str
    created_at: datetime | None = Field(default=None, alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True
