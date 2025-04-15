from PySide6.QtCore import (
    Qt, 
    QTimer, 
    QTime, 
    QDateTime, 
    QPropertyAnimation, 
    QEasingCurve, 
    Signal,
    QEvent, 
    QSize, 
    QRect, 
)
from PySide6.QtGui import (
    QIcon, 
    QGuiApplication, 
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStyle,
    QVBoxLayout,
    QWidget,
    QMenu,
    QSlider,
    QGraphicsOpacityEffect,
    QStyleFactory,
    QTabWidget,
    QPushButton,
    QFrame,
    QComboBox,
    QGridLayout,
    QSpacerItem,
    QSizePolicy
)

from system_tray_icon import SystemTrayIcon
from settings_window import SettingsWindow 

from custom_widgets import (
    RRButton,
    NoScrollComboBox,
    BrightnessIcon,
    AnimatedSliderBS,
    SeparatorLine,
)

from utils.monitor_utils import (
    get_monitors_info, 
    print_mi, 
    set_resolution, 
    set_refresh_rate, 
    get_brightness_sbc, 
    set_brightness_sbc, 
    get_brightness_vcp, 
    set_brightness_vcp, 
    get_contrast_vcp, 
    set_contrast_vcp, 
)
from utils.reg_utils import (
    reg_write_bool, 
    reg_read_bool, 
    reg_write_list, 
    reg_read_list, 
    reg_write_dict, 
    reg_read_dict
)
from utils.utils import get_idle_time, is_laptop
from utils.lock_detect import LockDetect

import config as cfg

import screeninfo

import darkdetect

import sys
import os
import ctypes
import threading
import time
import platform

import requests
from packaging.version import Version
import webbrowser



# MARK: SliderFrame
class SliderFrame(QWidget):
    def __init__(self, parent, icon_path, slider_value, slider_callback, label_text):
        super().__init__(parent)

        self.font_size = "22px"
        self.font_weight = "bold"
        self.padding_bottom = "2px"

        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(0, 0, 2, 0)
        self.hbox.setSpacing(0)

        self.icon = BrightnessIcon(icon_path=icon_path)
        self.icon.set_value(slider_value)
        self.hbox.addWidget(self.icon)

        spacer = QSpacerItem(6, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hbox.addItem(spacer)

        self.slider = AnimatedSliderBS(Qt.Orientation.Horizontal, 
                                       scrollStep=1, 
                                       singleStep=1, 
                                       pageStep=10)
        self.slider.setMaximum(100)
        self.slider.setValue(slider_value)
        self.slider.valueChanged.connect(slider_callback)
        self.hbox.addWidget(self.slider)

        spacer = QSpacerItem(3, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hbox.addItem(spacer)

        self.label = QLabel()
        self.label.setFixedWidth(39)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(str(label_text))
        self.label.setStyleSheet(f"""
                                 font-size: {self.font_size}; 
                                 font-weight: {self.font_weight}; 
                                 padding-bottom: {self.padding_bottom}; 
                                 """) # padding-bottom: 4px; background-color: green; font-size: 22px; font-weight: bold; font: 600 16pt "{cfg.font_family}";
        self.hbox.addWidget(self.label)

        self.slider.add_icon(self.icon) # Connect icon to slider to animate the icon
        self.slider.add_label(self.label) # Connect label to slider to animate the label



# MARK: MainWindow
class MainWindow(QMainWindow):

    theme_changed = Signal(str)
    lock_state_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.theme_changed.connect(self._apply_theme)
        self.lock_state_changed.connect(self._on_lock_state_change)

        self.win_release = platform.release()
        print(f"Windows release: {self.win_release}")

        self.is_laptop = is_laptop()

        self.theme = darkdetect.theme()

        # General settings
        self.enable_rounded_corners = reg_read_bool(cfg.REGISTRY_PATH, "EnableRoundedCorners", False if self.win_release != "11" else True)
        if self.enable_rounded_corners:
            self.window_corner_radius = cfg.WIN11_WINDOW_CORNER_RADIUS
            self.window_offset = cfg.WIN11_WINDOW_OFFSET
        else:
            self.window_corner_radius = 0
            self.window_offset = 0

        self.enable_fusion_theme = reg_read_bool(cfg.REGISTRY_PATH, "EnableFusionTheme", False)
        if self.enable_fusion_theme:
            QApplication.instance().setStyle("Fusion")
        self.update_theme_colors(self.theme)

        self.enable_break_reminders = reg_read_bool(cfg.REGISTRY_PATH, "EnableBreakReminders", False)

        self.hidden_displays = reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays")

        self.custom_monitor_names = reg_read_dict(cfg.REGISTRY_PATH, "CustomMonitorNames")
        print(f"custom_monitor_names {self.custom_monitor_names}")

        self.monitors_order = reg_read_list(cfg.REGISTRY_PATH, "MonitorsOrder")

        # Resolution settings
        self.show_resolution = reg_read_bool(cfg.REGISTRY_PATH, "ShowResolution")

        # Refresh rate settings
        self.show_refresh_rates = reg_read_bool(cfg.REGISTRY_PATH, "ShowRefreshRates")
        self.excluded_rates = list(map(int, reg_read_list(cfg.REGISTRY_PATH, "ExcludedHzRates")))
        # self.excluded_rates = list(map(int, filter(None, reg_read_list(cfg.REGISTRY_PATH, "ExcludedHzRates"))))

        # Brightness settings
        self.restore_last_brightness = reg_read_bool(cfg.REGISTRY_PATH, "RestoreLastBrightness")
        
        self.brightness_values = reg_read_dict(cfg.REGISTRY_PATH, "BrightnessValues")
        print(f"self.brightness_values {self.brightness_values}")

        self.time_adjustment_startup = reg_read_bool(cfg.REGISTRY_PATH, "TimeAdjustmentStartup")
        self.time_adjustment_data = reg_read_dict(cfg.REGISTRY_PATH, "TimeAdjustmentData")
        # self.time_adjustment_data = {}

        # DDC/CI settings
        self.show_contrast_sliders = reg_read_bool(cfg.REGISTRY_PATH, "ShowContrastSliders", False)
        self.contrast_values = reg_read_dict(cfg.REGISTRY_PATH, "ContrastValues")
        print(f"self.contrast_values {self.contrast_values}")

        self.link_brightness = reg_read_bool(cfg.REGISTRY_PATH, "LinkBrightness", False)


        self.settings_window = None  # No settings window yet
        self.rr_buttons = {}  # Dictionary to store refresh rate buttons for each monitor
        self.br_sliders = {}  # Dictionary to store brightness sliders
        self.contrast_sliders = {}  # Dictionary to store contrast sliders

        self.window_open = False
        self.brightness_sync_thread = None

        self.monitors_dict = {}
        self.update_monitors_info()



        self.setWindowTitle(cfg.app_name)

        self.window_width = 358
        self.window_height = 231

        self.setMinimumWidth(self.window_width)
        self.setMaximumWidth(self.window_width)
        self.resize(self.window_width, self.window_height)

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)

        # This container holds the window contents
        central_widget = QWidget()
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            f"""
            #Container {{
            background: {self.bg_color};
            border-radius: {self.window_corner_radius}px;
            border: 1px solid {self.border_color};
            }}
            """
        )
        


        self.monitors_frame = QWidget()
        # self.monitors_frame.setStyleSheet("border-radius: 9px; background-color: red")
        self.monitors_layout = QVBoxLayout(self.monitors_frame)
        self.monitors_layout.setContentsMargins(7, 7, 7, 0)
        self.monitors_layout.setSpacing(6) # Set spacing between monitor frames

        self.bottom_frame = QWidget()
        # self.bottom_frame.setStyleSheet("""
        #     background-color: green;
        #     border-bottom-left-radius: 9px;
        #     border-bottom-right-radius: 9px;
        # """)
        
        self.bottom_frame.installEventFilter(self)
        self.bottom_hbox = QHBoxLayout(self.bottom_frame)

        # self.bottom_frame.setFixedHeight(60)
        # self.bottom_hbox.setContentsMargins(7, 0, 11, 0)

        self.bottom_hbox.setContentsMargins(7, 5, 7, 7)

        self.bottom_hbox.setSpacing(4)

        

        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.setContentsMargins(0, 0, 0, 0)
        central_widget_layout.setSpacing(0)
        central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget_layout.addWidget(self.monitors_frame)
        # central_widget_layout.addStretch()  # Add stretch to push the bottom frame to the bottom
        central_widget_layout.addWidget(self.bottom_frame)

        self.setCentralWidget(central_widget)



        # Create the system tray icon
        self.tray_icon = SystemTrayIcon(self)

        # Run the theme listener in a separate thread
        threading.Thread(target=darkdetect.listener, 
                         args=(lambda theme: self.theme_changed.emit(theme),), # _apply_theme
                         daemon=True).start()


        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_all_tasks)
        self.last_check_time = QDateTime.currentDateTime()

        self.time_active = 0
        self.saved_time = 0

        # Run the lock state listener in a separate thread
        self.lock_listener = LockDetect(lambda state: self.lock_state_changed.emit(state)) # _on_lock_state_change
        threading.Thread(target=self.lock_listener.run, daemon=True).start()

        self.previous_screeninfo = screeninfo.get_monitors()
        self.start_checking(interval=(cfg.timer_interval * 1000))  # Start checking every minute
        if self.time_adjustment_startup:
            self.execute_recent_task()


        # check for updates on startup
        update_available, latest_version = self.check_for_update()
        if update_available:
            self.tray_icon.show_notification(
                        "New Update Available!",
                        f"A new version of MoniTune (v{latest_version}) is ready! Click here to download.",
                        QIcon(cfg.app_icon_path),
                        on_click_callback=lambda: webbrowser.open(cfg.LATEST_RELEASE_URL)
                    )

        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.bottom_frame.setStyleSheet("background-color: green;") 
        # self.openSettingsWindow() # Open settings window on startup



    # MARK: _on_lock_state_change()
    def _on_lock_state_change(self, state: str):
        print(f"State changed to: {state}")
        if state == "unlocked":
            print("Screen unlocked at:", QTime.currentTime().toString("HH:mm"))
            self.execute_recent_task(delay=10 * 1000) # Execute after 10 seconds  
            self.start_checking()

        elif state == "locked":
            print("Screen locked at:", QTime.currentTime().toString("HH:mm"))
            self.stop_checking()


    # MARK: stop_checking()
    def stop_checking(self):
        self.timer.stop()
        print("Task checking stopped")

    # MARK: start_checking()
    def start_checking(self, interval=60000):
        self.last_check_time = QDateTime.currentDateTime()
        self.timer.start(interval)
        print("Task checking started")


    # MARK: check_all_tasks()
    def check_all_tasks(self):
        current_time = QTime.currentTime().toString("HH:mm")
        current_datetime = QDateTime.currentDateTime()
        print(f"Checking tasks at: {current_time}")
        # print(f"self.time_adjustment_data {self.time_adjustment_data}")


        # Monitor connected monitors
        current_screeninfo = screeninfo.get_monitors()

        previous_serials = {monitor.name for monitor in self.previous_screeninfo}
        current_serials = {monitor.name for monitor in current_screeninfo}

        added_monitors = current_serials - previous_serials
        removed_monitors = previous_serials - current_serials

        if added_monitors:
            print(f"New monitors added: {added_monitors}")
            # QTimer.singleShot(10000, lambda: self.execute_recent_task(delay=10000))
            QTimer.singleShot(10 * 1000, self.execute_recent_task)
        if removed_monitors:
            print(f"Monitors removed: {removed_monitors}")
        # if not added_monitors and not removed_monitors:
        #     print("No changes in connected monitors.")

        self.previous_screeninfo = current_screeninfo


        # MARK: Check time adjustment tasks
        if not added_monitors:
            if current_time in self.time_adjustment_data:
                self.apply_brightness(self.time_adjustment_data[current_time])
            else:
                print("No tasks at this time")
        else:
            print("Skipped time adjustment tasks due to new monitor(s)")

        self.last_check_time = current_datetime


        # MARK: Check idle time for break reminders
        if not self.enable_break_reminders:
            self.time_active = 0
            self.saved_time = 0
        else:
            idle_time = get_idle_time()
            if idle_time is not None:
                print(f"idle_time: {idle_time:.2f} sec")

                if idle_time > 5 * 60:
                    print("idle 5min, reset time_active")
                    self.time_active = 0
                    self.saved_time = 0
                elif idle_time < cfg.timer_interval * 1.0:
                    self.time_active += cfg.timer_interval
                    self.time_active += self.saved_time
                    self.saved_time = 0

                    if self.time_active >= cfg.break_notification_interval * 60:
                        print("show break notification")
                        self.break_notification()
                        self.time_active = 0
                else:
                    self.saved_time += cfg.timer_interval

                print(f"time_active: {self.time_active / 60} min, saved_time: {self.saved_time / 60} min")
        


    # MARK: execute_recent_task()
    def execute_recent_task(self, delay=0):
        if not self.time_adjustment_data:
            print("execute_recent_task: No tasks found")
            print("Restoring last change")
            self.apply_brightness(self.brightness_values, delay=delay)
            return

        current_time = QTime.currentTime().toString("HH:mm")
        past_tasks = [time for time in self.time_adjustment_data.keys() if time <= current_time]
        if past_tasks:
            recent_task_time = max(past_tasks)
            print(f"Executing recent task at: {recent_task_time}")
            self.apply_brightness(self.time_adjustment_data[recent_task_time], delay=delay)
        else:
            print("No past tasks to execute for today, checking previous day")
            if self.time_adjustment_data:
                recent_task_time = max(self.time_adjustment_data.keys())
                print(f"Executing last task from previous day at: {recent_task_time}")
                self.apply_brightness(self.time_adjustment_data[recent_task_time], delay=delay)
    


    # MARK: apply_brightness()
    def apply_brightness(self, brightness_data, delay=0):
        print(f"apply_brightness: {brightness_data}, delay: {delay / 1000} sec")
        
        self.update_monitors_info()
        for serial in self.monitors_dict:
            if serial in brightness_data:
                self.brightness_values[serial] = brightness_data[serial]

        # play slider animation if window is open
        if self.window_open and (delay == 0):
            QTimer.singleShot(0, lambda: self.animate_sliders(self.br_sliders, self.brightness_values))
        else:
            threading.Timer((delay / 1000), self.brightness_sync_onetime).start() # change brightness after delay



    # MARK: check_for_update()
    def check_for_update(self):
        try:
            response = requests.get(cfg.UPDATE_CHECK_URL)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = Version(latest_release["tag_name"].lstrip("v"))
                current_version = Version(cfg.version)

                # Compare versions
                if latest_version > current_version:
                    print(f"New version available: {latest_version}. Current version: {current_version}.")
                    return True, latest_version
                else:
                    print(f"Current version {current_version} is up to date.")
                    return False, latest_version
            else:
                print(f"Error fetching release data: {response.status_code}")
                return False, None
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False, None

    # MARK: break_notification()
    def break_notification(self):
        self.tray_icon.show_notification(
            "Take a break from the screen!",
            "Look at least 6 meters away from the screen for 20 seconds.",
            QIcon(self.eye_icon_path)
        )



    # MARK: update_monitors_info()
    def update_monitors_info(self):
        monitors_info = get_monitors_info()

        # Exclude monitors that are in self.hidden_displays
        monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in self.hidden_displays]
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        self.monitors_dict = monitors_dict
        # print(f"self.monitors_dict {self.monitors_dict}")



    # MARK: update_central_widget()
    def update_central_widget(self):
        self.window_offset = cfg.WIN11_WINDOW_OFFSET if self.enable_rounded_corners else 0
        corner_radius = cfg.WIN11_WINDOW_CORNER_RADIUS if self.enable_rounded_corners else 0
        self.centralWidget().setStyleSheet(
            f"""
            #Container {{
            background: {self.bg_color};
            border-radius: {corner_radius}px;
            border: 1px solid {self.border_color};
            }}
            """
        )


    # MARK: update_theme_colors()
    def update_theme_colors(self, theme: str):
        if theme == "Light" or (self.win_release != "11" and not self.enable_fusion_theme):
            # colors for light theme
            self.bg_color = cfg.bg_color_light
            self.border_color = cfg.border_color_light
            self.fr_color = cfg.fr_color_light  
            self.fr_border_color = cfg.fr_border_color_light
            self.rr_border_color = cfg.rr_border_color_light
            self.rr_fg_color = cfg.rr_fg_color_light
            self.rr_hover_color = cfg.rr_hover_color_light
            self.separator_color = cfg.separator_color_light

            # icons
            self.settings_icon_path = cfg.settings_icon_light_path
            self.monitor_icon_path = cfg.monitor_icon_light_path
            self.laptop_icon_path = cfg.laptop_icon_light_path
            self.sun_icon_path = cfg.sun_icon_light_path
            self.down_arrow_icon_path = cfg.down_arrow_icon_light_path
            self.eye_icon_path = cfg.eye_icon_light_path
            self.contrast_icon_path = cfg.contrast_icon_light_path
            self.link_icon_path = cfg.link_icon_light_path
        else:
            # colors for dark theme
            self.bg_color = cfg.bg_color_dark
            self.border_color = cfg.border_color_dark
            self.fr_color = cfg.fr_color_dark  
            self.fr_border_color = cfg.fr_border_color_dark
            self.rr_border_color = cfg.rr_border_color_dark
            self.rr_fg_color = cfg.rr_fg_color_dark
            self.rr_hover_color = cfg.rr_hover_color_dark
            self.separator_color = cfg.separator_color_dark

            # icons
            self.settings_icon_path = cfg.settings_icon_dark_path
            self.monitor_icon_path = cfg.monitor_icon_dark_path
            self.laptop_icon_path = cfg.laptop_icon_dark_path
            self.sun_icon_path = cfg.sun_icon_dark_path
            self.down_arrow_icon_path = cfg.down_arrow_icon_dark_path
            self.eye_icon_path = cfg.eye_icon_dark_path
            self.contrast_icon_path = cfg.contrast_icon_dark_path
            self.link_icon_path = cfg.link_icon_dark_path

        # print("Checking MEIPASS contents:")
        # print(os.listdir(sys._MEIPASS))



    # MARK: _apply_theme()
    def _apply_theme(self, theme: str):
        print(f"Theme changed to: {theme}")
        self.theme = theme
        self.update_theme_colors(theme)
        self.update_central_widget()
        self.tray_icon.changeIconTheme(theme)
        if self.settings_window:
            self.settings_window.theme = theme
            self.settings_window.updateLayout()



    # MARK: eventFilter()
    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        # hide window when focus is lost
        if event.type() == QEvent.Type.WindowDeactivate:
            # self.hide()
            self.animateWindowClose()
            return True
        
        # Handle scroll events on the bottom frame
        if source == self.bottom_frame and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            self.on_bottom_frame_scroll(delta)
            return True
        
        # Handle right mouse button click on bottom_frame
        if source == self.bottom_frame and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.RightButton:
                print("Right mouse button clicked on bottom frame")
                return True
        
        return super().eventFilter(source, event)



    # MARK: updateMonitorsFrame()
    def updateMonitorsFrame(self):
        
        start_time = time.time()


        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.br_sliders.clear()  # Clear brightness sliders dictionary
        self.contrast_sliders.clear()  # Clear contrast sliders dictionary



        self.update_monitors_info()
        print_mi(self.monitors_dict)

        # placeholder if no monitors are available (or all are hidden)
        if not self.monitors_dict:  # Check if no monitors are available
            placeholder_frame = QWidget()
            placeholder_frame.setObjectName("EmptyPlaceholder")
            placeholder_frame.setStyleSheet(
                f"""
                #EmptyPlaceholder {{
                background: {self.fr_color};
                border-radius: {6 if self.enable_rounded_corners else 0}px;
                border: 1px solid {self.fr_border_color}; 
                }}
                """
            )
            placeholder_layout = QVBoxLayout(placeholder_frame)
            placeholder_layout.setContentsMargins(14, 12, 14, 14)
            # placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            placeholder_label = QLabel(
                'No compatible displays found. '
                'Please check that "DDC/CI" is enabled for your displays, '
                'or make sure the monitors are not currently hidden.'
            )
            placeholder_label.setWordWrap(True)
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            placeholder_label.setSizePolicy(QSizePolicy.Policy.Preferred, 
                                            QSizePolicy.Policy.MinimumExpanding)
            placeholder_label.setStyleSheet("""
                                            font-size: 16px;
                                            font-weight: bold;
                                            """)
            placeholder_layout.addWidget(placeholder_label)

            self.monitors_layout.addWidget(placeholder_frame)

            return


        
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.monitors_order if serial in self.monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [serial for serial in self.monitors_dict if serial not in monitors_order]
        print(f"monitors_order: {monitors_order}")




        # print monitors order for testing
        print("monitors order:")
        for monitor_serial in self.monitors_order:
            if monitor_serial in self.monitors_dict:
                monitor_name = self.custom_monitor_names.get(monitor_serial, self.monitors_dict[monitor_serial]['display_name'])
                print(f"  {monitor_name} ({monitor_serial})")




        for index, monitor_serial in enumerate(monitors_order):

            monitor = self.monitors_dict[monitor_serial]
            # print(f"monitor {monitor}")

            monitor_frame = QWidget()
            monitor_frame.setObjectName("MonitorsFrame")
            monitor_frame.setStyleSheet(
                f"""
                #MonitorsFrame {{
                background: {self.fr_color};
                border-radius: {6 if self.enable_rounded_corners else 0}px;
                border: 1px solid {self.fr_border_color}; 
                }}
                """
            )
            monitor_vbox = QVBoxLayout(monitor_frame)
            monitor_vbox.setSpacing(5)  # Spacing between monitor frames
            monitor_vbox.setContentsMargins(7, 7, 7, 7)
            

            # MARK: Monitor Label
            label_frame = QWidget()
            # label_frame.setMinimumHeight(34)
            # label_frame.setFixedHeight(34)
            label_hbox = QHBoxLayout(label_frame)
            label_hbox.setContentsMargins(0, 0, 0, 0)
            label_hbox.setSpacing(6)

            # Add monitor icon
            monitor_icon = QLabel()
            # monitor_icon.setStyleSheet("""background-color: blue;""")
            icon_size = 30
            if (monitor["Device"] == "\\\\.\\DISPLAY1") and self.is_laptop:
                monitor_icon.setPixmap(QIcon(self.laptop_icon_path).pixmap(26, 26))
            else:
                monitor_icon.setPixmap(QIcon(self.monitor_icon_path).pixmap(icon_size, icon_size))
            monitor_icon.setFixedSize(icon_size, icon_size)
            monitor_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_hbox.addWidget(monitor_icon)


            monitor_label_text = self.custom_monitor_names[monitor_serial] if monitor_serial in self.custom_monitor_names else monitor["display_name"]
            monitor_label = QLabel(monitor_label_text)
            # monitor_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            # monitor_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
            # monitor_label.setFixedHeight(80)
            monitor_label.setStyleSheet(f"""
                                        font-size: 16px; font-weight: bold;

                                        

                                        
                                        """) # padding-left: 1px; background-color: blue; padding-bottom: 2px; font-size: 16px; font-weight: bold; font: 16px "{cfg.font_family}";
            label_hbox.addWidget(monitor_label)
            
            
            if self.show_resolution:
                available_resolutions = monitor["AvailableResolutions"]
                sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
                formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]
                
                res_combobox = NoScrollComboBox()
                absolute_icon_path = os.path.abspath(self.down_arrow_icon_path).replace('\\', '/')
                res_combobox.setStyleSheet(f"""
                                            /* Basic QComboBox style */
                                            QComboBox {{
                                                font-size: 14px; font-weight: bold;
                                                padding-left: 7px;
                                                {"background-color: " + self.rr_fg_color + ";" if not self.enable_fusion_theme else ""}
                                            }}
                                            /* Dropdown list style */
                                            QComboBox QAbstractItemView {{
                                                padding: 0px;
                                            }}
                                            QComboBox::drop-down {{
                                                border: 0px;
                                            }}
                                            QComboBox::down-arrow {{
                                                image: url('{absolute_icon_path}');
                                                width: 11px;
                                                height: 11px;
                                                margin-right: 10px;
                                                }}
                                            """)
                
                max_res_length = max(len(res) for res in formatted_resolutions)
                res_combobox_width = 105 if max_res_length <= 9 else 112 if max_res_length == 10 else 120
                res_combobox.setFixedWidth(res_combobox_width)
                res_combobox.setSizePolicy(QSizePolicy.Policy.Fixed, 
                                           QSizePolicy.Policy.Expanding)
                res_combobox.addItems(formatted_resolutions)
                res_combobox.setCurrentText(monitor["Resolution"])
                res_combobox.currentIndexChanged.connect(lambda index, 
                                                         m=monitor, 
                                                         cb=res_combobox: 
                                                         self.on_resolution_select(m, cb.currentText()))
                label_hbox.addWidget(res_combobox)


            monitor_vbox.addWidget(label_frame)
            



            # MARK: Refresh Rates
            if self.show_refresh_rates:

                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=self.separator_color))
                
                refresh_rates = monitor["AvailableRefreshRates"]
                refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]

                if len(refresh_rates) >= 2:
                    rr_frame = QWidget()
                    rr_grid = QGridLayout(rr_frame)
                    rr_grid.setContentsMargins(0, 0, 0, 0)
                    rr_grid.setSpacing(0)

                    self.rr_buttons[monitor_serial] = []  # Initialize list for this monitor

                    num_columns = 6
                    for idx, rate in enumerate(refresh_rates):
                        rr_button = RRButton(f"{rate} Hz")
                        if rate == monitor["RefreshRate"]:
                            rr_button.setChecked(True)
                        rr_button.clicked.connect(lambda checked, 
                                                  r=rate, 
                                                  m=monitor, 
                                                  btn=rr_button: 
                                                  self.on_rr_button_clicked(r, m, btn))
                        

                        row = idx // num_columns
                        col = idx % num_columns
                        
                        rr_grid.addWidget(rr_button, row, col)

                        self.rr_buttons[monitor_serial].append(rr_button)  # Store button

                    monitor_vbox.addWidget(rr_frame)

                    
            
            # MARK: Brightness
            if monitor["method"] == "VCP":
                br_level = get_brightness_vcp(monitor["hPhysicalMonitor"], retries=5)
            else:
                br_level = get_brightness_sbc(display=monitor['serial'])

            if br_level is None:
                print(f"Brightness level is None for monitor {monitor['serial']}")
                br_level = self.brightness_values.get(monitor["serial"], 50)
                monitor_frame.setDisabled(True)  # Disable the entire monitor frame if brightness is None

            # Add separator line
            monitor_vbox.addWidget(SeparatorLine(color=self.separator_color))

            if self.restore_last_brightness and (monitor['serial'] in self.brightness_values):
                pass
            else:
                self.brightness_values[monitor['serial']] = br_level

            br_frame = SliderFrame(
                parent=self,
                icon_path=self.sun_icon_path,
                slider_value=br_level,
                slider_callback=lambda value, ms=monitor_serial: self.on_brightness_change(value, ms),
                label_text=br_level
            )

            self.br_sliders[monitor['serial']] = br_frame.slider  # Store slider in dictionary

            monitor_vbox.addWidget(br_frame)


            # MARK: Contrast
            if self.show_contrast_sliders and (monitor["method"] == "VCP"):
                contrast_level = None
                if monitor_frame.isEnabled(): # check contrast only if monitor is enabled
                    contrast_level = get_contrast_vcp(monitor["hPhysicalMonitor"], 
                                                    retries=5)
                print(f"contrast_level {monitor['serial']} {contrast_level}")
                
                if contrast_level is None:
                    print(f"Contrast level is None for monitor {monitor['serial']}")
                    contrast_level = self.contrast_values.get(monitor["serial"], 50)
                    monitor_frame.setDisabled(True)  # Disable the entire monitor frame

                # self.contrast_values[monitor_serial] = contrast_level # dont change contrast
                
                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=self.separator_color))

                contrast_frame = SliderFrame(
                    parent=self,
                    icon_path=self.contrast_icon_path,
                    slider_value=contrast_level,
                    slider_callback=lambda value, ms=monitor_serial: self.on_contrast_change(value, ms),
                    label_text=contrast_level
                )

                self.contrast_sliders[monitor['serial']] = contrast_frame.slider  # Store slider in dictionary

                monitor_vbox.addWidget(contrast_frame)


            self.monitors_layout.addWidget(monitor_frame)


            # QTimer.singleShot(0, lambda: print("br_label width:", br_label.width())) # Print width of br_label after the layout is updated

            # label_frame.setStyleSheet("background-color: red")
            # if self.show_refresh_rates: rr_frame.setStyleSheet("background-color: green")
            # br_frame.setStyleSheet("background-color: blue")
            # br_slider.setStyleSheet("background-color: red")


        print(f"self.brightness_values {self.brightness_values}")
        print(f"self.contrast_values {self.contrast_values}")

        print(f"updateMonitorsFrame took {time.time() - start_time:.4f} seconds")

    
    
    # MARK: updateBottomFrame()
    def updateBottomFrame(self):
        print("updateBottomFrame count ", self.bottom_hbox.count())

        start_time = time.time()

        # Clear old widgets
        while self.bottom_hbox.count():
            child = self.bottom_hbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


        name_title = QLabel("Scroll to adjust brightness")
        name_title.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 padding-bottom: 2px;

                                 """) # padding-left: 5px; background-color: blue;
        
        self.link_br_btn = QPushButton()
        self.link_br_btn.setCheckable(True)
        self.link_br_btn.setChecked(self.link_brightness)
        self.link_br_btn.setFixedWidth(41) # 39
        self.link_br_btn.setFixedHeight(39)
        # self.link_br_btn.setIcon(QIcon(self.link_icon_path))
        self.link_br_btn.setIcon(self.get_link_icon())
        self.link_br_btn.setIconSize(QSize(21, 21))
        self.link_br_btn.toggled.connect(self.toggle_link_brightness)

        settings_button = QPushButton()
        settings_button.setFixedWidth(41) # 39
        settings_button.setFixedHeight(39)
        settings_button.setIcon(QIcon(self.settings_icon_path))
        settings_button.setIconSize(QSize(21, 21))
        settings_button.clicked.connect(self.openSettingsWindow)

        self.bottom_hbox.addWidget(name_title)
        self.bottom_hbox.addWidget(self.link_br_btn)
        self.bottom_hbox.addWidget(settings_button)

        print(f"updateBottomFrame took {time.time() - start_time:.4f} seconds")


    # MARK: toggle_link_brightness()
    def toggle_link_brightness(self, checked):
        self.link_brightness = checked
        self.link_br_btn.setIcon(self.get_link_icon())
        reg_write_bool(cfg.REGISTRY_PATH, "LinkBrightness", checked)
        print(f"Link brightness is now {'on' if checked else 'off'}")


    # MARK: get_link_icon()
    def get_link_icon(self):
        if self.enable_fusion_theme:
            icon_path = cfg.link_icon_light_path if self.theme == "Light" else cfg.link_icon_dark_path
        else:
            if self.theme == "Light":
                icon_path = cfg.link_icon_dark_path if self.link_brightness else cfg.link_icon_light_path
            else:
                icon_path = cfg.link_icon_light_path if self.link_brightness else cfg.link_icon_dark_path
        return QIcon(icon_path)



    # MARK: on_rr_button_clicked()
    def on_rr_button_clicked(self, rate, monitor, button: RRButton):
        print(f"Selected refresh rate: {rate} Hz for monitor {monitor["serial"]}")
        # print(monitor)

        self.update_monitors_info()
        updated_monitor = self.monitors_dict.get(monitor["serial"], None)

        if not updated_monitor:
            print(f"Monitor {monitor['Device']} not found")
            button.setChecked(False)
            return
        
        if updated_monitor and (updated_monitor["RefreshRate"] == rate):
            print(f"Monitor {monitor['Device']} already has refresh rate {rate} Hz")
            return

        # save brightness and contrast before changing refresh rate
        brightness_before = None
        contrast_before = None
        serial = monitor["serial"]
        method = self.monitors_dict[serial]["method"]

        # get brightness before changing refresh rate
        if serial in self.brightness_values:
            brightness_before = self.brightness_values[serial]
        else:
            if method == "VCP":
                brightness_before = get_brightness_vcp(monitor["hPhysicalMonitor"], retries=7)
            else:
                brightness_before = get_brightness_sbc(serial)
        # get contrast before changing refresh rate
        if (method == "VCP") and self.show_contrast_sliders:
            if serial in self.contrast_values:
                contrast_before = self.contrast_values[serial]
            else:
                contrast_before = get_contrast_vcp(monitor["hPhysicalMonitor"], retries=7)

        #restore brightness and contrast after 6 seconds
        def restore_parameters():
            print(f"restore_parameters {monitor['serial']}: {brightness_before}, {contrast_before}")
            if brightness_before is not None:
                self.brightness_values[monitor['serial']] = brightness_before
            if contrast_before is not None:
                self.contrast_values[monitor['serial']] = contrast_before
            self.brightness_sync_onetime()
            
        if not set_refresh_rate(monitor, rate): # set refresh rate
            button.setChecked(False)
        else:
            threading.Timer(6, restore_parameters).start()
            # QTimer.singleShot(6000, restore_parameters)

            # disable all other buttons for this monitor
            for btn in self.rr_buttons[serial]:
                if btn != button:
                    btn.setChecked(False)



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor, resolution):
        print(f"on_resolution_select {monitor['serial']} {resolution}")
        
        width, height = map(int, resolution.split('x'))
        set_resolution(monitor["Device"], width, height)
        
        QTimer.singleShot(500, self.updateSizeAndPosition)


    # MARK: on_brightness_change()
    def on_brightness_change(self, value, monitor_serial):
        # print(f"on_brightness_change: {value}, {monitor_serial}")

        if self.link_brightness:
            previous_value = self.brightness_values.get(monitor_serial, 0)
            change = value - previous_value
            print(f"Brightness change for {monitor_serial}: {change}")

            for serial, slider in self.br_sliders.items():
                if (serial != monitor_serial) and slider.isEnabled():
                    new_value = max(0, min(100, (slider.value() + change)))
                    slider.setValueBS(int(new_value))
                    self.brightness_values[serial] = int(new_value)

        self.brightness_values[monitor_serial] = int(value)

    # MARK: on_contrast_change()
    def on_contrast_change(self, value, monitor_serial):
        # print(f"on_contrast_change: {value}, {monitor_serial}")
        self.contrast_values[monitor_serial] = int(value)

    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, delta):
        # print("on_bottom_frame_scroll ", delta)

        link_brightness_save = self.link_brightness
        self.link_brightness = False  # Disable linking temporarily

        for slider in self.br_sliders.values():
            new_value = max(0, min(100, slider.value() + (1 if delta > 0 else -1)))
            slider.setValue(new_value)
        
        self.link_brightness = link_brightness_save  # Restore linking state

    # MARK: brightness_sync()
    def brightness_sync(self):
        # self.update_monitors_info()

        previous_brightness_values = {}
        previous_contrast_values = {}

        while self.window_open:
            # start_time = time.time()
            
            brightness_values_copy = self.brightness_values.copy()
            for monitor_serial, brightness in brightness_values_copy.items():
                if (monitor_serial in self.monitors_dict) and ( # check if monitor is connected
                    previous_brightness_values.get(monitor_serial) != brightness # check if brightness changed
                ):
                    try:
                        if self.monitors_dict[monitor_serial]["method"] == "VCP":
                            if not set_brightness_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                               brightness, 
                                               retries=1):
                                raise Exception(f"Failed to set brightness for monitor {monitor_serial}")
                            
                            print(f"brightness_sync set_brightness_vcp {monitor_serial} {brightness}")
                        else:
                            set_brightness_sbc(monitor_serial, brightness)
                            print(f"brightness_sync set_brightness {monitor_serial} {brightness}")

                        previous_brightness_values[monitor_serial] = brightness
                        reg_write_dict(cfg.REGISTRY_PATH, "BrightnessValues", self.brightness_values)

                    except Exception as e:
                        print(f"Error: {e}")
            
            if self.show_contrast_sliders:
                contrast_values_copy = self.contrast_values.copy()
                for monitor_serial, contrast in contrast_values_copy.items():
                    if (monitor_serial in self.monitors_dict) and ( # check if monitor is connected
                        previous_contrast_values.get(monitor_serial) != contrast # check if contrast changed
                    ):
                        try:
                            if not set_contrast_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                                    contrast, 
                                                    retries=1):
                                raise Exception(f"Failed to set contrast for monitor {monitor_serial}")
                            
                            print(f"brightness_sync set_contrast_vcp {monitor_serial} {contrast}")

                            previous_contrast_values[monitor_serial] = contrast
                            reg_write_dict(cfg.REGISTRY_PATH, "ContrastValues", self.contrast_values)

                        except Exception as e:
                            print(f"Error: {e}")


            # print(f"Brightness sync took {time.time() - start_time:.4f} seconds")

            time.sleep(0.10) # 0.15


    # MARK: brightness_sync_onetime()
    def brightness_sync_onetime(self):
        print("brightness_sync_onetime")
        start_time = time.time()
        # self.update_monitors_info()

        brightness_values_copy = self.brightness_values.copy()
        # print(f"brightness_values_copy {brightness_values_copy}")
        for monitor_serial, brightness in brightness_values_copy.items():
            if monitor_serial in self.monitors_dict:  # Check if monitor is connected
                try:
                    if self.monitors_dict[monitor_serial]["method"] == "VCP":
                        if not set_brightness_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                           brightness, 
                                           retries=5):
                            raise Exception(f"Failed to set brightness for monitor {monitor_serial}")

                        print(f"brightness_sync_onetime set_brightness_vcp {monitor_serial} {brightness}")
                    else:
                        set_brightness_sbc(monitor_serial, brightness)
                        print(f"brightness_sync_onetime set_brightness {monitor_serial} {brightness}")

                except Exception as e:
                    print(f"Error: {e}")
        
        if self.show_contrast_sliders:
            contrast_values_copy = self.contrast_values.copy()
            for monitor_serial, contrast in contrast_values_copy.items():
                if monitor_serial in self.monitors_dict: # Check if monitor is connected
                    try:
                        if not set_contrast_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                         contrast, 
                                         retries=5):
                            raise Exception(f"Failed to set contrast for monitor {monitor_serial}")
                        
                        print(f"brightness_sync_onetime set_contrast_vcp {monitor_serial} {contrast}")

                    except Exception as e:
                        print(f"Error: {e}")

        print(f"brightness_sync_onetime took {time.time() - start_time:.4f} seconds")


    # MARK: showEvent()
    def showEvent(self, event):
        print("showEvent")

        self.updateBottomFrame() # Update bottom frame contents each time the window is shown
        self.updateMonitorsFrame()  # Update frame contents each time the window is shown
        
        # hide window to avoid flickering before opening animation (when close animation disabled)
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(screen_geometry.width(), screen_geometry.height())

        QTimer.singleShot(0, self.animateWindowOpen)
        # QTimer.singleShot(0, self.updateSizeAndPosition)

        self.activateWindow()
        self.raise_()
        
        self.window_open = True
        if self.brightness_sync_thread is None or not self.brightness_sync_thread.is_alive():
            print("brightness_sync_thread start")
            # self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
            # self.brightness_sync_thread.start()
            QTimer.singleShot(250, self.start_brightness_sync_thread) 

            # self.brightness_sync_thread = threading.Timer(0.25, self.brightness_sync)
            # self.brightness_sync_thread.daemon = True
            # self.brightness_sync_thread.start()
            # print("brightness_sync_thread started")
        else:
            print("brightness_sync_thread is already running")

        super().showEvent(event)

        if self.restore_last_brightness:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.br_sliders, self.brightness_values))
        if self.show_contrast_sliders:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.contrast_sliders, self.contrast_values))


    # MARK: animate_sliders()
    def animate_sliders(self, sliders, values):
        for index, (serial, slider) in enumerate(sliders.items()):
            if serial in values:
                print(f"animate_sliders {serial} {values[serial]}")
                # QTimer.singleShot(index * 100, lambda s=slider: s.animate_to(int(values[serial])))
                slider.animate_to(int(values[serial]))


    # MARK: start_brightness_sync_thread()
    def start_brightness_sync_thread(self):
        print("brightness_sync_thread started")
        self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
        self.brightness_sync_thread.start()



    # MARK: hideEvent()
    def hideEvent(self, event):
        print("hideEvent")
        self.window_open = False
        self.stop_brightness_sync_thread()
        # QTimer.singleShot(2000, self.stop_brightness_sync_thread)  # Add 2-second delay
        # QTimer.singleShot(1000, self.brightness_sync_onetime)
        super().hideEvent(event)


    # MARK: stop_brightness_sync_thread()
    def stop_brightness_sync_thread(self):
        if self.brightness_sync_thread and self.brightness_sync_thread.is_alive():
            # print("brightness_sync_thread.join()")
            self.brightness_sync_thread.join()  # Stop brightness sync thread
            if not self.brightness_sync_thread.is_alive():
                print("thread is dead")
            else:
                print("thread is still alive")
        else:
            print("brightness_sync_thread is not running")


    # MARK: updateSizeAndPosition()
    def updateSizeAndPosition(self):
        print("updateSizeAndPosition sizeHint:", self.sizeHint().height(), "self.height()", self.height())
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - self.window_offset, 
                  screen_geometry.height() - self.sizeHint().height() - self.window_offset)
        self.resize(self.width(), self.sizeHint().height())



    # MARK: animateWindowOpen()
    def animateWindowOpen(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        start_rect = QRect(screen_geometry.width(), 
                           screen_geometry.height() - self.sizeHint().height() - self.window_offset, 
                           self.width(), 
                           self.sizeHint().height()
                           )
        end_rect = QRect(screen_geometry.width() - self.width() - self.window_offset, 
                         screen_geometry.height() - self.sizeHint().height() - self.window_offset, 
                         self.width(), 
                         self.sizeHint().height()
                         )

        print("self.width()", self.width(), "self.height()", self.sizeHint().height())

        self.open_animation = QPropertyAnimation(self, b"geometry") 
        self.open_animation.setStartValue(start_rect)
        self.open_animation.setEndValue(end_rect)
        # self.open_animation.setDuration(300)
        self.open_animation.setDuration(300)
        # self.open_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.open_animation.setEasingCurve(QEasingCurve.Type.OutExpo)

        self.open_opacity_effect = QGraphicsOpacityEffect(self)   
        self.setGraphicsEffect(self.open_opacity_effect)
        self.open_opacity_animation = QPropertyAnimation(self.open_opacity_effect, b"opacity")
        self.open_opacity_animation.setDuration(300)
        # self.open_opacity_animation.setDuration(275)
        self.open_opacity_animation.setStartValue(0)
        self.open_opacity_animation.setEndValue(1)
        # self.open_opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.open_opacity_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        self.open_animation.start()
        self.open_opacity_animation.start()

    # MARK: animateWindowClose()
    def animateWindowClose(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        current_rect = self.geometry()
        end_rect = QRect(screen_geometry.width(), 
                         screen_geometry.height() - self.sizeHint().height() - self.window_offset, 
                         self.width(), 
                         self.sizeHint().height()
                         )
        
        self.close_animation = QPropertyAnimation(self, b"geometry") 
        self.close_animation.setStartValue(current_rect)
        self.close_animation.setEndValue(end_rect)
        # self.close_animation.setDuration(300)
        self.close_animation.setDuration(250)
        # self.close_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.close_animation.setEasingCurve(QEasingCurve.Type.InExpo)
        
        self.close_opacity_effect = QGraphicsOpacityEffect(self)  
        self.setGraphicsEffect(self.close_opacity_effect)
        self.close_opacity_animation = QPropertyAnimation(self.close_opacity_effect, b"opacity")
        self.close_opacity_animation.setDuration(250)
        self.close_opacity_animation.setStartValue(1)
        self.close_opacity_animation.setEndValue(0)
        # self.close_opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.close_opacity_animation.setEasingCurve(QEasingCurve.Type.InExpo)
        
        self.close_animation.finished.connect(self.hide) # hide window after animation is done
        self.close_animation.start()
        self.close_opacity_animation.start()
        


    # MARK: openSettingsWindow()
    def openSettingsWindow(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        elif self.settings_window.isMinimized():
            self.settings_window.showNormal()
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()



# MARK: main
if __name__ == "__main__":

    # Check if another instance is already running
    if getattr(sys, 'frozen', False):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex = kernel32.CreateMutexW(None, False, "MoniTune-Qt")
        if not mutex: # Error creating mutex
            print(f"Error code: {ctypes.get_last_error()}")
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS (mutex already exists)
            print("Another instance is already running")
            sys.exit(1)

    app = QApplication([])

    # print(QStyleFactory.keys()) # ['windows11', 'windowsvista', 'Windows', 'Fusion']
    # app.setStyle("windows11")
    print(f"Current style: {app.style().objectName()}")


    window = MainWindow()

    if not getattr(sys, 'frozen', False): # if run from source code
        # window.openSettingsWindow()
        window.show()

    app.exec()