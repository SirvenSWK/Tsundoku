from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

@dataclass
class Task:
    id: UUID
    title: str
    description: str
    deadline: datetime | None
    duration: timedelta | None
    priority: str
    completed: bool