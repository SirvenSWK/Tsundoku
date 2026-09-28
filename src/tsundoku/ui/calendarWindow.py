import PySide6.QtWidgets as QtWidget
from PySide6.QtCore import QDate
from PySide6.QtGui import QTextCharFormat

from tsundoku.tools import googleCalendar
from tsundoku.tools.taskManager import taskManager


class CalendarPage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.taskManager = taskManager
        self.calendar = QtWidget.QCalendarWidget()
        self.markedDates = set()
        self.calendar.selectionChanged.connect(self.dateSelected)
        self.selectedDateLabel = QtWidget.QLabel()
        self.itemsLayout = QtWidget.QVBoxLayout()
        self.statusLabel = QtWidget.QLabel()

        layout = QtWidget.QVBoxLayout()
        layout.addWidget(self.calendar)
        layout.addWidget(self.selectedDateLabel)
        layout.addLayout(self.itemsLayout)
        layout.addWidget(self.statusLabel)
        layout.addStretch()
        self.setLayout(layout)
        self.refreshCalendar()

    def refreshCalendar(self):
        self.markItemDates()
        self.dateSelected()

    def dateSelected(self):
        selectedDate = self.calendar.selectedDate()
        selectedDateText = selectedDate.toString("yyyy-MM-dd")
        self.selectedDateLabel.setText(f"Selected date: {selectedDateText}")
        self.statusLabel.clear()
        self._clearItems()

        items = []
        items.extend(
            (task.scheduledStart, task, "task")
            for task in self.taskManager.getTasks()
            if task.scheduledStart is not None
            and task.scheduledStart.strftime("%Y-%m-%d") == selectedDateText
        )
        items.extend(
            (event.scheduledStart, event, "event")
            for event in self.taskManager.getEvents()
            if event.scheduledStart is not None
            and event.scheduledStart.strftime("%Y-%m-%d") == selectedDateText
        )
        items.sort(key=lambda item: (item[0].hour, item[0].minute, item[2]))

        if not items:
            self.itemsLayout.addWidget(QtWidget.QLabel("No tasks or events"))
            return

        for start, item, itemType in items:
            row = QtWidget.QHBoxLayout()
            timeText = "All day" if item.isAllDay else start.strftime("%H:%M")
            kindText = "Event" if itemType == "event" else "Task"
            row.addWidget(QtWidget.QLabel(f"{timeText} · {kindText}: {item.title}"))
            importedFromGoogle = bool(getattr(item, "sourceGoogleEventID", None))
            exportButton = QtWidget.QPushButton(
                "Imported from Google" if importedFromGoogle else
                "Update Google Calendar" if item.googleEventID else "Add to Google Calendar"
            )
            exportButton.setEnabled(not importedFromGoogle)
            exportButton.clicked.connect(
                lambda _, item=item, itemType=itemType: self.exportItem(item, itemType)
            )
            row.addWidget(exportButton)
            deleteButton = QtWidget.QPushButton("Delete")
            deleteButton.clicked.connect(
                lambda _, item=item, itemType=itemType: self.deleteItem(item, itemType)
            )
            row.addWidget(deleteButton)
            self.itemsLayout.addLayout(row)

    def _clearItems(self):
        while self.itemsLayout.count():
            item = self.itemsLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                childLayout = item.layout()
                while childLayout.count():
                    child = childLayout.takeAt(0)
                    if child.widget() is not None:
                        child.widget().deleteLater()

    def exportItem(self, item, itemType):
        try:
            if itemType == "event":
                googleCalendar.sync_event(item)
            else:
                googleCalendar.sync_task(item)
            self.taskManager.save()
            self.dateSelected()
            self.statusLabel.setText("Added to Google Calendar.")
        except googleCalendar.GoogleCalendarError as error:
            self.statusLabel.setText(str(error))
        except Exception as error:
            self.statusLabel.setText(f"Couldn't save the Google Calendar update: {error}")

    def deleteItem(self, item, itemType):
        itemName = "task" if itemType == "task" else "event"
        message = f'Delete this {itemName} from Tsundoku? This removes it from this device.'
        if getattr(item, "sourceGoogleEventID", None):
            message += " It remains in Google Calendar and may be imported again later."
        elif item.googleEventID:
            message += " Its Google Calendar copy will remain."
        answer = QtWidget.QMessageBox.question(
            self,
            f"Delete {itemName}",
            message,
            QtWidget.QMessageBox.StandardButton.Yes | QtWidget.QMessageBox.StandardButton.No,
            QtWidget.QMessageBox.StandardButton.No,
        )
        if answer != QtWidget.QMessageBox.StandardButton.Yes:
            return
        try:
            if itemType == "task":
                self.taskManager.removeTask(item)
            else:
                self.taskManager.removeEvent(item)
            self.taskManager.save()
        except Exception as error:
            collection = self.taskManager.getTasks() if itemType == "task" else self.taskManager.getEvents()
            if item not in collection:
                if itemType == "task":
                    self.taskManager.addTask(item)
                else:
                    self.taskManager.addEvent(item)
            self.statusLabel.setText(f"Couldn't delete the {itemName}: {error}")
            return
        self.refreshCalendar()
        self.statusLabel.setText(f"{itemName.capitalize()} deleted from Tsundoku.")

    def markItemDates(self):
        for markedDate in self.markedDates:
            self.calendar.setDateTextFormat(markedDate, QTextCharFormat())
        self.markedDates.clear()
        for item in (*self.taskManager.getTasks(), *self.taskManager.getEvents()):
            if item.scheduledStart is None:
                continue
            dateFormat = QTextCharFormat()
            dateFormat.setFontWeight(1000)
            itemDate = item.scheduledStart.date()
            qtDate = QDate(itemDate.year, itemDate.month, itemDate.day)
            self.calendar.setDateTextFormat(qtDate, dateFormat)
            self.markedDates.add(qtDate)
