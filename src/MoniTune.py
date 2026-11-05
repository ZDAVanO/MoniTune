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
    QTranslator,
    QLocale,
)
from PySide6.QtGui import (
    QIcon, 
    QGuiApplication, 
    QWheelEvent,
    QCursor,
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
    ButtonGridFrame,
    SliderFrame,
    HoverIconButton,
    NoScrollComboBox,
    StyledComboBox,
    SeparatorLine,
)

from services.settings_manager import get_settings
from services.brightness_coordinator import BrightnessCoordinator
from services.window_positioner import calculate_window_rects, calculate_close_rect
from utils.monitor_utils import (
    Monitor,
    get_monitors, 
    get_monitor_device_names,
)
from utils.reg_utils import (
    reg_write_bool, 
    reg_read_bool, 
    reg_write_int,
    reg_read_int,
    reg_write_list, 
    reg_read_list, 
    reg_write_dict, 
    reg_read_dict,
    add_to_startup,
    remove_from_startup,
)
from utils.utils import (
    get_idle_time, 
    is_laptop, 
    is_on_battery, 
    get_display_timeouts, 
    check_github_update_available,
)
from utils.lock_detect import LockDetect
from utils.power_detect import PowerDetect, is_energy_saver_active
from utils.active_process import ActiveProcessListener, get_active_process

from utils.logger import get_logger, set_file_logging
logger = get_logger(__name__) # debug, info, warning, error, critical

import config as cfg
import resources_rc

import darkdetect

import sys
import os
import ctypes
import threading
from pathlib import Path
import psutil
import platform
import time


import webbrowser



# MARK: MainWindow
class MainWindow(QMainWindow):

    theme_changed = Signal(str)
    lock_state_changed = Signal(str)
    active_process_changed = Signal(dict)
    energy_saver_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        self.theme_changed.connect(self._apply_theme)
        self.lock_state_changed.connect(self._on_lock_state_change)
        self.active_process_changed.connect(self._on_active_process_change)
        self.energy_saver_changed.connect(self._on_energy_saver_change)

        self.win_release = platform.release()
        logger.info(f"win_release: {self.win_release}")
        # self.win_release = 10

        self.is_laptop = is_laptop()
        logger.info(f"is_laptop: {self.is_laptop}")

        # self.exe_path = os.path.realpath(sys.argv[0])
        self.exe_path = psutil.Process().exe()
        logger.info(f"exe_path: {self.exe_path}")

        self._load_settings()

        if self.settings.launch_on_startup:
            self.update_autostart()

        self._determine_theme(darkdetect.theme())
        if self.settings.enable_fusion_theme:
            QApplication.instance().setStyle("Fusion")

        self.display_timeout_ac, self.display_timeout_dc = get_display_timeouts()
        # self.display_timeout_ac = self.display_timeout_dc = 120 # 2 min for testing
        logger.info(f"display_timeout_ac: {self.display_timeout_ac} sec, display_timeout_dc: {self.display_timeout_dc} sec")

        self.window_open = False
        self.brightness_sync_thread = None
        self.settings_window = None

        self.br_frames = {}  # Dictionary to store brightness frames
        self.contrast_frames = {}  # Dictionary to store contrast frames
        # self.monitors_widgets = [] # List to store monitor frame widgets for easy hiding/showing

        self.monitors_dict = {}  # Dictionary to store all monitors info
        self.active_monitors_dict = {} # Dictionary to store active monitors info (not hidden)
        # self.update_monitors_info()

        self.active_process = None # using for settings window
        self.prev_active_process = None
        self.profile_active = False
        self._linking_suspended = False

        self._init_ui()

        # Create the system tray icon
        self.tray_icon = SystemTrayIcon(self)

        # Run the theme listener in a separate thread
        threading.Thread(target=darkdetect.listener, 
                         args=(lambda theme: self.theme_changed.emit(theme),), # _apply_theme
                         daemon=True).start()
        
        # Run lock state listener in a separate thread
        self.lock_listener = LockDetect(lambda state: self.lock_state_changed.emit(state)) # _on_lock_state_change
        threading.Thread(target=self.lock_listener.run, daemon=True).start()

        self.coordinator = BrightnessCoordinator()
        self.is_power_saving_active = False
        self.is_popup = False
        self.current_screen = None

        self.is_energy_saver = is_energy_saver_active()
        logger.info(f"is_energy_saver on startup: {self.is_energy_saver}")
        self.power_listener = PowerDetect(lambda state: self.energy_saver_changed.emit(state))
        threading.Thread(target=self.power_listener.run, daemon=True).start()

        self.process_listener = ActiveProcessListener(lambda pi: self.active_process_changed.emit(pi))
        self.process_listener_thread = None
        if self.settings.enable_profiles:
            self.start_process_listener() # Run process listener in a separate thread


        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_all_tasks)
        # self.last_check_time = QDateTime.currentDateTime()
        self.last_check_time = None

        self.time_active = 0
        self.saved_time = 0
        self.screen_disabled = False

        # self.previous_monitor_list = get_monitor_list()
        self.previous_monitor_list = get_monitor_device_names()
        self.update_monitors_info()
        self.start_checking(interval=(cfg.timer_interval * 1000))  # Start self.timer
        # if self.settings.enable_time_adjustment and self.settings.time_adjustment_startup:
        if self.settings.time_adjustment_startup:
            self.execute_recent_task()

        self.apply_power_saving_state()


        # timer for hiding the popup window
        self.popup_timer = QTimer(singleShot=True)
        # self.popup_timer.timeout.connect(self.animateWindowClose)
        self.popup_timer.timeout.connect(self.hide_window)


        self.check_for_updates()


    # MARK: _load_settings()
    def _load_settings(self):
        self.settings = get_settings()

    def __getattr__(self, name: str):
        if name != "settings" and hasattr(self, "settings"):
            try:
                return getattr(self.settings, name)
            except AttributeError:
                pass
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


    # MARK: _init_ui()
    def _init_ui(self):
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

        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.setContentsMargins(7, 7, 7, 7)
        central_widget_layout.setSpacing(5)
        central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.monitors_frame = QWidget()
        # self.monitors_frame.setStyleSheet("border-radius: 9px; background-color: red")
        self.monitors_layout = QVBoxLayout(self.monitors_frame)
        self.monitors_layout.setContentsMargins(0, 0, 0, 0)
        self.monitors_layout.setSpacing(6) # Set spacing between monitor frames

        self.bottom_frame = QWidget()
        # self.bottom_frame.setStyleSheet("""
        #     background-color: green;
        #     border-bottom-left-radius: 9px;
        #     border-bottom-right-radius: 9px;
        # """)
        
        self.bottom_frame.installEventFilter(self)
        self.bottom_frame_hbox = QHBoxLayout(self.bottom_frame)

        # self.bottom_frame_hbox.setContentsMargins(7, 0, 11, 0)
        # self.bottom_frame_hbox.setContentsMargins(7, 5, 7, 7)
        self.bottom_frame_hbox.setContentsMargins(0, 0, 0, 0) # for popup
        self.bottom_frame_hbox.setSpacing(4) # spacing between bottom_frame buttons

        central_widget_layout.addWidget(self.monitors_frame)
        central_widget_layout.addWidget(self.bottom_frame)

        self.setCentralWidget(central_widget)
        self.update_central_widget()


    # MARK: check_for_updates()
    def check_for_updates(self):
        update_available, latest_version = check_github_update_available(
        repo_api_url=cfg.UPDATE_CHECK_URL,
        current_version=cfg.version,
        )
        if update_available:
            self.tray_icon.show_notification(
                "New Update Available!",
                f"A new version of {cfg.app_name} (v{latest_version}) is ready! Click here to download.",
                QIcon(cfg.icons["monitune"]["Light"]),
                on_click_callback=lambda: webbrowser.open(cfg.LATEST_RELEASE_URL)
            )


    # MARK: _on_energy_saver_change()
    def _on_energy_saver_change(self, is_active: bool):
        logger.info(f"Energy Saver state changed to: {is_active}")
        self.is_energy_saver = is_active
        mode = getattr(self.settings, "power_saving_mode", "windows")
        if mode == "windows":
            self.apply_power_saving_state()
        elif self.window_open:
            self.updateBottomFrame()

    # MARK: Power Saving Methods
    @property
    def pre_saving_brightness(self):
        return self.coordinator.pre_saving_brightness

    def is_power_saving_effective(self) -> bool:
        """Returns True if Power Saving limits should currently be enforced."""
        return self.coordinator.is_power_saving_effective(
            enable_limits=getattr(self.settings, "enable_power_saving_limits", True),
            mode=getattr(self.settings, "power_saving_mode", "windows"),
            manual_state=getattr(self.settings, "power_saving_manual_state", False),
            is_windows_energy_saver=getattr(self, "is_energy_saver", False),
        )

    def apply_power_saving_state(self, force=False):
        """Enforces or releases power saving brightness limits on all monitors."""
        effective = self.is_power_saving_effective()
        if (effective == self.is_power_saving_active) and not force:
            return

        self.is_power_saving_active = effective
        logger.info(f"apply_power_saving_state: active={effective}")

        limits = getattr(self.settings, "power_saving_limits", {}) or {}

        if not self.active_monitors_dict:
            self.update_monitors_info()

        monitors_to_process = list(self.active_monitors_dict.keys())
        if not monitors_to_process:
            monitors_to_process = list(self.settings.brightness_values.keys())

        self._linking_suspended = True
        try:
            if effective:
                # Entering or updating power saving: clamp to limit
                target_values = self.coordinator.enter_power_saving(
                    live_brightness=self.settings.brightness_values,
                    fallback_brightness=self.settings.manual_brightness_values,
                    limits=limits,
                )

                for serial in monitors_to_process:
                    if serial in self.br_frames:
                        limit = limits.get(serial, 100)
                        target_val = target_values.get(serial, self.settings.brightness_values.get(serial, 50))
                        frame = self.br_frames[serial]
                        frame.slider.blockSignals(True)
                        frame.set_max_limit(limit, snap=not self.window_open)
                        frame.slider.blockSignals(False)
                        if not self.window_open:
                            frame.setValueBS(target_val)

                self.apply_brightness(target_values)

            else:
                # Exiting power saving: release limit and restore brightness
                restored_values = self.coordinator.exit_power_saving()

                for serial in monitors_to_process:
                    if serial in self.br_frames:
                        target_val = restored_values.get(serial, self.settings.brightness_values.get(serial, 50))
                        frame = self.br_frames[serial]
                        frame.slider.blockSignals(True)
                        frame.set_max_limit(100)
                        frame.slider.blockSignals(False)
                        if not self.window_open:
                            frame.setValueBS(target_val)

                if self.profile_active:
                    logger.info("Exited power saving: re-applying active profile brightness")
                    proc = getattr(self, "prev_active_process", None) or getattr(self, "active_process", None)
                    if proc:
                        self.prev_active_process = None
                        self._on_active_process_change({"exe_path": proc})
                elif self.settings.enable_time_adjustment:
                    logger.info("Exited power saving: executing recent schedule task")
                    self.execute_recent_task()
                else:
                    logger.info(f"Exited power saving: restoring pre-saving brightness {restored_values}")
                    for serial, val in restored_values.items():
                        self.settings.manual_brightness_values[serial] = val
                    self.settings.save("manual_brightness_values")
                    self.apply_brightness(restored_values)
        finally:
            self._linking_suspended = False

        if self.window_open:
            self.updateBottomFrame()

    def toggle_manual_power_saving(self, checked: bool):
        self.settings.power_saving_manual_state = checked
        self.settings.save("power_saving_manual_state")
        if hasattr(self, "power_saving_btn"):
            self.power_saving_btn.setIcon(self.get_icon_for_toggle_state("leaf", checked))
        logger.info(f"power_saving_manual_state toggled: {checked}")
        self.apply_power_saving_state()

    def on_power_saving_mode_changed(self, mode: str):
        logger.info(f"on_power_saving_mode_changed: {mode}")
        self.apply_power_saving_state(force=True)
        if self.window_open:
            self.updateBottomFrame()

    def on_power_saving_enabled_toggled(self, enabled: bool):
        logger.info(f"on_power_saving_enabled_toggled: {enabled}")
        self.apply_power_saving_state(force=True)
        if self.window_open:
            self.updateBottomFrame()

    def update_power_saving_limits(self):
        if self.is_power_saving_effective():
            self.apply_power_saving_state(force=True)

    # MARK: _on_lock_state_change()
    def _on_lock_state_change(self, state: str):
        logger.info(f"Screen state changed to: {state}")
        if state == "unlocked":
            self.execute_recent_task(delay=10 * 1000) # Execute after 10 seconds  
            # QTimer.singleShot(10 * 1000, self.execute_recent_task)

            # self.start_checking(interval=(cfg.timer_interval * 1000))
            QTimer.singleShot(15 * 1000, lambda: self.start_checking(interval=(cfg.timer_interval * 1000)))

            if self.settings.enable_profiles:
                self.start_process_listener()

        elif state == "locked":
            self.stop_checking()

            if self.settings.enable_profiles:
                self.stop_process_listener()


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
        self.screen_disabled = False
        self.timer.start(interval)
        logger.info(f"Task checking started (interval: {interval / 1000} sec)")


    # MARK: check_all_tasks()
    def check_all_tasks(self):
        log_messages = []
        current_time = QTime.currentTime().toString("HH:mm")
        idle_time = get_idle_time()
        can_change_br = True


        current_energy_saver = is_energy_saver_active()
        if current_energy_saver != self.is_energy_saver:
            self.energy_saver_changed.emit(current_energy_saver)

        timeout = self.display_timeout_ac
        power_type = "AC" # AC - plugged, DC - battery
        if self.is_laptop:
            on_battery = is_on_battery()
            timeout = self.display_timeout_dc if on_battery else self.display_timeout_ac
            power_type = "DC" if on_battery else "AC"
        

        # Calculate time_active, saved_time
        if self.settings.enable_idle_detection:
            if idle_time > (self.settings.break_idle_threshold * 60):
                logger.info(f"idle {self.settings.break_idle_threshold}min, reset time_active")
                self.time_active = 0
                self.saved_time = 0
            elif idle_time < (cfg.timer_interval * 1.0):
                self.time_active += cfg.timer_interval + self.saved_time
                self.saved_time = 0
            else:
                self.saved_time += cfg.timer_interval
        else:
            self.time_active += cfg.timer_interval
            self.saved_time = 0

        log_messages.append(
            f"idle: {idle_time:.2f}s, "
            f"timeout({power_type}): {timeout}s, "
            f"active: {self.time_active / 60:.2f}m, "
            f"saved: {self.saved_time / 60:.2f}m"
        )

    
        # Monitor connected monitors
        current_monitor_list = get_monitor_device_names()
        # logger.info(f"current_monitor_list: {current_monitor_list}")
        previous_serials = set(self.previous_monitor_list)
        current_serials = set(current_monitor_list)

        added_monitors = current_serials - previous_serials
        removed_monitors = previous_serials - current_serials

        if added_monitors or removed_monitors:
            self.update_monitors_info()

        if added_monitors:
            logger.info(f"Added monitors: {added_monitors}")
            if self.is_power_saving_effective():
                self.apply_power_saving_state(force=True)
            # QTimer.singleShot(10000, lambda: self.execute_recent_task(delay=10000))
            QTimer.singleShot(10 * 1000, self.execute_recent_task)
            can_change_br = False
        if removed_monitors:
            logger.info(f"Removed monitors: {removed_monitors}")
            for serial in removed_monitors:
                self.coordinator.remove_monitor(serial)

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


        # Check time adjustment tasks
        if (self.last_check_time != current_time) and can_change_br and self.settings.enable_time_adjustment:
            if current_time in self.settings.time_adjustment_data:
                if not self.profile_active:
                    self.apply_brightness(self.settings.time_adjustment_data[current_time])
                    log_messages.append(f"Applied brightness: {self.settings.time_adjustment_data[current_time]}")
            else:
                log_messages.append("idle")

        
        # Check time active for break reminders
        if (self.settings.enable_break_reminders and 
            (self.time_active >= (self.settings.break_notification_interval * 60)) and 
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

        if self.profile_active:
            logger.info(f"execute_recent_task: profile_active: {self.profile_active}, skip")
            return

        if (not self.settings.time_adjustment_data) or (not self.settings.enable_time_adjustment):
            logger.info("execute_recent_task: No tasks found")
            if self.settings.restore_last_brightness:
                logger.info("execute_recent_task: Restoring last brightness values")
                # self.apply_brightness(self.settings.brightness_values, delay=delay)
                self.apply_brightness(self.settings.manual_brightness_values, delay=delay)
            return

        # Get the current time and find the most recent task time
        current_time = QTime.currentTime().toString("HH:mm")
        recent_task_time = self.get_recent_task_time(current_time)
        if recent_task_time:
            logger.info(f"Executing task at: {recent_task_time}, delay: {delay / 1000} sec")
            self.apply_brightness(self.settings.time_adjustment_data[recent_task_time], delay=delay)
        else:
            logger.info("No task time available to execute")


    # MARK: get_recent_task_time()
    def get_recent_task_time(self, current_time: str):
        """Returns the most recent task time from time_adjustment_data."""
        task_data = getattr(self.settings, "time_adjustment_data", {}) or {}
        return self.coordinator.get_recent_task_time(task_data.keys(), current_time)


    # MARK: apply_brightness()
    def apply_brightness(self, brightness_data, delay=0):
        logger.info(f"apply_brightness: {brightness_data}, delay: {delay / 1000} sec")

        if self.is_power_saving_effective():
            limits = getattr(self.settings, "power_saving_limits", {}) or {}
            brightness_data = {
                s: self.coordinator.clamp_value(s, val, limit=limits.get(s, 100))
                for s, val in brightness_data.items()
            }

        self.update_monitors_info()
        for serial in self.active_monitors_dict:
            if serial in brightness_data:
                self.settings.brightness_values[serial] = brightness_data[serial]

        # play slider animation if window is open
        if self.window_open and (delay == 0):
            QTimer.singleShot(0, lambda: self.animate_sliders(self.br_frames, self.settings.brightness_values))
        else:
            if self.settings.show_brightness_popup:
                QTimer.singleShot(delay, self.show_popup)
            else:
                threading.Timer((delay / 1000), self.brightness_sync_onetime).start() # change brightness after delay


    # MARK: update_monitors_info()
    def update_monitors_info(self):
        monitors_info = get_monitors()
        self.monitors_dict = {monitor.serial: monitor for monitor in monitors_info}
        logger.debug(f"monitors_dict: {self.monitors_dict}")

        # Exclude monitors that are in self.settings.hidden_displays
        active_monitors_info = [monitor for monitor in monitors_info if monitor.serial not in self.settings.hidden_displays]
        self.active_monitors_dict = {monitor.serial: monitor for monitor in active_monitors_info}
        logger.info(f"active_monitors_dict {self.active_monitors_dict}")



    # MARK: update_central_widget()
    def update_central_widget(self, checked=None):
        self.window_offset = cfg.WIN11_WINDOW_OFFSET if self.settings.enable_rounded_corners else 0
        corner_radius = cfg.WIN11_WINDOW_CORNER_RADIUS if self.settings.enable_rounded_corners else 0
        self.centralWidget().setStyleSheet(
            f"""
            #Container {{
            background: {cfg.colors["main_bg"][self.theme]};
            border-radius: {corner_radius}px;
            border: 1px solid {cfg.colors["main_border"][self.theme]};
            }}
            """
        )


    # MARK: start_process_listener()
    def start_process_listener(self):
        logger.info("start_process_listener")
        self.process_listener_thread = threading.Thread(target=self.process_listener.run, daemon=True)
        self.process_listener_thread.start()
        logger.info(f"process_listener_thread.is_alive(): {self.process_listener_thread.is_alive()}")

    # MARK: stop_process_listener()
    def stop_process_listener(self):
        logger.info("stop_process_listener")
        if self.process_listener_thread:
            self.process_listener.stop()
            self.process_listener_thread.join()
            logger.info(f"process_listener_thread.is_alive(): {self.process_listener_thread.is_alive()}")
            
        self.profile_active = False
        self.execute_recent_task()

    # MARK: toggle_process_listener()
    def toggle_process_listener(self, enabled):
        if enabled:
            self.start_process_listener()
        else:
            self.stop_process_listener()


    # MARK: _on_active_process_change()
    def _on_active_process_change(self, process_info):
        exe_path = process_info["exe_path"]
        self.active_process = exe_path # using for settings window
        logger.info(f"Active process changed: {exe_path}")
        # hwnd, pid, p_name, p_path = get_active_process()

        # # close window if focus lost
        # if self.window_open and (exe_path != self.exe_path):
        #     logger.info(f"window_open and exe_path != self.exe_path, closing window")
        #     # self.animateWindowClose()
        #     self.hide_window()
        
        if (exe_path == self.prev_active_process):
            logger.info(f"exe_path == prev_active_process, skip")
            return


        profile_key = None
        profile = None

        # 1. Check for exact exe_path match
        if exe_path in self.settings.profiles_data:
            profile_key = exe_path
            profile = self.settings.profiles_data[exe_path]
        else:
            start_time = time.time()
            logger.info(f"No exact match for exe_path: {exe_path}, checking parent folders")
            # 2. Check for parent folder matches, prefer deepest match
            exe_path_norm = os.path.normcase(os.path.normpath(exe_path))
            best_match = ""

            for key in self.settings.profiles_data:
                key_norm = os.path.normcase(os.path.normpath(key))
                # Ensure trailing separator for folder match
                folder = key_norm if key_norm.endswith(os.sep) else key_norm + os.sep

                if exe_path_norm.startswith(folder):
                    # Prefer the longest (deepest) match
                    if len(folder) > len(best_match):
                        best_match = folder
                        profile_key = key

            if profile_key:
                profile = self.settings.profiles_data[profile_key]
            
            logger.info(f"Time taken to check parent folders: {time.time() - start_time:.2f} sec")


        if profile:
            self.reset_popup_timer()  # Reset the popup timer
            logger.info(f"Applying profile: {profile} (key: {profile_key})")
            self.profile_active = True
            self.apply_brightness(profile)
        else:
            if self.profile_active:
                self.reset_popup_timer()  # Reset the popup timer
                self.profile_active = False
                logger.info(f"Disabling profile")
                self.execute_recent_task()
            else: # reduce br changes when moving between processes outside profiles_data
                logger.info(f"No active profile, skip")
                
        self.prev_active_process = exe_path



    # MARK: update_autostart()
    def update_autostart(self, checked=None):
        if not getattr(sys, 'frozen', False): # if not running as EXE
            logger.info("Not running as EXE, skipping startup registry modification")
            return
        
        if self.settings.launch_on_startup:
            logger.info("Adding to startup")
            add_to_startup(cfg.app_name, self.exe_path)
        else:
            logger.info("Removing from startup")
            remove_from_startup(cfg.app_name)

    # MARK: update_logging()
    def update_logging(self, checked=None):
        if checked is not None:
            self.settings.enable_logging = checked
        set_file_logging(self.settings.enable_logging)


    # MARK: _determine_theme()
    def _determine_theme(self, theme: str = "Light"):
        """Determine self.theme and self.color_theme based on windows version and theme."""
        if (self.win_release != "11") and (not self.settings.enable_fusion_theme):
            self.theme = "Light"
        else:
            self.theme = theme
        logger.info(f"theme: {self.theme}")

        self.color_theme = f"Fusion{self.theme}" if self.settings.enable_fusion_theme else self.theme
        logger.info(f"color_theme: {self.color_theme}")

        return self.theme, self.color_theme

    # MARK: _apply_theme()
    def _apply_theme(self, theme: str):
        logger.info(f"Theme changed to: {theme}")
        self._determine_theme(theme)
        self.update_central_widget()
        self.tray_icon.changeIconTheme(theme)
        if self.settings_window:
            self.settings_window.theme = theme
            self.settings_window.color_theme = self.color_theme
            self.settings_window.update_tab_widget(force=True)



    # MARK: eventFilter()
    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        # hide window when focus is lost
        if event.type() == QEvent.Type.WindowDeactivate:
            logger.info("Window deactivated, hiding")
            # self.hide()
            # self.animateWindowClose()
            self.hide_window()
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
    def updateMonitorsFrame(self, popup=False):
        start_time = time.time()

        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # # Clear old monitor frames widgets but not the placeholder
        # for widget in self.monitors_widgets:
        #     widget.deleteLater()
        # self.monitors_widgets.clear()

        self.br_frames.clear()  # Clear brightness frames dictionary
        self.contrast_frames.clear()  # Clear contrast frames dictionary

        # placeholder if no monitors are available (or all are hidden)
        if not self.active_monitors_dict:  # Check if no monitors are available
            self.placeholder_widget = QWidget()
            self.placeholder_widget.setObjectName("MonitorWidget")
            self.placeholder_widget.setStyleSheet(
                f"""
                #MonitorWidget {{
                background: {cfg.colors["frame_bg"][self.theme]};
                border-radius: {6 if self.settings.enable_rounded_corners else 0}px;
                border: 1px solid {cfg.colors["frame_border"][self.theme]}; 
                }}
                """
            )

            placeholder_layout = QVBoxLayout(self.placeholder_widget)
            placeholder_layout.setContentsMargins(14, 12, 14, 14)

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
                                            font-size: 16px; font-weight: bold;
                                            """)
            placeholder_layout.addWidget(placeholder_label)
            self.monitors_layout.addWidget(self.placeholder_widget)
            return

        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.settings.monitors_order if serial in self.active_monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [serial for serial in self.active_monitors_dict if serial not in monitors_order]
        logger.debug(f"monitors_order: {monitors_order}")
        


        for index, monitor_serial in enumerate(monitors_order):
            monitor: Monitor = self.active_monitors_dict[monitor_serial]
            logger.info(f"{index + 1}: {monitor}")

            monitor_widget = QWidget()
            monitor_widget.setObjectName("MonitorWidget")
            monitor_widget.setStyleSheet(
                f"""
                #MonitorWidget {{
                background: {cfg.colors["frame_bg"][self.theme]};
                border-radius: {6 if self.settings.enable_rounded_corners else 0}px;
                border: 1px solid {cfg.colors["frame_border"][self.theme]}; 
                }}
                """
            )
            monitor_vbox = QVBoxLayout(monitor_widget)
            monitor_vbox.setSpacing(5)  # Spacing between monitor frames
            monitor_vbox.setContentsMargins(7, 7, 7, 7)
            

            # MARK: Label Frame
            label_frame = QWidget()
            label_hbox = QHBoxLayout(label_frame)
            # label_frame.setStyleSheet("background-color: red")
            label_hbox.setContentsMargins(0, 0, 0, 0)
            label_hbox.setSpacing(5)

            if monitor.method == "VCP": 
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
                                          m=monitor,
                                          mf=monitor_widget:
                                          self.power_off_monitor(m, mf))
                label_hbox.addWidget(power_btn)

                monitor_widget.enterEvent = lambda event, pb=power_btn: pb.applyHoverIcon()
                monitor_widget.leaveEvent = lambda event, pb=power_btn: pb.applyDefaultIcon()
            else: 
                # add monitor icon
                monitor_icon = QLabel()
                # monitor_icon.setStyleSheet("""background-color: blue;""")
                icon_size = 30
                if (monitor.device_name == "\\\\.\\DISPLAY1") and self.is_laptop:
                    monitor_icon.setPixmap(QIcon(cfg.icons["laptop"][self.theme]).pixmap(26, 26))
                else:
                    monitor_icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(icon_size, icon_size))
                monitor_icon.setFixedSize(icon_size, icon_size)
                monitor_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label_hbox.addWidget(monitor_icon)


            monitor_label_text = self.settings.custom_monitor_names[monitor_serial] if monitor_serial in self.settings.custom_monitor_names else monitor.display_name
            monitor_label = QLabel(monitor_label_text)
            # monitor_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            # monitor_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
            # monitor_label.setFixedHeight(80)
            monitor_label.setStyleSheet(f"""
                                        font-size: 16px; font-weight: bold;

                                        """) # background-color: blue;
            label_hbox.addWidget(monitor_label)
            

            # MARK: Resolution
            if self.settings.show_resolution and (not popup):
                available_resolutions = monitor.available_resolutions
                formatted_resolutions = [f"{width}x{height}" for width, height in available_resolutions]
                max_res_length = max(len(res) for res in formatted_resolutions)
                res_combobox_width = 110 if (max_res_length <= 9) else 120 if (max_res_length == 10) else 130
                rc_bg_color = (cfg.colors["combobox_bg"][self.theme] 
                               if not self.settings.enable_fusion_theme else None)
                
                res_combobox = StyledComboBox(self,
                                              down_arrow=cfg.icons["down_arrow"][self.theme], 
                                              bg_color=rc_bg_color,
                                              )
                res_combobox.setFixedWidth(res_combobox_width)
                res_combobox.setSizePolicy(QSizePolicy.Policy.Fixed, 
                                           QSizePolicy.Policy.Expanding)
                for res in available_resolutions:
                    res_combobox.addItem(f"{res[0]}x{res[1]}", res)
                res_combobox.setCurrentText(f"{monitor.resolution[0]}x{monitor.resolution[1]}")
                res_combobox.currentIndexChanged.connect(lambda index, 
                                                         m=monitor, 
                                                         cb=res_combobox: 
                                                         self.on_resolution_select(m, cb.currentData()))
                label_hbox.addWidget(res_combobox)

            monitor_vbox.addWidget(label_frame)
            

            # MARK: Refresh Rates
            refresh_rates = monitor.available_refresh_rates

            # Ensure the serial key exists
            if monitor_serial not in self.settings.excluded_rates:
                self.settings.excluded_rates[monitor_serial] = []
                logger.info(f"Added serial {monitor_serial} to excluded_rates with empty list")

            refresh_rates = [rate for rate in refresh_rates if rate not in self.settings.excluded_rates[monitor_serial]]

            if self.settings.show_refresh_rates and (len(refresh_rates) >= 2) and (not popup):
                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

                rr_frame = ButtonGridFrame(refresh_rates, 
                                           monitor.refresh_rate, 
                                           callback=lambda value, m=monitor: self.on_rr_button_click(value, m))
                monitor_vbox.addWidget(rr_frame)
                # rr_frame.setStyleSheet("background-color: green")
            
            
            # MARK: Brightness
            br_level = monitor.get_brightness(retries=5)
            # br_level = None
            brightness_failed = False
            if br_level is None:
                logger.warning(f"Failed to get brightness for monitor {monitor}")
                br_level = self.settings.brightness_values.get(monitor.serial, 50)
                brightness_failed = True

            # Add separator line
            monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

            if (self.settings.restore_last_brightness or popup) and (monitor.serial in self.settings.brightness_values):
                # restore brightness from saved values (restore_last_brightness feature)
                pass
            else:
                # didn't restore brightness, so save current value
                self.settings.brightness_values[monitor.serial] = br_level

            br_frame = SliderFrame(
                main_window=self,
                icon_path=cfg.icons["sun"][self.theme],
                value=br_level,
                slider_callback=lambda value, ms=monitor_serial: self.on_brightness_change(value, ms),
                disabled=brightness_failed,
            )
            br_frame.hardware_brightness = br_level
            self.br_frames[monitor.serial] = br_frame  # Store frame in dictionary
            if self.is_power_saving_effective():
                limit = (self.settings.power_saving_limits or {}).get(monitor.serial, 100)
                br_frame.set_max_limit(limit)
                if br_level > limit:
                    self.coordinator.record_pre_saving_brightness(monitor.serial, br_level)
                    br_frame.setValueBS(limit)
                    self.settings.brightness_values[monitor.serial] = limit
                    threading.Timer(0.05, self.brightness_sync_onetime).start()
            monitor_vbox.addWidget(br_frame)


            # MARK: Contrast
            if self.settings.show_contrast_sliders and (monitor.method == "VCP") and (not popup):
                contrast_level = None
                if br_frame.isEnabled():
                    contrast_level = monitor.get_contrast(retries=5)
                # contrast_level = None

                contrast_failed = False
                if contrast_level is None:
                    logger.warning(f"Failed to get contrast for monitor {monitor}")
                    contrast_level = self.settings.contrast_values.get(monitor.serial, 50)
                    contrast_failed = True

                # self.contrast_values[monitor_serial] = contrast_level # dont change contrast
                
                # Add separator line
                monitor_vbox.addWidget(SeparatorLine(color=cfg.colors["separator"][self.theme]))

                contrast_frame = SliderFrame(
                    main_window=self,
                    icon_path=cfg.icons["contrast"][self.theme],
                    value=contrast_level,
                    slider_callback=lambda value, ms=monitor_serial: self.on_contrast_change(value, ms),
                    disabled=contrast_failed,
                )
                self.contrast_frames[monitor.serial] = contrast_frame
                monitor_vbox.addWidget(contrast_frame)

            self.monitors_layout.addWidget(monitor_widget)
            # self.monitors_widgets.append(monitor_widget)  # Store monitor frame in list

        logger.debug(f"brightness_values {self.settings.brightness_values}")
        logger.debug(f"contrast_values {self.settings.contrast_values}")

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
        bf_label.setWordWrap(True)
        bf_label.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 padding-bottom: 2px;

                                 """) # padding-left: 5px; background-color: blue;
        self.bottom_frame_hbox.addWidget(bf_label)

        self.is_energy_saver = is_energy_saver_active()
        logger.info(f"updateBottomFrame is_energy_saver: {self.is_energy_saver}")

        mode = getattr(self.settings, "power_saving_mode", "windows")
        limits_enabled = getattr(self.settings, "enable_power_saving_limits", True)

        if limits_enabled:
            if mode == "windows":
                if self.is_energy_saver:
                    self.energy_saver_indicator = QPushButton()
                    self.energy_saver_indicator.setFixedSize(30, 39)
                    self.energy_saver_indicator.setIcon(QIcon(cfg.icons["leaf"][self.theme]))
                    self.energy_saver_indicator.setIconSize(QSize(21, 21))
                    self.energy_saver_indicator.setFlat(True)
                    self.energy_saver_indicator.setToolTip("Energy Saver is active (Following Windows. Switch to manual in Settings)")
                    self.energy_saver_indicator.setStyleSheet("""
                        QPushButton {
                            background: transparent;
                            border: none;
                        }
                    """)
                    self.bottom_frame_hbox.addWidget(self.energy_saver_indicator)
            else:
                self.power_saving_btn = QPushButton()
                self.power_saving_btn.setCheckable(True)
                manual_state = bool(getattr(self.settings, "power_saving_manual_state", False))
                self.power_saving_btn.setChecked(manual_state)
                self.power_saving_btn.setFixedSize(41, 39)
                self.power_saving_btn.setIcon(self.get_icon_for_toggle_state("leaf", manual_state))
                self.power_saving_btn.setIconSize(QSize(21, 21))
                self.power_saving_btn.setToolTip("Power Saving (Manual mode)")
                self.power_saving_btn.toggled.connect(self.toggle_manual_power_saving)
                self.bottom_frame_hbox.addWidget(self.power_saving_btn)

        if len(self.active_monitors_dict) > 1:
            self.link_br_btn = QPushButton()
            self.link_br_btn.setCheckable(True)
            self.link_br_btn.setChecked(self.settings.link_brightness)
            self.link_br_btn.setFixedSize(41, 39) # 39 39
            self.link_br_btn.setIcon(self.get_icon_for_toggle_state("link", self.settings.link_brightness))
            self.link_br_btn.setIconSize(QSize(21, 21))
            self.link_br_btn.setToolTip("Link brightness levels")
            self.link_br_btn.toggled.connect(self.toggle_link_brightness)
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
        self.settings.link_brightness = checked
        self.link_br_btn.setIcon(self.get_icon_for_toggle_state("link", checked))
        logger.info(f"link_brightness - {checked}")


    # MARK: get_icon_for_toggle_state()
    def get_icon_for_toggle_state(self, icon_name, checked):
        if self.settings.enable_fusion_theme:
            icon_path = cfg.icons[icon_name][self.theme]
        else:
            if self.theme == "Light":
                icon_path = cfg.icons[icon_name]["Dark"] if checked else cfg.icons[icon_name]["Light"]
            else:
                icon_path = cfg.icons[icon_name]["Light"] if checked else cfg.icons[icon_name]["Dark"]
        return QIcon(icon_path)


    # MARK: power_off_monitor()
    def power_off_monitor(self, monitor: Monitor, monitor_widget: QWidget):
        status_4 = monitor.set_power_mode(4, retries=7)
        # time.sleep(0.1)
        status_5 = monitor.set_power_mode(5, retries=7)
        logger.info(f"power_off_monitor {monitor.display_name}: status_4: {status_4}, status_5: {status_5}")
        
        if status_4 or status_5:
            monitor_widget.setDisabled(True)
        else:
            logger.warning(f"Failed to power off monitor {monitor.display_name}.")


    # MARK: on_rr_button_click()
    def on_rr_button_click(self, rate, monitor: Monitor):
        logger.info(f"Selected refresh rate: {rate} Hz for monitor {monitor}")

        self.update_monitors_info()
        updated_monitor: Monitor = self.active_monitors_dict.get(monitor.serial, None)

        if not updated_monitor:
            logger.warning(f"Monitor {monitor} not found")
            return False
        
        if updated_monitor and (updated_monitor.refresh_rate == rate):
            logger.info(f"Monitor {monitor} already has refresh rate {rate} Hz")
            return False

        # save brightness and contrast before changing refresh rate
        brightness_before = None
        contrast_before = None
        serial = monitor.serial
        method = monitor.method

        # get brightness before changing refresh rate
        if serial in self.settings.brightness_values:
            brightness_before = self.settings.brightness_values[serial]
        else:
            brightness_before = monitor.get_brightness(retries=7)

        # get contrast before changing refresh rate
        if (method == "VCP") and self.settings.show_contrast_sliders:
            if serial in self.settings.contrast_values:
                contrast_before = self.settings.contrast_values[serial]
            else:
                contrast_before = monitor.get_contrast(retries=7)

        logger.info(f"brightness_before: {brightness_before}, contrast_before: {contrast_before}")

        #restore brightness and contrast after 6 seconds
        def restore_parameters():
            logger.info(f"restore_parameters {monitor}: {brightness_before}, {contrast_before}")
            if brightness_before is not None:
                self.settings.brightness_values[serial] = brightness_before
            if contrast_before is not None:
                self.settings.contrast_values[serial] = contrast_before
            self.brightness_sync_onetime()
            
        # if not set_refresh_rate(monitor, rate): # set refresh rate
        if not monitor.set_refresh_rate(rate):
            return False
        else:
            threading.Timer(6, restore_parameters).start()
            # QTimer.singleShot(6000, restore_parameters)
            return True



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor: Monitor, resolution):
        logger.info(f"on_resolution_select {monitor} {resolution}")
        
        width, height = resolution
        monitor.set_resolution(width, height)
        
        QTimer.singleShot(500, self.updateSizeAndPosition)


    # MARK: on_brightness_change()
    def on_brightness_change(self, value, monitor_serial):
        # logger.info(f"on_brightness_change: {value}, {monitor_serial}")
        is_ps = self.is_power_saving_effective()
        limits = self.settings.power_saving_limits or {}

        if self.settings.link_brightness and not self._linking_suspended:
            new_values = self.coordinator.calculate_linked_change(
                master_serial=monitor_serial,
                new_master_value=value,
                current_values=self.settings.brightness_values,
                limits=limits,
                is_power_saving=is_ps,
            )
            for serial, new_val in new_values.items():
                if serial != monitor_serial and serial in self.br_frames:
                    if self.br_frames[serial].slider.isEnabled():
                        self.br_frames[serial].setValueBS(new_val)
                self.settings.brightness_values[serial] = new_val
                if not is_ps:
                    self.settings.manual_brightness_values[serial] = new_val
        else:
            clamped_val = self.coordinator.resolve_brightness(
                enable_profiles=False,
                profile_value=None,
                enable_schedule=False,
                schedule_value=None,
                manual_value=value,
                is_power_saving=is_ps,
                power_saving_limit=limits.get(monitor_serial, 100),
            )
            self.settings.brightness_values[monitor_serial] = clamped_val
            if not is_ps:
                self.settings.manual_brightness_values[monitor_serial] = clamped_val

        if not is_ps:
            self.settings.save("manual_brightness_values")

        self.reset_popup_timer()  # Reset the popup timer


    # MARK: on_contrast_change()
    def on_contrast_change(self, value, monitor_serial):
        # print(f"on_contrast_change: {value}, {monitor_serial}")
        self.settings.contrast_values[monitor_serial] = int(value)


    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, delta):
        # logger.info(f"on_bottom_frame_scroll delta: {delta}")

        self._linking_suspended = True
        try:
            for frame in self.br_frames.values():
                slider = frame.slider
                if slider.isEnabled():
                    limit = getattr(slider, "max_limit", slider.maximum())
                    new_value = max(0, min(limit, slider.value() + (1 if delta > 0 else -1)))
                    slider.setValue(new_value)
        finally:
            self._linking_suspended = False


    # MARK: brightness_sync()
    def brightness_sync(self):
        # self.update_monitors_info()

        previous_brightness_values = {}
        previous_contrast_values = {}

        while self.window_open:
            # start_time = time.time()
            
            brightness_values_copy = self.settings.brightness_values.copy()
            for monitor_serial, brightness in brightness_values_copy.items():
                if self.is_power_saving_effective():
                    limit = (self.settings.power_saving_limits or {}).get(monitor_serial, 100)
                    brightness = self.coordinator.clamp_value(monitor_serial, brightness, limit=limit)
                    self.settings.brightness_values[monitor_serial] = brightness

                if (monitor_serial in self.active_monitors_dict) and ( # check if monitor is connected
                    previous_brightness_values.get(monitor_serial) != brightness # check if brightness changed
                ):
                    try:
                        monitor: Monitor = self.active_monitors_dict[monitor_serial]
                        if not monitor.set_brightness(brightness, retries=1):
                            raise Exception(f"Failed to set brightness for monitor {monitor}")
                        logger.info(f"brightness_sync set_brightness {monitor}: {brightness}")

                        previous_brightness_values[monitor_serial] = brightness
                        self.settings.save("brightness_values")

                    except Exception as e:
                        logger.error(f"Error: {e}")
            
            if self.settings.show_contrast_sliders:
                contrast_values_copy = self.settings.contrast_values.copy()
                for monitor_serial, contrast in contrast_values_copy.items():
                    if (monitor_serial in self.active_monitors_dict) and ( # check if monitor is connected
                        previous_contrast_values.get(monitor_serial) != contrast # check if contrast changed
                    ):
                        try:
                            monitor: Monitor = self.active_monitors_dict[monitor_serial]
                            if not monitor.set_contrast(contrast, retries=1):
                                raise Exception(f"Failed to set contrast for monitor {monitor}")
                            logger.info(f"brightness_sync set_contrast {monitor}: {contrast}")

                            previous_contrast_values[monitor_serial] = contrast
                            self.settings.save("contrast_values")

                        except Exception as e:
                            logger.error(f"Error: {e}")

            # logger.debug(f"Brightness sync took {time.time() - start_time:.4f} seconds")
            time.sleep(0.10) # 0.15


    # MARK: brightness_sync_onetime()
    def brightness_sync_onetime(self):
        logger.info("brightness_sync_onetime")
        start_time = time.time()
        # self.update_monitors_info()

        brightness_values_copy = self.settings.brightness_values.copy()
        for monitor_serial, brightness in brightness_values_copy.items():
            if monitor_serial in self.active_monitors_dict:  # Check if monitor is connected
                if self.is_power_saving_effective():
                    limit = (self.settings.power_saving_limits or {}).get(monitor_serial, 100)
                    brightness = self.coordinator.clamp_value(monitor_serial, brightness, limit=limit)
                    self.settings.brightness_values[monitor_serial] = brightness
                try:
                    monitor: Monitor = self.active_monitors_dict[monitor_serial]
                    if not monitor.set_brightness(brightness, retries=7):
                        raise Exception(f"Failed to set brightness for monitor {monitor}")
                    logger.info(f"brightness_sync_onetime set_brightness {monitor}: {brightness}")

                except Exception as e:
                    logger.error(f"Error: {e}")
        
        if self.settings.show_contrast_sliders:
            contrast_values_copy = self.settings.contrast_values.copy()
            for monitor_serial, contrast in contrast_values_copy.items():
                if monitor_serial in self.active_monitors_dict: # Check if monitor is connected
                    try:
                        monitor: Monitor = self.active_monitors_dict[monitor_serial]
                        if not monitor.set_contrast(contrast, retries=7):
                            raise Exception(f"Failed to set contrast for monitor {monitor}")
                        logger.info(f"brightness_sync_onetime set_contrast {monitor}: {contrast}")

                    except Exception as e:
                        logger.error(f"Error: {e}")

        logger.info(f"brightness_sync_onetime took {time.time() - start_time:.4f} seconds")


    # MARK: get_screen_and_target_rect()
    def get_screen_and_target_rect(self, screen=None):
        if screen is None:
            screen = getattr(self, "current_screen", None)
        if screen is None and self.isVisible():
            screen = self.screen() or QGuiApplication.screenAt(self.geometry().center())
        if screen is None:
            cursor_pos = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()

        full_rect = screen.geometry()
        work_rect = screen.availableGeometry()

        win_w = self.width()
        win_h = self.sizeHint().height()
        offset = self.window_offset

        is_popup = getattr(self, "is_popup", False)
        popup_pos = getattr(self.settings, "popup_position", "bottom_right")

        taskbar_edge, target_rect, start_rect, end_rect = calculate_window_rects(
            full_rect=full_rect,
            work_rect=work_rect,
            win_w=win_w,
            win_h=win_h,
            offset=offset,
            is_popup=is_popup,
            popup_position=popup_pos,
        )
        return screen, taskbar_edge, target_rect, start_rect, end_rect

    # MARK: showEvent()
    def showEvent(self, event):
        logger.info("showEvent")

        # hide window offscreen to avoid flickering before opening animation
        if getattr(self, "current_screen", None) is None:
            self.current_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        screen = self.current_screen
        full_rect = screen.geometry()
        self.move(full_rect.right() + 100, full_rect.bottom() + 100)

        super().showEvent(event)
        self.window_open = True

        if self.settings.enable_window_animation:
            QTimer.singleShot(0, self.animateWindowOpen)
        else:
            QTimer.singleShot(0, self.updateSizeAndPosition)

        self.raise_()


    # MARK: show_window()
    def show_window(self):
        logger.info("show_window")

        if self.window_open:
            logger.info("Window is already open")
            return

        self.current_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.is_popup = False
        self.update_monitors_info()

        self.updateBottomFrame() # Update bottom frame contents each time the window is shown
        self.bottom_frame.show()
        self.updateMonitorsFrame()  # Update frame contents each time the window is shown
        
        self.show() # call showEvent()
        self.activateWindow() # focus on window
        
        self.start_brightness_sync_thread(delay_msec=250)

        if self.settings.restore_last_brightness:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.br_frames, self.settings.brightness_values))
        if self.settings.show_contrast_sliders:
            QTimer.singleShot(150, lambda: self.animate_sliders(self.contrast_frames, self.settings.contrast_values))


    # MARK: show_popup()
    def show_popup(self):
        logger.info("show_popup")
        
        if self.window_open:
            logger.info("Window is already open")
            return

        self.current_screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.is_popup = True
        # self.update_monitors_info()

        self.updateBottomFrame() # Update bottom frame contents each time the window is shown
        self.bottom_frame.hide()
        self.updateMonitorsFrame(popup=True)  # Update frame contents each time the window is shown
        
        # Suppress popup if enabled and all active monitors are already at target brightness
        if self.settings.skip_popup_if_unchanged:
            all_matched = bool(self.br_frames) and all(
                getattr(frame, "hardware_brightness", frame.slider.value()) == self.settings.brightness_values.get(serial)
                for serial, frame in self.br_frames.items()
                if serial in self.active_monitors_dict
            )
            if all_matched:
                logger.info("show_popup: All monitors already match target brightness, suppressing popup")
                threading.Thread(target=self.brightness_sync_onetime, daemon=True).start()
                return

        self.show() # call showEvent()
        
        self.start_brightness_sync_thread(delay_msec=250)
        # threading.Timer(0.25, self.brightness_sync_onetime).start() # change brightness after delay

        # if self.settings.restore_last_brightness or True:
        QTimer.singleShot(300, lambda: self.animate_sliders(self.br_frames, self.settings.brightness_values))
        # if self.settings.show_contrast_sliders:
        #     QTimer.singleShot(300, lambda: self.animate_sliders(self.contrast_frames, self.settings.contrast_values))

        # QTimer.singleShot(1750, self.animateWindowClose)
        self.popup_timer.start(1750)


    # MARK: reset_popup_timer()
    def reset_popup_timer(self):
        if self.window_open and self.popup_timer.isActive():
            logger.info("Resetting popup timer")
            self.popup_timer.start(1750)


    # MARK: hide_window()
    def hide_window(self):
        logger.info("hide_window")

        self.window_open = False

        if self.settings.enable_window_animation:
            self.animateWindowClose()
        else:
            self.hide()

        self.stop_brightness_sync_thread()


    # MARK: hideEvent()
    def hideEvent(self, event):
        logger.info("hideEvent")

        self.window_open = False
        self.current_screen = None
        # self.stop_brightness_sync_thread()

        # QTimer.singleShot(2000, self.stop_brightness_sync_thread)  # Add 2-second delay
        # QTimer.singleShot(1000, self.brightness_sync_onetime)
        super().hideEvent(event)


    # MARK: start_brightness_sync_thread()
    def start_brightness_sync_thread(self, delay_msec=250):
        delay_sec = delay_msec / 1000.0
        if (self.brightness_sync_thread is None) or (not self.brightness_sync_thread.is_alive()):
            self.brightness_sync_thread = threading.Timer(delay_sec, self.brightness_sync)
            self.brightness_sync_thread.daemon = True
            self.brightness_sync_thread.start()
            logger.info(f"brightness_sync_thread started, delay: {delay_sec}s")
        else:
            logger.info("brightness_sync_thread is already running")

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


    # MARK: animate_sliders()
    def animate_sliders(self, frames: dict, values: dict):
        logger.info(f"animate_sliders: {list(frames.keys())}, {values}")
        for index, (serial, frame) in enumerate(frames.items()):
            if serial in values:
                # QTimer.singleShot(index * 100, lambda s=slider: s.animate_to(int(values[serial])))
                frame.animate_to(int(values[serial]))


    # MARK: updateSizeAndPosition()
    def updateSizeAndPosition(self):
        screen, taskbar_edge, target_rect, _, _ = self.get_screen_and_target_rect()
        logger.info(f"taskbar_edge: {taskbar_edge}, target_rect: {target_rect}")

        self.move(target_rect.x(), target_rect.y())
        logger.info(f"move: ({target_rect.x()}, {target_rect.y()})")

        self.resize(target_rect.width(), target_rect.height())
        logger.info(f"resize: ({target_rect.width()}, {target_rect.height()})")



    # MARK: animateWindowOpen()
    def animateWindowOpen(self):
        screen, taskbar_edge, target_rect, start_rect, _ = self.get_screen_and_target_rect()
        end_rect = target_rect
        
        logger.info(f"taskbar_edge: {taskbar_edge}, start_rect: {start_rect}, end_rect: {end_rect}")

        self.open_animation = QPropertyAnimation(self, b"geometry") 
        self.open_animation.setStartValue(start_rect)
        self.open_animation.setEndValue(end_rect)
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
        
        self.open_animation.finished.connect(self.on_open_animation_finished)  # Update size and position after animation is done
        self.open_animation.start()
        self.open_opacity_animation.start()

    def on_open_animation_finished(self):
        logger.info("Open animation finished")


    # MARK: animateWindowClose()
    def animateWindowClose(self):
        screen, taskbar_edge, target_rect, _, end_rect = self.get_screen_and_target_rect()
        current_rect = self.geometry()
        end_rect = calculate_close_rect(target_rect, end_rect, current_rect)
        
        logger.info(f"current_rect: {current_rect}, end_rect: {end_rect}")
        
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
        
        # self.close_animation.finished.connect(self.hide) # hide window after animation is done
        self.close_animation.finished.connect(self.on_close_animation_finished)
        self.close_animation.start()
        self.close_opacity_animation.start()
        
    def on_close_animation_finished(self):
        logger.info("Close animation finished")
        self.hide()
        self.current_screen = None


    # MARK: openSettingsWindow()
    def openSettingsWindow(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        elif self.settings_window.isMinimized():
            self.settings_window.showNormal()

        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()


    # MARK: on_exit()
    def on_exit(self):
        logger.info("Exiting application...")
        QGuiApplication.quit()



# MARK: main
if __name__ == "__main__":

    app = QApplication([]) 
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(cfg.icons["monitune"]["Light"]))

    logger.info(f"Starting {cfg.app_name} (v{cfg.version})")

    # Check if another instance is already running
    if getattr(sys, 'frozen', False):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex = kernel32.CreateMutexW(None, False, "MoniTuneQtMutex")
        if not mutex: # Error creating mutex
            logger.error(f"Error code: {ctypes.get_last_error()}")
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS (mutex already exists)
            logger.warning(f"Another instance of {cfg.app_name} is already running.")
            # Create a message box to notify the user
            QMessageBox.information(
                None,
                cfg.app_name,
                f"Another instance of {cfg.app_name} is already running.\nPlease close the other instance to continue.",
                QMessageBox.StandardButton.Ok
            )
            sys.exit(1)

    logger.info(f"Available styles: {QStyleFactory.keys()}") # ['windows11', 'windowsvista', 'Windows', 'Fusion']
    # app.setStyle("windows11")
    logger.info(f"Current style: {app.style().objectName()}")

    window = MainWindow()

    if not getattr(sys, 'frozen', False): # if run from source code
        window.openSettingsWindow()
        window.show_window()

    sys.exit(app.exec())