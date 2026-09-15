import PySide6.QtWidgets as QtWidget

from tsundoku.models import settings


class settingsPage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        self.apiLabel = QtWidget.QLabel("Groq API key: ")
        self.apiText = QtWidget.QLineEdit()
        self.saveButton = QtWidget.QPushButton("Save")



        self.apiText.setEchoMode(QtWidget.QLineEdit.EchoMode.Password)

        layout = QtWidget.QHBoxLayout()

        layout.addWidget(self.apiLabel)
        layout.addWidget(self.apiText)
        layout.addWidget(self.saveButton)

        self.setLayout(layout)

        self.saveButton.clicked.connect(self.saveSettings)

        existingApiKey = settings.loadApi()

        if existingApiKey:
            self.apiText.setText("Api key detected")
        

    def saveSettings(self):
        apiKey = self.apiText.text().strip()
        settings.saveApiKey(apiKey)