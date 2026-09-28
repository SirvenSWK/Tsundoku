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
    description: str
    scheduledStart: datetime | None = None
    deadline: datetime | None = None
    durationMinutes: int | None = None
    priority: str
    completed: bool
    ingestionID: UUID | None = None
    parentID: UUID | None = None
    eventID: UUID | None = None
    googleEventID: str | None = None
    googleCalendarID: str | None = None
    isAllDay: bool = False

class EventRecord(BaseModel):
    id: UUID
    title: str
    description: str
    scheduledStart: datetime | None
    isAllDay: bool
    ingestionID: UUID | None = None
    googleEventID: str | None = None
    googleCalendarID: str | None = None
    sourceGoogleEventID: str | None = None
    sourceGoogleCalendarID: str | None = None


class TaskStoreDocument(BaseModel):
    version: int = Field(default=1, ge=1)
    ingestions: list[IngestionRecord] = Field(default_factory=list)
    tasks: list[TaskRecord] = Field(default_factory=list)
    events: list[EventRecord] = Field(default_factory=list)
