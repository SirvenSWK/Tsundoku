import tsundoku.ui.homeWindow as homeWindow
import tsundoku.ui.calendarWindow as calendarWindow

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tsundoku")
        self.resize(900, 600)

        # Navigation between pages
        self.pages = QStackedWidget()

        self.homePage = homeWindow.HomePage()
        self.calendarPage = calendarWindow.CalendarPage()

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
