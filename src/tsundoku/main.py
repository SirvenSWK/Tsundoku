import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
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


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        self.inputBox = QPlainTextEdit()
        self.inputBox.setPlaceholderText(
            "Hello user, tell me what's up?"
        )

        self.organizeButton = QPushButton("Organize")

        layout = QVBoxLayout()
        layout.addWidget(self.inputBox)
        layout.addWidget(self.organizeButton)

        self.setLayout(layout)


class CalendarPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QPushButton("Calendar goes here"))

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tsundoku")
        self.resize(900, 600)

        # Pages
        self.pages = QStackedWidget()

        self.homePage = HomePage()
        self.calendarPage = CalendarPage()

        self.pages.addWidget(self.homePage)
        self.pages.addWidget(self.calendarPage)

        # Navigation
        self.homeBtn = QPushButton("Home")
        self.calendarBtn = QPushButton("Calendar")

        self.homeBtn.clicked.connect(self.changeToHome)
        self.calendarBtn.clicked.connect(self.changeToCalendar)

        navLayout = QHBoxLayout()
        navLayout.addWidget(self.homeBtn)
        navLayout.addWidget(self.calendarBtn)

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(navLayout)
        mainLayout.addWidget(self.pages)

        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)

        self.setCentralWidget(centralWidget)

    def changeToHome(self):
        self.pages.setCurrentIndex(0)

    def changeToCalendar(self):
        self.pages.setCurrentIndex(1)


task = Task(
    id=uuid4(),
    title="Sample Task",
    description="This is a sample task.",
    deadline=datetime.now() + timedelta(days=1),
    duration=timedelta(hours=2),
    priority="High",
    completed=False,
)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()