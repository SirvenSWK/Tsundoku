import json
from pathlib import Path
import os
import tempfile
from uuid import UUID

from tsundoku.models.task_store import TaskStoreDocument
from tsundoku.models.tasks import Ingestion, Task, Event
from tsundoku.models.storage_paths import data_directory, migrate_legacy_file

LEGACY_TASKS_FILE = Path(__file__).resolve().parent.parent / "Data" / "tasks.json"
tasksFile = data_directory() / "tasks.json"


class TaskManager:
    def __init__(self) -> None:
        self.ingestions: list[Ingestion] = []
        self.tasks: list[Task] = []
        self.events: list[Event] = []

    def addIngestion(self, ingestion: Ingestion) -> None:
        if not any(existing.id == ingestion.id for existing in self.ingestions):
            self.ingestions.append(ingestion)

    def addEvent(self, event: Event) -> None:
        if not any(existing.id == event.id for existing in self.events):
            self.events.append(event)

    def addTask(self, task: Task) -> None:
        if not any(existing.id == task.id for existing in self.tasks):
            self.tasks.append(task)

    def removeEvent(self, event: Event) -> None:
        self.events.remove(event)

    def removeTask(self, task: Task) -> None:
        self.tasks.remove(task)

    def getTasks(self) -> list[Task]:
        return self.tasks

    def getEvents(self) -> list[Event]:
        return self.events

    def tasksForIngestion(self, ingestionID: UUID) -> list[Task]:
        return [t for t in self.tasks if t.ingestionID == ingestionID]

    def childTasks(self, parentID: UUID) -> list[Task]:
        return [t for t in self.tasks if t.parentID == parentID]

    def save(self) -> None:
        doc = TaskStoreDocument(
            ingestions=[i.toRecord() for i in self.ingestions],
            tasks=[t.toRecord() for t in self.tasks],
            events=[e.toRecord() for e in self.events],
        )
        tasksFile.parent.mkdir(parents=True, exist_ok=True)
        temporaryPath = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=tasksFile.parent,
                prefix=f"{tasksFile.name}.", suffix=".tmp", delete=False,
            ) as file:
                temporaryPath = Path(file.name)
                json.dump(doc.model_dump(mode="json"), file, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporaryPath, tasksFile)
        finally:
            if temporaryPath is not None and temporaryPath.exists():
                temporaryPath.unlink()

    def load(self) -> None:
        migrate_legacy_file(LEGACY_TASKS_FILE, tasksFile)
        if not tasksFile.exists():
            self.ingestions = []
            self.tasks = []
            self.events = []
            return
        with tasksFile.open(encoding="utf-8") as file:
            data = json.load(file)
        doc = TaskStoreDocument.model_validate(data)
        self.ingestions = [Ingestion.fromRecord(r) for r in doc.ingestions]
        self.tasks = [Task.fromRecord(r) for r in doc.tasks]
        self.events = [Event.fromRecord(r) for r in doc.events]

taskManager = TaskManager()
