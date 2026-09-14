from tsundoku.tools import organizer, taskManager
import PySide6.QtWidgets as QtWidget


class HomePage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.taskManager = taskManager.TaskManager()
        self.taskManager.load()
        self.inputBox = QtWidget.QPlainTextEdit()
        self.inputBox.setPlaceholderText(
            "Hello user, tell me what's up?"
        )
        self.listOfTasks = QtWidget.QListWidget()

        self.organizeButton = QtWidget.QPushButton("Organize")

        self.organizeButton.clicked.connect(self.organize)

        layout = QtWidget.QVBoxLayout()
        layout.addWidget(self.inputBox)
        layout.addWidget(self.organizeButton)
        layout.addWidget(self.listOfTasks)

        self.setLayout(layout)
        self.refreshTaskList()

    def refreshTaskList(self) -> None:
        self.listOfTasks.clear()

        for task in self.taskManager.getTasks():
            prefix = " ↳ " if task.parentID else ""

            durationText = ""
            if task.duration is not None:
                minutes = int(task.duration.total_seconds() // 60)
                durationText = f" · {minutes} min"
        priorityText = f" · {task.priority}"

        self.listOfTasks.addItem(
            f"{prefix}{task.title}{durationText}{priorityText}"
        )
    def organize(self):
        text = self.inputBox.toPlainText().strip()

        if not text:
            return

        result = organizer.organizeWithLlm(text)
        ingestion, newTasks = organizer.applyOrganizeResult(result, text)
        self.taskManager.addIngestion(ingestion)
        for task in newTasks:
            self.taskManager.addTask(task)

        self.taskManager.save()
        self.refreshTaskList()
        self.inputBox.clear()
