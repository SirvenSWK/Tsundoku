import json
from pathlib import Path
from uuid import UUID

from tsundoku.models.task_store import TaskStoreDocument
from tsundoku.models.tasks import Ingestion, Task

tasksFile = Path(__file__).resolve().parent.parent / "Data" / "tasks.json"


class TaskManager:
    def __init__(self) -> None:
        self.ingestions: list[Ingestion] = []
        self.tasks: list[Task] = []

    def addIngestion(self, ingestion: Ingestion) -> None:
        self.ingestions.append(ingestion)

    def addTask(self, task: Task) -> None:
        self.tasks.append(task)

    def removeTask(self, task: Task) -> None:
        self.tasks.remove(task)

    def getTasks(self) -> list[Task]:
        return self.tasks

    def tasksForIngestion(self, ingestionID: UUID) -> list[Task]:
        return [t for t in self.tasks if t.ingestionID == ingestionID]

    def childTasks(self, parentID: UUID) -> list[Task]:
        return [t for t in self.tasks if t.parentID == parentID]

    def save(self) -> None:
        doc = TaskStoreDocument(
            ingestions=[i.toRecord() for i in self.ingestions],
            tasks=[t.toRecord() for t in self.tasks],
        )
        tasksFile.parent.mkdir(parents=True, exist_ok=True)
        with tasksFile.open("w", encoding="utf-8") as file:
            json.dump(doc.model_dump(mode="json"), file, indent=4)

    def load(self) -> None:
        if not tasksFile.exists():
            self.ingestions = []
            self.tasks = []
            return
        with tasksFile.open(encoding="utf-8") as file:
            data = json.load(file)
        doc = TaskStoreDocument.model_validate(data)
        self.ingestions = [Ingestion.fromRecord(r) for r in doc.ingestions]
        self.tasks = [Task.fromRecord(r) for r in doc.tasks]
