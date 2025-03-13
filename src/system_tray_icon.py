from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict
import config
from config import tray_icons

import darkdetect






class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)

        icon = reg_read_list(config.REGISTRY_PATH, "TrayIcon")
        self.icon_name = icon[0] if icon else "monitune"
        
        
        self.icon_theme = darkdetect.theme()


        # self.setIcon(QIcon(config.app_icon_path))
        self.changeIcon(tray_icons[self.icon_name][self.icon_theme])
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
        
    def changeIcon(self, icon_path):
        self.setIcon(QIcon(icon_path))

    def changeIconName(self, icon_name):
        if icon_name in tray_icons:
            self.icon_name = icon_name
            icon_path = tray_icons[icon_name][self.icon_theme]
            self.changeIcon(icon_path)
        else:
            print("Invalid icon name. Please choose 'monitune', 'mdl2', or 'fluent'.")

    def changeIconTheme(self, theme):
        if theme in ["Light", "Dark"]:
            self.icon_theme = theme
            icon_path = tray_icons[self.icon_name][theme]
            self.changeIcon(icon_path)
        else:
            print("Invalid theme. Please choose 'Light' or 'Dark'.")

    

    def on_message_click(self):
        print("on_message_click")

