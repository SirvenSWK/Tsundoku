import PySide6.QtWidgets as QtWidget
from PySide6.QtGui import QTextCharFormat
from tsundoku.tools.taskManager import taskManager


class CalendarPage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()

        self.taskManager = taskManager

        self.calendar = QtWidget.QCalendarWidget()
        self.calendar.selectionChanged.connect(self.dateSelected)

        self.selectedDateLabel = QtWidget.QLabel()

        layout = QtWidget.QVBoxLayout()
        layout.addWidget(self.calendar)
        layout.addWidget(self.selectedDateLabel)

        self.setLayout(layout)

        self.dateSelected()
        self.markTaskDates()

    def dateSelected(self):
        selectedDate = self.calendar.selectedDate()
        selectedDateText = selectedDate.toString("yyyy-MM-dd")

        matchingTasks = []

        for task in self.taskManager.getTasks():
            if task.scheduledStart is None:
                continue

            taskDate = task.scheduledStart.strftime("%Y-%m-%d")

            if taskDate == selectedDateText:
                matchingTasks.append(task)

        if matchingTasks:
            taskLines = []

            for task in matchingTasks:
                if task.isAllDay:
                    taskLines.append(
                        f"All day - {task.title}"
                    )
                else:
                    taskLines.append(
                        f"{task.scheduledStart.strftime('%H:%M')} - {task.title}"
                    )

            taskText = "\n".join(taskLines)

            self.selectedDateLabel.setText(
                f"Selected date: {selectedDateText}\n\n{taskText}"
            )
        else:
            self.selectedDateLabel.setText(
                f"Selected date: {selectedDateText}\n\nNo tasks"
            )

    def markTaskDates(self):
        for task in self.taskManager.getTasks():
            if task.scheduledStart is None:
                continue

            date = task.scheduledStart.date()

            format = QTextCharFormat()
            format.setFontWeight(1000)

            self.calendar.setDateTextFormat(
                date,
                format
            )