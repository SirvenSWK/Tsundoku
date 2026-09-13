from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from tsundoku.models.task_store import IngestionRecord, TaskRecord


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
    deadline: datetime | None
    duration: timedelta | None
    priority: str
    completed: bool
    parentID: UUID | None = None
    ingestionID: UUID | None = None

    def toRecord(self) -> TaskRecord:
        durationMinutes = None
        if self.duration is not None:
            durationMinutes = int(self.duration.total_seconds() // 60)
        return TaskRecord(
            id=self.id,
            title=self.title,
            description=self.description,
            deadline=self.deadline,
            durationMinutes=durationMinutes,
            priority=self.priority,
            completed=self.completed,
            ingestionID=self.ingestionID,
            parentID=self.parentID,
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
            deadline=record.deadline,
            duration=duration,
            priority=record.priority,
            completed=record.completed,
            ingestionID=record.ingestionID,
            parentID=record.parentID,
        )
