import tsundoku.ui.mainWindow as mainWindow
import PySide6.QtWidgets as QtWidget

class CalendarPage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidget.QVBoxLayout()

        layout.addWidget(QtWidget.QLabel("CALENDAR INTEGRATION HERE COMING SOON!"))

        self.setLayout(layout)