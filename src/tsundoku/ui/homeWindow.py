from tsundoku.tools import organizer, taskManager
import PySide6.QtWidgets as QtWidget


class HomePage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.pendingIngestions = {}
        self.taskManager = taskManager.TaskManager()
        self.taskManager.load()
        self.inputBox = QtWidget.QPlainTextEdit()
        self.inputBox.setPlaceholderText(
            "Hello user, tell me what's up?"
        )
        self.reviewPanel = QtWidget.QFrame()
        self.reviewLayout = QtWidget.QVBoxLayout()
        self.reviewPanel.setLayout(self.reviewLayout)

        self.organizeButton = QtWidget.QPushButton("Organize")

        self.organizeButton.clicked.connect(self.organize)

        layout = QtWidget.QVBoxLayout()
        layout.addWidget(self.inputBox)
        layout.addWidget(self.organizeButton)
        layout.addWidget(self.reviewPanel)

        self.setLayout(layout)

    def refreshViewPanel(self, message: str = "Nothing organized yet!"):
        self.clearReviewPanel()
        self.reviewLayout.addWidget(QtWidget.QLabel(message))


    def organize(self):
        text = self.inputBox.toPlainText().strip()

        if not text:
            return

        result = organizer.organizeWithLlm(text)

        if not result.tasks:
            self.refreshViewPanel(
                result.message
                or "I couldn't find an actionable task"
            )
            return
        
        ingestion, newTasks = organizer.applyOrganizeResult(result, text)

        self.pendingIngestions[ingestion.id] = ingestion

        self.displayTasks(newTasks)
        self.inputBox.clear()

    def displayTasks(self, tasks):
        self.clearReviewPanel()

        if not tasks:
            self.reviewLayout.addWidget(
                QtWidget.QLabel(
                    "I couldn't find an actionable task.\n"
                    "Tell me what you need to do."
                )
            )
            return

        for task in tasks:
            taskCard = self.addTaskCard(task)
            self.reviewLayout.addWidget(taskCard)
    def clearReviewPanel(self):
        while self.reviewLayout.count():
            item = self.reviewLayout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()
    def addTaskCard(self, task):
        taskCard = QtWidget.QFrame()
        taskCard.setFrameShape(QtWidget.QFrame.Shape.StyledPanel)

        taskLayout = QtWidget.QVBoxLayout(taskCard)

        titleLabel = QtWidget.QLabel(task.title)
        titleLabel.setStyleSheet(
            "Font-size : 16px ; font-weight : bold ;"
        )
        priorityLabel = QtWidget.QLabel(
            f"Priority {task.priority}"
        )
        durationText = (
            str(task.duration)
            if task.duration is not None
            else "Not specified"
        )
        durationLabel = QtWidget.QLabel(durationText)
        taskLayout.addWidget(titleLabel)

        if task.description:
            descriptionLabel = QtWidget.QLabel(task.description)
            descriptionLabel.setWordWrap(True)
            taskLayout.addWidget(descriptionLabel)

        taskLayout.addWidget(priorityLabel)
        taskLayout.addWidget(durationLabel)

        buttonLayout = QtWidget.QHBoxLayout()

        acceptButton = QtWidget.QPushButton("Accept")
        rejectButton = QtWidget.QPushButton("Reject")
        addDetailButton = QtWidget.QPushButton("Add details")

        buttonLayout.addWidget(acceptButton)
        buttonLayout.addWidget(rejectButton)
        buttonLayout.addWidget(addDetailButton)

        taskLayout.addLayout(buttonLayout)

        additionalInfoBox = QtWidget.QPlainTextEdit()
        additionalInfoBox.setPlaceholderText(
            "Add details such as the date, topics, location, "
            "difficulty, or how long this should take..."
        )
        additionalInfoBox.setVisible(False)

        reorganizeButton = QtWidget.QPushButton("Reorganize")

        reorganizeButton.setVisible(False)

        taskLayout.addWidget(additionalInfoBox)
        taskLayout.addWidget(reorganizeButton)

        addDetailButton.clicked.connect(
            lambda: self.showAdditionalInfo(
                additionalInfoBox,
                reorganizeButton,
            )
        )
        reorganizeButton.clicked.connect(
            lambda: self.reorganizeTask(
                task,
                additionalInfoBox,
            )
        )

        rejectButton.clicked.connect(
            lambda: self.rejectTask(taskCard, task)
        )
        acceptButton.clicked.connect(
            lambda: self.acceptTask(taskCard, task)
        )
        return taskCard

    def showAdditionalInfo(self, infoBox, reorganizeButton):
        infoBox.setVisible(True)
        reorganizeButton.setVisible(True)
        infoBox.setFocus()

    def reorganizeTask(self, task, infoBox):

        additionalInfo = infoBox.toPlainText().strip()

        if not additionalInfo:
                return

        combinedText = (
            f"Original task: {task.title}\n"
            f"Existing description: {task.description}\n"
            f"Additional information: {additionalInfo}"
        )

        result = organizer.organizeWithLlm(combinedText)

        if not result.tasks:
            self.refreshViewPanel (
                result.message
                or "I couldn't create an improved task proposal."
            )
            return
        ingestion, newTasks = organizer.applyOrganizeResult(
            result,
            combinedText,
        )

        self.taskManager.addIngestion(ingestion)

        for newTask in newTasks:
            self.taskManager.addTask(newTask)

        self.taskManager.save()
        self.displayTasks(newTasks)

    def rejectTask(self, taskCard, task):

        self.pendingIngestions.pop(task.ingestionID, None)

        self.reviewLayout.removeWidget(taskCard)
        taskCard.deleteLater()

    def acceptTask(self, taskCard, task):
        ingestion = self.pendingIngestions.get(task.ingestionID)


        if ingestion is not None:
            self.taskManager.addIngestion(ingestion)

        self.taskManager.addTask(task)
        self.taskManager.save()

        self.reviewLayout.removeWidget(taskCard)
        taskCard.deleteLater()
