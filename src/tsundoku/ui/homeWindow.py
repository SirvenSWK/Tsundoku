from tsundoku.tools import organizer
from tsundoku.tools import googleCalendar
from tsundoku.tools.taskManager import taskManager
from tsundoku.models import settings
import PySide6.QtWidgets as QtWidget


class HomePage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.pendingIngestions = {}
        self.taskManager = taskManager
        self.taskManager.load()
        self.setupNotice = QtWidget.QLabel()
        self.setupNotice.setWordWrap(True)
        self.inputBox = QtWidget.QPlainTextEdit()
        self.reviewPanel = QtWidget.QFrame()
        self.reviewLayout = QtWidget.QVBoxLayout()
        self.reviewPanel.setLayout(self.reviewLayout)

        self.organizeButton = QtWidget.QPushButton("Organize")
        self.organizeButton.clicked.connect(self.organize)

        layout = QtWidget.QVBoxLayout()
        layout.addWidget(self.setupNotice)
        layout.addWidget(self.inputBox)
        layout.addWidget(self.organizeButton)
        layout.addWidget(self.reviewPanel)
        self.setLayout(layout)
        self.refreshSetupPrompt()

    def refreshSetupPrompt(self):
        missing = []
        if not settings.hasAiAccess():
            missing.append("finish the AI demo setup")
        if not googleCalendar.is_connected():
            missing.append("log into Google Calendar in Settings")

        if missing:
            message = "Before organizing tasks, " + " and ".join(missing) + "."
            self.setupNotice.setText(message)
            self.inputBox.setPlaceholderText(message)
        else:
            self.setupNotice.clear()
            self.inputBox.setPlaceholderText("Tell Tsundoku what's on your mind…")

    def refreshViewPanel(self, message: str = "Nothing organized yet!"):
        self.clearReviewPanel()
        self.reviewLayout.addWidget(QtWidget.QLabel(message))

    def organize(self):
        text = self.inputBox.toPlainText().strip()
        if not text:
            return

        result = organizer.organizeWithLlm(text)
        if not result.tasks and not result.events:
            self.refreshViewPanel(result.message or "I couldn't find an actionable task or event.")
            return

        ingestion, events, tasks = organizer.applyOrganizeResult(result, text)
        self.pendingIngestions[ingestion.id] = ingestion
        self.displayEventsAndTasks(events, tasks)
        self.inputBox.clear()

    def displayEventsAndTasks(self, events, tasks):
        self.clearReviewPanel()
        if not events and not tasks:
            self.reviewLayout.addWidget(QtWidget.QLabel("I couldn't find an actionable task or event."))
            return

        for event in events:
            eventCard = QtWidget.QFrame()
            eventCard.setFrameShape(QtWidget.QFrame.Shape.StyledPanel)
            eventLayout = QtWidget.QVBoxLayout(eventCard)
            titleLabel = QtWidget.QLabel(f"Event: {event.title}")
            titleLabel.setStyleSheet("font-size: 18px; font-weight: bold;")
            eventLayout.addWidget(titleLabel)

            if event.description:
                descriptionLabel = QtWidget.QLabel(event.description)
                descriptionLabel.setWordWrap(True)
                eventLayout.addWidget(descriptionLabel)
            if event.scheduledStart is not None:
                dateFormat = "%Y-%m-%d" if event.isAllDay else "%Y-%m-%d %H:%M"
                eventLayout.addWidget(QtWidget.QLabel(event.scheduledStart.strftime(dateFormat)))

            relatedTasks = [task for task in tasks if task.eventID == event.id]
            if relatedTasks:
                eventLayout.addWidget(QtWidget.QLabel("Preparation tasks:"))
                for task in relatedTasks:
                    eventLayout.addWidget(QtWidget.QLabel(f"• {task.title}"))

            buttonLayout = QtWidget.QHBoxLayout()
            acceptButton = QtWidget.QPushButton("Accept")
            rejectButton = QtWidget.QPushButton("Reject")
            buttonLayout.addWidget(acceptButton)
            buttonLayout.addWidget(rejectButton)
            eventLayout.addLayout(buttonLayout)
            acceptButton.clicked.connect(
                lambda _, event=event, relatedTasks=relatedTasks, card=eventCard:
                    self.acceptEvent(event, relatedTasks, card)
            )
            rejectButton.clicked.connect(
                lambda _, event=event, card=eventCard: self.rejectProposal(event, card)
            )
            self.reviewLayout.addWidget(eventCard)

        for task in tasks:
            if task.eventID is None:
                self.reviewLayout.addWidget(self.addTaskCard(task))

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
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        taskLayout.addWidget(titleLabel)
        if task.description:
            descriptionLabel = QtWidget.QLabel(task.description)
            descriptionLabel.setWordWrap(True)
            taskLayout.addWidget(descriptionLabel)

        taskLayout.addWidget(QtWidget.QLabel(f"Priority {task.priority}"))
        scheduledText = (
            task.scheduledStart.strftime("%Y-%m-%d" if task.isAllDay else "%Y-%m-%d %H:%M")
            if task.scheduledStart is not None else "Starting time not specified"
        )
        taskLayout.addWidget(QtWidget.QLabel(scheduledText))

        buttonLayout = QtWidget.QHBoxLayout()
        acceptButton = QtWidget.QPushButton("Accept")
        rejectButton = QtWidget.QPushButton("Reject")
        addDetailButton = QtWidget.QPushButton("Add details")
        for button in (acceptButton, rejectButton, addDetailButton):
            buttonLayout.addWidget(button)
        taskLayout.addLayout(buttonLayout)

        additionalInfoBox = QtWidget.QPlainTextEdit()
        additionalInfoBox.setPlaceholderText(
            "Add details such as the date, topics, location, difficulty, or duration..."
        )
        additionalInfoBox.setVisible(False)
        reorganizeButton = QtWidget.QPushButton("Reorganize")
        reorganizeButton.setVisible(False)
        taskLayout.addWidget(additionalInfoBox)
        taskLayout.addWidget(reorganizeButton)

        addDetailButton.clicked.connect(
            lambda: self.showAdditionalInfo(additionalInfoBox, reorganizeButton)
        )
        reorganizeButton.clicked.connect(
            lambda: self.reorganizeTask(task, additionalInfoBox)
        )
        rejectButton.clicked.connect(lambda: self.rejectProposal(task, taskCard))
        acceptButton.clicked.connect(lambda: self.acceptTask(taskCard, task))
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
            f"Original task: {task.title}\nExisting description: {task.description}\n"
            f"Additional information: {additionalInfo}"
        )
        result = organizer.organizeWithLlm(combinedText)
        if not result.tasks and not result.events:
            self.refreshViewPanel(result.message or "I couldn't create an improved proposal.")
            return
        ingestion, events, tasks = organizer.applyOrganizeResult(result, combinedText)
        self.pendingIngestions[ingestion.id] = ingestion
        self.displayEventsAndTasks(events, tasks)

    def acceptEvent(self, event, tasks, eventCard):
        ingestion = self.pendingIngestions.get(event.ingestionID)
        if ingestion is not None:
            self.taskManager.addIngestion(ingestion)
        self.taskManager.addEvent(event)
        for task in tasks:
            self.taskManager.addTask(task)
        self.taskManager.save()
        self.removeProposalCard(eventCard)

    def acceptTask(self, taskCard, task):
        ingestion = self.pendingIngestions.get(task.ingestionID)
        if ingestion is not None:
            self.taskManager.addIngestion(ingestion)
        self.taskManager.addTask(task)
        self.taskManager.save()
        self.removeProposalCard(taskCard)

    def rejectProposal(self, proposal, card):
        self.removeProposalCard(card)

    def removeProposalCard(self, card):
        self.reviewLayout.removeWidget(card)
        card.deleteLater()
