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
    QWheelEvent,
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
    QSizePolicy,
    QMessageBox
)

from system_tray_icon import SystemTrayIcon
from settings_window import SettingsWindow 

from custom_widgets import (
    CheckLockButton,
    HoverIconButton,
    NoScrollComboBox,
    StyledComboBox,
    BrightnessIcon,
    AnimatedSliderBS,
    SeparatorLine,
)

from utils.monitor_utils import (
    get_monitors_info, 
    get_monitor_list,
    print_mi, 
    set_resolution, 
    set_refresh_rate, 
    get_brightness_sbc, 
    set_brightness_sbc, 
    get_brightness_vcp, 
    set_brightness_vcp, 
    get_contrast_vcp, 
    set_contrast_vcp, 
    get_power_mode_vcp,
    set_power_mode_vcp,
)
from utils.reg_utils import (
    reg_write_bool, 
    reg_read_bool, 
    reg_write_list, 
    reg_read_list, 
    reg_write_dict, 
    reg_read_dict,
    add_to_startup,
    remove_from_startup,
)
from utils.utils import get_idle_time, is_laptop, is_on_battery, get_display_timeouts
from utils.lock_detect import LockDetect

from utils.logger import get_logger
logger = get_logger(__name__) # debug, info, warning, error, critical

import config as cfg

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



# MARK: ButtonGridFrame
class ButtonGridFrame(QFrame):
    def __init__(self, parent, values, active_value, callback=None):
        super().__init__(parent)

        self.parent = parent
        self.values = values
        self.active_value = active_value
        self.callback = callback

        self.buttons = []

        self.setObjectName("ButtonGridFrame")
        # self.setStyleSheet(f"""
        #     #ButtonGridFrame {{
        #         background-color: gray;
        #         border-radius: 6px;
        #     }}
        # """)

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)

        num_columns = 6
        for idx, value in enumerate(values):
            button = CheckLockButton(f"{value} Hz")
            button.setMinimumWidth(55)
            button.setFixedHeight(28) # 26
            if value == self.active_value:
                button.setChecked(True)
            button.clicked.connect(lambda checked, 
                                   r=value, 
                                   btn=button: 
                                   self.on_button_click(r, btn))
            
            row = idx // num_columns
            col = idx % num_columns
            
            self.grid.addWidget(button, row, col)

            self.buttons.append(button)  # Store button

    # MARK: on_button_click()
    def on_button_click(self, value, button):
        logger.info(f"Button clicked: {value}")

        callback_result = self.callback(value)

        if callback_result:
            # disable all other buttons for this monitor
            for btn in self.buttons:
                if btn != button:
                    btn.setChecked(False)
        else:
            button.setChecked(False)  # Revert the button state if callback fails
            # button.setStyleSheet("background-color: #ff3232;")
            # button.setStyleSheet(f"""
            #     QPushButton {{
            #         background-color: #ff4545;
            #     }}
            #     """)
            button.setToolTip("Failed to set refresh rate")
            button.setDisabled(True)



# MARK: SliderFrame
class SliderFrame(QFrame):
    def __init__(self, parent, icon_path, value, slider_callback=None):
        super().__init__(parent)

        self.parent = parent

        self.bg_color = 'transparent'
        self.border_radius = 6

        self.setObjectName("SliderFrame")
        # self.setStyleSheet(f"""
        #     #SliderFrame {{
        #         background-color: transparent;
        #         border-radius: 6px;
        #     }}
        #     #SliderFrame:hover {{
        #         background-color: {'rgba(0, 0, 0, 0.03)' if self.parent.theme == "Light" else 'rgba(255, 255, 255, 0.03)'};
        #         border-radius: 6px;
        #     }}
        # """)

        self.slider_callback = slider_callback

        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(0, 0, 2, 0)
        self.hbox.setSpacing(0)

        self.icon = BrightnessIcon(icon_path=icon_path)
        self.icon.set_value(value)
        # self.icon.setStyleSheet(f"""
        #                          background-color: green;
                                
        #                          """)
        
        self.slider = AnimatedSliderBS(Qt.Orientation.Horizontal, 
                                       scrollStep=1, # step when scrolling with mouse wheel
                                       singleStep=1, # step when pressing arrow keys
                                       pageStep=10) # step when pressing page up/down keys
        self.slider.setRange(0, 100)
        self.slider.setValue(value)
        
        self.label = QLabel()
        self.label.setFixedSize(39, 30)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(str(value))
        self.label.setStyleSheet(f"""
                                 font-size: 22px; 
                                 font-weight: bold; 
                                 padding-bottom: 2px; 

                                 """) # background-color: green;
        
        # add widgets to layout
        self.hbox.addWidget(self.icon)
        self.hbox.addItem(QSpacerItem(6, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.hbox.addWidget(self.slider)
        self.hbox.addItem(QSpacerItem(3, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.hbox.addWidget(self.label)

        if self.slider_callback:
            self.slider.valueChanged.connect(self.slider_callback)
        self.slider.valueChanged.connect(lambda value, lbl=self.label: lbl.setText(str(value)))
        self.slider.valueChanged.connect(lambda value, ico=self.icon: ico.animate_to(value))
        self.slider.animation.valueChanged.connect(self.update_ui_elements)

        # self.slider.setStyleSheet("background-color: red")
        # self.setStyleSheet("background-color: blue")

    def update_ui_elements(self, value):
        self.label.setText(str(value))
        self.icon.set_value(value)

    def animate_to(self, target_value, duration=1000, easing_curve=QEasingCurve.Type.OutCubic):
        logger.info(f"SliderFrame animate_to {self.slider.value()}-{target_value}")
        self.icon.stop_animation()  # Stop any ongoing animation in the icon
        self.slider.animate_to(target_value, duration, easing_curve)

    def setValueBS(self, value):
        if (self.slider.animation.state() == QPropertyAnimation.State.Running):
            self.slider.stop_animation()  # Stop any ongoing animation in the slider

        self.slider.blockSignals(True)  # Block signals during animation
        self.slider.setValue(value)
        self.slider.blockSignals(False)  # Unblock signals after setting value

        self.label.setText(str(value))
        self.icon.animate_to(value)

    # def enterEvent(self, event):
    #     logger.info("SliderFrame enterEvent")
    #     super().enterEvent(event)

    # def leaveEvent(self, event):
    #     logger.info("SliderFrame leaveEvent")
    #     super().leaveEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        logger.info("SliderFrame wheelEvent")

        delta = event.angleDelta().y()
        step = 1
        
        if delta > 0:
            new_value = min(self.slider.value() + step, self.slider.maximum())
        else:
            new_value = max(self.slider.value() - step, self.slider.minimum())

        self.slider.setValue(new_value)
        event.accept()  # Accept the event to prevent further processing

    def update_styles(self, bg_color: str = 'transparent', border_radius: int = 6):
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.setStyleSheet(f"""
            #SliderFrame {{
                background-color: {self.bg_color};
                border-radius: {self.border_radius}px;
            }}
        """)


# MARK: MainWindow
class MainWindow(QMainWindow):

    theme_changed = Signal(str)
    lock_state_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.theme_changed.connect(self._apply_theme)
        self.lock_state_changed.connect(self._on_lock_state_change)

        self.win_release = platform.release()
        logger.info(f"win_release: {self.win_release}")
        # self.win_release = 10

        self.is_laptop = is_laptop()
        logger.info(f"is_laptop: {self.is_laptop}")

        self.exe_path = os.path.realpath(sys.argv[0])
        logger.info(f"exe_path: {self.exe_path}")

        # General settings
        self.launch_on_startup = reg_read_bool(cfg.REGISTRY_PATH, "LaunchOnStartup", False)
        logger.info(f"launch_on_startup: {self.launch_on_startup}")
        if self.launch_on_startup:
            self.update_autostart()
        
        self.enable_rounded_corners = reg_read_bool(cfg.REGISTRY_PATH, "EnableRoundedCorners", False if self.win_release != "11" else True)
        logger.debug(f"enable_rounded_corners: {self.enable_rounded_corners}")
        if self.enable_rounded_corners:
            self.window_corner_radius = cfg.WIN11_WINDOW_CORNER_RADIUS
            self.window_offset = cfg.WIN11_WINDOW_OFFSET
        else:
            self.window_corner_radius = 0
            self.window_offset = 0

        self.enable_fusion_theme = reg_read_bool(cfg.REGISTRY_PATH, "EnableFusionTheme", False)
        logger.debug(f"enable_fusion_theme: {self.enable_fusion_theme}")
        if self.enable_fusion_theme:
            QApplication.instance().setStyle("Fusion")

        if (self.win_release != "11") and (not self.enable_fusion_theme):
            self.theme = "Light"
        else:
            self.theme = darkdetect.theme()
        logger.debug(f"theme: {self.theme}")

        self.enable_break_reminders = reg_read_bool(cfg.REGISTRY_PATH, "EnableBreakReminders", False)
        logger.debug(f"enable_break_reminders: {self.enable_break_reminders}")

        self.hidden_displays = reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays")
        logger.debug(f"hidden_displays: {self.hidden_displays}")

        self.custom_monitor_names = reg_read_dict(cfg.REGISTRY_PATH, "CustomMonitorNames")
        logger.info(f"custom_monitor_names: {self.custom_monitor_names}")

        self.monitors_order = reg_read_list(cfg.REGISTRY_PATH, "MonitorsOrder")
        logger.debug(f"monitors_order: {self.monitors_order}")

        # Resolution settings
        self.show_resolution = reg_read_bool(cfg.REGISTRY_PATH, "ShowResolution")
        logger.debug(f"show_resolution: {self.show_resolution}")

        # Refresh rate settings
        self.show_refresh_rates = reg_read_bool(cfg.REGISTRY_PATH, "ShowRefreshRates")
        logger.debug(f"show_refresh_rates: {self.show_refresh_rates}")
        self.excluded_rates = reg_read_dict(cfg.REGISTRY_PATH, "ExcludedHzRates")
        logger.debug(f"excluded_rates: {self.excluded_rates}")

        # Brightness settings
        self.restore_last_brightness = reg_read_bool(cfg.REGISTRY_PATH, "RestoreLastBrightness")
        logger.debug(f"restore_last_brightness: {self.restore_last_brightness}")
        
        self.brightness_values = reg_read_dict(cfg.REGISTRY_PATH, "BrightnessValues")
        logger.info(f"brightness_values: {self.brightness_values}")

        self.time_adjustment_startup = reg_read_bool(cfg.REGISTRY_PATH, "TimeAdjustmentStartup")
        logger.debug(f"time_adjustment_startup: {self.time_adjustment_startup}")
        self.time_adjustment_data = reg_read_dict(cfg.REGISTRY_PATH, "TimeAdjustmentData")
        # self.time_adjustment_data = {}
        logger.debug(f"time_adjustment_data: {self.time_adjustment_data}")

        # DDC/CI settings
        self.show_contrast_sliders = reg_read_bool(cfg.REGISTRY_PATH, "ShowContrastSliders", False)
        logger.debug(f"show_contrast_sliders: {self.show_contrast_sliders}")
        self.contrast_values = reg_read_dict(cfg.REGISTRY_PATH, "ContrastValues")
        logger.info(f"contrast_values: {self.contrast_values}")

        self.link_brightness = reg_read_bool(cfg.REGISTRY_PATH, "LinkBrightness", False)
        logger.debug(f"link_brightness: {self.link_brightness}")

        self.display_timeout_ac, self.display_timeout_dc = get_display_timeouts()
        # self.display_timeout_ac = self.display_timeout_dc = 120 # 2 min for testing
        logger.info(f"display_timeout_ac: {self.display_timeout_ac} sec, display_timeout_dc: {self.display_timeout_dc} sec")


        self.window_open = False
        self.brightness_sync_thread = None
        self.settings_window = None  # No settings window yet

        self.br_frames = {}  # Dictionary to store brightness frames
        self.contrast_frames = {}  # Dictionary to store contrast frames

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
            background: {cfg.colors["main_bg"][self.theme]};
            border-radius: {self.window_corner_radius}px;
            border: 1px solid {cfg.colors["main_border"][self.theme]};
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
        self.bottom_frame_hbox = QHBoxLayout(self.bottom_frame)

        # self.bottom_frame.setFixedHeight(60)
        # self.bottom_frame_hbox.setContentsMargins(7, 0, 11, 0)

        self.bottom_frame_hbox.setContentsMargins(7, 5, 7, 7)

        self.bottom_frame_hbox.setSpacing(4)



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
        # self.last_check_time = QDateTime.currentDateTime()
        self.last_check_time = None

        self.time_active = 0
        self.saved_time = 0
        self.screen_disabled = False

        # Run the lock state listener in a separate thread
        self.lock_listener = LockDetect(lambda state: self.lock_state_changed.emit(state)) # _on_lock_state_change
        threading.Thread(target=self.lock_listener.run, daemon=True).start()

        self.previous_monitor_list = get_monitor_list()
        self.start_checking(interval=(cfg.timer_interval * 1000))  # Start checking every minute
        if self.time_adjustment_startup:
            self.execute_recent_task()


        # check for updates on startup
        update_available, latest_version = self.check_for_update()
        if update_available:
            self.tray_icon.show_notification(
                        "New Update Available!",
                        f"A new version of MoniTune (v{latest_version}) is ready! Click here to download.",
                        QIcon(cfg.icons["monitune"]["Light"]),
                        on_click_callback=lambda: webbrowser.open(cfg.LATEST_RELEASE_URL)
                    )

        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.bottom_frame.setStyleSheet("background-color: green;") 
        # self.openSettingsWindow() # Open settings window on startup



    # MARK: _on_lock_state_change()
    def _on_lock_state_change(self, state: str):
        logger.info(f"Screen state changed to: {state}")
        if state == "unlocked":
            self.execute_recent_task(delay=10 * 1000) # Execute after 10 seconds  
            # QTimer.singleShot(10 * 1000, self.execute_recent_task)
            self.start_checking(interval=(cfg.timer_interval * 1000))
        elif state == "locked":
            self.stop_checking()


    # MARK: stop_checking()
    def stop_checking(self):
        self.timer.stop()
        logger.info("Task checking stopped")

    # MARK: start_checking()
    def start_checking(self, interval=60000):
        # self.last_check_time = QDateTime.currentDateTime()
        self.last_check_time = None
        self.time_active = 0
        self.saved_time = 0
        self.timer.start(interval)
        logger.info(f"Task checking started (interval: {interval / 1000} sec)")


    # MARK: check_all_tasks()
    def check_all_tasks(self):
        log_messages = []
        current_time = QTime.currentTime().toString("HH:mm")
        idle_time = get_idle_time()
        can_change_br = True


        timeout = self.display_timeout_ac
        power_type = "AC" # AC - plugged, DC - battery
        if self.is_laptop:
            on_battery = is_on_battery()
            timeout = self.display_timeout_dc if on_battery else self.display_timeout_ac
            power_type = "DC" if on_battery else "AC"
        

        # Calculate time_active, saved_time
        if idle_time > (5 * 60):
            logger.info(f"idle {5}min, reset time_active")
            self.time_active = 0
            self.saved_time = 0
        elif idle_time < (cfg.timer_interval * 1.0):
            self.time_active += cfg.timer_interval
            self.time_active += self.saved_time
            self.saved_time = 0
        else:
            self.saved_time += cfg.timer_interval

        
        log_messages.append(
            f"idle: {idle_time:.2f}s, "
            f"timeout({power_type}): {timeout}s, "
            f"active: {self.time_active / 60:.2f}m, "
            f"saved: {self.saved_time / 60:.2f}m"
        )

    
        # Monitor connected monitors
        current_monitor_list = get_monitor_list()
        # logger.info(f"current_monitor_list: {current_monitor_list}")
        previous_serials = set(self.previous_monitor_list)
        current_serials = set(current_monitor_list)

        added_monitors = current_serials - previous_serials
        removed_monitors = previous_serials - current_serials

        if added_monitors:
            logger.info(f"Added monitors: {added_monitors}")
            # QTimer.singleShot(10000, lambda: self.execute_recent_task(delay=10000))
            QTimer.singleShot(10 * 1000, self.execute_recent_task)
            can_change_br = False
        if removed_monitors:
            logger.info(f"Removed monitors: {removed_monitors}")

        self.previous_monitor_list = current_monitor_list


        # Monitor display timeout
        if (timeout >= 120) and (idle_time >= timeout):
            logger.info(f"Display timeout reached ({power_type}): {timeout} sec")
            self.screen_disabled = True

        if self.screen_disabled and (idle_time < timeout):
            logger.info("Activity after timeout, restoring brightness")
            self.screen_disabled = False
            QTimer.singleShot(10 * 1000, self.execute_recent_task)
            can_change_br = False


        # MARK: Check time adjustment tasks
        if (self.last_check_time != current_time) and can_change_br:
            if current_time in self.time_adjustment_data:
                self.apply_brightness(self.time_adjustment_data[current_time])
                log_messages.append(f"Applied brightness: {self.time_adjustment_data[current_time]}")
            else:
                log_messages.append("idle")

        
        # MARK: Check time active for break reminders
        if (self.enable_break_reminders and 
            (self.time_active >= (cfg.break_notification_interval * 60)) and 
            (self.window_open == False)
        ):
            logger.info(f"show break notification, time_active: {self.time_active / 60} min")
            self.tray_icon.show_notification(
                "Take a break from the screen!",
                "Look at least 6 meters away from the screen for 20 seconds.",
                QIcon(cfg.icons["eye"][self.theme])
            )
            self.time_active = 0
        
        
        logger.info(" | ".join(log_messages))
        self.last_check_time = current_time



    # MARK: execute_recent_task()
    def execute_recent_task(self, delay=0):
        if not self.time_adjustment_data:
            logger.info("execute_recent_task: No tasks found, restoring last change")
            self.apply_brightness(self.brightness_values, delay=delay)
            return

        current_time = QTime.currentTime().toString("HH:mm")
        past_tasks = [time for time in self.time_adjustment_data.keys() if time <= current_time]
        if past_tasks:
            recent_task_time = max(past_tasks)
            logger.info(f"Executing recent task at: {recent_task_time}, delay: {delay / 1000} sec")
            self.apply_brightness(self.time_adjustment_data[recent_task_time], delay=delay)
        else:
            logger.info("No past tasks to execute for today, checking previous day")
            if self.time_adjustment_data:
                recent_task_time = max(self.time_adjustment_data.keys())
                logger.info(f"Executing last task from previous day at: {recent_task_time}, delay: {delay / 1000} sec")
                self.apply_brightness(self.time_adjustment_data[recent_task_time], delay=delay)
    


    # MARK: apply_brightness()
    def apply_brightness(self, brightness_data, delay=0):
        logger.info(f"apply_brightness: {brightness_data}, delay: {delay / 1000} sec")
        
        self.update_monitors_info()
        for serial in self.monitors_dict:
            if serial in brightness_data:
                self.brightness_values[serial] = brightness_data[serial]

        # play slider animation if window is open
        if self.window_open and (delay == 0):
            QTimer.singleShot(0, lambda: self.animate_sliders(self.br_frames, self.brightness_values))
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
                    logger.info(f"New version available: {latest_version}. Current version: {current_version}.")
                    return True, latest_version
                else:
                    logger.info(f"Current version {current_version} is up to date.")
                    return False, latest_version
            else:
                logger.error(f"Error fetching release data: {response.status_code}")
                return False, None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None



    # MARK: update_monitors_info()
    def update_monitors_info(self):
        monitors_info = get_monitors_info()

        # Exclude monitors that are in self.hidden_displays
        monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in self.hidden_displays]
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        self.monitors_dict = monitors_dict
        logger.debug(f"monitors_dict {self.monitors_dict}")



    # MARK: update_central_widget()
    def update_central_widget(self):
        self.window_offset = cfg.WIN11_WINDOW_OFFSET if self.enable_rounded_corners else 0
        corner_radius = cfg.WIN11_WINDOW_CORNER_RADIUS if self.enable_rounded_corners else 0
        self.centralWidget().setStyleSheet(
            f"""
            #Container {{
            background: {cfg.colors["main_bg"][self.theme]};
            border-radius: {corner_radius}px;
            border: 1px solid {cfg.colors["main_border"][self.theme]};
            }}
            """
        )



    # MARK: update_autostart()
    def update_autostart(self):
        if not getattr(sys, 'frozen', False): # if not running as EXE
            logger.info("Not running as EXE, skipping startup registry modification")
            return
        
        if self.launch_on_startup:
            logger.info("Adding to startup")
            add_to_startup(cfg.app_name, self.exe_path)
        else:
            logger.info("Removing from startup")
            remove_from_startup(cfg.app_name)



    # MARK: _apply_theme()
    def _apply_theme(self, theme: str):
        logger.info(f"Theme changed to: {theme}")
        if (self.win_release != "11") and (not self.enable_fusion_theme):
            self.theme = "Light"
        else:
            self.theme = theme
        self.update_central_widget()
        self.tray_icon.changeIconTheme(theme)
        if self.settings_window:
            self.settings_window.theme = theme
            self.settings_window.update_tab_widget()



    # MARK: eventFilter()
    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        # hide window when focus is lost
        if event.type() == QEvent.Type.WindowDeactivate:
            # self.hide()
            self.animateWindowClose()
            return True
        
        # Handle scroll events on the bottom frame
        if (source == self.bottom_frame) and (event.type() == QEvent.Type.Wheel):
            delta = event.angleDelta().y()
            self.on_bottom_frame_scroll(delta)
            return True
        
        # Handle right mouse button click on bottom_frame
        if (source == self.bottom_frame) and (event.type() == QEvent.Type.MouseButtonPress):
            if event.button() == Qt.MouseButton.LeftButton:
                logger.info("bottom frame LMB click")
                return True
            if event.button() == Qt.MouseButton.RightButton:
                logger.info("bottom frame RMB click")
                self.execute_recent_task()
                return True
        
        # Add hover effect to all SliderFrame instances when hovering over bottom_frame
        if (source == self.bottom_frame) and (event.type() in [QEvent.Type.Enter, QEvent.Type.Leave]):
            hover = event.type() == QEvent.Type.Enter
            for frame in self.br_frames.values():
                if frame.isEnabled():
                    frame.update_styles(bg_color=cfg.colors["frame_hover"][self.theme] if hover else 'transparent')
            return True
        
        # # Add hover effect to all br_frames except the one the mouse is on when link_brightness is enabled
        # if (source in self.br_frames.values()) and (event.type() in [QEvent.Type.Enter, QEvent.Type.Leave]):
        #     hover = event.type() == QEvent.Type.Enter
        #     for frame in self.br_frames.values():
        #         if frame.isEnabled() and (frame != source) and self.link_brightness:
        #             frame.update_styles(bg_color=cfg.colors["frame_hover"][self.theme] if hover else 'transparent')
        #     return True
        
        return super().eventFilter(source, event)



    # MARK: updateMonitorsFrame()
    def updateMonitorsFrame(self):
        
        start_time = time.time()

        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.br_frames.clear()  # Clear brightness frames dictionary
        self.contrast_frames.clear()  # Clear contrast frames dictionary


        # print_mi(self.monitors_dict)


        # placeholder if no monitors are available (or all are hidden)
        if not self.monitors_dict:  # Check if no monitors are available
            placeholder_frame = QWidget()
            placeholder_frame.setObjectName("EmptyPlaceholder")
            placeholder_frame.setStyleSheet(
                f"""
                #EmptyPlaceholder {{
                background: {cfg.colors["frame_bg"][self.theme]};
                border-radius: {6 if self.enable_rounded_corners else 0}px;
                border: 1px solid {cfg.colors["frame_border"][self.theme]}; 
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
        logger.info(f"monitors_order: {monitors_order}")
        


        for index, monitor_serial in enumerate(monitors_order):
            monitor = self.monitors_dict[monitor_serial]
            
            logger.info(
                f"display_name: {monitor['display_name']} | "
                f"serial: {monitor['serial']} | "
                f"method: {monitor['method']} | "
                f"Device: {monitor['Device']} | "
                f"hPhysicalMonitor: {monitor['hPhysicalMonitor']}"
            )

            monitor_frame = QWidget()
            monitor_frame.setObjectName("MonitorsFrame")
            monitor_frame.setStyleSheet(
                f"""
                #MonitorsFrame {{
                background: {cfg.colors["frame_bg"][self.theme]};
                border-radius: {6 if self.enable_rounded_corners else 0}px;
                border: 1px solid {cfg.colors["frame_border"][self.theme]}; 
                }}
                """
            )
            monitor_vbox = QVBoxLayout(monitor_frame)
            monitor_vbox.setSpacing(5)  # Spacing between monitor frames
            monitor_vbox.setContentsMargins(7, 7, 7, 7)
            

            # MARK: Label Frame
            label_frame = QWidget()
            label_hbox = QHBoxLayout(label_frame)
            label_hbox.setContentsMargins(0, 0, 0, 0)
            label_hbox.setSpacing(5)

            if monitor["method"] == "VCP": 
                # add power button with monitor icon
                power_btn = HoverIconButton(icon_path=cfg.icons["monitor"][self.theme],
                                            hover_icon_path=cfg.icons["shutdown"][self.theme])
                power_btn.setFlat(True)
                power_btn.setStyleSheet("""
                                        QPushButton {
                                            background-color: transparent;
                                        }
                                        """) 
                power_btn.setSizePolicy(QSizePolicy.Policy.Preferred, 
                                        QSizePolicy.Policy.Expanding)
                power_btn.setFixedSize(30, 30)
                power_btn.setIconSize(QSize(30, 30))
                power_btn.setToolTip("Power off")
                power_btn.clicked.connect(lambda checked,
                                          mf=monitor_frame,
                                          h=monitor["hPhysicalMonitor"]: 
                                          self.disable_monitor(h, mf))
                label_hbox.addWidget(power_btn)

                monitor_frame.enterEvent = lambda event, pb=power_btn: pb.applyHoverIcon()
                monitor_frame.leaveEvent = lambda event, pb=power_btn: pb.applyDefaultIcon()
            else: 
                # add monitor icon
                monitor_icon = QLabel()
                # monitor_icon.setStyleSheet("""background-color: blue;""")
                icon_size = 30
                if (monitor["Device"] == "\\\\.\\DISPLAY1") and self.is_laptop:
                    monitor_icon.setPixmap(QIcon(cfg.icons["laptop"][self.theme]).pixmap(26, 26))
                else:
                    monitor_icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(icon_size, icon_size))
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

                                        """) # background-color: blue;
            label_hbox.addWidget(monitor_label)
            

            # MARK: Resolution
            if self.show_resolution:
                available_resolutions = monitor["AvailableResolutions"]
                sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
                formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]
                max_res_length = max(len(res) for res in formatted_resolutions)
                res_combobox_width = 105 if (max_res_length <= 9) else 112 if (max_res_length == 10) else 120
                rc_bg_color = (cfg.colors["combobox_bg"][self.theme] 
                               if not self.enable_fusion_theme else None)
                
                res_combobox = StyledComboBox(self,
                                              down_arrow=cfg.icons["down_arrow"][self.theme], 
                                              bg_color=rc_bg_color,
                                              )
                res_combobox.setFixedWidth(res_combobox_width)
                res_combobox.setSizePolicy(QSizePolicy.Policy.Fixed, 
                                           QSizePolicy.Policy.Expanding)
                for res in sorted_resolutions:
                    res_combobox.addItem(f"{res[0]}x{res[1]}", res)
                res_combobox.setCurrentText(f"{monitor['Resolution'][0]}x{monitor['Resolution'][1]}")
                res_combobox.currentIndexChanged.connect(lambda index, 
                                                         m=monitor, 
                                                         cb=res_combobox: 
                                                         self.on_resolution_select(m, cb.currentData()))
                label_hbox.addWidget(res_combobox)

            monitor_vbox.addWidget(label_frame)
            

            # MARK: Refresh Rates
            refresh_rates = monitor["AvailableRefreshRates"]

            # Ensure the serial key exists
            if monitor_serial not in self.excluded_rates:
                self.excluded_rates[monitor_serial] = []
                logger.info(f"Added serial {monitor_serial} to excluded_rates with empty list")

            refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates[monitor_serial]]

            if self.show_refresh_rates and (len(refresh_rates) >= 2):
                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

                rr_frame = ButtonGridFrame(self, 
                                        refresh_rates, 
                                        monitor["RefreshRate"], 
                                        callback=lambda value, m=monitor: self.on_rr_button_click(value, m))
                monitor_vbox.addWidget(rr_frame)
            
            
            # MARK: Brightness
            if monitor["method"] == "VCP":
                br_level = get_brightness_vcp(monitor["hPhysicalMonitor"], retries=5)
            else:
                br_level = get_brightness_sbc(display=monitor['serial'])

            # br_level = None
            brightness_failed = False
            if br_level is None:
                logger.warning(f"Failed to get brightness for monitor {monitor['serial']}")
                br_level = self.brightness_values.get(monitor["serial"], 50)
                brightness_failed = True

            # Add separator line
            monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

            if self.restore_last_brightness and (monitor['serial'] in self.brightness_values):
                pass
            else:
                self.brightness_values[monitor['serial']] = br_level

            br_frame = SliderFrame(
                parent=self,
                icon_path=cfg.icons["sun"][self.theme],
                value=br_level,
                slider_callback=lambda value, ms=monitor_serial: self.on_brightness_change(value, ms)
            )
            if brightness_failed:
                br_frame.setDisabled(True)

            self.br_frames[monitor['serial']] = br_frame  # Store frame in dictionary
            # br_frame.installEventFilter(self)

            monitor_vbox.addWidget(br_frame)


            # MARK: Contrast
            if self.show_contrast_sliders and (monitor["method"] == "VCP"):
                contrast_level = None
                if br_frame.isEnabled():
                    contrast_level = get_contrast_vcp(monitor["hPhysicalMonitor"], retries=5)
                
                contrast_failed = False
                if contrast_level is None:
                    logger.warning(f"Failed to get contrast for monitor {monitor['serial']}")
                    contrast_level = self.contrast_values.get(monitor["serial"], 50)
                    contrast_failed = True

                # self.contrast_values[monitor_serial] = contrast_level # dont change contrast
                
                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

                contrast_frame = SliderFrame(
                    parent=self,
                    icon_path=cfg.icons["contrast"][self.theme],
                    value=contrast_level,
                    slider_callback=lambda value, ms=monitor_serial: self.on_contrast_change(value, ms)
                )
                if contrast_failed:
                    contrast_frame.setDisabled(True)

                self.contrast_frames[monitor['serial']] = contrast_frame

                monitor_vbox.addWidget(contrast_frame)


            self.monitors_layout.addWidget(monitor_frame)


            # QTimer.singleShot(0, lambda: print("br_label width:", br_label.width())) # Print width of br_label after the layout is updated

            # label_frame.setStyleSheet("background-color: red")
            # if self.show_refresh_rates: rr_frame.setStyleSheet("background-color: green")


        logger.info(f"brightness_values {self.brightness_values}")
        logger.info(f"contrast_values {self.contrast_values}")

        logger.info(f"updateMonitorsFrame took {time.time() - start_time:.4f} seconds")

    

    # MARK: updateBottomFrame()
    def updateBottomFrame(self):
        
        start_time = time.time()

        # Clear old widgets
        # print("updateBottomFrame count ", self.bottom_frame_hbox.count())
        while self.bottom_frame_hbox.count():
            child = self.bottom_frame_hbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


        bf_label = QLabel("Scroll to adjust brightness")
        bf_label.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 padding-bottom: 2px;

                                 """) # padding-left: 5px; background-color: blue;
        self.bottom_frame_hbox.addWidget(bf_label)

        # self.buttons_frame = QFrame()
        # self.buttons_frame.setFrameShape(QFrame.Shape.StyledPanel)
        # self.buttons_frame.setFixedSize(41, 39) # 39 39
        # buttons_layout = QGridLayout(self.buttons_frame)
        # buttons_layout.setContentsMargins(0, 0, 0, 0)
        # buttons_layout.setSpacing(0)
        # for row in range(2):
        #     for col in range(2):
        #         num = row * 2 + col + 1
        #         button = QPushButton()
        #         button.setCheckable(True)
        #         buttons_layout.addWidget(button, row, col)
        # self.bottom_frame_hbox.addWidget(self.buttons_frame)

        self.link_br_btn = QPushButton()
        self.link_br_btn.setCheckable(True)
        self.link_br_btn.setChecked(self.link_brightness)
        self.link_br_btn.setFixedSize(41, 39) # 39 39
        self.link_br_btn.setIcon(self.get_icon_for_toggle_state("link", self.link_brightness))
        self.link_br_btn.setIconSize(QSize(21, 21))
        self.link_br_btn.setToolTip("Link brightness levels")
        self.link_br_btn.toggled.connect(self.toggle_link_brightness)
        if len(self.monitors_dict) < 2:
            self.link_br_btn.setDisabled(True)
        self.bottom_frame_hbox.addWidget(self.link_br_btn)

        settings_btn = QPushButton()
        settings_btn.setFixedSize(41, 39) # 39 39
        settings_btn.setIcon(QIcon(cfg.icons["settings"][self.theme]))
        settings_btn.setIconSize(QSize(21, 21))
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self.openSettingsWindow)
        self.bottom_frame_hbox.addWidget(settings_btn)

        logger.info(f"updateBottomFrame took {time.time() - start_time:.4f} seconds")


    # MARK: toggle_link_brightness()
    def toggle_link_brightness(self, checked):
        self.link_brightness = checked
        self.link_br_btn.setIcon(self.get_icon_for_toggle_state("link", self.link_brightness))
        reg_write_bool(cfg.REGISTRY_PATH, "LinkBrightness", checked)
        logger.info(f"link_brightness - {checked}")


    def get_icon_for_toggle_state(self, icon_name, checked):
        if self.enable_fusion_theme:
            icon_path = cfg.icons[icon_name][self.theme]
        else:
            if self.theme == "Light":
                icon_path = cfg.icons[icon_name]["Dark"] if checked else cfg.icons[icon_name]["Light"]
            else:
                icon_path = cfg.icons[icon_name]["Light"] if checked else cfg.icons[icon_name]["Dark"]
        return QIcon(icon_path)


    # MARK: disable_monitor()
    def disable_monitor(self, hPhysicalMonitor, monitor_frame):
        if set_power_mode_vcp(hPhysicalMonitor, 4, retries=7):
            logger.info(f"Monitor powered off successfully.")
            monitor_frame.setDisabled(True)
        else:
            logger.warning(f"Failed to power off monitor {hPhysicalMonitor}.")


    # MARK: on_rr_button_click()
    def on_rr_button_click(self, rate, monitor):
        logger.info(f"Selected refresh rate: {rate} Hz for monitor {monitor['serial']}")

        self.update_monitors_info()
        updated_monitor = self.monitors_dict.get(monitor["serial"], None)

        if not updated_monitor:
            logger.warning(f"Monitor {monitor['Device']} not found")
            return False
        
        if updated_monitor and (updated_monitor["RefreshRate"] == rate):
            logger.info(f"Monitor {monitor['Device']} already has refresh rate {rate} Hz")
            return False

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

        logger.info(f"brightness_before: {brightness_before}, contrast_before: {contrast_before}")

        #restore brightness and contrast after 6 seconds
        def restore_parameters():
            logger.info(f"restore_parameters {monitor['serial']}: {brightness_before}, {contrast_before}")
            if brightness_before is not None:
                self.brightness_values[monitor['serial']] = brightness_before
            if contrast_before is not None:
                self.contrast_values[monitor['serial']] = contrast_before
            self.brightness_sync_onetime()
            
        if not set_refresh_rate(monitor, rate): # set refresh rate
            return False
        else:
            threading.Timer(6, restore_parameters).start()
            # QTimer.singleShot(6000, restore_parameters)
            return True



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor, resolution):
        logger.info(f"on_resolution_select {monitor['serial']} {resolution}")
        
        width, height = resolution
        set_resolution(monitor["Device"], width, height)
        
        QTimer.singleShot(500, self.updateSizeAndPosition)


    # MARK: on_brightness_change()
    def on_brightness_change(self, value, monitor_serial):
        # print(f"on_brightness_change: {value}, {monitor_serial}")

        if self.link_brightness:
            previous_value = self.brightness_values.get(monitor_serial, 0)
            change = value - previous_value
            # print(f"Brightness change for {monitor_serial}: {change}")

            for serial, frame in self.br_frames.items():
                slider = frame.slider
                
                if (serial != monitor_serial) and slider.isEnabled():

                    # new_value = max(0, min(100, (slider.value() + change)))

                    # use prev_value to preserve the offset between sliders
                    prev_value = self.brightness_values.get(serial, 0)
                    new_value = max(0, min(100, (prev_value + change)))

                    frame.setValueBS(int(new_value))

                    self.brightness_values[serial] = int(new_value)

        self.brightness_values[monitor_serial] = int(value)

    # MARK: on_contrast_change()
    def on_contrast_change(self, value, monitor_serial):
        # print(f"on_contrast_change: {value}, {monitor_serial}")
        self.contrast_values[monitor_serial] = int(value)

    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, delta):
        logger.debug(f"on_bottom_frame_scroll delta: {delta}")

        link_brightness_save = self.link_brightness
        self.link_brightness = False  # Disable linking temporarily

        for frame in self.br_frames.values():
            slider = frame.slider
            if slider.isEnabled():
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
                            
                            logger.info(f"brightness_sync set_brightness_vcp {monitor_serial} {brightness}")
                        else:
                            set_brightness_sbc(monitor_serial, brightness)
                            logger.info(f"brightness_sync set_brightness {monitor_serial} {brightness}")

                        previous_brightness_values[monitor_serial] = brightness
                        reg_write_dict(cfg.REGISTRY_PATH, "BrightnessValues", self.brightness_values)

                    except Exception as e:
                        logger.error(f"Error: {e}")
            
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
                            
                            logger.info(f"brightness_sync set_contrast_vcp {monitor_serial} {contrast}")

                            previous_contrast_values[monitor_serial] = contrast
                            reg_write_dict(cfg.REGISTRY_PATH, "ContrastValues", self.contrast_values)

                        except Exception as e:
                            logger.error(f"Error: {e}")


            # logger.debug(f"Brightness sync took {time.time() - start_time:.4f} seconds")

            time.sleep(0.10) # 0.15


    # MARK: brightness_sync_onetime()
    def brightness_sync_onetime(self):
        logger.info("brightness_sync_onetime")
        start_time = time.time()
        # self.update_monitors_info()

        brightness_values_copy = self.brightness_values.copy()
        for monitor_serial, brightness in brightness_values_copy.items():
            if monitor_serial in self.monitors_dict:  # Check if monitor is connected
                try:
                    if self.monitors_dict[monitor_serial]["method"] == "VCP":
                        if not set_brightness_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                           brightness, 
                                           retries=7):
                            raise Exception(f"Failed to set brightness for monitor {monitor_serial}")

                        logger.info(f"brightness_sync_onetime set_brightness_vcp {monitor_serial} {brightness}")
                    else:
                        set_brightness_sbc(monitor_serial, brightness)
                        logger.info(f"brightness_sync_onetime set_brightness {monitor_serial} {brightness}")

                except Exception as e:
                    logger.error(f"Error: {e}")
        
        if self.show_contrast_sliders:
            contrast_values_copy = self.contrast_values.copy()
            for monitor_serial, contrast in contrast_values_copy.items():
                if monitor_serial in self.monitors_dict: # Check if monitor is connected
                    try:
                        if not set_contrast_vcp(self.monitors_dict[monitor_serial]["hPhysicalMonitor"], 
                                         contrast, 
                                         retries=7):
                            raise Exception(f"Failed to set contrast for monitor {monitor_serial}")
                        
                        logger.info(f"brightness_sync_onetime set_contrast_vcp {monitor_serial} {contrast}")

                    except Exception as e:
                        logger.error(f"Error: {e}")

        logger.info(f"brightness_sync_onetime took {time.time() - start_time:.4f} seconds")


    # MARK: showEvent()
    def showEvent(self, event):
        logger.info("showEvent")

        self.update_monitors_info()

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
            logger.info("brightness_sync_thread start")

            # self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
            # self.brightness_sync_thread.start()
            QTimer.singleShot(250, self.start_brightness_sync_thread) 

            # self.brightness_sync_thread = threading.Timer(0.25, self.brightness_sync)
            # self.brightness_sync_thread.daemon = True
            # self.brightness_sync_thread.start()
        else:
            logger.info("brightness_sync_thread is already running")

        super().showEvent(event)

        if self.restore_last_brightness:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.br_frames, self.brightness_values))
        if self.show_contrast_sliders:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.contrast_frames, self.contrast_values))


    def on_exit(self):
        logger.info("Exiting application")

        # Close app
        QGuiApplication.quit()


    # MARK: animate_sliders()
    def animate_sliders(self, frames, values):
        logger.info(f"animate_sliders: {list(frames.keys())}, {values}")
        for index, (serial, frame) in enumerate(frames.items()):
            if serial in values:
                # QTimer.singleShot(index * 100, lambda s=slider: s.animate_to(int(values[serial])))
                frame.animate_to(int(values[serial]))



    # MARK: start_brightness_sync_thread()
    def start_brightness_sync_thread(self):
        logger.info("brightness_sync_thread started")
        self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
        self.brightness_sync_thread.start()



    # MARK: hideEvent()
    def hideEvent(self, event):
        logger.info("hideEvent")
        self.window_open = False
        self.stop_brightness_sync_thread()
        # QTimer.singleShot(2000, self.stop_brightness_sync_thread)  # Add 2-second delay
        # QTimer.singleShot(1000, self.brightness_sync_onetime)
        super().hideEvent(event)


    # MARK: stop_brightness_sync_thread()
    def stop_brightness_sync_thread(self):
        if self.brightness_sync_thread and self.brightness_sync_thread.is_alive():
            self.brightness_sync_thread.join()  # Stop brightness sync thread
            if not self.brightness_sync_thread.is_alive():
                logger.info("brightness_sync_thread is dead")
            else:
                logger.info("brightness_sync_thread is still alive")
        else:
            logger.info("brightness_sync_thread is not running")


    # MARK: updateSizeAndPosition()
    def updateSizeAndPosition(self):
        logger.info(f"updateSizeAndPosition self.sizeHint().height(): {self.sizeHint().height()}, self.height(): {self.height()}")
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - self.window_offset, 
                  screen_geometry.height() - self.sizeHint().height() - self.window_offset)
        logger.debug(f"self.move({screen_geometry.width() - self.width() - self.window_offset}, {screen_geometry.height() - self.sizeHint().height() - self.window_offset})")
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

        logger.debug(f"self.width() {self.width()}, self.sizeHint().height() {self.sizeHint().height()}")

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

    app = QApplication([]) 
    app.setWindowIcon(QIcon(cfg.icons["monitune"]["Light"]))

    logger.info(f"Starting app (v{cfg.version})")


    # Check if another instance is already running
    if getattr(sys, 'frozen', False):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex = kernel32.CreateMutexW(None, False, "MoniTune-Qt")
        if not mutex: # Error creating mutex
            logger.error(f"Error code: {ctypes.get_last_error()}")
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS (mutex already exists)
            logger.warning("Another instance is already running")

            # Create a message box to notify the user
            QMessageBox.information(
                None,
                "MoniTune",
                "Another instance of MoniTune is already running.\nPlease close the other instance to continue.",
                QMessageBox.StandardButton.Ok
            )

            sys.exit(1)


    logger.info(f"Available styles: {QStyleFactory.keys()}") # ['windows11', 'windowsvista', 'Windows', 'Fusion']
    # app.setStyle("windows11")
    logger.info(f"Current style: {app.style().objectName()}")


    window = MainWindow()

    if not getattr(sys, 'frozen', False): # if run from source code
        window.openSettingsWindow()
        window.show()

    app.exec()