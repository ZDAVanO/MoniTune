from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
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

# from monitor_utils import get_monitors_info

edge_padding = 11











class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Custom Title Bar")
        self.resize(358, 231)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)

        # This container holds the window contents, so we can style it.
        central_widget = QWidget()
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """
            #Container {
            background: #202020;
            border-radius: 9px;
            border: 1px solid #303030;
            }
            """
        )
        

        self.settings_window = None  # No settings window yet


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
        central_widget_layout.addStretch()  # Add stretch to push the bottom frame to the bottom
        central_widget_layout.addWidget(self.bottom_frame)

        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)

        self.createTrayIcon()
        # self.updateFrameContents()

        self.bottom_frame.installEventFilter(self)


    def createTrayIcon(self):
        self.tray_icon = SystemTrayIcon(self)



    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        # hide window when focus is lost
        if event.type() == QEvent.Type.WindowDeactivate:
            # if source is self:
            self.hide()
        
        # Handle scroll events on the bottom frame
        if source == self.bottom_frame and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta > 0:
                print("scroll up")
            else:
                print("scroll down")
        
        return super().eventFilter(source, event)




    def updateFrameContents(self):
        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                # print("child.widget().deleteLater()")
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

        print("updateFrameContents sizeHint:", self.sizeHint().height())
        
        


    def showEvent(self, event):
        print("showEvent")

        # monitors_info = get_monitors_info()
        # print("monitors_info", monitors_info)

        # self.adjustWindowPosition()

        self.updateFrameContents()  # Update frame contents each time the window is shown
        
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()

        self.move(screen_geometry.width(), screen_geometry.height())
        # self.animateWindowOpen()
        QTimer.singleShot(0, self.animateWindowOpen)

        # QTimer.singleShot(0, self.updateSizeAndPosition)

        # window_height = self.sizeHint().height()  # Use sizeHint().height() instead of self.height()
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - window_height - edge_padding)
        
        print("self.width()", self.width(), "self.height()", self.height())
        print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding)
        

        self.activateWindow()
        self.raise_()
        

        super().showEvent(event)
        
        print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())







    def updateSizeAndPosition(self):
        print("updateSizeAndPosition sizeHint:", self.sizeHint().height(), "self.height()", self.height())
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding)
        self.resize(self.width(), self.sizeHint().height())


    # def adjustWindowPosition(self):
    #     # screen_geometry = QGuiApplication.primaryScreen().geometry()
    #     screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
    #     self.move(screen_geometry.width() - self.width(), screen_geometry.height() - self.height())

    def animateWindowOpen(self):
        # screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        # start_rect = QRect(screen_geometry.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        # end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        start_rect = QRect(screen_geometry.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        
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
        if self.settings_window is None:
            self.settings_window = SettingsWindow()
        if self.settings_window.isMinimized():
            self.settings_window.showNormal()
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()




if __name__ == "__main__":
    app = QApplication([])

    # print(QStyleFactory.keys())
    # app.setStyle("windows11")

    window = MainWindow()
    window.show()
    app.exec()