from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSlider, QPushButton, QHBoxLayout, QComboBox, QFrame, QCheckBox, QScrollArea, QLineEdit, QListWidget, QListWidgetItem, QTimeEdit, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QIcon

from custom_widgets.custom_sliders import NoScrollSlider

from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict
import config
from config import tray_icons

import webbrowser
import time




# MARK: SettingToggle
class SettingToggle:
    def __init__(self, parent, setting_name, reg_setting_name, callback=None):
        self.parent = parent
        self.setting_name = setting_name
        self.reg_setting_name = reg_setting_name
        self.callback = callback

    def toggle(self, state):
        print(f"Setting {self.setting_name} to {state}")
        setattr(self.parent, self.setting_name, state)
        reg_write_bool(config.REGISTRY_PATH, self.reg_setting_name, state)
        if callable(self.callback):
            self.callback()

    def create_toggle(self, label, tool_tip=""):
        checkbox = QCheckBox(label)
        checkbox.setToolTip(tool_tip)
        var = getattr(self.parent, self.setting_name)
        checkbox.setChecked(var)
        checkbox.stateChanged.connect(lambda: self.toggle(checkbox.isChecked()))
        return checkbox



# MARK: ChooseIconWidget
class ChooseIconWidget(QFrame):
    def __init__(self, parent):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.parent = parent

        layout = QHBoxLayout()
        
        label = QLabel("Tray icon")
        layout.addWidget(label)

        self.icon_buttons = []
        self.tray_icons = tray_icons

        for icon_name, icon_variants in self.tray_icons.items():
            button = QPushButton()
            button.setFixedHeight(32)
            button.setIcon(QIcon(icon_variants["Dark"]))  # Assuming dark theme for now
            button.setCheckable(True)
            button.setStyleSheet("background-color: #515151;")
            button.clicked.connect(lambda checked, btn=button, name=icon_name: self.on_icon_button_clicked(btn, name))
            layout.addWidget(button)
            self.icon_buttons.append(button)

        self.setLayout(layout)

    def on_icon_button_clicked(self, button, icon_name):
        for btn in self.icon_buttons:
            btn.setChecked(False)
        button.setChecked(True)
        print(f"Selected icon: {icon_name}")

        self.parent.tray_icon.changeIconName(icon_name)
        reg_write_list(config.REGISTRY_PATH, "TrayIcon", [icon_name])

    def select_icon(self, icon_name):
        if icon_name in self.tray_icons:
            for button in self.icon_buttons:
                button.setChecked(False)
            selected_button = next(btn for btn, name in zip(self.icon_buttons, self.tray_icons.keys()) if name == icon_name)
            selected_button.setChecked(True)
            print(f"select_icon Selected icon: {icon_name}")



# MARK: TimeAdjustmentFrame
class TimeAdjustmentFrame(QFrame):
    def __init__(self, parent, monitors_order, monitors_dict, time_str=None, brightness_data=None):
        super().__init__(parent)
        self.parent = parent
        self.monitors_order = monitors_order
        self.monitors_dict = monitors_dict
        self.setMaximumWidth(400)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Prevent frame from expanding
        self.frame_layout = QVBoxLayout(self)

        self.time_edit_layout = QHBoxLayout()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        if time_str:
            self.time_edit.setTime(QTime.fromString(time_str, 'HH:mm'))
        else:
            # self.time_edit.setTime(QTime.fromString("12:30", 'HH:mm'))
            self.time_edit.setTime(self.time_edit.time().currentTime())
        self.time_edit_layout.addWidget(self.time_edit)

        self.delete_button = QPushButton("Remove time")
        self.delete_button.clicked.connect(self.delete_frame)
        self.time_edit_layout.addWidget(self.delete_button)

        self.frame_layout.addLayout(self.time_edit_layout)


        self.time_edit.timeChanged.connect(self.update_time)

        self.sliders = {}
        self.brightness_data = brightness_data if brightness_data else {monitor_id: 50 for monitor_id in self.monitors_order}  # Initialize brightness data

        for monitor_id in self.monitors_order:
            slider_label = QLabel(f"{self.monitors_dict[monitor_id]['display_name']}")

            slider_layout = QHBoxLayout()
            slider = NoScrollSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(self.brightness_data.get(monitor_id, 50))
            slider.valueChanged.connect(lambda value, monitor_id=monitor_id: self.update_brightness(monitor_id, value))
            slider_layout.addWidget(slider)

            value_label = QLabel(f"{slider.value()}")
            slider.valueChanged.connect(lambda value, label=value_label: label.setText(f"{value}"))
            slider_layout.addWidget(value_label)

            self.frame_layout.addWidget(slider_label)
            self.frame_layout.addLayout(slider_layout)

            self.sliders[monitor_id] = slider

    def update_brightness(self, monitor_id, value):
        self.brightness_data[monitor_id] = value
        # print(f"Updated brightness data: {self.brightness_data}")

    def update_time(self):
        new_time_str = self.time_edit.time().toString('HH:mm')
        # print(f"Updated time: {new_time_str}")

    def delete_frame(self):
        self.parent.time_adjustment_frames.remove(self)
        self.deleteLater()
        # print("Frame deleted")

    def get_data(self):
        return {
            "time": self.time_edit.time().toString('HH:mm'),
            "brightness": self.brightness_data
        }




# MARK: SettingsWindow
class SettingsWindow(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        
        self.parent = parent_window

        self.setWindowTitle(f"{config.app_name} Settings")
        self.setWindowIcon(QIcon(config.app_icon_path))
        
        self.resize(450, 500)
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        # self.tab_widget.setDocumentMode(True)
        settings_layout.addWidget(self.tab_widget)

        self.time_adjustment_data = {}  # Dictionary to store time and brightness data
        self.time_adjustment_frames = []  # List to store TimeAdjustmentFrame instances
        # print("self.time_adjustment_data", self.time_adjustment_data)


    # MARK: closeEvent
    def closeEvent(self, event):
        print("Settings window closeEvent")

        
        self.save_adjustment_data()

        event.ignore()
        self.hide()
        # self.close()

    # MARK: showEvent
    def showEvent(self, event):
        print("Settings window showEvent")
        # self.updateLayout()
        QTimer.singleShot(0, self.updateLayout)
        super().showEvent(event)


    # MARK: save_adjustment_data
    def save_adjustment_data(self):
        # self.time_adjustment_data.clear()
        
        self.time_adjustment_data = {
            frame.get_data()["time"]: frame.get_data()["brightness"]
            for frame in self.time_adjustment_frames
        }
        self.time_adjustment_frames = []

        # Sort the time adjustment data by time
        sorted_time_adjustment_data = dict(sorted(self.time_adjustment_data.items()))

        print(f"Collected time adjustment data: {sorted_time_adjustment_data}")
        reg_write_dict(config.REGISTRY_PATH, "TimeAdjustmentData", sorted_time_adjustment_data)

        self.parent.time_adjustment_data = sorted_time_adjustment_data
        self.parent.update_scheduler_tasks()




    # MARK: updateLayout
    def updateLayout(self):

        # Clear old widgets
        # print("Clearing tabs : ", self.tab_widget.count())
        while self.tab_widget.count(): # num of tabs
            self.tab_widget.removeTab(0) # remove the first tab



        # MARK: get monitors info
        monitors_info = get_monitors_info()

        # hidden_displays = reg_read_list(config.REGISTRY_PATH, "HiddenDisplays")
        # # Exclude monitors that are in self.hidden_displays
        # monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in hidden_displays]

        # Створюємо словник, де ключ — серійний номер
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        reg_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in reg_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]
        custom_monitor_names = reg_read_dict(config.REGISTRY_PATH, "CustomMonitorNames")



        # MARK: General Tab
        general_tab = QWidget()
        # general_tab.setStyleSheet("background-color: blue")
        general_layout = QVBoxLayout(general_tab)
        general_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        general_layout.addWidget(SettingToggle(self.parent, 
                                               "enable_rounded_corners", 
                                               "EnableRoundedCorners",
                                               self.parent.update_central_widget)
                                               .create_toggle(
                                                   "Rounded Corners", 
                                                   "Enable rounded corners for the main window"
                                                   ))
        general_layout.addWidget(SettingToggle(self.parent, 
                                               "enable_fusion_theme", 
                                               "EnableFusionTheme")
                                               .create_toggle(
                                                   "Fusion Theme", 
                                                   "Enables Fusion theme. Requires app restart"
                                                   ))

        icon_widget = ChooseIconWidget(self.parent)
        icon = reg_read_list(config.REGISTRY_PATH, "TrayIcon")
        print("Icon:", icon) # ['fluent']
        icon_widget.select_icon(icon[0] if icon else "monitune")
        general_layout.addWidget(icon_widget)





        # # MARK: Monitor Settings Tab
        # monitor_settings_tab = QWidget()
        # # general_tab.setStyleSheet("background-color: blue")
        # monitor_settings_layout = QVBoxLayout(monitor_settings_tab)

        # self.tab_widget.addTab(monitor_settings_tab, "Monitor Settings")






        # MARK: Hide Displays
        hide_displays_widget = QFrame()
        hide_displays_widget.setFrameShape(QFrame.StyledPanel)
        hide_displays_layout = QVBoxLayout(hide_displays_widget)
        hide_displays_label = QLabel("Hide Displays")
        hide_displays_layout.addWidget(hide_displays_label)

        hidden_displays = reg_read_list(config.REGISTRY_PATH, "HiddenDisplays")
        # hidden_displays = list(map(str, filter(None, reg_read_list(config.REGISTRY_PATH, "HiddenDisplays"))))
        print("reg Hidden displays:", hidden_displays)

        def update_hidden_displays(monitor_id, state):
            # print(f"Monitor ID: {monitor_id}, State: {state}")
            if state == 2:
                if monitor_id not in hidden_displays:
                    hidden_displays.append(monitor_id)
            else:
                if monitor_id in hidden_displays:
                    hidden_displays.remove(monitor_id)
            reg_write_list(config.REGISTRY_PATH, "HiddenDisplays", hidden_displays)
            self.parent.hidden_displays = hidden_displays
            print(f"Updated hidden displays: {hidden_displays}")

        for monitor_id in monitors_order:
            checkbox = QCheckBox(f"{monitors_dict[monitor_id]['display_name']}")
            checkbox.setChecked(monitor_id in hidden_displays)
            checkbox.stateChanged.connect(lambda state, mid=monitor_id: update_hidden_displays(mid, state))
            hide_displays_layout.addWidget(checkbox)

        general_layout.addWidget(hide_displays_widget)












        # MARK: Rename Monitors
        rename_monitors_widget = QFrame()
        rename_monitors_widget.setFrameShape(QFrame.StyledPanel)
        rename_monitors_layout = QVBoxLayout(rename_monitors_widget)
        rename_monitors_label = QLabel("Rename Monitors")
        rename_monitors_layout.addWidget(rename_monitors_label)
        # rename_monitors_layout.setSpacing(0)

        def save_name(monitor_id, new_name):
            if 0 < len(new_name) <= 50:
                custom_monitor_names[monitor_id] = new_name
            elif len(new_name) == 0:
                custom_monitor_names.pop(monitor_id, None)
            print(f"Updated names: {custom_monitor_names}")
            self.parent.custom_monitor_names = custom_monitor_names
            # # self.show_parent_window()
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



        # MARK: Reorder Monitors
        def save_order():
            monitors_order = [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]
            print("New order:", monitors_order)
            reg_write_list(config.REGISTRY_PATH, "MonitorsOrder", monitors_order)
            self.parent.monitors_order = monitors_order
            # self.show_parent_window()

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
        resolution_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # show_resolution_checkbox = QCheckBox("Show Resolutions")
        # allow_res_change_checkbox = QCheckBox("Allow Resolution Change")
        resolution_layout.addWidget(SettingToggle(self.parent,
                                                  "show_resolution",
                                                  "ShowResolution")
                                                  .create_toggle(
                                                      "Show Resolutions",
                                                      "Show resolution for each monitor"
                                                      ))
        resolution_layout.addWidget(SettingToggle(self.parent,
                                                  "allow_res_change",
                                                  "AllowResolutionChange")
                                                  .create_toggle(
                                                      "Allow Resolution Change",
                                                      "Allow changing the resolution of monitors"
                                                      ))


        self.tab_widget.addTab(resolution_tab, "Resolution")
        


        # MARK: Refresh Rates Tab
        refresh_rate_tab = QWidget()
        refresh_rate_layout = QVBoxLayout(refresh_rate_tab)
        refresh_rate_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        refresh_rate_layout.addWidget(SettingToggle(self.parent,
                                                    "show_refresh_rates",
                                                    "ShowRefreshRates")
                                                    .create_toggle(
                                                        "Show Refresh Rates",
                                                        "Show buttons to change refresh rate"
                                                        ))


        # MARK: Exclude Refresh Rates
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
            # self.show_parent_window()
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
        brightness_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        brightness_layout.addWidget(SettingToggle(self.parent,
                                                  "restore_last_brightness",
                                                  "RestoreLastBrightness")
                                                  .create_toggle(
                                                      "Restore Last Brightness",
                                                      "Restore the last brightness level when window opens"
                                                      ))
        self.tab_widget.addTab(brightness_tab, "Brightness")



        # MARK: Time adjustment Frame
        time_adjustment_frame = QFrame()
        time_adjustment_frame.setFrameShape(QFrame.StyledPanel)
        time_adjustment_layout = QVBoxLayout(time_adjustment_frame)
        time_adjustment_label = QLabel("Time adjustment")
        time_adjustment_layout.addWidget(time_adjustment_label)
        time_adjustment_layout.addWidget(SettingToggle(self.parent,
                                                       "time_adjustment_startup",
                                                       "TimeAdjustmentStartup")
                                                       .create_toggle(
                                                              "Check at app startup",
                                                              "Adjust the brightness to match the most relecant time when the app starts"
                                                              ))

        def add_time_adjustment_frame(time_str=None, brightness_data=None):
            # print("Adding time adjustment frame")
            frame = TimeAdjustmentFrame(self, monitors_order, monitors_dict, time_str, brightness_data)
            self.time_adjustment_frames.append(frame)
            scroll_layout.addWidget(frame)

        add_frame_button = QPushButton("Add a time")
        add_frame_button.clicked.connect(lambda: add_time_adjustment_frame())
        time_adjustment_layout.addWidget(add_frame_button)

        scroll_area = QScrollArea()
        # scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(scroll_content)
        time_adjustment_layout.addWidget(scroll_area)
        brightness_layout.addWidget(time_adjustment_frame)

        # Restore TimeAdjustmentFrame widgets from registry
        saved_data = reg_read_dict(config.REGISTRY_PATH, "TimeAdjustmentData")
        # print("Saved data:", saved_data)
        for time_str, brightness_data in saved_data.items():
            # print(f"Adding frame with time: {time_str}, brightness: {brightness_data}")
            add_time_adjustment_frame(time_str, brightness_data)



        # MARK: About Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        about_label = QLabel(f"{config.app_name} v{config.version}")
        about_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        check_update_button = QPushButton("Check for Updates")
        check_update_button.setMinimumWidth(150)
        check_update_button.clicked.connect(lambda: webbrowser.open("https://github.com/ZDAVanO/MoniTune/releases/latest"))
        
        learn_more_label = QLabel('<a href="https://github.com/ZDAVanO/MoniTune" style="text-decoration: none;">Learn More</a>')
        learn_more_label.setOpenExternalLinks(True)  # Дозволяє відкривати посилання у браузері

        about_layout.addWidget(about_label, alignment=Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(check_update_button, alignment=Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(learn_more_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.tab_widget.addTab(about_tab, "About")
        
        
    # MARK: show_parent_window
    def show_parent_window(self):
        QTimer.singleShot(400, self.parent.show)












