from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from utils.reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict
import config as cfg
import resources_rc
from config import tray_icons

import darkdetect

import os

import logging
logger = logging.getLogger(__name__)



# MARK: SystemTrayIcon
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)

        icon = reg_read_list(cfg.REGISTRY_PATH, "TrayIcon")
        self.icon_name = icon[0] if icon else "monitune"
        logger.debug(f"icon_name: {self.icon_name}")
        
        self.icon_theme = darkdetect.theme()

        self.changeIcon(tray_icons[self.icon_name][self.icon_theme])
        self.setToolTip(f"{cfg.app_name} v{cfg.version}")

        self.tray_menu = QMenu()
        show_action = self.tray_menu.addAction("Quick Access \tLeft-click")
        show_action.triggered.connect(self.show_main_window)
        
        settings_action = self.tray_menu.addAction("Settings")
        settings_action.triggered.connect(parent.openSettingsWindow)  # Connect to openSettingsWindow method
        
        self.tray_menu.addSeparator()

        display_settings_action = self.tray_menu.addAction("Display Settings")  # New menu option
        display_settings_action.triggered.connect(self.open_display_settings)  # Connect to new method

        night_light_settings_action = self.tray_menu.addAction("Night Light Settings")  # New menu option
        night_light_settings_action.triggered.connect(self.open_night_light_settings)  # Connect to new method
        
        self.tray_menu.addSeparator()  # Add separator before Exit action
        
        exit_action = self.tray_menu.addAction("Exit")
        # exit_action.triggered.connect(QGuiApplication.quit)
        exit_action.triggered.connect(parent.on_exit)  # Connect to close method of parent window

        self.setContextMenu(self.tray_menu)
        self.activated.connect(self.trayIconClicked)
        self.show()

    # MARK: trayIconClicked()
    def trayIconClicked(self, reason):
        # print("trayIconClicked reason:", reason)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            logger.info("Tray icon clicked")
            self.show_main_window()
        # elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        #     self.parent().openSettingsWindow()  # Trigger Settings on double-click

    def show_main_window(self):
        # self.parent().show()
        self.parent().show_window()

    # MARK: show_notification()
    def show_notification(self, title, message, icon, on_click_callback=None):
        self.messageClicked.disconnect()  # Disconnect any previously connected signal
        if on_click_callback:
            self.messageClicked.connect(on_click_callback)  # Connect the new callback
        self.showMessage(title, message, icon)

    # MARK: changeIcon()  
    def changeIcon(self, icon_path):
        self.setIcon(QIcon(icon_path))

    # MARK: changeIconName()
    def changeIconName(self, icon_name):
        if icon_name in tray_icons:
            self.icon_name = icon_name
            icon_path = tray_icons[icon_name][self.icon_theme]
            self.changeIcon(icon_path)
        else:
            logger.warning(f"Invalid icon name: {icon_name}. Available options are: {list(tray_icons.keys())}")

    # MARK: changeIconTheme()
    def changeIconTheme(self, theme):
        if theme in ["Light", "Dark"]:
            self.icon_theme = theme
            icon_path = tray_icons[self.icon_name][theme]
            self.changeIcon(icon_path)
        else:
            logger.warning(f"Invalid theme: {theme}. Available options are: ['Light', 'Dark']")

    
    # MARK: open_display_settings()
    def open_display_settings(self):
        os.system(f"start {cfg.DISPLAY_SETTINGS_URL}")  # Opens Windows display settings

    # MARK: open_night_light_settings()
    def open_night_light_settings(self):
        os.system(f"start {cfg.NIGHT_LIGHT_SETTINGS_URL}")

