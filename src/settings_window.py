from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTabWidget, 
    QLabel, 
    QSlider, 
    QPushButton, 
    QHBoxLayout, 
    QComboBox, 
    QFrame, 
    QCheckBox, 
    QScrollArea, 
    QLineEdit, 
    QListWidget, 
    QListWidgetItem, 
    QTimeEdit, 
    QSizePolicy,
    QSpacerItem,
    QMessageBox,
    QFileDialog,
    QApplication,
)
from PySide6.QtCore import (
    Qt, 
    QTimer, 
    QTime,
)
from PySide6.QtGui import QIcon

from custom_widgets import (
    NoScrollSlider,
    SeparatorLine,
    FadingWidget,
)

from utils.monitor_utils import (
    get_monitors_info, 
    )
from utils.reg_utils import (
    is_dark_theme, 
    key_exists, 
    create_reg_key, 
    reg_write_bool, 
    reg_read_bool, 
    reg_write_list, 
    reg_read_list, 
    reg_write_dict, 
    reg_read_dict,
    delete_reg_key,
    )
import config as cfg
from config import tray_icons

from pathlib import Path

import time

import logging
logger = logging.getLogger(__name__)



# MARK: BaseSettingFrame
class BaseSettingFrame(QFrame):
    def __init__(self, 
                 title: str, 
                 descr: str = None):
        super().__init__(frameShape=QFrame.Shape.StyledPanel)

        self.setObjectName("SettingFrame")

        self.layout_ = QVBoxLayout(self)
        # self.layout_.setContentsMargins(0, 0, 0, 0)
        # self.layout_.setSpacing(0)

        # Title bar
        self.title_layout = QHBoxLayout()
        # self.title_layout.setContentsMargins(9, 0, 9, 0)
        self.title_layout.setSpacing(6)

        # Description block
        if title:
            descr_widget = QWidget()
            descr_widget.setSizePolicy(QSizePolicy.Policy.Expanding, 
                                       QSizePolicy.Policy.Preferred)
            # descr_widget.setStyleSheet("background-color: red;")

            self.descr_layout = QVBoxLayout(descr_widget)
            self.descr_layout.setContentsMargins(2, 0, 0, 0)
            self.descr_layout.setSpacing(0)

            self.title_label = QLabel(title)
            self.title_label.setWordWrap(True)
            # self.title_label.setStyleSheet("background-color: blue;")
            self.descr_layout.addWidget(self.title_label)

            if descr:
                fading_widget = FadingWidget(fade_opacity=0.75, duration=300)

                self.descr_label = QLabel(descr)
                # self.descr_label.setStyleSheet("background-color: green;")
                self.descr_label.setWordWrap(True)
                fading_widget.box_layout.addWidget(self.descr_label)

                self.descr_layout.addWidget(fading_widget)

            self.title_layout.addWidget(descr_widget)

        self.layout_.addLayout(self.title_layout)

    # MARK: highlight_frame()
    def highlight_frame(self):
        self.setStyleSheet("""
            QFrame#SettingFrame {
                border: 2px solid #4cd964;
                border-radius: 6px;
            }
            """)
        # QTimer.singleShot(5000, lambda: self.setStyleSheet(""))


# MARK: SettingFrame
class SettingFrame(BaseSettingFrame):
    def __init__(self, 
                 settings_window, 
                 title : str = None,
                 descr : str = None,
                 ):
        super().__init__(title=title, descr=descr)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, 
                           QSizePolicy.Policy.Fixed)

        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        self.title_layout.setContentsMargins(9, 9, 9, 6)

        self.layout_.addWidget(SeparatorLine(color=cfg.colors["s_sep"][settings_window.color_theme]))

        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(9, 7, 9, 9)
        self.content_layout.setSpacing(6)
        self.layout_.addLayout(self.content_layout)



# MARK: SettingToggleButton
class SettingToggleButton(QPushButton):
    def __init__(self, 
                 main_window, 
                 tool_tip,
                 setting_name, 
                 reg_setting_name, 
                 callback=None, 
                 after_restart=False):
        super().__init__()

        self.main_window = main_window
        self.setting_name = setting_name
        self.reg_setting_name = reg_setting_name
        self.callback = callback
        self.after_restart = after_restart

        self.setMinimumSize(77, 28)
        self.setCheckable(True)

        checked = getattr(self.main_window, self.setting_name)
        self.setChecked(checked)
        self.setText("Enabled" if checked else "Disabled")
        
        if tool_tip:
            self.setToolTip(tool_tip)

        self.toggled.connect(self.on_toggle)
        
    # MARK: on_toggle()
    def on_toggle(self, checked):
        logger.info(f"toggle {self.setting_name} - {checked}")
        self.setText("Enabled" if checked else "Disabled")

        # print(self.sizeHint().width())
        # print(self.height())

        if not self.after_restart:
            setattr(self.main_window, self.setting_name, checked)
        reg_write_bool(cfg.REGISTRY_PATH, self.reg_setting_name, checked)
        if callable(self.callback):
            self.callback(checked)



# MARK: SettingToggleFrame
class SettingToggleFrame(BaseSettingFrame):
    def __init__(self, 
                 main_window,
                 title: str, 
                 descr: str, 
                 setting_name, 
                 reg_setting_name, 
                 callback = None,
                 after_restart=False,
                 ):
        super().__init__(title=title, descr=descr)
        
        self.btn = SettingToggleButton(main_window=main_window,
                                       tool_tip=None,
                                       setting_name=setting_name,
                                       reg_setting_name=reg_setting_name,
                                       callback=callback,
                                       after_restart=after_restart)
        self.title_layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignRight)


# MARK: SettingButtonFrame
class SettingButtonFrame(BaseSettingFrame):
    def __init__(self, 
                 title: str, 
                 descr: str = None, 
                 button_text: str = None, 
                 callback = None):
        super().__init__(title=title, descr=descr)
        
        if not button_text:
            button_text = title

        self.btn = QPushButton(button_text)
        self.btn.setStyleSheet("padding: 7px 18px;") # padding: 5px 15px;
        self.btn.setSizePolicy(QSizePolicy.Policy.Fixed, 
                               QSizePolicy.Policy.Fixed)
        if callback:
            self.btn.clicked.connect(callback)

        self.title_layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignRight)



# MARK: TrayIconSelector
class TrayIconSelector(BaseSettingFrame):
    def __init__(self, main_window):
        super().__init__(title="Tray icon", descr=None)
        self.main_window = main_window

        self.icon_buttons = []
        self.tray_icons = tray_icons

        for icon_name, icon_variants in self.tray_icons.items():
            button = QPushButton()
            button.setStyleSheet("""
                                 padding: 10px 10px;
                                 """)
            button.setIcon(QIcon(icon_variants[self.main_window.theme]))
            button.setCheckable(True)
            button.clicked.connect(lambda checked, 
                                   btn=button, 
                                   name=icon_name: 
                                   self.on_icon_button_clicked(btn, name))
            self.title_layout.addWidget(button)
            self.icon_buttons.append(button)

    # MARK: on_icon_button_clicked()
    def on_icon_button_clicked(self, button, icon_name):
        for btn in self.icon_buttons:
            btn.setChecked(False)
        button.setChecked(True)
        logger.info(f"Selected icon: {icon_name}")

        self.main_window.tray_icon.changeIconName(icon_name)
        reg_write_list(cfg.REGISTRY_PATH, "TrayIcon", [icon_name])

    # MARK: select_icon()
    def select_icon(self, icon_name):
        if (icon_name in self.tray_icons):
            for button in self.icon_buttons:
                button.setChecked(False)
            selected_button = next(btn for btn, name in zip(self.icon_buttons, self.tray_icons.keys()) if name == icon_name)
            selected_button.setChecked(True)
            logger.info(f"select_icon: {icon_name}")



# MARK: BaseBrightnessSlidersFrame
class BaseBrightnessSlidersFrame(SettingFrame):
    def __init__(self, 
                 settings_window, 
                 monitors_order, 
                 display_names, 
                 brightness_data=None
                 ):
        super().__init__(settings_window)
        self.settings_window = settings_window

        self.sliders = {}
        self.brightness_data = brightness_data if brightness_data else {serial: 50 for serial in monitors_order}
        
        # init layouts
        self.setMaximumWidth(600)

        self.layout_.setContentsMargins(0, 4, 0, 4)
        self.layout_.setSpacing(3)

        self.title_layout.setContentsMargins(5, 0, 5, 0)
        self.title_layout.setSpacing(3)

        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # init sliders
        sliders_container = QHBoxLayout()
        sliders_container.setContentsMargins(9, 0, 9, 0)
        sliders_container.setSpacing(0)

        names_layout = QVBoxLayout()
        sliders_layout = QVBoxLayout()
        sliders_container.addLayout(names_layout)
        sliders_container.addItem(QSpacerItem(6, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        sliders_container.addLayout(sliders_layout)

        for serial in monitors_order:
            label = QLabel(f"{display_names[serial]}")
            names_layout.addWidget(label)

            slider_layout = QHBoxLayout()
            slider = NoScrollSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(self.brightness_data.get(serial, 50))
            self.sliders[serial] = slider

            spacer = QSpacerItem(3, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

            value_label = QLabel(f"{slider.value()}")
            value_label.setFixedWidth(19)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            slider.valueChanged.connect(lambda value, label=value_label: label.setText(f"{value}"))
            slider.valueChanged.connect(lambda value, s=serial: self.update_brightness(s, value))

            slider_layout.addWidget(slider)
            slider_layout.addItem(spacer)
            slider_layout.addWidget(value_label)
            sliders_layout.addLayout(slider_layout)

        self.content_layout.addLayout(sliders_container)

    def update_brightness(self, monitor_id, value):
        self.brightness_data[monitor_id] = value
        self.save_data()



# MARK: TimeAdjustmentFrame
class TimeAdjustmentFrame(BaseBrightnessSlidersFrame):
    def __init__(self, 
                 settings_window, 
                 monitors_order, 
                 display_names, 
                 time_str=None, 
                 brightness_data=None):
        super().__init__(settings_window, 
                         monitors_order, 
                         display_names, 
                         brightness_data)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        if time_str:
            self.time_edit.setTime(QTime.fromString(time_str, 'HH:mm'))
        else:
            self.time_edit.setTime(QTime.fromString("12:30", 'HH:mm'))
            # self.time_edit.setTime(self.time_edit.time().currentTime())
        self.time_edit.timeChanged.connect(self.update_time)
        self.title_layout.addWidget(self.time_edit)

        self.delete_button = QPushButton("Remove time")
        self.delete_button.setStyleSheet("padding: 4px 10px;")
        self.delete_button.clicked.connect(self.delete_frame)
        self.title_layout.addWidget(self.delete_button)
        self.title_layout.addStretch() # Add stretch to push widgets to the left

    def save_data(self): # using in BaseBrightnessSlidersFrame
        self.settings_window.save_adjustment_data()

    def update_time(self):
        self.save_data()

    def delete_frame(self):
        self.settings_window.time_adjustment_frames.remove(self)
        self.deleteLater()
        self.save_data()

    def get_data(self):
        return {
            "time": self.time_edit.time().toString('HH:mm'),
            "brightness_data": self.brightness_data
        }

    # def adjust_all_sliders(self, event):
    #     delta = event.angleDelta().y() // 120  # Each scroll step is 120 units
    #     for slider in self.sliders.values():
    #         new_value = max(0, min(100, slider.value() + delta))
    #         slider.setValue(new_value)



# MARK: ProfileFrame
class ProfileFrame(BaseBrightnessSlidersFrame):
    def __init__(self, 
                 settings_window, 
                 monitors_order, 
                 display_names, 
                 process=None, 
                 brightness_data=None
                 ):
        super().__init__(settings_window, 
                         monitors_order, 
                         display_names, 
                         brightness_data)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("path/to/app.exe")
        if process:
            self.entry.setText(process)
        self.entry.textChanged.connect(self.on_path_change)
        self.title_layout.addWidget(self.entry)

        self.select_button = QPushButton("Select")
        self.select_button.setStyleSheet("padding: 4px 10px;")
        self.select_button.clicked.connect(self.choose_exe_dialog)
        self.title_layout.addWidget(self.select_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("padding: 4px 10px;")
        self.delete_button.clicked.connect(self.delete_frame)
        self.title_layout.addWidget(self.delete_button)

    def save_data(self): # using in BaseBrightnessSlidersFrame
        self.settings_window.save_profiles_data()

    def on_path_change(self, text):
        self.save_data()

    def delete_frame(self):
        self.settings_window.profiles_frames.remove(self)
        self.deleteLater()
        self.save_data()

    def get_data(self):
        return {
            "path": self.entry.text(),
            "brightness_data": self.brightness_data
        }

    def choose_exe_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select .exe file", "", "EXE Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.entry.setText(file_path)



# MARK: ScrollableTab
class ScrollableTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        # container.setStyleSheet("background-color: blue;")
        self.layout_ = QVBoxLayout(container)
        self.layout_.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)



# MARK: SettingsWindow
class SettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        
        self.main_window = main_window
        self.theme = self.main_window.theme
        self.color_theme = self.main_window.color_theme

        self.setWindowTitle(f"{cfg.app_name} Settings")
        self.setWindowIcon(QIcon(cfg.icons["monitune"]["Light"]))
        
        self.resize(475, 600)
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)

        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        # self.tab_widget.setDocumentMode(True)

        self.selected_tab = 0  # Variable to store the selected tab index
        self.tab_widget.currentChanged.connect(self.on_tab_change)
        settings_layout.addWidget(self.tab_widget)

        # variables
        self.time_adjustment_data = {}  # Dictionary to store time and brightness data
        self.time_adjustment_frames = []  # List to store TimeAdjustmentFrame instances
        # print("self.time_adjustment_data", self.time_adjustment_data)

        self.profiles_data = {}
        self.profiles_frames = []
        self.ap_timer = None

        self.serial_list = []



    # MARK: showEvent()
    def showEvent(self, event):
        logger.info("Settings window opened")
        # self.update_tab_widget()
        QTimer.singleShot(0, self.update_tab_widget)
        super().showEvent(event)

    # MARK: closeEvent()
    def closeEvent(self, event):
        # logger.info("Settings window closed")
        event.ignore()
        self.hide() # hide instead of close to prevent app closing

    # MARK: hideEvent()
    def hideEvent(self, event):
        super().hideEvent(event)
        logger.info("Settings window hidden")

        if self.ap_timer:
            self.ap_timer.stop()
            logger.info("ap_timer stopped")



    # MARK: save_adjustment_data()
    def save_adjustment_data(self):

        self.time_adjustment_data = {
            frame.get_data()["time"]: frame.get_data()["brightness_data"]
            for frame in self.time_adjustment_frames
        } # filter duplicates

        # Sort the time adjustment data by time
        sorted_time_adjustment_data = dict(sorted(self.time_adjustment_data.items()))

        logger.info(f"Collected time adjustment data: {sorted_time_adjustment_data}")
        reg_write_dict(cfg.REGISTRY_PATH, "TimeAdjustmentData", sorted_time_adjustment_data)
        self.main_window.time_adjustment_data = sorted_time_adjustment_data


    # MARK: save_profiles_data()
    def save_profiles_data(self):
        self.profiles_data = {}
        for frame in self.profiles_frames:
            data = frame.get_data()
            path = data["path"]
            brightness_data = data["brightness_data"]
            if path != "":
                resolved_path = str(Path(path).resolve())
            else:
                resolved_path = ""
            self.profiles_data[resolved_path] = brightness_data

        logger.info(f"Collected profiles data: {self.profiles_data}")
        reg_write_dict(cfg.REGISTRY_PATH, "ProfilesData", self.profiles_data)
        self.main_window.profiles_data = self.profiles_data



    # MARK: show_main_window()
    def show_main_window(self):
        QTimer.singleShot(400, self.main_window.show)


    # Mark: on_tab_change()
    def on_tab_change(self, index):
        logger.debug(f"on_tab_change index: {index}")
        self.selected_tab = index


    # MARK: update_tab_widget()
    def update_tab_widget(self):
        
        monitors_info = get_monitors_info()
        serial_list = [monitor['serial'] for monitor in monitors_info]
        if serial_list == self.serial_list:
            logger.info("Monitors info not changed")
            return
        self.serial_list = serial_list


        self.tab_widget.blockSignals(True)
        # Clear old widgets
        # print("Clearing tabs : ", self.tab_widget.count())
        while self.tab_widget.count(): # num of tabs
            self.tab_widget.removeTab(0) # remove the first tab

        self.time_adjustment_frames = [] # clear the list of frames
        self.profiles_frames = [] # clear the list of frames


        # hidden_displays = reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays")
        # # Exclude monitors that are in self.hidden_displays
        # monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in hidden_displays]

        # Створюємо словник, де ключ — серійний номер
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        reg_order = reg_read_list(cfg.REGISTRY_PATH, "MonitorsOrder")
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in reg_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]
        custom_monitor_names = reg_read_dict(cfg.REGISTRY_PATH, "CustomMonitorNames")

        display_names = {}
        for monitor in monitors_info:
            serial = monitor['serial']
            if serial in custom_monitor_names:
                display_names[serial] = f"{custom_monitor_names[serial]} ({monitor['display_name']})"
            else:
                display_names[serial] = monitor['display_name']


        # MARK: General Tab
        general_tab = ScrollableTab()
        self.tab_widget.addTab(general_tab, "General")
        
        general_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window, 
                                                           title="Launch on startup",
                                                           descr=None, # tool_tip="Launch MoniTune on Windows startup"
                                                           setting_name="launch_on_startup", 
                                                           reg_setting_name="LaunchOnStartup",
                                                           callback=self.main_window.update_autostart))

        general_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window, 
                                                           title="Rounded Corners",
                                                           descr="Enable rounded corners for the main window.",
                                                           setting_name="enable_rounded_corners", 
                                                           reg_setting_name="EnableRoundedCorners",
                                                           callback=self.main_window.update_central_widget))
        
        general_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                           title="Show Resolutions",
                                                           descr="Show resolution selector for each monitor.",
                                                           setting_name="show_resolution",
                                                           reg_setting_name="ShowResolution"))

        general_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window, 
                                                           title="Fusion Theme [Experimental]",
                                                           descr="Enable Fusion theme. Requires app restart.",
                                                           setting_name="enable_fusion_theme", 
                                                           reg_setting_name="EnableFusionTheme",
                                                           callback=None,
                                                           after_restart=True))

        general_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window, 
                                                           title="Eye Break Reminder",
                                                           descr="Get reminders every 30 minutes to rest your eyes.",
                                                           setting_name="enable_break_reminders", 
                                                           reg_setting_name="EnableBreakReminders"))
        


        icon_widget = TrayIconSelector(self.main_window)
        icon = reg_read_list(cfg.REGISTRY_PATH, "TrayIcon")
        logger.info(f"Icon: {icon}")
        icon_widget.select_icon(icon[0] if icon else "monitune")
        general_tab.layout_.addWidget(icon_widget)



        # MARK: Hide Displays
        hidden_displays = reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays")
        logger.info(f"Hidden displays (reg): {hidden_displays}")

        def update_hidden_displays(monitor_id, state):
            # print(f"Monitor ID: {monitor_id}, State: {state}")
            if state == 2:
                if monitor_id not in hidden_displays:
                    hidden_displays.append(monitor_id)
            else:
                if monitor_id in hidden_displays:
                    hidden_displays.remove(monitor_id)
            reg_write_list(cfg.REGISTRY_PATH, "HiddenDisplays", hidden_displays)
            self.main_window.hidden_displays = hidden_displays
            logger.info(f"Updated hidden displays: {hidden_displays}")

        hide_displays_frame = SettingFrame(self, "Hide Displays")
        for serial in monitors_order:
            checkbox = QCheckBox(display_names[serial])
            checkbox.setChecked(serial in hidden_displays)
            checkbox.stateChanged.connect(lambda state, s=serial: update_hidden_displays(s, state))
            hide_displays_frame.content_layout.addWidget(checkbox)
        general_tab.layout_.addWidget(hide_displays_frame)



        # MARK: Rename Monitors
        def save_name(monitor_id, new_name):
            if 0 < len(new_name) <= 50:
                custom_monitor_names[monitor_id] = new_name
            elif len(new_name) == 0:
                custom_monitor_names.pop(monitor_id, None)
            logger.info(f"Updated names: {custom_monitor_names}")
            self.main_window.custom_monitor_names = custom_monitor_names
            # # self.show_main_window()
            reg_write_dict(cfg.REGISTRY_PATH, "CustomMonitorNames", custom_monitor_names)

        rename_monitors_frame = SettingFrame(self, "Rename Monitors")
        for serial in monitors_order:
            row_frame = QWidget()
            row_layout = QHBoxLayout(row_frame)
            # row_frame.setStyleSheet("background-color: red")
            row_layout.setContentsMargins(0, 0, 0, 0)

            icon = QLabel()
            icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(22, 22))
            row_layout.addWidget(icon)

            label = QLabel(f"{monitors_dict[serial]['display_name']}")
            # label.setStyleSheet("background-color: red")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(label)

            entry = QLineEdit()
            entry.setStyleSheet("padding: 4px 4px;")
            entry.setPlaceholderText("Enter new name")
            entry.setMaxLength(25)
            placeholder = custom_monitor_names.get(serial, "")
            entry.setText(placeholder)
            entry.textChanged.connect(lambda text, serial=serial: save_name(serial, text))
            row_layout.addWidget(entry)

            row_layout.setStretch(0, 0)  # icon – only as much space as needed
            row_layout.setStretch(1, 1)  # label – 50% of the remaining space
            row_layout.setStretch(2, 1)  # entry – 50% of the remaining space

            rename_monitors_frame.content_layout.addWidget(row_frame)
        general_tab.layout_.addWidget(rename_monitors_frame)



        # MARK: Reorder Monitors
        def save_order():
            monitors_order = [list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(list_widget.count())]
            logger.info(f"New monitors_order: {monitors_order}")
            reg_write_list(cfg.REGISTRY_PATH, "MonitorsOrder", monitors_order)
            self.main_window.monitors_order = monitors_order
            # self.show_main_window()

        reorder_monitors_frame = SettingFrame(self, "Reorder Monitors")
        reorder_monitors_frame.content_layout.setContentsMargins(1, 0, 1, 3)
        reorder_monitors_frame.content_layout.setSpacing(0)

        list_widget = QListWidget()
        list_widget.setFrameShape(QFrame.Shape.NoFrame)
        height_map = {1: 27,
                      2: 56,
                      3: 84,
                      4: 112}
        list_widget.setFixedHeight(height_map.get(len(monitors_order), 111))
        list_widget.setStyleSheet("""
                                  QListWidget::item {
                                    padding: 5px;
                                  }
                                  """)
        list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # allow drag-and-drop
        list_widget.model().rowsMoved.connect(save_order)
        
        # monitors_order = [1, 2, 3]
        for serial in monitors_order:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, serial)

            widget = QWidget()
            # widget.setStyleSheet("background-color: red;")
            layout = QHBoxLayout(widget)
            # layout.setContentsMargins(2, 0, 2, 0)
            # layout.setContentsMargins(0, 0, 0, 0)
            layout.setContentsMargins(3, 0, 3, 0)

            icon = QLabel()
            icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(22, 22))
            icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout.addWidget(icon)

            label = QLabel(display_names[serial])
            # label = QLabel(f"Monitor {serial}")
            layout.addWidget(label)

            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)

        reorder_monitors_frame.content_layout.addWidget(list_widget)
        general_tab.layout_.addWidget(reorder_monitors_frame)



        # MARK: Reset Settings
        def confirm_and_delete():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.NoIcon)  # Без іконки
            msg_box.setWindowTitle("Confirm Reset")
            msg_box.setText("Are you sure you want to reset settings?\n"
                            "This action cannot be undone.\n\n"
                            "Changes will take effect after restarting the application.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            reply = msg_box.exec()
            if reply == QMessageBox.StandardButton.Yes:
                delete_reg_key(cfg.REGISTRY_PATH)

        reset_settings_frame = SettingButtonFrame(title="Reset settings",
                                                  descr="Hit this button to clear config.",
                                                  button_text="Reset Settings",
                                                  callback=confirm_and_delete)
        general_tab.layout_.addWidget(reset_settings_frame)



        # MARK: Refresh Rates Tab
        refresh_rate_tab = ScrollableTab()
        self.tab_widget.addTab(refresh_rate_tab, "Refresh Rate")

        refresh_rate_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                                title="Show Refresh Rates",
                                                                descr="Show buttons to change refresh rate of monitors.",
                                                                setting_name="show_refresh_rates",
                                                                reg_setting_name="ShowRefreshRates"))


        # MARK: Exclude Refresh Rates
        excluded_rates = reg_read_dict(cfg.REGISTRY_PATH, "ExcludedHzRates")
        logger.info(f"Excluded refresh rates (reg): {excluded_rates}")

        # Function to update the excluded list
        def update_excluded_rates(state, rate, serial):
            logger.info(f"state: {state}, rate: {rate}, ")

            # Ensure the serial key exists
            if serial not in excluded_rates:
                excluded_rates[serial] = []

            if state == 2: # If the switch is on
                if rate in excluded_rates[serial]:
                    excluded_rates[serial].remove(rate)
            else:  # If the switch is off
                if rate not in excluded_rates[serial]:
                    excluded_rates[serial].append(rate)

            reg_write_dict(cfg.REGISTRY_PATH, "ExcludedHzRates", excluded_rates)
            self.main_window.excluded_rates = excluded_rates
            logger.info(f"Updated excluded list: {excluded_rates}")

        exclude_rr_frame = SettingFrame(self, "Exclude Refresh Rates")

        # for monitor in monitors_info:
        for serial in monitors_order:
            monitor = monitors_dict[serial]
            available_rates = sorted(set(monitor['AvailableRefreshRates']))

            exclude_rr_monitor_frame = SettingFrame(self)
            # exclude_rr_monitor_frame.title_layout.setSpacing(6)

            icon = QLabel()
            icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(22, 22))
            exclude_rr_monitor_frame.title_layout.addWidget(icon)

            rr_label = QLabel(display_names[serial])
            exclude_rr_monitor_frame.title_layout.addWidget(rr_label)
            exclude_rr_monitor_frame.title_layout.addStretch()  # push the label to the left

            for rate in available_rates:
                rate_checkbox = QCheckBox(f"{rate} Hz")
                exclude_rr_monitor_frame.content_layout.addWidget(rate_checkbox)

                if serial in excluded_rates:
                    if rate not in excluded_rates[serial]:
                        rate_checkbox.setChecked(True)
                else:
                    rate_checkbox.setChecked(True)
                
                rate_checkbox.stateChanged.connect(lambda state, 
                                                   rate=rate, 
                                                   ms=serial: 
                                                   update_excluded_rates(state, rate, ms))
                
            exclude_rr_frame.content_layout.addWidget(exclude_rr_monitor_frame)

        refresh_rate_tab.layout_.addWidget(exclude_rr_frame)



        # MARK: Brightness Tab
        brightness_tab = ScrollableTab()
        self.tab_widget.addTab(brightness_tab, "Brightness")

        brightness_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                              title="Restore Last Brightness",
                                                              descr="Restore the last brightness level when window opens.",
                                                              setting_name="restore_last_brightness",
                                                              reg_setting_name="RestoreLastBrightness"))
        
        brightness_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                              title="Show Popup on background change",
                                                              descr="Show app window when brightness changing in background.",
                                                              setting_name="show_brightness_popup",
                                                              reg_setting_name="ShowBrightnessPopup"))



        # MARK: Time adjustment Frame
        time_adjustment_frame = SettingFrame(settings_window=self, 
                                             title="Time Adjustment", 
                                             descr="Automatically set your monitors to a specific brightness level at a desired time.")

        time_adjustment_toggle = SettingToggleButton(self.main_window,
                                                     "Automatically adjust brightness depending on the time.",
                                                     "enable_time_adjustment",
                                                     "EnableTimeAdjustment",
                                                     callback=self.main_window.execute_recent_task
                                                     )
        time_adjustment_frame.title_layout.addWidget(time_adjustment_toggle)

        time_adjustment_frame.content_layout.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                                     title="Check at app startup",
                                                                     descr="Adjust the brightness to match the most relevant time when MoniTune starts.",
                                                                     setting_name="time_adjustment_startup",
                                                                     reg_setting_name="TimeAdjustmentStartup"))

        def add_time_adjustment_frame(time_str=None, brightness_data=None, highlight=False):
            # print("Adding time adjustment frame")
            frame = TimeAdjustmentFrame(self, monitors_order, display_names, time_str, brightness_data)
            self.time_adjustment_frames.append(frame)
            scroll_layout.insertWidget(1, frame) # Add to the top of the scroll area
            # Highlight the newly added frame
            if highlight:
                frame.highlight_frame()

        add_frame_btn = QPushButton("Add a time")
        add_frame_btn.setStyleSheet("padding: 5px 15px;")
        add_frame_btn.clicked.connect(lambda: (add_time_adjustment_frame(highlight=True), 
                                               self.save_adjustment_data()))

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        # scroll_layout.setSpacing(0)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        scroll_layout.addWidget(add_frame_btn)

        time_adjustment_frame.content_layout.addWidget(scroll_content)
        brightness_tab.layout_.addWidget(time_adjustment_frame)

        # Restore TimeAdjustmentFrame widgets from registry
        saved_data = reg_read_dict(cfg.REGISTRY_PATH, "TimeAdjustmentData")
        # print("Saved data:", saved_data)
        for time_str, brightness_data in reversed(saved_data.items()):
            # print(f"Adding frame with time: {time_str}, brightness: {brightness_data}")
            add_time_adjustment_frame(time_str, brightness_data)



        # MARK: Profiles Tab
        profiles_tab = ScrollableTab()
        self.tab_widget.addTab(profiles_tab, "Profiles")

        profiles_frame = SettingFrame(self, "Profiles", "Automatically adjust brightness depending on the focused app.")
        profiles_toggle = SettingToggleButton(self.main_window,
                                       "Automatically adjust brightness depending on the focused app.",
                                       "enable_profiles",
                                       "EnableProfiles",
                                       callback=self.main_window.toggle_process_listener
                                       )
        # profiles_frame.title_layout.addStretch()
        profiles_frame.title_layout.addWidget(profiles_toggle)


        def add_profile_frame(path=None, brightness_data=None, highlight=False):
            frame = ProfileFrame(self, monitors_order, display_names, path, brightness_data)
            self.profiles_frames.append(frame)
            center_layout.insertWidget(1, frame) # Add to the top
            # Highlight the newly added frame
            if highlight:
                frame.highlight_frame()

        def update_ap_line_edit():
            path = self.main_window.active_process
            if path == self.main_window.monitune_exe:
                logger.debug(f"update_ap_line_edit MoniTune is active ({path})")
                return
            logger.debug(f"update_ap_line_edit: {path}")
            ap_line_edit.setText(path)

        # active process frame
        ap_frame = QFrame(frameShape=QFrame.Shape.StyledPanel)
        ap_frame_layout = QHBoxLayout(ap_frame)

        ap_frame_label = QLabel("Active app:")
        ap_frame_layout.addWidget(ap_frame_label)

        ap_line_edit = QLineEdit()
        ap_frame_layout.addWidget(ap_line_edit, stretch=1)

        ap_copy_btn = QPushButton("Copy")
        ap_copy_btn.setStyleSheet("padding: 4px 10px;")
        ap_copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(ap_line_edit.text()))
        ap_frame_layout.addWidget(ap_copy_btn)

        ap_add_btn = QPushButton("Add")
        ap_add_btn.setStyleSheet("padding: 4px 10px;")
        ap_add_btn.clicked.connect(lambda: (add_profile_frame(path=ap_line_edit.text(), highlight=True), 
                                            self.save_profiles_data()))
        ap_frame_layout.addWidget(ap_add_btn)

        self.ap_timer = QTimer()
        self.ap_timer.timeout.connect(update_ap_line_edit)
        self.ap_timer.start(1000)

        profiles_frame.content_layout.addWidget(ap_frame)

        # profiles frames
        add_frame_btn = QPushButton("Add profile")
        add_frame_btn.setStyleSheet("padding: 5px 15px;")
        add_frame_btn.clicked.connect(lambda: (add_profile_frame(highlight=True), 
                                               self.save_profiles_data()))

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        # scroll_layout.setSpacing(0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        center_layout.addWidget(add_frame_btn)

        profiles_frame.content_layout.addWidget(center_widget)

        # Restore ProfileFrame widgets from registry
        profiles_data = reg_read_dict(cfg.REGISTRY_PATH, "ProfilesData")
        for path, brightness_data in reversed(profiles_data.items()):
            add_profile_frame(path, brightness_data)

        profiles_tab.layout_.addWidget(profiles_frame)



        # MARK: DDC/CI Tab
        dcc_ci_tab = ScrollableTab()
        self.tab_widget.addTab(dcc_ci_tab, "DDC/CI")

        dcc_ci_tab.layout_.addWidget(SettingToggleFrame(main_window=self.main_window,
                                                          title="Show Contrast Sliders [Experimental]",
                                                          descr=None, # tool_tip="Show sliders to change contrast"
                                                          setting_name="show_contrast_sliders",
                                                          reg_setting_name="ShowContrastSliders"))



        # MARK: About Tab
        about_tab = ScrollableTab()
        self.tab_widget.addTab(about_tab, "About")

        def check_update():
            update_available, latest_version = self.main_window.check_for_update()
            if update_available and latest_version:
                check_update_frame.descr_label.setText(f"Update available: <a href='{cfg.LATEST_RELEASE_URL}'>v{latest_version}</a>")
                check_update_frame.descr_label.setOpenExternalLinks(True)
            elif latest_version:
                check_update_frame.descr_label.setText(
                    f"""
                    <div>
                        You are using the latest version.
                        <br>
                        Last check: {time.strftime("%H:%M:%S")}
                    </div>
                    """)
            else:
                check_update_frame.descr_label.setText(
                    f"""
                    <div>
                        Failed to check for updates. Please try again later.
                        <br>
                        Or check manually <a href='{cfg.LATEST_RELEASE_URL}'>here</a>.
                    </div>
                    """)
                check_update_frame.descr_label.setOpenExternalLinks(True)

        check_update_frame = SettingButtonFrame(title=f"{cfg.app_name} v{cfg.version}",
                                                  descr="Checking for updates...",
                                                  button_text="Check for Updates",
                                                  callback=check_update)
        check_update_frame.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        check_update()
        about_tab.layout_.addWidget(check_update_frame)


        # Add a link to the GitHub repository
        learn_more_label = QLabel(f'<a href="{cfg.LEARN_MORE_URL}" style="text-decoration: none;">Learn More</a>')
        learn_more_label.setOpenExternalLinks(True)  # Allows you to open links in the browser
        about_tab.layout_.addWidget(learn_more_label, alignment=Qt.AlignmentFlag.AlignCenter)



        # restore the selected tab
        self.tab_widget.blockSignals(False)
        self.tab_widget.setCurrentIndex(self.selected_tab)













