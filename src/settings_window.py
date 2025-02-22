from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSlider, QPushButton, QApplication, QMainWindow, QHBoxLayout, QComboBox, QFrame, QCheckBox, QScrollArea
from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
import random
import webbrowser

import config

from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict

class SettingsWindow(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        
        self.parent_window = parent_window

        self.setWindowTitle("Settings")
        self.resize(450, 400)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        settings_layout.addWidget(self.tab_widget)


        # Add button to show parent window
        self.show_parent_button = QPushButton("Show Parent Window")
        self.show_parent_button.clicked.connect(self.show_parent_window)
        settings_layout.addWidget(self.show_parent_button)

        # Add button to change parent window's test_var
        self.change_var_button = QPushButton("Change Parent Variable")
        self.change_var_button.clicked.connect(self.change_parent_var)
        settings_layout.addWidget(self.change_var_button)

        

    def closeEvent(self, event):
        print("Settings window closeEvent")
        event.ignore()
        self.hide()
        # self.close()

    def showEvent(self, event):
        print("Settings window showEvent")
        self.updateLayout()
        super().showEvent(event)

    def updateLayout(self):

        # Clear old widgets
        while self.tab_widget.count(): # num of tabs
            self.tab_widget.removeTab(0) # remove the first tab




        def toggle_setting(setting_name, reg_setting_name, bool, callback=None):
            print(f"Setting {setting_name} to {bool}")
            setattr(self.parent_window, setting_name, bool)
            reg_write_bool(config.REGISTRY_PATH, reg_setting_name, bool)
            if callable(callback):
                callback()
            # self.load_ui()

        def create_setting_checkbox(checkbox_label, 
                                    setting_name, 
                                    reg_setting_name, 
                                    callback=None,
                                    ):
            checkbox = QCheckBox(checkbox_label)
            var = getattr(self.parent_window, setting_name)
            checkbox.setChecked(var)
            checkbox.stateChanged.connect(lambda: toggle_setting(setting_name, 
                                                                 reg_setting_name, 
                                                                 checkbox.isChecked(), 
                                                                 callback,
                                                                 ))
            return checkbox

        
        # MARK: General Tab
        general_tab = QWidget()
        # general_tab.setStyleSheet("background-color: blue")
        general_layout = QVBoxLayout(general_tab)
        general_layout.setAlignment(Qt.AlignTop)
        general_layout.addWidget(create_setting_checkbox("Rounded Corners", 
                                                         "enable_rounded_corners", 
                                                         "EnableRoundedCorners",
                                                         self.parent_window.update_rounded_corners
                                                         ))
        self.tab_widget.addTab(general_tab, "General")
        
        # MARK: Resolution Tab
        resolution_tab = QWidget()
        resolution_layout = QVBoxLayout(resolution_tab)
        resolution_layout.setAlignment(Qt.AlignTop)
        # show_resolution_checkbox = QCheckBox("Show Resolutions")
        # allow_res_change_checkbox = QCheckBox("Allow Resolution Change")
        resolution_layout.addWidget(create_setting_checkbox("Show Resolutions",
                                                            "show_resolution",
                                                            "ShowResolution",
                                                            ))
        resolution_layout.addWidget(create_setting_checkbox("Allow Resolution Change",
                                                            "allow_res_change",
                                                            "AllowResolutionChange",
                                                            ))
        self.tab_widget.addTab(resolution_tab, "Resolution")
        

        # MARK: Refresh Rates Tab
        refresh_rate_tab = QWidget()
        refresh_rate_layout = QVBoxLayout(refresh_rate_tab)
        refresh_rate_layout.setAlignment(Qt.AlignTop)
        refresh_rate_layout.addWidget(create_setting_checkbox("Show Refresh Rates",
                                                             "show_refresh_rates",
                                                             "ShowRefreshRates",
                                                             ))
        
        exclude_rr_frame = QFrame()
        exclude_rr_layout = QVBoxLayout(exclude_rr_frame)
        exclude_rr_label = QLabel("Exclude Refresh Rates")
        exclude_rr_layout.addWidget(exclude_rr_label)
        
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        for rate in ["60 Hz", "75 Hz", "120 Hz"]:
            rate_checkbox = QCheckBox(rate)
            scroll_layout.addWidget(rate_checkbox)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        exclude_rr_layout.addWidget(scroll_area)
        
        refresh_rate_layout.addWidget(exclude_rr_frame)
        self.tab_widget.addTab(refresh_rate_tab, "Refresh Rate")
        
        # MARK: Brightness Tab
        brightness_tab = QWidget()
        brightness_layout = QVBoxLayout(brightness_tab)
        brightness_layout.setAlignment(Qt.AlignTop)
        brightness_layout.addWidget(create_setting_checkbox("Restore Last Brightness",
                                                           "restore_last_brightness",
                                                           "RestoreLastBrightness",
                                                           ))
        self.tab_widget.addTab(brightness_tab, "Brightness")
        
        # MARK: About Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setAlignment(Qt.AlignTop)
        about_label = QLabel(f"{config.app_name} v{config.version}")
        check_update_button = QPushButton("Check for Updates")
        check_update_button.clicked.connect(lambda: webbrowser.open("https://github.com/ZDAVanO/MoniTune/releases/latest"))
        about_layout.addWidget(about_label)
        about_layout.addWidget(check_update_button)
        self.tab_widget.addTab(about_tab, "About")
        

    def show_parent_window(self):
        self.parent_window.show()

    def change_parent_var(self):
        setattr(self.parent_window, "test_var", random.randint(1, 100))
        # self.parent_window.test_var = 100











