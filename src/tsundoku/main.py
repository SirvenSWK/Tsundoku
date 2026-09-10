import sys
import tsundoku.models.tasks as tasks
import tsundoku.ui.mainWindow as mainWindow
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)

    window = mainWindow.MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()