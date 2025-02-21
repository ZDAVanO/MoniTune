import random  # Add this import
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
    QStyleFactory,
    QTabWidget,  # Add these imports
    QPushButton,
    QDialog,
)
from system_tray_icon import SystemTrayIcon  # Add this import
from random import randint  # Add this import

edge_padding = 11





class AnotherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(600, 450)
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)  # Make it a regular window with minimize and maximize buttons

        layout = QVBoxLayout()
        # self.label = QLabel("Another Window % d" % randint(0, 100))
        # layout.addWidget(self.label)

        self.tab_widget = QTabWidget()
        for i in range(1, 6):
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.addWidget(QLabel(f"Content for Tab {i}"))
            tab.setLayout(tab_layout)
            self.tab_widget.addTab(tab, f"Tab {i}")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)









class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.w = None  # No external window yet.

        self.setWindowTitle("Custom Title Bar")
        self.resize(358, 231)

        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)
        central_widget = QWidget()
        # This container holds the window contents, so we can style it.
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """#Container {
            background: #202020;
            border-radius: 9px;
            border: 1px solid #303030;
        }"""
        )

        work_space_layout = QVBoxLayout()
        work_space_layout.setContentsMargins(11, 11, 11, 11)

        self.slider_frame = QWidget()
        self.slider_frame.setStyleSheet("background-color: red;")  # Set background color to red
        self.slider_layout = QVBoxLayout()
        self.slider_frame.setLayout(self.slider_layout)
        work_space_layout.addWidget(self.slider_frame)

        work_space_layout.addStretch()  # Add stretch to push "Hello, World!" to the bottom
        work_space_layout.addWidget(QLabel("Hello, World!", self))

        self.settings_button = QPushButton("Settings", self)
        self.settings_button.clicked.connect(self.openSettingsWindow)
        work_space_layout.addWidget(self.settings_button)

        self.work_space_layout = work_space_layout  # Save the layout as an instance variable

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
        # print("eventFilter source", source, "event", event.type())

        if event.type() == QEvent.Type.WindowDeactivate:
            self.hide()

        return super().eventFilter(source, event)

    def updateFrameContents(self):
        # Clear old widgets
        while self.slider_layout.count():
            child = self.slider_layout.takeAt(0)
            if child.widget():
                print("child.widget().deleteLater()")
                child.widget().deleteLater()

        # Add new random number of sliders
        num_sliders = random.randint(1, 5)
        print("num_sliders", num_sliders)
        for _ in range(num_sliders):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(random.randint(0, 100))
            self.slider_layout.addWidget(slider)

    def showEvent(self, event):
        print("showEvent")

        # self.adjustWindowPosition()

        self.updateFrameContents()  # Update frame contents each time the window is shown
        self.animateWindowOpen()
        self.activateWindow()
        self.raise_()
        super().showEvent(event)

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
            self.w = AnotherWindow()
        self.w.show()
        # self.settings_window = AnotherWindow()
        # self.settings_window.show()




if __name__ == "__main__":
    app = QApplication([])

    # print(QStyleFactory.keys())
    # app.setStyle("windows11")

    window = MainWindow()
    window.show()
    app.exec()