import PySide6.QtWidgets as QtWidget

from tsundoku.models import settings
from tsundoku.tools import googleCalendar


class settingsPage(QtWidget.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidget.QVBoxLayout()

        layout.addWidget(QtWidget.QLabel("AI organizer"))
        self.apiStatus = QtWidget.QLabel()
        self.apiStatus.setWordWrap(True)
        self.refreshAiStatus()
        layout.addWidget(self.apiStatus)

        layout.addSpacing(24)
        layout.addWidget(QtWidget.QLabel("Google Calendar"))
        self.calendarNote = QtWidget.QLabel()
        self.calendarNote.setWordWrap(True)
        self.googleStatus = QtWidget.QLabel()
        self.connectButton = QtWidget.QPushButton("Connect Google Calendar")
        self.disconnectButton = QtWidget.QPushButton("Disconnect")
        self.connectButton.clicked.connect(self.connectGoogleCalendar)
        self.disconnectButton.clicked.connect(self.disconnectGoogleCalendar)
        layout.addWidget(self.googleStatus)
        layout.addWidget(self.calendarNote)
        layout.addWidget(self.connectButton)
        layout.addWidget(self.disconnectButton)
        layout.addStretch()
        self.setLayout(layout)
        self.refreshGoogleStatus()

    def refreshAiStatus(self):
        if settings.loadAiProxyUrl():
            self.apiStatus.setText(
                "Demo organizer is ready. Usage limits are applied automatically."
            )
        elif settings.loadApi():
            self.apiStatus.setText(
                "A local development key is configured. Shared demos should use the limited Vercel proxy."
            )
        else:
            self.apiStatus.setText(
                "AI demo setup is not finished yet. The app maintainer needs to configure the Vercel proxy."
            )

    def refreshGoogleStatus(self):
        connected = googleCalendar.is_connected()
        configured = googleCalendar.has_client_credentials()
        self.googleStatus.setText(
            "Connected · Tsundoku calendar is ready" if connected else "Google Calendar is not connected"
        )
        if not configured:
            self.calendarNote.setText(
                "Google Calendar isn't configured in this build yet. Ask the app maintainer to finish setup."
            )
        elif connected:
            self.calendarNote.setText(
                "Your visible Google Calendar events are available in Tsundoku. "
                "Reconnect to import newly added events. Tsundoku exports go to your separate Tsundoku calendar."
            )
            self.connectButton.setText("Reconnect and refresh")
        else:
            self.calendarNote.setText(
                "Connect once to import visible calendar events and create a separate Tsundoku calendar. "
                "Your calendar data stays on this device."
            )
            self.connectButton.setText("Connect Google Calendar")
        self.disconnectButton.setEnabled(connected)

    def connectGoogleCalendar(self):
        self.connectButton.setEnabled(False)
        self.googleStatus.setText("Opening Google sign-in…")
        imported = None
        try:
            imported = googleCalendar.connect()
        except googleCalendar.GoogleCalendarError as error:
            QtWidget.QMessageBox.warning(self, "Google Calendar", str(error))
        finally:
            self.refreshGoogleStatus()
            if imported is not None:
                self.googleStatus.setText("Connected to Google Calendar.")
                self.calendarNote.setText(
                    f"Setup complete. Imported {imported} existing event occurrences. "
                    "New Tsundoku exports go into your separate Tsundoku calendar."
                )
            self.connectButton.setEnabled(True)

    def disconnectGoogleCalendar(self):
        googleCalendar.disconnect()
        self.refreshGoogleStatus()
