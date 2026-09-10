import tsundoku.models.tasks as tasks
from tsundoku.tools import taskManager
import PySide6.QtWidgets as QtWidget
from uuid import uuid4

class HomePage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.taskManager = taskManager.TaskManager()
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

    def organize(self):
        text = self.inputBox.toPlainText().strip()

        if not text:
            return

        task = tasks.Task(
            id=uuid4(),
            title=text,
            description="",
            deadline=None,
            duration=None,
            priority="normal",
            completed=False
        )

        self.taskManager.addTask(task)
        self.listOfTasks.addItem(task.title)