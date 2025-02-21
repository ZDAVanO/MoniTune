from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(QPixmap(16, 16)))  # Set your icon here
        self.setToolTip("MoniTune")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(parent.show)
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QGuiApplication.quit)

        self.setContextMenu(tray_menu)
        self.activated.connect(self.trayIconClicked)
        self.show()

    def trayIconClicked(self, reason):
        print("trayIconClicked reason:", reason)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent().show()

