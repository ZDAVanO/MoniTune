from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

import config

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(config.app_icon_path))
        self.setToolTip(f"{config.app_name} v{config.version}")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Quick Access \tLeft-click")
        show_action.triggered.connect(parent.show)
        
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(parent.openSettingsWindow)  # Connect to openSettingsWindow method
        
        tray_menu.addSeparator()  # Add separator before Exit action
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QGuiApplication.quit)

        self.setContextMenu(tray_menu)
        self.activated.connect(self.trayIconClicked)
        self.messageClicked.connect(self.on_message_click)
        self.show()
        # self.showMessage("MoniTune", "MoniTune is running in the background.", QIcon(config.app_icon_path))

    def trayIconClicked(self, reason):
        # print("trayIconClicked reason:", reason)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent().show()
        # elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        #     self.parent().openSettingsWindow()  # Trigger Settings on double-click

    def show_notification(self, title, message, icon):
        self.showMessage(title, message, icon)
        

    def on_message_click(self):
        print("on_message_click")

