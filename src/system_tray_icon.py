from PySide6.QtGui import QIcon, QPixmap, QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

import config

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(config.app_icon_path))
        self.setToolTip(f"{config.app_name} v{config.version}")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(parent.show)
        
        settings_action = tray_menu.addAction("Settings")  # Add this action
        settings_action.triggered.connect(parent.openSettingsWindow)  # Connect to openSettingsWindow method
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QGuiApplication.quit)

        self.setContextMenu(tray_menu)
        self.activated.connect(self.trayIconClicked)
        self.show()

    def trayIconClicked(self, reason):
        # print("trayIconClicked reason:", reason)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent().show()

