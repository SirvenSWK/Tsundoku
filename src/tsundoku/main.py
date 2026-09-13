import sys

import tsundoku.ui.mainWindow as mainWindow
from PySide6.QtWidgets import QApplication


def runApp():
    app = QApplication(sys.argv)

    window = mainWindow.MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    runApp()
