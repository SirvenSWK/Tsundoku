import sys

from PySide6.QtWidgets import QApplication
from tsundoku.ui.openingWindow import OpeningWindow


def runApp():
    app = QApplication(sys.argv)
    app.setApplicationName("Tsundoku")

    openingWindow = OpeningWindow()
    mainWindow = None

    def openHome():
        nonlocal mainWindow
        from tsundoku.ui.mainWindow import MainWindow

        mainWindow = MainWindow()
        openingWindow.finishLoading()

    def revealHome():
        if mainWindow is not None:
            mainWindow.show()
            openingWindow.close()

    openingWindow.readyToLoad.connect(openHome)
    openingWindow.dismissed.connect(revealHome)
    openingWindow.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    runApp()
