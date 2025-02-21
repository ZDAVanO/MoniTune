from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSlider
from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
import random

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(600, 450)
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)  # Make it a regular window with minimize and maximize buttons

        layout = QVBoxLayout()
        # self.label = QLabel("Another Window % d" % randint(0, 100))
        # layout.addWidget(self.label)

        self.tab_widget = QTabWidget()
        # for i in range(1, 6):
        #     tab = QWidget()
        #     tab_layout = QVBoxLayout()
        #     tab_layout.addWidget(QLabel(f"Content for Tab {i}"))
        #     tab.setLayout(tab_layout)
        #     self.tab_widget.addTab(tab, f"Tab {i}")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # self.close()

    def showEvent(self, event):
        print("Settings window is now visible")
        self.updateLayout()
        super().showEvent(event)

    def updateLayout(self):
        # Clear old widgets
        print("removed tabs:", self.tab_widget.count())
        while self.tab_widget.count():
            self.tab_widget.removeTab(0)

        # Add new tabs
        num_tabs = random.randint(1, 5)
        for i in range(num_tabs):
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.addWidget(QLabel(f"Content for Tab {i}"))

            # Add four sliders to each tab
            for _ in range(4):
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(0, 100)
                slider.setValue(random.randint(0, 100))
                tab_layout.addWidget(slider)

            tab.setLayout(tab_layout)
            self.tab_widget.addTab(tab, f"Tab {i}")
