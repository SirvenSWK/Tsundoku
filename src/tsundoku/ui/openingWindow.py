from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QPoint,
    Qt,
    Signal,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QMainWindow, QWidget


class OpeningWindow(QMainWindow):
    """Bear rises into view, waits for startup, then drops away."""

    readyToLoad = Signal()
    dismissed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tsundoku")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(650, 750)
        canvas = QWidget()
        canvas.setStyleSheet("background: #f5f3ef;")
        self.setCentralWidget(canvas)

        self.bear = QLabel("🐻", canvas)
        self.bear.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bear.setFont(QFont("Segoe UI Emoji", 92))
        self.bear.setStyleSheet("background: transparent; border: none;")
        self.bear.resize(140, 140)

        x = (self.width() - self.bear.width()) // 2
        self.restPosition = QPoint(x, (self.height() - self.bear.height()) // 2)
        self.bear.move(x, self.height() + 20)

        self.popAnimation = QPropertyAnimation(self.bear, b"pos", self)
        self.popAnimation.setStartValue(QPoint(x, self.height() + 20))
        self.popAnimation.setEndValue(self.restPosition)
        self.popAnimation.setDuration(720)
        self.popAnimation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.popAnimation.finished.connect(self._afterPop)

        self.dropAnimation = QPropertyAnimation(self.bear, b"pos", self)
        self.dropAnimation.setEndValue(QPoint(x, self.height() + 30))
        self.dropAnimation.setDuration(560)
        self.dropAnimation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.dropAnimation.finished.connect(self.dismissed)

        self.loadingFinished = False
        self.dropStarted = False
        self._centerOnScreen()
        self.popAnimation.start()

    def finishLoading(self):
        self.loadingFinished = True
        if self.popAnimation.state() == QAbstractAnimation.State.Stopped:
            self._startDrop()

    def _afterPop(self):
        self.readyToLoad.emit()
        if self.loadingFinished:
            self._startDrop()

    def _startDrop(self):
        if self.dropStarted:
            return
        self.dropStarted = True
        self.dropAnimation.setStartValue(self.bear.pos())
        self.dropAnimation.start()

    def _centerOnScreen(self):
        screen = self.screen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2,
        )
