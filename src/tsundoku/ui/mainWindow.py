import tsundoku.ui.homeWindow as homeWindow
import tsundoku.ui.calendarWindow as calendarWindow
import tsundoku.ui.settingsWindow as settingsWindow

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
        self.resize(650, 750)

        # Navigation between pages
        self.pages = QStackedWidget()

        self.homePage = homeWindow.HomePage()
        self.calendarPage = calendarWindow.CalendarPage()
        self.settingsPage = settingsWindow.settingsPage()

        self.pages.addWidget(self.homePage)
        self.pages.addWidget(self.calendarPage)
        self.pages.addWidget(self.settingsPage)

        # Navigation
        self.homeBtn = QPushButton("Home")
        self.calendarBtn = QPushButton("Calendar")
        self.settingsBtn = QPushButton("Settings")

        self.homeBtn.clicked.connect(self.changeToHome)
        self.calendarBtn.clicked.connect(self.changeToCalendar)
        self.settingsBtn.clicked.connect(self.changeToSettings)

        navLayout = QHBoxLayout()
        navLayout.addWidget(self.homeBtn)
        navLayout.addWidget(self.calendarBtn)
        navLayout.addWidget(self.settingsBtn)

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
    def changeToSettings(self):
        self.pages.setCurrentIndex(2)
