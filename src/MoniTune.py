from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QGuiApplication, QWheelEvent, QKeyEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStyle,
    QToolButton,
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

from custom_widgets.custom_comboboxes import NoScrollComboBox
from custom_widgets.custom_sliders import CustomSlider, AnimatedSlider, AnimatedSliderBlockSignals
from custom_widgets.custom_buttons import RRButton
from custom_widgets.custom_labels import BrightnessIcon

from brightness_scheduler import BrightnessScheduler

from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, get_brightness, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict
import config
from config import WIN11_WINDOW_CORNER_RADIUS, WIN11_WINDOW_OFFSET

import darkdetect

import sys
import os
import ctypes
import threading
import time
import platform

import psutil



def is_laptop():
    battery = psutil.sensors_battery()
    return battery is not None



class SeparatorLine(QFrame):
    def __init__(self, color: str = None, line_width: int = 1, parent=None):
        super().__init__(parent)

        fusion_style = QStyleFactory.create("Fusion")

        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyle(fusion_style)
        if color:
            self.setStyleSheet(f"color: {color};")
        self.setLineWidth(line_width)



# MARK: MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.is_laptop = is_laptop()

        self.window_width = 358
        self.window_height = 231

        self.setMinimumWidth(self.window_width)
        self.setMaximumWidth(self.window_width)
        
        self.enable_rounded_corners = reg_read_bool(config.REGISTRY_PATH, "EnableRoundedCorners")
        if self.enable_rounded_corners:
            self.window_corner_radius = WIN11_WINDOW_CORNER_RADIUS
            self.window_offset = WIN11_WINDOW_OFFSET
        else:
            self.window_corner_radius = 0
            self.window_offset = 0

        self.custom_monitor_names = reg_read_dict(config.REGISTRY_PATH, "CustomMonitorNames")
        print(f"custom_monitor_names {self.custom_monitor_names}")

        self.monitors_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")


        self.show_resolution = reg_read_bool(config.REGISTRY_PATH, "ShowResolution")
        self.allow_res_change = reg_read_bool(config.REGISTRY_PATH, "AllowResolutionChange")


        self.show_refresh_rates = reg_read_bool(config.REGISTRY_PATH, "ShowRefreshRates")
        self.excluded_rates = list(map(int, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates")))
        # self.excluded_rates = list(map(int, filter(None, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates"))))

        
        self.restore_last_brightness = reg_read_bool(config.REGISTRY_PATH, "RestoreLastBrightness")
        
        self.hidden_displays = reg_read_list(config.REGISTRY_PATH, "HiddenDisplays")



        self.settings_window = None  # No settings window yet
        self.rr_buttons = {}  # Dictionary to store refresh rate buttons for each monitor
        self.br_sliders = {}  # Dictionary to store brightness sliders

        self.window_open = False
        self.brightness_sync_thread = None

        self.brightness_values = reg_read_dict(config.REGISTRY_PATH, "BrightnessValues")
        print(f"self.brightness_values {self.brightness_values}")
        self.previous_brightness_values = {}  # Dictionary to store previous brightness values


        self.update_bottom_frame = True # Flag to update bottom frame
        self.connected_monitors = []  # List to store currently connected monitors


        self.win_release = platform.release()
        self.enable_fusion_theme = reg_read_bool(config.REGISTRY_PATH, "EnableFusionTheme")
        if self.enable_fusion_theme:
            QApplication.instance().setStyle("Fusion")
        self.update_theme_colors(darkdetect.theme())


        self.setWindowTitle("MoniTune")
        self.resize(self.window_width, self.window_height)

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
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
        self.bottom_frame.setFixedHeight(60)
        self.bottom_frame.installEventFilter(self)
        self.bottom_hbox = QHBoxLayout(self.bottom_frame)
        self.bottom_hbox.setContentsMargins(7, 0, 11, 0)
        # self.bottom_hbox.setContentsMargins(7, 0, 7, 0)
        self.bottom_hbox.setSpacing(5)

        # self.updateBottomFrame()

        

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
        # self.tray_icon.showMessage("MoniTune", "MoniTune is running", QIcon(config.app_icon_path))
        # self.tray_icon.changeIconTheme(darkdetect.theme())
        # self.tray_icon.changeIconName("monitune")

        # Run the theme listener in a separate thread
        threading.Thread(target=darkdetect.listener, args=(self.on_theme_change,), daemon=True).start()



        # Time adjustment
        self.time_adjustment_startup = reg_read_bool(config.REGISTRY_PATH, "TimeAdjustmentStartup")
        self.time_adjustment_data = reg_read_dict(config.REGISTRY_PATH, "TimeAdjustmentData")
        self.scheduler = BrightnessScheduler()
        self.update_scheduler_tasks()
        if self.time_adjustment_startup:
            self.scheduler.execute_recent_task()




        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.bottom_frame.setStyleSheet("background-color: green;") 
        # self.openSettingsWindow() # Open settings window on startup

        


    # MARK: update_scheduler_tasks()
    def update_scheduler_tasks(self):
        print("update_scheduler_tasks")
        self.scheduler.clear_all_tasks()

        for time_str, brightness_data in self.time_adjustment_data.items():
            # self.scheduler.add_task(time_str, lambda: self.test_br_change_to(brightness_data))
            self.scheduler.add_task(time_str, lambda bd=brightness_data: self.bg_br_change(bd))

        self.scheduler.start_checking()


    # MARK: bg_br_change()
    def bg_br_change(self, brightness_data):
        print("bg_br_change")
        # self.show()
        self.update_connected_monitors()
        # print(f"self.connected_monitors {self.connected_monitors}")
        for monitor_serial in self.connected_monitors:
            if monitor_serial in brightness_data:
                # update brightness slider
                if monitor_serial in self.br_sliders:
                    if self.window_open:
                        QTimer.singleShot(0, self.start_brightness_animation) # play slider animation if window is open
                    # else:
                    #     self.br_sliders[monitor_serial].setValue(brightness_data[monitor_serial])
                self.brightness_values[monitor_serial] = brightness_data[monitor_serial]
            else:
                print(f"Monitor {monitor_serial} not found in brightness_data ----------------------------------------------------------------")

        self.brightness_sync_onetime()

        # QTimer.singleShot(1000, self.animateWindowClose)


    # MARK: update_connected_monitors()
    def update_connected_monitors(self):
        monitors_info = get_monitors_info()

        # Exclude monitors that are in self.hidden_displays
        monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in self.hidden_displays]
        # print(f" -------- update_connected_monitors monitors_info {monitors_info}")

        self.connected_monitors = [monitor['serial'] for monitor in monitors_info]









    # MARK: update_central_widget()
    def update_central_widget(self):
        self.window_offset = WIN11_WINDOW_OFFSET if self.enable_rounded_corners else 0
        corner_radius = WIN11_WINDOW_CORNER_RADIUS if self.enable_rounded_corners else 0
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
            self.bg_color = config.bg_color_light
            self.border_color = config.border_color_light

            self.fr_color = config.fr_color_light  
            self.fr_border_color = config.fr_border_color_light

            self.rr_border_color = config.rr_border_color_light
            self.rr_fg_color = config.rr_fg_color_light
            self.rr_hover_color = config.rr_hover_color_light

            self.separator_color = config.separator_color_light

            # icons
            self.settings_icon_path = config.settings_icon_light_path

            self.monitor_icon_path = config.monitor_icon_light_path
            self.laptop_icon_path = config.laptop_icon_light_path

            self.sun_icon_path = config.sun_icon_light_path

            self.down_arrow_icon_path = config.down_arrow_icon_light_path
        else:
            # colors for dark theme
            self.bg_color = config.bg_color_dark
            self.border_color = config.border_color_dark

            self.fr_color = config.fr_color_dark  
            self.fr_border_color = config.fr_border_color_dark

            self.rr_border_color = config.rr_border_color_dark
            self.rr_fg_color = config.rr_fg_color_dark
            self.rr_hover_color = config.rr_hover_color_dark

            self.separator_color = config.separator_color_dark

            # icons
            self.settings_icon_path = config.settings_icon_dark_path

            self.monitor_icon_path = config.monitor_icon_dark_path
            self.laptop_icon_path = config.laptop_icon_dark_path

            self.sun_icon_path = config.sun_icon_dark_path

            self.down_arrow_icon_path = config.down_arrow_icon_dark_path

        # print("Checking MEIPASS contents:")
        # print(os.listdir(sys._MEIPASS))

    # MARK: on_theme_change()
    def on_theme_change(self, theme: str): # "Light" or "Dark"
        print(f"Theme changed to: {theme}")
        self.update_theme_colors(theme)
        self.update_central_widget()
        self.update_bottom_frame = True
        self.tray_icon.changeIconTheme(theme)

        



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




        monitors_info = get_monitors_info()

        # Exclude monitors that are in self.hidden_displays
        monitors_info = [monitor for monitor in monitors_info if monitor['serial'] not in self.hidden_displays]

        if not monitors_info:  # Check if no monitors are available
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

            # placeholder_label = QLabel("No monitors found")
            placeholder_label = QLabel(
                'No compatible displays found. '
                'Please check that "DDC/CI" is enabled for your displays, '
                'or make sure the monitors are not currently hidden.'
            )
            placeholder_label.setWordWrap(True)
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            placeholder_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
            placeholder_label.setStyleSheet("""
                                            font-size: 16px;
                                            font-weight: bold;
                                            color: lightgray;
                                            """)
            placeholder_layout.addWidget(placeholder_label)

            self.monitors_layout.addWidget(placeholder_frame)

            return


        print(f"monitors_info {monitors_info}")
        # monitors_info.reverse()  # Invert the order of monitors
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.monitors_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]

        self.connected_monitors = [monitor['serial'] for monitor in monitors_info]  # Update connected monitors list





        for index, monitor_serial in enumerate(monitors_order):
            if monitor_serial in self.hidden_displays:
                continue

            monitor = monitors_dict[monitor_serial]

            
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
            monitor_vbox.setContentsMargins(0, 0, 0, 0)
            # monitor_vbox.setSpacing(5)  # Spacing between monitor frames
            monitor_vbox.setSpacing(0)  # Spacing between monitor frames
            monitor_vbox.setContentsMargins(7, 7, 7, 7)
            # monitor_vbox.setContentsMargins(0, 5, 0, 5)
            

            # MARK: Monitor Label
            label_frame = QWidget()
            # label_frame.setMinimumHeight(34)
            # label_frame.setFixedHeight(34)
            label_hbox = QHBoxLayout(label_frame)
            # label_hbox.setContentsMargins(12, 7, 7, 0)
            label_hbox.setContentsMargins(7, 7, 7, 0)
            label_hbox.setContentsMargins(0, 0, 0, 0)
            # label_hbox.setSpacing(5)
            label_hbox.setSpacing(7)
            label_hbox.setSpacing(6)
            # label_hbox.setSpacing(2)

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

                                        

                                        
                                        """) # padding-left: 1px; background-color: blue; padding-bottom: 2px; font-size: 16px; font-weight: bold; font: 16px "{config.font_family}";
            label_hbox.addWidget(monitor_label)
            
            
            if self.show_resolution:
                if self.allow_res_change:
                    available_resolutions = monitor["AvailableResolutions"]
                    sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
                    formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]
                    
                    res_combobox = NoScrollComboBox()
                    absolute_icon_path = os.path.abspath(self.down_arrow_icon_path).replace('\\', '/')
                    res_combobox.setStyleSheet(f"""
                                               /* Основний стиль QComboBox */
                                                QComboBox {{
                                                    font-size: 14px; font-weight: bold;
                                                    padding-left: 7px;
                                                    {"background-color: " + self.rr_fg_color + ";" if not self.enable_fusion_theme else ""}
                                                }}
                                                /* Стиль випадаючого списку */
                                                QComboBox QAbstractItemView {{
                                                    padding: 0px;
                                                }}
                                                QComboBox::drop-down {{
                                                    border: 0px;
                                                }}
                                                QComboBox::down-arrow {{
                                                    image: url('{absolute_icon_path}'); /* Використовуйте прямі слеші */
                                                    width: 11px;
                                                    height: 11px;
                                                    margin-right: 10px;
                                                    }}
                                                """)
                    res_combobox.setFixedWidth(120)
                    # res_combobox.setFixedWidth(105)
                    res_combobox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
                    res_combobox.addItems(formatted_resolutions)
                    res_combobox.setCurrentText(monitor["Resolution"])
                    res_combobox.currentIndexChanged.connect(lambda index, m=monitor, cb=res_combobox: self.on_resolution_select(m, cb.currentText()))
                    label_hbox.addWidget(res_combobox)
                else:
                    res_label = QLabel(monitor['Resolution'])
                    res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # res_label.setMinimumWidth(105)
                    res_label.setFixedWidth(105)
                    res_label.setStyleSheet(f"""
                                            font-size: 14px; font-weight: bold; 
                                            background-color: {self.rr_fg_color}; 
                                            border: 1px solid {self.rr_border_color};  
                                            border-radius: {6 if self.enable_rounded_corners else 0}px; 

                                            padding: 3px;
                                            padding-bottom: 3px;
                                            """)
                    label_hbox.addWidget(res_label)

            monitor_vbox.addWidget(label_frame)
            
            monitor_vbox.setSpacing(5)


            # Add separator line
            separator_line1 = SeparatorLine(color=self.separator_color)
            monitor_vbox.addWidget(separator_line1)


            # MARK: Refresh Rates
            if self.show_refresh_rates:

                monitor_vbox.setSpacing(5)  # Spacing between monitor frames //////////////////////////////////////////////////////////////////
                
                refresh_rates = monitor["AvailableRefreshRates"]
                refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]

                if len(refresh_rates) >= 2:
                    rr_frame = QWidget()
                    rr_grid = QGridLayout(rr_frame)
                    # rr_grid.setContentsMargins(5, 0, 5, 0)
                    rr_grid.setContentsMargins(6, 0, 6, 0)
                    rr_grid.setContentsMargins(0, 0, 0, 0)

                    # rr_grid.setContentsMargins(11, 0, 11, 0)
                    # rr_grid.setContentsMargins(10, 0, 10, 0)
                    rr_grid.setSpacing(0)

                    self.rr_buttons[monitor_serial] = []  # Initialize list for this monitor

                    num_columns = 6
                    for idx, rate in enumerate(refresh_rates):
                        rr_button = RRButton(f"{rate} Hz")
                        if rate == monitor["RefreshRate"]:
                            rr_button.setChecked(True)
                        rr_button.clicked.connect(lambda checked, r=rate, m=monitor, btn=rr_button: self.on_rr_button_clicked(r, m, btn))
                        

                        row = idx // num_columns
                        col = idx % num_columns
                        
                        rr_grid.addWidget(rr_button, row, col)

                        self.rr_buttons[monitor_serial].append(rr_button)  # Store button

                    monitor_vbox.addWidget(rr_frame)

                    # Add separator line
                    separator_line2 = SeparatorLine(color=self.separator_color)
                    monitor_vbox.addWidget(separator_line2)
            



            # MARK: Brightness

            br_frame = QWidget()
            br_hbox = QHBoxLayout(br_frame)
            # br_hbox.setContentsMargins(7, 0, 7, 7)
            # br_hbox.setContentsMargins(16, 0, 7, 7)

            # br_hbox.setContentsMargins(12, 0, 7, 7)
            # br_hbox.setSpacing(1)

            # br_hbox.setContentsMargins(12, 0, 9, 7)
            # br_hbox.setContentsMargins(5, 0, 2, 0)
            br_hbox.setContentsMargins(0, 0, 2, 0)
            # br_hbox.setContentsMargins(0, 0, 0, 0)
            
            # br_hbox.setSpacing(3)
            br_hbox.setSpacing(0)



            br_level = get_brightness(display=monitor['serial'])[0]

            # print(f"-------------- br_level {monitor['serial']} {self.brightness_values[monitor['serial']]}")
            if self.restore_last_brightness and monitor['serial'] in self.brightness_values:
                # br_level = int(self.brightness_values[monitor['serial']])
                pass
            else:
                # br_level = get_brightness(display=monitor['serial'])[0]
                # self.brightness_values[monitor['serial']] = get_brightness(display=monitor['serial'])[0]
                self.brightness_values[monitor['serial']] = br_level
            # print(f"xxxxxxxxxxxxxxxxxxxx br_level {monitor['serial']} {self.brightness_values[monitor['serial']]}")



            


            
            sun_icon = BrightnessIcon(icon_path=self.sun_icon_path)
            # sun_icon.setStyleSheet("""
            #                        background-color: green;

            #                        """) # background-color: green;
            sun_icon.set_value(br_level)
            br_hbox.addWidget(sun_icon)



            # Add spacer between sun icon and slider
            sun_slider_spacer = QSpacerItem(6, 0, QSizePolicy.Minimum, QSizePolicy.Expanding) # 3
            br_hbox.addItem(sun_slider_spacer)






            br_slider = AnimatedSliderBlockSignals(Qt.Orientation.Horizontal, 
                                     scrollStep=1, 
                                     singleStep=1,
                                     pageStep=10) # keyboard step
            br_slider.setMaximum(100)  # Set maximum value to 100
            br_slider.setValue(br_level)
            
            self.br_sliders[monitor['serial']] = br_slider  # Store slider in dictionary
            
            br_label = QLabel()
            # br_label.setFixedWidth(26) 
            br_label.setFixedWidth(39) # 2-26 3-39px
            # br_label.setFixedWidth(32) # 2-23 3-32px
            # br_label.setFixedHeight(100)
            br_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # br_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            br_label.setText(str(br_level))
            br_label.setStyleSheet(f"""
                                   font-size: 22px; font-weight: bold; 
                                   padding-bottom: 2px;

                                   
                                   """) # padding-bottom: 4px; background-color: green; font-size: 22px; font-weight: bold; font: 600 16pt "{config.font_family}";
            
            br_slider.add_icon(sun_icon) # Connect icon to slider to animate the icon
            br_slider.add_label(br_label) # Connect label to slider to animate the label
            br_slider.valueChanged.connect(lambda value, icon=sun_icon, label=br_label, ms=monitor_serial: self.on_brightness_change(value, icon, label, ms))
            br_hbox.addWidget(br_slider)


            # Add spacer between slider and label
            slider_label_spacer = QSpacerItem(3, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            br_hbox.addItem(slider_label_spacer)


            br_hbox.addWidget(br_label)

            monitor_vbox.addWidget(br_frame)
            
            self.monitors_layout.addWidget(monitor_frame)



            # QTimer.singleShot(0, lambda: print("br_label width:", br_label.width())) # Print width of br_label after the layout is updated

            # label_frame.setStyleSheet("background-color: red")
            # if self.show_refresh_rates: rr_frame.setStyleSheet("background-color: green")
            # br_frame.setStyleSheet("background-color: blue")
            # br_slider.setStyleSheet("background-color: red")


        print(f"self.brightness_values {self.brightness_values}")

        end_time = time.time()
        print(f"updateMonitorsFrame took {end_time - start_time:.4f} seconds")

    
    
    # MARK: updateBottomFrame()
    def updateBottomFrame(self):
        print("updateBottomFrame count ", self.bottom_hbox.count())
        # Clear old widgets
        while self.bottom_hbox.count():
            child = self.bottom_hbox.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


        name_title = QLabel("Scroll to adjust brightness")
        name_title.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 padding-bottom: 3px;

                                 """) # padding-left: 5px; background-color: blue;
        
        self.settings_button = QPushButton()
        # self.settings_button.setFlat(True)
        # self.settings_button.setStyleSheet("""
                                 
        #                          """)
        self.settings_button.setFixedWidth(41)
        # self.settings_button.setFixedWidth(39)
        self.settings_button.setFixedHeight(39)
        self.settings_button.setIcon(QIcon(self.settings_icon_path))
        self.settings_button.setIconSize(QSize(21, 21))
        # self.settings_button.setStyleSheet("border: none;")
        # self.settings_button.setStyleSheet("QPushButton { border: none; }")
        self.settings_button.clicked.connect(self.openSettingsWindow)

        self.bottom_hbox.addWidget(name_title)
        self.bottom_hbox.addWidget(self.settings_button)




    # MARK: on_rr_button_clicked()
    def on_rr_button_clicked(self, rate, monitor, button):
        print(f"Selected refresh rate: {rate} Hz for monitor {monitor["serial"]}")
        # print(monitor)

        set_refresh_rate_br(monitor, rate, refresh=False)

        monitors_info = get_monitors_info()
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        current_rr = monitors_dict[monitor["serial"]]["RefreshRate"]
        # print(f"Current refresh rate: {current_rr} Hz")
        # print(f"Selected refresh rate: {rate} Hz")

        if monitor["serial"] in monitors_dict:
            if current_rr != rate:
                button.setChecked(False)
            else:
                for btn in self.rr_buttons[monitor["serial"]]:
                    if btn != button:
                        btn.setChecked(False)
                button.setChecked(True)



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor, resolution):
        print(f"on_resolution_select {monitor['serial']} {resolution}")
        
        width, height = map(int, resolution.split('x'))
        set_resolution(monitor["Device"], width, height)
        
        QTimer.singleShot(500, self.updateSizeAndPosition)


    # MARK: on_brightness_change()
    def on_brightness_change(self, value, icon, label, monitor_serial):
        # print(f"on_brightness_change {value} {label} {monitor_serial}")
        icon.set_value(value)
        label.setText(str(value))
        self.brightness_values[monitor_serial] = int(value)
        # print(f"on_brightness_change {monitor_serial}", self.brightness_values[monitor_serial])

    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, delta):
        # print("on_bottom_frame_scroll ", delta)
        for slider in self.br_sliders.values():
            new_value = max(0, min(100, slider.value() + (1 if delta > 0 else -1)))
            slider.setValue(new_value)

    # MARK: brightness_sync()
    def brightness_sync(self):
        first_iteration = True
        while self.window_open:
            start_time = time.time()
            
            brightness_values_copy = self.brightness_values.copy()
            for monitor_serial, brightness in brightness_values_copy.items():
                if monitor_serial in self.connected_monitors:  # Перевірка підключення монітора
                    try:
                        if first_iteration or self.previous_brightness_values.get(monitor_serial) != brightness:
                            print(f"brightness_sync set_brightness {monitor_serial} {brightness}")
                            set_brightness(monitor_serial, brightness)
                            self.previous_brightness_values[monitor_serial] = brightness
                    except Exception as e:
                        print(f"Error: {e}")
            
            reg_write_dict(config.REGISTRY_PATH, "BrightnessValues", self.brightness_values)
            
            first_iteration = False
            
            end_time = time.time()
            # print(f"Brightness sync took {end_time - start_time:.4f} seconds")
            
            # time.sleep(0.15)
            time.sleep(0.10)


    # MARK: brightness_sync_onetime()
    def brightness_sync_onetime(self):
        print("brightness_sync_onetime")
        start_time = time.time()
        brightness_values_copy = self.brightness_values.copy()
        # print(f"brightness_values_copy {brightness_values_copy}")
        for monitor_serial, brightness in brightness_values_copy.items():
            if monitor_serial in self.connected_monitors:  # Check if monitor is connected
                try:
                    set_brightness(monitor_serial, brightness)
                    print(f"brightness_sync_onetime set_brightness {monitor_serial} {brightness}")
                except Exception as e:
                    print(f"Error: {e}")
        
        # reg_write_dict(config.REGISTRY_PATH, "BrightnessValues", self.brightness_values)

        end_time = time.time()  # End time measurement
        print(f"brightness_sync_onetime sync took {end_time - start_time:.4f} seconds")

    # MARK: showEvent()
    def showEvent(self, event):
        print("showEvent")

        if self.update_bottom_frame:
            self.updateBottomFrame()
            self.update_bottom_frame = False

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

        else:
            print("brightness_sync_thread is already running")

        super().showEvent(event)

        if self.restore_last_brightness:
            QTimer.singleShot(150, self.start_brightness_animation)

    # MARK: start_brightness_animation()
    def start_brightness_animation(self):
        for index, (serial, slider) in enumerate(self.br_sliders.items()):
            # QTimer.singleShot(index * 100, lambda s=slider: s.animate_to(100))
            # QTimer.singleShot(index * 100, lambda s=slider: s.animate_to(int(self.brightness_values[serial])))
            print(f"start_brightness_animation {serial} {self.brightness_values[serial]}")
            slider.animate_to(int(self.brightness_values[serial]))

    # MARK: start_brightness_sync_thread()
    def start_brightness_sync_thread(self):
        print("brightness_sync_thread started")
        self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
        self.brightness_sync_thread.start()



    # MARK: hideEvent()
    def hideEvent(self, event):
        print("hideEvent")

        self.stop_brightness_sync_thread()
        # QTimer.singleShot(2000, self.stop_brightness_sync_thread)  # Add 2-second delay

        # QTimer.singleShot(1000, self.brightness_sync_onetime)
        

        super().hideEvent(event)

    # MARK: stop_brightness_sync_thread()
    def stop_brightness_sync_thread(self):
        self.window_open = False
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
        self.move(screen_geometry.width() - self.width() - self.window_offset, screen_geometry.height() - self.sizeHint().height() - self.window_offset)
        self.resize(self.width(), self.sizeHint().height())



    # MARK: animateWindowOpen()
    def animateWindowOpen(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        # start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        # end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - self.window_offset, self.width(), self.sizeHint().height())
        end_rect = QRect(screen_geometry.width() - self.width() - self.window_offset, screen_geometry.height() - self.sizeHint().height() - self.window_offset, self.width(), self.sizeHint().height())

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
        # start_rect = QRect(screen_geometry.width() - self.width() - self.window_offset, screen_geometry.height() - self.sizeHint().height() - self.window_offset, self.width(), self.sizeHint().height())
        current_rect = self.geometry()
        end_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - self.window_offset, self.width(), self.sizeHint().height())
        
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
        if not mutex: # Помилка створення м'ютекса
            print(f"Error code: {ctypes.get_last_error()}")
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS (м'ютекс вже є)
            print("Another instance is already running")
            sys.exit(1)

    app = QApplication([])

    # print(QStyleFactory.keys()) # ['windows11', 'windowsvista', 'Windows', 'Fusion']
    # app.setStyle("windows11")
    print(f"Current style: {app.style().objectName()}")


    window = MainWindow()
    window.show()
    app.exec()