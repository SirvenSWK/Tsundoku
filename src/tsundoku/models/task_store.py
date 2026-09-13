from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class IngestionRecord(BaseModel):
    id: UUID
    rawText: str
    timeStamp: datetime


class TaskRecord(BaseModel):
    id: UUID
    title: str
    description: str = ""
    deadline: datetime | None = None
    durationMinutes: int | None = None
    priority: str = "normal"
    completed: bool = False
    ingestionID: UUID | None = None
    parentID: UUID | None = None


class TaskStoreDocument(BaseModel):
    version: int = Field(default=1, ge=1)
    ingestions: list[IngestionRecord] = Field(default_factory=list)
    tasks: list[TaskRecord] = Field(default_factory=list)
