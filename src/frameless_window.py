from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
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
    QGraphicsOpacityEffect,
    QStyleFactory,
    QTabWidget,  # Add these imports
    QPushButton,
    QDialog,
    QFrame,
)

from system_tray_icon import SystemTrayIcon
from settings_window import SettingsWindow 

import random


edge_padding = 11











class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.w = None  # No external window yet.

        self.setWindowTitle("Custom Title Bar")
        self.resize(358, 231)

        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # print("Qt.FramelessWindowHint", Qt.WindowType.FramelessWindowHint)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)

        # This container holds the window contents, so we can style it.
        central_widget = QWidget()
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """#Container {
            background: #202020;
            border-radius: 9px;
            border: 1px solid #303030;
        }"""
        )

        self.monitors_frame = QWidget()
        self.monitors_frame.setStyleSheet("background-color: red;")  # Set background color to red
        self.monitors_layout = QVBoxLayout()
        self.monitors_frame.setLayout(self.monitors_layout)

        self.bottom_frame = QFrame()
        self.bottom_frame.setStyleSheet("background-color: green;")  # Set background color to green
        self.bottom_hbox = QHBoxLayout(self.bottom_frame)
        name_title = QLabel("Scroll to adjust brightness")
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.openSettingsWindow)
        self.bottom_hbox.addWidget(name_title)
        self.bottom_hbox.addWidget(settings_button)
        self.bottom_frame.setLayout(self.bottom_hbox)

        central_widget_layout = QVBoxLayout()
        central_widget_layout.setContentsMargins(11, 11, 11, 11)
        central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget_layout.addWidget(self.monitors_frame)
        central_widget_layout.addWidget(self.bottom_frame)

        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)

        self.createTrayIcon()

    def createTrayIcon(self):
        self.tray_icon = SystemTrayIcon(self)

    # def onTrayIconActivated(self, reason):
    #     if reason == QSystemTrayIcon.ActivationReason.Trigger:
    #         self.show()

    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        if event.type() == QEvent.Type.WindowDeactivate:
            if source is self:
                self.hide()

        return super().eventFilter(source, event)

    def updateFrameContents(self):
        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                print("child.widget().deleteLater()")
                child.widget().deleteLater()

        # Add new random number of sliders
        num_sliders = random.randint(1, 10)
        # num_sliders = 10

        print("num_sliders", num_sliders)
        for _ in range(num_sliders):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(random.randint(0, 100))
            self.monitors_layout.addWidget(slider)

        
        


    def showEvent(self, event):
        print("showEvent")
        

        # self.adjustWindowPosition()

        self.updateFrameContents()  # Update frame contents each time the window is shown

        self.animateWindowOpen()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        # window_height = self.sizeHint().height()  # Use sizeHint().height() instead of self.height()
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - window_height - edge_padding)
        
        print("self.width()", self.width(), "self.height()", self.height())
        print("sizeHint:", self.sizeHint().height())
        self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding)


        self.activateWindow()
        self.raise_()

        super().showEvent(event)
        
        print("sizeHint:", self.sizeHint().height())


    


    # def adjustWindowPosition(self):
    #     # screen_geometry = QGuiApplication.primaryScreen().geometry()
    #     screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
    #     self.move(screen_geometry.width() - self.width(), screen_geometry.height() - self.height())

    def animateWindowOpen(self):
        # screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        start_rect = QRect(screen_geometry.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(350)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(350)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        
        self.animation.start()
        self.opacity_animation.start()

    def openSettingsWindow(self):
        if self.w is None:
            self.w = SettingsWindow()
        if self.w.isMinimized():
            self.w.showNormal()
        self.w.show()
        self.w.activateWindow()
        self.w.raise_()




if __name__ == "__main__":
    app = QApplication([])

    # print(QStyleFactory.keys())
    # app.setStyle("windows11")

    window = MainWindow()
    window.show()
    app.exec()