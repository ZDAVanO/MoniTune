from PyQt6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QMenu,
    QSlider,
    QGraphicsOpacityEffect,  # Add this import
)
from system_tray_icon import SystemTrayIcon  # Add this import


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Title Bar")
        self.resize(400, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)
        central_widget = QWidget()
        # This container holds the window contents, so we can style it.
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """#Container {
            background: #202020;
            border-radius: 9px;
        }"""
        )

        work_space_layout = QVBoxLayout()
        work_space_layout.setContentsMargins(11, 11, 11, 11)
        work_space_layout.addWidget(QLabel("Hello, World!", self))

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)

        work_space_layout.addWidget(slider)

        centra_widget_layout = QVBoxLayout()
        centra_widget_layout.setContentsMargins(0, 0, 0, 0)
        centra_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        centra_widget_layout.addLayout(work_space_layout)

        central_widget.setLayout(centra_widget_layout)
        self.setCentralWidget(central_widget)

        self.createTrayIcon()



    def createTrayIcon(self):
        self.tray_icon = SystemTrayIcon(self)

    # def onTrayIconActivated(self, reason):
    #     if reason == QSystemTrayIcon.ActivationReason.Trigger:
    #         self.show()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.WindowDeactivate:
            self.hide()
        return super().eventFilter(source, event)

    def showEvent(self, event):
        print("showEvent")

        self.adjustWindowPosition()

        self.animateWindowIn()
        self.activateWindow()
        self.raise_()
        super().showEvent(event)

    def adjustWindowPosition(self):
        # screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width(), screen_geometry.height() - self.height())

    def animateWindowIn(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.height(), self.width(), self.height())
        end_rect = QRect(screen_geometry.width() - self.width(), screen_geometry.height() - self.height(), self.width(), self.height())
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        
        self.animation.start()
        self.opacity_animation.start()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()