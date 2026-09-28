from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from tsundoku.models.task_store import IngestionRecord, TaskRecord, EventRecord


@dataclass
class Ingestion:
    id: UUID
    rawText: str
    timeStamp: datetime

    def toRecord(self) -> IngestionRecord:
        return IngestionRecord(
            id=self.id,
            rawText=self.rawText,
            timeStamp=self.timeStamp,
        )

    @classmethod
    def fromRecord(cls, record: IngestionRecord) -> "Ingestion":
        return cls(
            id=record.id,
            rawText=record.rawText,
            timeStamp=record.timeStamp,
        )


@dataclass
class Task:
    id: UUID
    title: str
    description: str
    scheduledStart: datetime | None
    deadline: datetime | None
    duration: timedelta | None
    priority: str
    completed: bool
    parentID: UUID | None = None
    ingestionID: UUID | None = None
    isAllDay: bool = False
    eventID: UUID | None = None
    googleEventID: str | None = None
    googleCalendarID: str | None = None

    def toRecord(self) -> TaskRecord:
        durationMinutes = None
        if self.duration is not None:
            durationMinutes = int(self.duration.total_seconds() // 60)
        return TaskRecord(
            id=self.id,
            title=self.title,
            description=self.description,
            scheduledStart=self.scheduledStart,
            deadline=self.deadline,
            durationMinutes=durationMinutes,
            priority=self.priority,
            completed=self.completed,
            ingestionID=self.ingestionID,
            parentID=self.parentID,
            isAllDay=self.isAllDay,
            eventID=self.eventID,
            googleEventID=self.googleEventID,
            googleCalendarID=self.googleCalendarID,
        )

    @classmethod
    def fromRecord(cls, record: TaskRecord) -> "Task":
        duration = None
        if record.durationMinutes is not None:
            duration = timedelta(minutes=record.durationMinutes)
        return cls(
            id=record.id,
            title=record.title,
            description=record.description,
            scheduledStart=record.scheduledStart,
            deadline=record.deadline,
            duration=duration,
            priority=record.priority,
            completed=record.completed,
            ingestionID=record.ingestionID,
            parentID=record.parentID,
            isAllDay=record.isAllDay,
            eventID=record.eventID,
            googleEventID=record.googleEventID,
            googleCalendarID=record.googleCalendarID,
        )

@dataclass
class Event:
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

    def toRecord(self) -> EventRecord:
        return EventRecord(
            id=self.id,
            title=self.title,
            description=self.description,
            scheduledStart=self.scheduledStart,
            isAllDay=self.isAllDay,
            ingestionID=self.ingestionID,
            googleEventID=self.googleEventID,
            googleCalendarID=self.googleCalendarID,
            sourceGoogleEventID=self.sourceGoogleEventID,
            sourceGoogleCalendarID=self.sourceGoogleCalendarID,
        )

    @classmethod
    def fromRecord(cls, record: EventRecord) -> "Event":
        return cls(
            id=record.id,
            title=record.title,
            description=record.description,
            scheduledStart=record.scheduledStart,
            isAllDay=record.isAllDay,
            ingestionID=record.ingestionID,
            googleEventID=record.googleEventID,
            googleCalendarID=record.googleCalendarID,
            sourceGoogleEventID=record.sourceGoogleEventID,
            sourceGoogleCalendarID=record.sourceGoogleCalendarID,
        )
