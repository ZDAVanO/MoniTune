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
    QSpinBox,
    QProgressBar,
)
from PySide6.QtCore import (
    Qt, 
    QTimer, 
    QTime,
    QSize,
)
from PySide6.QtGui import QIcon

from custom_widgets import (
    NoScrollSlider,
    SeparatorLine,
    FadingWidget,
)

from services.settings_manager import get_settings
from utils.monitor_utils import (
    get_monitors, 
)
from utils.reg_utils import (
    is_dark_theme, 
    key_exists, 
    create_reg_key, 
    reg_write_bool, 
    reg_read_bool, 
    reg_write_int,
    reg_read_int,
    reg_write_list, 
    reg_read_list, 
    reg_write_dict, 
    reg_read_dict,
    delete_reg_key,
)
from utils.utils import (
    check_github_update_available,
)
import config as cfg
import resources_rc
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




# MARK: BaseToggleButton
class BaseToggleButton(QPushButton):
    def __init__(self, 
                 tool_tip=None, 
                 initial_state=False, 
                 callback=None):
        super().__init__()

        self.callback = callback

        # self.setMinimumSize(77, 28)
        self.setCheckable(True)
        self.setChecked(initial_state)
        self.setText("Enabled" if initial_state else "Disabled")

        if tool_tip:
            self.setToolTip(tool_tip)

        self.toggled.connect(self.on_toggle)

    # MARK: on_toggle()
    def on_toggle(self, checked):
        logger.info(f"toggle button - {checked}")
        self.setText("Enabled" if checked else "Disabled")

        if callable(self.callback):
            self.callback(checked)


# MARK: SettingToggleButton
class SettingToggleButton(BaseToggleButton):
    def __init__(self, 
                 main_window, 
                 tool_tip,
                 setting_name, 
                 reg_setting_name, 
                 callback=None, 
                 after_restart=False):
        
        

        # Отримуємо поточний стан з main_window перед ініціалізацією базового класу
        checked = getattr(main_window, setting_name)
        
        super().__init__(
            tool_tip=tool_tip,
            initial_state=checked,
            callback=callback
        )

        self.setMinimumSize(77, 28)

        self.main_window = main_window
        self.setting_name = setting_name
        self.reg_setting_name = reg_setting_name
        self.after_restart = after_restart

    # Перевизначаємо on_toggle
    def on_toggle(self, checked):
        logger.info(f"toggle {self.setting_name} - {checked}")
        self.setText("Enabled" if checked else "Disabled")

        if not self.after_restart:
            setattr(self.main_window, self.setting_name, checked)

        get_settings().set(self.setting_name, checked)

        if callable(self.callback):
            self.callback(checked)



# # MARK: SettingToggleButton
# class SettingToggleButton(QPushButton):
#     def __init__(self, 
#                  main_window, 
#                  tool_tip,
#                  setting_name, 
#                  reg_setting_name, 
#                  callback=None, 
#                  after_restart=False):
#         super().__init__()

#         self.main_window = main_window
#         self.setting_name = setting_name
#         self.reg_setting_name = reg_setting_name
#         self.callback = callback
#         self.after_restart = after_restart

#         self.setMinimumSize(77, 28)
#         self.setCheckable(True)

#         checked = getattr(self.main_window, self.setting_name)
#         self.setChecked(checked)
#         self.setText("Enabled" if checked else "Disabled")
        
#         if tool_tip:
#             self.setToolTip(tool_tip)

#         self.toggled.connect(self.on_toggle)
        
#     # MARK: on_toggle()
#     def on_toggle(self, checked):
#         logger.info(f"toggle {self.setting_name} - {checked}")
#         self.setText("Enabled" if checked else "Disabled")

#         # print(self.sizeHint().width())
#         # print(self.height())

#         if not self.after_restart:
#             setattr(self.main_window, self.setting_name, checked)
#         reg_write_bool(cfg.REGISTRY_PATH, self.reg_setting_name, checked)
#         if callable(self.callback):
#             self.callback(checked)



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


# MARK: BreakReminderSettingFrame
class BreakReminderSettingFrame(SettingFrame):
    def __init__(self, main_window):
        super().__init__(settings_window=main_window, 
                         title="Eye Break Reminder", 
                         descr="Get reminders to rest your eyes.")
        self.main_window = main_window

        self.enable_toggle = SettingToggleButton(
            main_window=main_window,
            tool_tip=None,
            setting_name="enable_break_reminders",
            reg_setting_name="EnableBreakReminders",
            callback=self.on_enable_toggled
        )
        self.title_layout.addWidget(self.enable_toggle, alignment=Qt.AlignmentFlag.AlignRight)

        self.sub_options_widget = QWidget()
        sub_layout = QVBoxLayout(self.sub_options_widget)
        sub_layout.setContentsMargins(0, 4, 0, 0)
        sub_layout.setSpacing(8)

        # 1) Idle Detection Sub-Row
        row1 = QWidget()
        r1_layout = QHBoxLayout(row1)
        r1_layout.setContentsMargins(0, 0, 0, 0)
        r1_layout.setSpacing(6)

        r1_info = QWidget()
        r1_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r1_info_layout = QVBoxLayout(r1_info)
        r1_info_layout.setContentsMargins(0, 0, 0, 0)
        r1_info_layout.setSpacing(0)
        r1_title = QLabel("Idle Detection")
        r1_descr = QLabel("Pause and reset timer when idle. If disabled, reminders trigger at fixed intervals.")
        r1_descr.setWordWrap(True)
        fading_descr1 = FadingWidget(fade_opacity=0.75, duration=300)
        fading_descr1.box_layout.addWidget(r1_descr)
        r1_info_layout.addWidget(r1_title)
        r1_info_layout.addWidget(fading_descr1)

        self.idle_toggle = SettingToggleButton(
            main_window=main_window,
            tool_tip=None,
            setting_name="enable_idle_detection",
            reg_setting_name="EnableIdleDetection"
        )
        r1_layout.addWidget(r1_info)
        r1_layout.addWidget(self.idle_toggle, alignment=Qt.AlignmentFlag.AlignRight)
        r1_layout.setStretch(0, 1)
        r1_layout.setStretch(1, 0)
        sub_layout.addWidget(row1)

        sub_layout.addWidget(SeparatorLine(color=cfg.colors["s_sep"][main_window.color_theme]))

        # 2) Reminder Interval Sub-Row
        row2 = QWidget()
        r2_layout = QHBoxLayout(row2)
        r2_layout.setContentsMargins(0, 0, 0, 0)
        r2_layout.setSpacing(6)

        r2_info = QWidget()
        r2_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r2_info_layout = QVBoxLayout(r2_info)
        r2_info_layout.setContentsMargins(0, 0, 0, 0)
        r2_info_layout.setSpacing(0)
        r2_title = QLabel("Reminder Interval")
        r2_descr = QLabel("Time interval between break reminders.")
        r2_descr.setWordWrap(True)
        fading_descr2 = FadingWidget(fade_opacity=0.75, duration=300)
        fading_descr2.box_layout.addWidget(r2_descr)
        r2_info_layout.addWidget(r2_title)
        r2_info_layout.addWidget(fading_descr2)

        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 180)
        self.interval_spinbox.setSuffix(" min")
        self.interval_spinbox.setFixedWidth(115)
        settings = get_settings()
        current_interval = settings.break_notification_interval
        self.interval_spinbox.setValue(current_interval)
        setattr(main_window, "break_notification_interval", current_interval)
        self.interval_spinbox.valueChanged.connect(self.on_interval_changed)

        r2_layout.addWidget(r2_info)
        r2_layout.addWidget(self.interval_spinbox, alignment=Qt.AlignmentFlag.AlignRight)
        r2_layout.setStretch(0, 1)
        r2_layout.setStretch(1, 0)
        sub_layout.addWidget(row2)

        sub_layout.addWidget(SeparatorLine(color=cfg.colors["s_sep"][main_window.color_theme]))

        # 3) Idle Reset Threshold Sub-Row
        row3 = QWidget()
        r3_layout = QHBoxLayout(row3)
        r3_layout.setContentsMargins(0, 0, 0, 0)
        r3_layout.setSpacing(6)

        r3_info = QWidget()
        r3_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        r3_info_layout = QVBoxLayout(r3_info)
        r3_info_layout.setContentsMargins(0, 0, 0, 0)
        r3_info_layout.setSpacing(0)
        r3_title = QLabel("Idle Reset Threshold")
        r3_descr = QLabel("Idle time required to reset the break timer.")
        r3_descr.setWordWrap(True)
        fading_descr3 = FadingWidget(fade_opacity=0.75, duration=300)
        fading_descr3.box_layout.addWidget(r3_descr)
        r3_info_layout.addWidget(r3_title)
        r3_info_layout.addWidget(fading_descr3)

        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(1, 60)
        self.threshold_spinbox.setSuffix(" min")
        self.threshold_spinbox.setFixedWidth(115)
        current_threshold = settings.break_idle_threshold
        self.threshold_spinbox.setValue(current_threshold)
        setattr(main_window, "break_idle_threshold", current_threshold)
        self.threshold_spinbox.valueChanged.connect(self.on_threshold_changed)

        r3_layout.addWidget(r3_info)
        r3_layout.addWidget(self.threshold_spinbox, alignment=Qt.AlignmentFlag.AlignRight)
        r3_layout.setStretch(0, 1)
        r3_layout.setStretch(1, 0)
        sub_layout.addWidget(row3)

        sub_layout.addWidget(SeparatorLine(color=cfg.colors["s_sep"][main_window.color_theme]))

        # 4) Next Reminder Progress Sub-Row
        row4 = QWidget()
        r4_layout = QVBoxLayout(row4)
        r4_layout.setContentsMargins(0, 0, 0, 0)
        r4_layout.setSpacing(6)

        r4_header = QWidget()
        r4_header_layout = QHBoxLayout(r4_header)
        r4_header_layout.setContentsMargins(0, 0, 0, 0)
        r4_header_layout.setSpacing(6)

        r4_title = QLabel("Next Reminder")
        self.progress_label = QLabel()
        fading_progress_label = FadingWidget(fade_opacity=0.75, duration=300)
        fading_progress_label.box_layout.addWidget(self.progress_label)

        r4_header_layout.addWidget(r4_title)
        r4_header_layout.addWidget(fading_progress_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        is_dark = "Dark" in main_window.color_theme
        bg_color = "#3c3c3c" if is_dark else "#e5e5e5"
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {bg_color};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: palette(highlight);
                border-radius: 3px;
            }}
        """)

        r4_layout.addWidget(r4_header)
        r4_layout.addWidget(self.progress_bar)
        sub_layout.addWidget(row4)

        self.content_layout.addWidget(self.sub_options_widget)

        initial_enabled = settings.enable_break_reminders
        self.sub_options_widget.setEnabled(initial_enabled)

        # Timer for updating progress (active only when widget is visible)
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_progress)

    def showEvent(self, event):
        super().showEvent(event)
        logger.info("BreakReminderSettingFrame shown, starting update_timer")
        self.update_progress()
        if not self.update_timer.isActive():
            self.update_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        logger.info("BreakReminderSettingFrame hidden, stopping update_timer")
        if self.update_timer.isActive():
            self.update_timer.stop()

    def update_progress(self):
        interval_min = getattr(self.main_window, "break_notification_interval", cfg.break_notification_interval)
        total_sec = max(1, interval_min * 60)
        active_sec = getattr(self.main_window, "time_active", 0)
        current_sec = min(active_sec, total_sec)

        self.progress_bar.setRange(0, total_sec)
        self.progress_bar.setValue(int(current_sec))

        enabled = getattr(self.main_window, "enable_break_reminders", False)
        if not enabled:
            self.progress_label.setText("Disabled")
            return

        remaining_sec = max(0, total_sec - current_sec)
        rem_min = int(remaining_sec // 60)
        rem_sec = int(remaining_sec % 60)

        if rem_min > 0:
            if rem_sec > 0:
                self.progress_label.setText(f"{rem_min}m {rem_sec:02d}s remaining")
            else:
                self.progress_label.setText(f"{rem_min} min remaining")
        else:
            self.progress_label.setText(f"{rem_sec}s remaining")

    def on_enable_toggled(self, enabled):
        self.sub_options_widget.setEnabled(enabled)
        self.update_progress()

    def on_interval_changed(self, value):
        get_settings().break_notification_interval = value
        setattr(self.main_window, "break_notification_interval", value)
        logger.info(f"Updated BreakNotificationInterval: {value}")
        self.update_progress()

    def on_threshold_changed(self, value):
        get_settings().break_idle_threshold = value
        setattr(self.main_window, "break_idle_threshold", value)
        logger.info(f"Updated BreakIdleThreshold: {value}")





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
        get_settings().tray_icon_name = icon_name

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



# MARK: PopupPositionFrame
class PopupPositionFrame(BaseSettingFrame):
    def __init__(self, main_window):
        super().__init__(title="Popup Position", 
                         descr="Choose which screen corner the brightness popup appears in.")
        self.main_window = main_window

        self.combo = QComboBox()
        self.combo.addItem("Bottom Right", "bottom_right")
        self.combo.addItem("Top Right", "top_right")
        self.combo.addItem("Bottom Left", "bottom_left")
        self.combo.addItem("Top Left", "top_left")
        self.combo.setMinimumWidth(180)

        current_pos = getattr(main_window.settings, "popup_position", "bottom_right")
        idx = self.combo.findData(current_pos)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

        self.combo.currentIndexChanged.connect(self.on_position_changed)
        self.title_layout.addWidget(self.combo, alignment=Qt.AlignmentFlag.AlignRight)

    def on_position_changed(self, index):
        pos = self.combo.currentData()
        logger.info(f"Popup position changed to: {pos}")
        get_settings().set("popup_position", pos)


# MARK: PowerSavingModeFrame
class PowerSavingModeFrame(BaseSettingFrame):
    def __init__(self, main_window):
        super().__init__(title="Activation Mode", 
                         descr="Choose whether to follow Windows Energy Saver or toggle manually in MoniTune.")
        self.main_window = main_window

        self.combo = QComboBox()
        self.combo.addItem("Follow Windows Energy Saver", "windows")
        self.combo.addItem("Manual control in MoniTune", "manual")
        self.combo.setMinimumWidth(240)

        current_mode = getattr(main_window.settings, "power_saving_mode", "windows")
        idx = self.combo.findData(current_mode)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

        self.combo.currentIndexChanged.connect(self.on_mode_changed)
        self.title_layout.addWidget(self.combo, alignment=Qt.AlignmentFlag.AlignRight)

    def on_mode_changed(self, index):
        mode = self.combo.currentData()
        logger.info(f"Power Saving mode changed to: {mode}")
        get_settings().set("power_saving_mode", mode)
        if hasattr(self.main_window, "on_power_saving_mode_changed"):
            self.main_window.on_power_saving_mode_changed(mode)


# MARK: PowerSavingLimitsFrame
class PowerSavingLimitsFrame(SettingFrame):
    def __init__(self, settings_window, monitors_order, display_names):
        super().__init__(settings_window, 
                         title="Monitor Brightness Limits",
                         descr="Set the maximum brightness allowed during Power Saving. Set to 100% for no limit.")
        self.settings_window = settings_window
        self.monitors_order = monitors_order
        self.display_names = display_names
        self.sliders = {}
        self._debounce_timers = {}

        limits_data = self.settings_window.settings.power_saving_limits or {}

        sliders_container = QHBoxLayout()
        sliders_container.setContentsMargins(9, 6, 9, 6)
        sliders_container.setSpacing(0)

        names_layout = QVBoxLayout()
        sliders_layout = QVBoxLayout()
        sliders_container.addLayout(names_layout)
        sliders_container.addItem(QSpacerItem(12, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        sliders_container.addLayout(sliders_layout)

        for serial in monitors_order:
            label = QLabel(display_names.get(serial, serial))
            names_layout.addWidget(label)

            slider_layout = QHBoxLayout()
            slider = NoScrollSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            initial_val = int(limits_data.get(serial, 100))
            slider.setValue(initial_val)
            self.sliders[serial] = slider

            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(300)
            timer.timeout.connect(lambda s=serial, sl=slider: self.commit_limit(s, sl.value()))
            self._debounce_timers[serial] = timer

            spacer = QSpacerItem(6, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

            value_label = QLabel("No limit" if initial_val == 100 else f"{initial_val}%")
            value_label.setFixedWidth(55)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            slider.valueChanged.connect(
                lambda val, s=serial, lbl=value_label, sl=slider: self.on_slider_value_changed(s, val, lbl, sl)
            )
            slider.sliderReleased.connect(
                lambda s=serial, sl=slider: self.on_slider_released(s, sl)
            )

            slider_layout.addWidget(slider)
            slider_layout.addItem(spacer)
            slider_layout.addWidget(value_label)
            sliders_layout.addLayout(slider_layout)

        self.content_layout.addLayout(sliders_container)

    def on_slider_value_changed(self, serial, value, label, slider):
        label.setText("No limit" if value == 100 else f"{value}%")
        if slider.isSliderDown():
            # Actively dragging with mouse: update label only, don't spam hardware
            timer = self._debounce_timers.get(serial)
            if timer and timer.isActive():
                timer.stop()
        else:
            # Changed without dragging (e.g. keyboard navigation): debounce commit
            timer = self._debounce_timers.get(serial)
            if timer:
                timer.start(300)

    def on_slider_released(self, serial, slider):
        timer = self._debounce_timers.get(serial)
        if timer and timer.isActive():
            timer.stop()
        self.commit_limit(serial, slider.value())

    def commit_limit(self, serial, value):
        current_limits = dict(self.settings_window.settings.power_saving_limits or {})
        if current_limits.get(serial) == int(value):
            return
        current_limits[serial] = int(value)
        self.settings_window.settings.set("power_saving_limits", current_limits)
        if hasattr(self.settings_window.main_window, "update_power_saving_limits"):
            self.settings_window.main_window.update_power_saving_limits()

    def on_slider_changed(self, serial, value, label):
        label.setText("No limit" if value == 100 else f"{value}%")
        self.commit_limit(serial, value)


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

        self.toggle_bth = BaseToggleButton(initial_state=True)
        # self.toggle_bth.setStyleSheet("padding: 4px 10px;")
        # self.toggle_bth.clicked.connect(self.choose_exe_dialog)
        self.title_layout.addWidget(self.toggle_bth)

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


# MARK: IgnoredProcessRow
class IgnoredProcessRow(QWidget):
    def __init__(self, settings_window, pattern: str):
        super().__init__()
        self.settings_window = settings_window
        self.pattern = pattern

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.entry = QLineEdit(pattern)
        self.entry.setReadOnly(True)
        layout.addWidget(self.entry, stretch=1)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("padding: 4px 10px;")
        self.delete_button.clicked.connect(lambda: self.settings_window.remove_ignored_process(self.pattern))
        layout.addWidget(self.delete_button)



# MARK: ScrollableTab
class ScrollableTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setStyleSheet("background-color: red;")

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
        self.settings = get_settings()
        self.theme = self.main_window.theme
        self.color_theme = self.main_window.color_theme

        self.setWindowTitle(f"{cfg.app_name} Settings")
        self.setWindowIcon(QIcon(cfg.icons["monitune"]["Light"]))
        
        self.resize(520, 620)
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)

        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        # self.tab_widget.setDocumentMode(True)
        # self.tab_widget.setStyleSheet(f"""
        #                               QTabWidget::pane {{
        #                                     background-color: transparent;
        #                                 }}
        #                               """)

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
        
        # self.serial_list = []

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    # MARK: showEvent()
    def showEvent(self, event):
        logger.info("Settings window opened")
        # self.update_tab_widget()
        QTimer.singleShot(0, self.update_tab_widget)
        super().showEvent(event)

        if self.ap_timer and (not self.ap_timer.isActive()):
            self.ap_timer.start(1000)
            logger.info("ap_timer started")

    # MARK: closeEvent()
    def closeEvent(self, event):
        logger.info("Settings window closed and unloaded")

        if self.ap_timer and self.ap_timer.isActive():
            self.ap_timer.stop()
            logger.info("ap_timer stopped")

        if self.main_window:
            self.main_window.settings_window = None

        super().closeEvent(event)

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
        self.settings.time_adjustment_data = sorted_time_adjustment_data


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
        self.settings.profiles_data = self.profiles_data

    # MARK: Ignored processes helpers
    def add_ignored_process(self, pattern: str):
        if not pattern:
            return
        cleaned = pattern.strip().strip('"').strip("'")
        if not cleaned:
            return
        current = list(self.settings.ignored_processes)
        if any(p.lower() == cleaned.lower() for p in current):
            logger.info(f"Process already in ignored list: {cleaned}")
            return
        current.append(cleaned)
        self.settings.ignored_processes = current
        self.populate_ignored_processes()

    def remove_ignored_process(self, pattern: str):
        cleaned = pattern.strip().strip('"').strip("'")
        current = [p for p in self.settings.ignored_processes if p.lower() != cleaned.lower()]
        self.settings.ignored_processes = current
        self.populate_ignored_processes()

    def populate_ignored_processes(self):
        if not hasattr(self, "ignored_list_layout"):
            return
        while self.ignored_list_layout.count():
            item = self.ignored_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for pattern in self.settings.ignored_processes:
            row = IgnoredProcessRow(self, pattern)
            self.ignored_list_layout.addWidget(row)



    # MARK: show_main_window()
    def show_main_window(self):
        QTimer.singleShot(400, self.main_window.show)


    # Mark: on_tab_change()
    def on_tab_change(self, index):
        logger.debug(f"on_tab_change index: {index}")
        self.selected_tab = index


    # MARK: update_tab_widget()
    def update_tab_widget(self, force=False):
        start_time = time.time()
        
        monitors_info = get_monitors()

        # # prevent unnecessary updates
        # serial_list = [monitor.serial for monitor in monitors_info]
        # if (serial_list == self.serial_list) and (not force):
        #     logger.info("Monitors info not changed")
        #     return
        # self.serial_list = serial_list


        self.tab_widget.blockSignals(True)
        # Clear old widgets
        # print("Clearing tabs : ", self.tab_widget.count())
        while self.tab_widget.count(): # num of tabs
            self.tab_widget.removeTab(0) # remove the first tab

        self.time_adjustment_frames = [] # clear the list of frames
        self.profiles_frames = [] # clear the list of frames


        # hidden_displays = reg_read_list(cfg.REGISTRY_PATH, "HiddenDisplays")
        # # Exclude monitors that are in self.hidden_displays
        # monitors_info = [monitor for monitor in monitors_info if monitor.serial not in hidden_displays]

        # Створюємо словник, де ключ — серійний номер
        monitors_dict = {monitor.serial: monitor for monitor in monitors_info}
        reg_order = self.settings.monitors_order
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in reg_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor.serial for monitor in monitors_info if monitor.serial not in monitors_order]
        custom_monitor_names = self.settings.custom_monitor_names

        display_names = {}
        short_display_names = {}
        for monitor in monitors_info:
            serial = monitor.serial
            if serial in custom_monitor_names:
                display_names[serial] = f"{custom_monitor_names[serial]} ({monitor.display_name})"
                short_display_names[serial] = custom_monitor_names[serial]
            else:
                display_names[serial] = monitor.display_name
                short_display_names[serial] = monitor.display_name


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
                                                           title="Enable Logging",
                                                           descr="Save application logs to MoniTune.log file.",
                                                           setting_name="enable_logging", 
                                                           reg_setting_name="EnableLogging",
                                                           callback=self.main_window.update_logging))

        general_tab.layout_.addWidget(BreakReminderSettingFrame(self.main_window))

        

        tray_icon_selector = TrayIconSelector(self.main_window)
        tray_icon = self.settings.tray_icon
        logger.info(f"tray_icon: {tray_icon}")
        tray_icon_selector.select_icon(tray_icon)
        general_tab.layout_.addWidget(tray_icon_selector)


        # MARK: Hide Displays
        hidden_displays = self.settings.hidden_displays
        logger.info(f"Hidden displays (settings): {hidden_displays}")

        def update_hidden_displays(monitor_id, state):
            if state == 2: # 2 - checked
                # if monitor_id not in hidden_displays:
                #     hidden_displays.append(monitor_id)
                if monitor_id in hidden_displays:
                    hidden_displays.remove(monitor_id)
            else: # 0 - unchecked
                # if monitor_id in hidden_displays:
                #     hidden_displays.remove(monitor_id)
                if monitor_id not in hidden_displays:
                    hidden_displays.append(monitor_id)
            self.settings.hidden_displays = hidden_displays
            logger.info(f"Updated hidden displays: {hidden_displays}")

        hide_displays_frame = SettingFrame(self, "Hide Displays")
        for serial in monitors_order:
            checkbox = QCheckBox(display_names[serial])
            checkbox.setChecked(serial not in hidden_displays)
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
            # # self.show_main_window()
            self.settings.custom_monitor_names = custom_monitor_names

        rename_monitors_frame = SettingFrame(self, "Rename Monitors")
        for serial in monitors_order:
            row_frame = QWidget()
            row_layout = QHBoxLayout(row_frame)
            # row_frame.setStyleSheet("background-color: red")
            row_layout.setContentsMargins(0, 0, 0, 0)

            icon = QLabel()
            icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(22, 22))
            row_layout.addWidget(icon)

            label = QLabel(f"{monitors_dict[serial].display_name}")
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
            self.settings.monitors_order = monitors_order
            # self.show_main_window()

        reorder_monitors_frame = SettingFrame(self, "Reorder Monitors")
        reorder_monitors_frame.content_layout.setContentsMargins(1, 0, 1, 3)
        reorder_monitors_frame.content_layout.setSpacing(0)

        list_widget = QListWidget()
        list_widget.setFrameShape(QFrame.Shape.NoFrame)
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        item_height = 36
        list_widget.setFixedHeight(len(monitors_order) * item_height)
        list_widget.setStyleSheet("""
                                  QListWidget {
                                      background: transparent;
                                  }
                                  QListWidget::item {
                                      padding: 0px;
                                      border: none;
                                  }
                                  """)
        list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # allow drag-and-drop
        list_widget.model().rowsMoved.connect(save_order)
        
        # monitors_order = [1, 2, 3]
        for serial in monitors_order:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, serial)

            widget = QWidget()
            widget.setFixedHeight(item_height)
            layout = QHBoxLayout(widget)
            # layout.setContentsMargins(2, 0, 2, 0)
            # layout.setContentsMargins(0, 0, 0, 0)
            layout.setContentsMargins(8, 0, 8, 0)

            icon = QLabel()
            icon.setPixmap(QIcon(cfg.icons["monitor"][self.theme]).pixmap(22, 22))
            icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout.addWidget(icon)

            label = QLabel(display_names[serial])
            # label = QLabel(f"Monitor {serial}")
            layout.addWidget(label)

            item.setSizeHint(QSize(0, item_height))
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
                self.settings.reset_to_defaults()

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
        excluded_rates = self.settings.excluded_rates
        logger.info(f"Excluded refresh rates: {excluded_rates}")

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

            self.settings.excluded_rates = excluded_rates
            logger.info(f"Updated excluded list: {excluded_rates}")

        exclude_rr_frame = SettingFrame(self, "Exclude Refresh Rates")

        # for monitor in monitors_info:
        for serial in monitors_order:
            monitor = monitors_dict[serial]
            available_rates = sorted(set(monitor.available_refresh_rates))

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
        
        # MARK: Popup Frame
        popup_frame = SettingFrame(settings_window=self, 
                                   title="Show Popup on background change", 
                                   descr="Show app window when brightness changing in background.")

        skip_popup_frame = SettingToggleFrame(main_window=self.main_window,
                                              title="Skip Popup if brightness unchanged",
                                              descr="Do not show popup if monitors already match the target brightness.",
                                              setting_name="skip_popup_if_unchanged",
                                              reg_setting_name="SkipPopupIfUnchanged")

        position_frame = PopupPositionFrame(main_window=self.main_window)

        def on_popup_toggled(checked):
            skip_popup_frame.setEnabled(checked)
            position_frame.setEnabled(checked)

        popup_toggle = SettingToggleButton(self.main_window,
                                           tool_tip="Show app window when brightness changing in background.",
                                           setting_name="show_brightness_popup",
                                           reg_setting_name="ShowBrightnessPopup",
                                           callback=on_popup_toggled)
        popup_frame.title_layout.addWidget(popup_toggle, alignment=Qt.AlignmentFlag.AlignRight)

        skip_popup_frame.setEnabled(self.settings.show_brightness_popup)
        position_frame.setEnabled(self.settings.show_brightness_popup)
        popup_frame.content_layout.addWidget(skip_popup_frame)
        popup_frame.content_layout.addWidget(position_frame)
        brightness_tab.layout_.addWidget(popup_frame)



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
                                                                     descr=f"Adjust the brightness to match the most relevant time when {cfg.app_name} starts.",
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

        # Restore TimeAdjustmentFrame widgets from settings
        saved_data = self.settings.time_adjustment_data
        # print("Saved data:", saved_data)
        for time_str, brightness_data in reversed(saved_data.items()):
            # print(f"Adding frame with time: {time_str}, brightness: {brightness_data}")
            add_time_adjustment_frame(time_str, brightness_data)



        # MARK: Power Saving Tab
        power_saving_tab = ScrollableTab()
        self.tab_widget.addTab(power_saving_tab, "Power Saving")

        power_saving_tab.layout_.addWidget(SettingToggleFrame(
            main_window=self.main_window,
            title="Enable Power Saving Limits",
            descr="Limit maximum brightness on configured monitors when power saving is active.",
            setting_name="enable_power_saving_limits",
            reg_setting_name="EnablePowerSavingLimits",
            callback=self.main_window.on_power_saving_enabled_toggled
        ))

        power_saving_tab.layout_.addWidget(PowerSavingModeFrame(self.main_window))

        power_saving_tab.layout_.addWidget(PowerSavingLimitsFrame(
            self, monitors_order, display_names
        ))

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
            if path == self.main_window.exe_path:
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
        ap_ignore_btn = QPushButton("Ignore")
        ap_ignore_btn.setStyleSheet("padding: 4px 10px;")
        ap_ignore_btn.setToolTip("Add the active app to the ignored processes list")
        ap_ignore_btn.clicked.connect(lambda: self.add_ignored_process(ap_line_edit.text()))
        ap_frame_layout.addWidget(ap_ignore_btn)

        self.ap_timer = QTimer()
        self.ap_timer.timeout.connect(update_ap_line_edit)
        self.ap_timer.start(1000)

        profiles_frame.content_layout.addWidget(ap_frame)

        # Debounce / Switch delay row
        delay_row = QFrame(frameShape=QFrame.Shape.StyledPanel)
        delay_layout = QHBoxLayout(delay_row)
        delay_label = QLabel("Switch delay:")
        delay_layout.addWidget(delay_label)
        delay_layout.addStretch()

        delay_spinbox = QSpinBox()
        delay_spinbox.setRange(0, 2000)
        delay_spinbox.setSingleStep(50)
        delay_spinbox.setSuffix(" ms")
        delay_spinbox.setFixedWidth(100)
        delay_spinbox.setValue(self.settings.profile_switch_delay_ms)
        delay_spinbox.setToolTip("Wait time before applying profile or restoring brightness on window focus change.\nPrevents flicker when Alt-Tabbing rapidly or clicking the taskbar/tray.")
        delay_spinbox.valueChanged.connect(lambda val: setattr(self.settings, "profile_switch_delay_ms", val))
        delay_layout.addWidget(delay_spinbox)

        profiles_frame.content_layout.addWidget(delay_row)

        # Profile path matching guide / examples
        hint_frame = QWidget()
        hint_layout = QVBoxLayout(hint_frame)
        hint_layout.setContentsMargins(4, 2, 4, 4)
        hint_label = QLabel(
            "<b>Path matching examples:</b><br>"
            "• <b>Exact executable:</b> <code>C:\\Games\\Cyberpunk 2077\\bin\\x64\\Cyberpunk2077.exe</code><br>"
            "• <b>Folder for all games inside:</b> <code>D:\\Games</code> or <code>C:\\SteamLibrary\\steamapps\\common</code><br>"
            "• <b>Priority:</b> More specific (deeper) folder paths always win over general parent directories."
        )
        hint_label.setWordWrap(True)
        fading_hint = FadingWidget(fade_opacity=0.75, duration=300)
        fading_hint.box_layout.addWidget(hint_label)
        hint_layout.addWidget(fading_hint)
        profiles_frame.content_layout.addWidget(hint_frame)

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

        # Restore ProfileFrame widgets from settings
        profiles_data = self.settings.profiles_data
        for path, brightness_data in reversed(profiles_data.items()):
            add_profile_frame(path, brightness_data)

        profiles_tab.layout_.addWidget(profiles_frame)

        # MARK: Ignored Processes Frame
        ignored_frame = SettingFrame(
            self,
            "Ignored Processes",
            "Processes that won't deactivate the active profile when focused (e.g. tray apps, overlays, volume mixers)."
        )

        add_ignored_row = QWidget()
        add_ignored_layout = QHBoxLayout(add_ignored_row)
        add_ignored_layout.setContentsMargins(0, 0, 0, 0)

        ignored_input = QLineEdit()
        ignored_input.setPlaceholderText("e.g. EarTrumpet.exe, C:\\Path\\App.exe, or folder")
        add_ignored_layout.addWidget(ignored_input, stretch=1)

        def choose_ignored_exe():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select executable to ignore", "", "EXE Files (*.exe);;All Files (*)"
            )
            if file_path:
                ignored_input.setText(file_path)

        ignored_select_btn = QPushButton("Select")
        ignored_select_btn.setStyleSheet("padding: 4px 10px;")
        ignored_select_btn.clicked.connect(choose_ignored_exe)
        add_ignored_layout.addWidget(ignored_select_btn)

        def on_add_ignored():
            text = ignored_input.text()
            if text:
                self.add_ignored_process(text)
                ignored_input.clear()

        ignored_add_btn = QPushButton("Add")
        ignored_add_btn.setStyleSheet("padding: 4px 10px;")
        ignored_add_btn.clicked.connect(on_add_ignored)
        add_ignored_layout.addWidget(ignored_add_btn)

        ignored_frame.content_layout.addWidget(add_ignored_row)

        ignored_list_container = QWidget()
        self.ignored_list_layout = QVBoxLayout(ignored_list_container)
        self.ignored_list_layout.setContentsMargins(0, 0, 0, 0)
        ignored_frame.content_layout.addWidget(ignored_list_container)

        self.populate_ignored_processes()

        profiles_tab.layout_.addWidget(ignored_frame)



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
            # update_available, latest_version = self.main_window.check_for_update()
            update_available, latest_version = check_github_update_available(
                repo_api_url=cfg.UPDATE_CHECK_URL,
                current_version=cfg.version,
            )
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

        logger.info(f"update_tab_widget took {time.time() - start_time:.4f} seconds")













