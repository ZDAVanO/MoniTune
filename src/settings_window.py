from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSlider, QPushButton, QApplication, QMainWindow, QHBoxLayout, QComboBox, QFrame, QCheckBox, QScrollArea, QLineEdit, QListWidget, QListWidgetItem, QSizePolicy
from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
import random
import webbrowser

import config
from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict
from PySide6.QtGui import QIcon

import time


class SettingsWindow(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        
        self.parent = parent_window

        self.setWindowTitle(f"{config.app_name} Settings")
        self.setWindowIcon(QIcon(config.app_icon_path))
        
        self.resize(450, 400)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        settings_layout.addWidget(self.tab_widget)


        # Add button to show parent window
        # self.show_parent_button = QPushButton("Show Parent Window")
        # self.show_parent_button.clicked.connect(self.parent.show)
        # settings_layout.addWidget(self.show_parent_button)

        # Add button to change parent window's test_var
        # self.change_var_button = QPushButton("Change Parent Variable")
        # self.change_var_button.clicked.connect(self.change_parent_var)
        # settings_layout.addWidget(self.change_var_button)

        

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
            setattr(self.parent, setting_name, bool)
            reg_write_bool(config.REGISTRY_PATH, reg_setting_name, bool)
            if callable(callback):
                callback()

            self.show_parent_window()

        def create_setting_checkbox(checkbox_label, 
                                    setting_name, 
                                    reg_setting_name, 
                                    callback=None,
                                    ):
            checkbox = QCheckBox(checkbox_label)
            var = getattr(self.parent, setting_name)
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
                                                         self.parent.update_central_widget
                                                         ))



        # get monitors info

        monitors_info = get_monitors_info()
        # Створюємо словник, де ключ — серійний номер
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        reg_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in reg_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]
        custom_monitor_names = reg_read_dict(config.REGISTRY_PATH, "CustomMonitorNames")



        # Add Rename Monitors setting

        rename_monitors_widget = QFrame()
        rename_monitors_widget.setFrameShape(QFrame.StyledPanel)
        rename_monitors_layout = QVBoxLayout(rename_monitors_widget)
        rename_monitors_label = QLabel("Rename Monitors")
        rename_monitors_layout.addWidget(rename_monitors_label)
        # rename_monitors_layout.setSpacing(0)

        def save_name(monitor_id, new_name):
            if 0 < len(new_name) <= 50:
                custom_monitor_names[monitor_id] = new_name
                print(f"Updated names: {custom_monitor_names}")
                self.parent.custom_monitor_names = custom_monitor_names
                # self.show_parent_window()
                reg_write_dict(config.REGISTRY_PATH, "CustomMonitorNames", custom_monitor_names)

        for monitor_id in monitors_order:
            row_frame = QWidget()
            row_layout = QHBoxLayout(row_frame)
            # row_frame.setStyleSheet("background-color: red")
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f"{monitors_dict[monitor_id]['display_name']}")
            label.setAlignment(Qt.AlignLeft)
            row_layout.addWidget(label)

            entry = QLineEdit()
            entry.setPlaceholderText("Enter new name")
            entry.setMaxLength(25)
            placeholder = custom_monitor_names.get(monitor_id, "")
            entry.setText(placeholder)
            entry.textChanged.connect(lambda text, serial=monitor_id: save_name(serial, text))
            row_layout.addWidget(entry)

            row_layout.setStretch(0, 1)
            row_layout.setStretch(1, 1) 

            rename_monitors_layout.addWidget(row_frame)





        general_layout.addWidget(rename_monitors_widget)



        # Add Reorder Monitors setting
        
        def save_order():
            monitors_order = [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]
            print("New order:", monitors_order)
            reg_write_list(config.REGISTRY_PATH, "MonitorsOrder", monitors_order)
            self.parent.monitors_order = monitors_order
            self.show_parent_window()

        reorder_monitors_widget = QFrame()
        reorder_monitors_widget.setFrameShape(QFrame.StyledPanel)
        reorder_monitors_layout = QVBoxLayout(reorder_monitors_widget)
        reorder_monitors_label = QLabel("Reorder Monitors")
        reorder_monitors_layout.addWidget(reorder_monitors_label)

        # print("monitors_order", monitors_order)
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)  # Дозволяє перетягування
        self.list_widget.model().rowsMoved.connect(save_order)
        
        for monitor_id in monitors_order:
            # item = QListWidgetItem(monitors_dict[monitor_id]['display_name'])
            item = QListWidgetItem(f"{custom_monitor_names[monitor_id]} ({monitors_dict[monitor_id]['display_name']})"
            if monitor_id in custom_monitor_names else monitors_dict[monitor_id]['display_name'])
            item.setData(Qt.UserRole, monitor_id)
            self.list_widget.addItem(item)

        reorder_monitors_layout.addWidget(self.list_widget)
        general_layout.addWidget(reorder_monitors_widget)



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
        


        # Add Exclude Refresh Rate setting

        all_rates = set()
        for monitor in monitors_info:
            all_rates.update(monitor['AvailableRefreshRates'])
        all_rates = sorted(all_rates)

        # excluded_rates = list(map(int, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates")))
        excluded_rates = list(map(int, filter(None, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates"))))


        # Функція для оновлення списку excluded

        def update_excluded(rate, value):
            print(f"Rate: {rate}, Switch: {value}")

            if value == 2: # Якщо перемикач увімкнений
                if rate in excluded_rates:
                    excluded_rates.remove(rate)
            else:  # Якщо перемикач вимкнений
                if rate not in excluded_rates:
                    excluded_rates.append(rate)

            reg_write_list(config.REGISTRY_PATH, "ExcludedHzRates", excluded_rates)
            self.parent.excluded_rates = excluded_rates
            self.show_parent_window()
            print(f"Updated excluded list: {excluded_rates}")


        exclude_rr_frame = QFrame()
        exclude_rr_frame.setFrameShape(QFrame.StyledPanel)

        exclude_rr_layout = QVBoxLayout(exclude_rr_frame)
        exclude_rr_label = QLabel("Exclude Refresh Rates")
        exclude_rr_layout.addWidget(exclude_rr_label)


        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        for rate in all_rates:
            rate_checkbox = QCheckBox(f"{rate} Hz")
            scroll_layout.addWidget(rate_checkbox)

            if rate not in excluded_rates:
                rate_checkbox.setChecked(True)
            
            rate_checkbox.stateChanged.connect(lambda state, rate=rate: update_excluded(rate, state))

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
        QTimer.singleShot(400, self.parent.show)

    def change_parent_var(self):
        setattr(self.parent, "test_var", random.randint(1, 100))
        # self.parent.test_var = 100











