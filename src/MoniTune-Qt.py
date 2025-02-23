from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QMenu,
    QSlider,
    QGraphicsOpacityEffect,
    QStyleFactory,
    QTabWidget,
    QPushButton,
    QDialog,
    QFrame,
    QComboBox,
    QGridLayout
)

from system_tray_icon import SystemTrayIcon
from settings_window import SettingsWindow 
import config

import random
import threading
import darkdetect

from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict

import time
import screen_brightness_control as sbc

import sys
import ctypes


class CustomSlider(QSlider):
    def wheelEvent(self, event: QWheelEvent):
        value = self.value()
        if event.angleDelta().y() > 0:
            self.setValue(value + 1)
        else:
            self.setValue(value - 1)










# MARK: MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.test_var = 5
        # self.icon_path = icon_path
        # self.settings_icon_light = settings_icon_light
        # self.settings_icon_dark = settings_icon_dark

        self.window_width = 358
        self.window_height = 231

        self.enable_rounded_corners = reg_read_bool(config.REGISTRY_PATH, "EnableRoundedCorners")
        if self.enable_rounded_corners:
            self.window_corner_radius = 9
            self.edge_padding = 11
        else:
            self.window_corner_radius = 0
            self.edge_padding = 0



        self.border_color_light = "#bebebe"
        self.border_color_dark = "#404040"

        self.bg_color_light = "#f3f3f3"
        self.bg_color_dark = "#202020"


        self.fr_color_light = "#fbfbfb"  
        self.fr_color_dark = "#2b2b2b"  

        self.fr_border_color_light = "#e5e5e5"
        self.fr_border_color_dark = "#1d1d1d"


        self.rr_border_color_dark = "#3f3f3f"
        self.rr_fg_color_dark = "#373737"
        self.rr_hover_color_dark = "#2c2c2c"

        self.rr_border_color_light = "#ececec"
        self.rr_fg_color_light = "#fefefe"
        self.rr_hover_color_light = "#f0f0f0"



        self.settings_window = None  # No settings window yet
        self.rr_buttons = {}  # Dictionary to store refresh rate buttons for each monitor
        self.br_sliders = []  # List to store brightness sliders

        self.window_open = False
        self.brightness_sync_thread = None

        self.brightness_values = {}
        # self.load_brightness_values_from_registry()
        brightness_data = reg_read_dict(config.REGISTRY_PATH, "BrightnessValues")
        print(f"brightness_data {brightness_data}")
        for monitor_serial, br_level in brightness_data.items():
            self.brightness_values[monitor_serial] = int(br_level)
        print(f"self.brightness_values {self.brightness_values}")


        # self.excluded_rates = list(map(int, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates")))
        self.excluded_rates = list(map(int, filter(None, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates"))))

        self.custom_monitor_names = reg_read_dict(config.REGISTRY_PATH, "CustomMonitorNames")
        print(f"custom_monitor_names {self.custom_monitor_names}")

        self.monitors_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")


        self.show_resolution = reg_read_bool(config.REGISTRY_PATH, "ShowResolution")
        self.allow_res_change = reg_read_bool(config.REGISTRY_PATH, "AllowResolutionChange")

        self.restore_last_brightness = reg_read_bool(config.REGISTRY_PATH, "RestoreLastBrightness")
        

        # self.show_refresh_rates = read_show_refresh_rates_from_registry()  # Add a flag to control the display of refresh rates
        self.show_refresh_rates = reg_read_bool(config.REGISTRY_PATH, "ShowRefreshRates")
        # print(f"show_refresh_rates {self.show_refresh_rates}")







        self.setWindowTitle("MoniTune")
        self.resize(self.window_width, self.window_height)

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)

        # This container holds the window contents, so we can style it.
        central_widget = QWidget()
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            f"""
            #Container {{
            background: #202020;
            border-radius: {self.window_corner_radius}px;
            border: 1px solid #404040;
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
        # 16 10
        self.bottom_hbox.setContentsMargins(7, 0, 9, 0)
        self.bottom_hbox.setSpacing(5)

        name_title = QLabel("Scroll to adjust brightness")
        name_title.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 
                                 """)
        
        settings_button = QPushButton()
        settings_button.setFixedWidth(43)
        settings_button.setFixedHeight(43)
        settings_button.setIcon(QIcon(config.settings_icon_dark_path))
        settings_button.setIconSize(QSize(25, 25))
        # settings_button.setStyleSheet("border: none;")
        # settings_button.setStyleSheet("QPushButton { border: none; }")
        settings_button.clicked.connect(self.openSettingsWindow)

        self.bottom_hbox.addWidget(name_title)
        self.bottom_hbox.addWidget(settings_button)
        

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
        threading.Thread(target=darkdetect.listener, args=(self.on_theme_change,), daemon=True).start()



        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.bottom_frame.setStyleSheet("background-color: green;") 
        self.openSettingsWindow() # Open settings window on startup

        





    # MARK: update_rounded_corners()
    def update_rounded_corners(self):
        new_corner_radius = 9 if self.enable_rounded_corners else 0
        self.window_corner_radius = new_corner_radius
        self.centralWidget().setStyleSheet(
            f"""
            #Container {{
            background: #202020;
            border-radius: {new_corner_radius}px;
            border: 1px solid #404040;
            }}
            """
        )

        self.edge_padding = 11 if self.enable_rounded_corners else 0


    # MARK: on_theme_change()
    def on_theme_change(self, theme: str):
        print(f"Theme changed to: {theme}")

        if theme == "Light":
            pass
        else:
            pass
    


    

    



    # MARK: eventFilter()
    def eventFilter(self, source, event):
        # print("eventFilter source", source, "event", event.type())

        # hide window when focus is lost
        if event.type() == QEvent.Type.WindowDeactivate:
            self.hide()
            # self.animateWindowClose()
            return True
        
        # Handle scroll events on the bottom frame
        if source == self.bottom_frame and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            self.on_bottom_frame_scroll(delta)
            return True
            
        
        return super().eventFilter(source, event)


    





    # MARK: updateFrameContents()
    def updateFrameContents(self):
        print("test_var", self.test_var)
        start_time = time.time()


        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.br_sliders.clear() # Clear brightness sliders list




        monitors_info = get_monitors_info()
        # print(f"monitors_info {monitors_info}")
        # monitors_info.reverse()  # Invert the order of monitors
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.monitors_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]






        for index, monitor_serial in enumerate(monitors_order):

            monitor = monitors_dict[monitor_serial]

            
            monitor_frame = QWidget()
            monitor_frame.setObjectName("MonitorsFrame")
            monitor_frame.setStyleSheet(
                """
                #MonitorsFrame {
                background: #2b2b2b;
                border-radius: 6px;
                border: 1px solid #1d1d1d;
                }
                """
            )
            monitor_vbox = QVBoxLayout(monitor_frame)
            monitor_vbox.setContentsMargins(0, 0, 0, 0)
            monitor_vbox.setSpacing(0)  # Remove spacing between frames
            
            label_frame = QWidget()
            label_hbox = QHBoxLayout(label_frame)
            label_hbox.setContentsMargins(7, 7, 7, 7)

            monitor_label_text = self.custom_monitor_names[monitor_serial] if monitor_serial in self.custom_monitor_names else monitor["display_name"]

            monitor_label = QLabel(monitor_label_text)
            # monitor_label.setFixedHeight(100)
            monitor_label.setStyleSheet("""
                                        font-size: 16px; 
                                        font-weight: bold;
                                        padding-left: 1px;
                                        background-color: blue;
                                        """)
            label_hbox.addWidget(monitor_label)
            
            if self.show_resolution:
                if self.allow_res_change:
                    available_resolutions = monitor["AvailableResolutions"]
                    sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
                    formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]

                    res_combobox = QComboBox()
                    res_combobox.setStyleSheet("font-size: 14px; font-weight: bold;  padding-left: 7px;")
                    res_combobox.setFixedWidth(120)
                    res_combobox.setFixedHeight(32)
                    res_combobox.addItems(formatted_resolutions)
                    res_combobox.setCurrentText(monitor["Resolution"])
                    res_combobox.currentIndexChanged.connect(lambda index, m=monitor, cb=res_combobox: self.on_resolution_select(m, cb.currentText()))
                    label_hbox.addWidget(res_combobox)
                else:
                    res_label = QLabel(monitor['Resolution'])
                    res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    res_label.setFixedWidth(105)
                    # res_label.setMinimumWidth(105)
                    res_label.setStyleSheet("""
                                            font-size: 14px; font-weight: bold; 
                                            background-color: #373737; 
                                            border: 1px solid #3f3f3f; 
                                            border-radius: 6px; 
                                            padding: 3px;
                                            padding-bottom: 3px;
                                            """)
                    label_hbox.addWidget(res_label)

            monitor_vbox.addWidget(label_frame)
            


            if self.show_refresh_rates:
                refresh_rates = monitor["AvailableRefreshRates"]
                refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]
                # rates = ["100 Hz", "2 Hz", "3 Hz", "4 Hz", "5 Hz", "6 Hz", "7 Hz", "8 Hz", "9 Hz", "10 Hz", "11 Hz", "12 Hz", "13 Hz", "14 Hz", "15 Hz", "16 Hz", "17 Hz", "18 Hz", "19 Hz", "20 Hz"]
                # rates = ["100 Hz", "2 Hz", "3 Hz", "4 Hz", "5 Hz",]

                if len(refresh_rates) >= 2:
                    rr_frame = QWidget()
                    rr_grid = QGridLayout(rr_frame)
                    rr_grid.setContentsMargins(5, 0, 5, 0)
                    rr_grid.setSpacing(0)

                    self.rr_buttons[monitor_serial] = []  # Initialize list for this monitor

                    num_columns = 6
                    for idx, rate in enumerate(refresh_rates):
                        rr_button = QPushButton(f"{rate} Hz")
                        rr_button.setCheckable(True)
                        if rate == monitor["RefreshRate"]:
                            rr_button.setChecked(True)
                        rr_button.clicked.connect(lambda checked, r=rate, m=monitor, btn=rr_button: self.on_rr_button_clicked(r, m, btn))
                        rr_button.setMinimumWidth(55)

                        row = idx // num_columns
                        col = idx % num_columns
                        
                        rr_grid.addWidget(rr_button, row, col)

                        self.rr_buttons[monitor_serial].append(rr_button)  # Store button

                    monitor_vbox.addWidget(rr_frame)
            




            br_frame = QWidget()
            
            br_hbox = QHBoxLayout(br_frame)
            br_hbox.setContentsMargins(7, 7, 7, 7)


            if self.restore_last_brightness and monitor['serial'] in self.brightness_values:
                br_level = int(self.brightness_values[monitor['serial']])
            else:
                br_level = sbc.get_brightness(display=monitor['serial'])[0]


            br_slider = CustomSlider(Qt.Orientation.Horizontal, singleStep=1)
            br_slider.setMaximum(100)  # Set maximum value to 100
            br_slider.setValue(br_level)
            
            br_label = QLabel()
            self.br_sliders.append(br_slider)
            br_label.setText(str(br_level))
            br_label.setStyleSheet("""
                                   font-size: 22px; 
                                   font-weight: bold; 
                                   padding-bottom: 4px;
                                   background-color: green;
                                   """)
            br_label.setFixedWidth(25) 
            br_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            br_slider.valueChanged.connect(lambda value, label=br_label, ms=monitor_serial: self.on_brightness_change(value, label, ms))
            
            br_hbox.addWidget(br_slider)
            br_hbox.addWidget(br_label)

            monitor_vbox.addWidget(br_frame)
            
            self.monitors_layout.addWidget(monitor_frame)


            self.brightness_values[monitor['serial']] = br_level
            print(f"self.brightness_values {self.brightness_values}")

            label_frame.setStyleSheet("background-color: red")
            if self.show_refresh_rates: rr_frame.setStyleSheet("background-color: green")
            br_frame.setStyleSheet("background-color: blue")
            br_slider.setStyleSheet("background-color: red")

        end_time = time.time()
        print(f"load_ui took {end_time - start_time:.4f} seconds")

        
            

    # MARK: on_rr_button_clicked()
    def on_rr_button_clicked(self, rate, monitor, button):
        print(f"Selected refresh rate: {rate} Hz for monitor {monitor["serial"]}")
        # update button states
        for btn in self.rr_buttons[monitor["serial"]]:
            if btn != button:
                btn.setChecked(False)
        button.setChecked(True)
        # set refresh rate
        set_refresh_rate_br(monitor, rate, refresh=False)


    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor, resolution):
        print(f"on_resolution_select {monitor['serial']} {resolution}")
        
        width, height = map(int, resolution.split('x'))
        set_resolution(monitor["Device"], width, height)
        
        QTimer.singleShot(250, self.updateSizeAndPosition)


    # MARK: on_brightness_change()
    def on_brightness_change(self, value, label, monitor_serial):
        # print(f"on_brightness_change {value} {label} {monitor_serial}")
        label.setText(str(value))
        self.brightness_values[monitor_serial] = int(value)

    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, delta):
        # print("on_bottom_frame_scroll ", delta)
        for slider in self.br_sliders:
            new_value = max(0, min(100, slider.value() + (1 if delta > 0 else -1)))
            slider.setValue(new_value)

    # MARK: brightness_sync()
    def brightness_sync(self):
        while self.window_open:
            # print("brightness_sync")

            start_time = time.time()

            brightness_values_copy = self.brightness_values.copy()
            # print(f"brightness_values_copy {brightness_values_copy}")
            for monitor_serial, brightness in brightness_values_copy.items():
                try:
                    current_brightness = sbc.get_brightness(display=monitor_serial)[0]
                    if current_brightness != brightness:
                        print(f"set_brightness {monitor_serial} {brightness}")
                        set_brightness(monitor_serial, brightness)
                except Exception as e:
                    print(f"Error: {e}")
            
            reg_write_dict(config.REGISTRY_PATH, "BrightnessValues", self.brightness_values)

            end_time = time.time()  # End time measurement
            # print(f"Brightness sync took {end_time - start_time:.4f} seconds")

            time.sleep(0.15)



    # MARK: showEvent()
    def showEvent(self, event):
        print("showEvent")


        self.updateFrameContents()  # Update frame contents each time the window is shown
        
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width(), screen_geometry.height())
        # self.animateWindowOpen()
        QTimer.singleShot(0, self.animateWindowOpen)
        # QTimer.singleShot(0, self.updateSizeAndPosition)

        # window_height = self.sizeHint().height()  # Use sizeHint().height() instead of self.height()
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - window_height - edge_padding)
        
        print("self.width()", self.width(), "self.height()", self.height())
        # print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding)
        

        self.activateWindow()
        self.raise_()
        
        self.window_open = True
        if self.brightness_sync_thread is None or not self.brightness_sync_thread.is_alive():
            print("brightness_sync_thread.start()")
            self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
            self.brightness_sync_thread.start()
        else:
            print("Brightness sync thread is already running")

        super().showEvent(event)



    def hideEvent(self, event):
        print("hideEvent")

        self.window_open = False
        if self.brightness_sync_thread and self.brightness_sync_thread.is_alive():
            print("brightness_sync_thread.join()")
            self.brightness_sync_thread.join()  # Stop brightness sync thread
            if not self.brightness_sync_thread.is_alive():
                print("thread is dead")
            else:
                print("thread is still alive")

        super().hideEvent(event)




    def updateSizeAndPosition(self):
        print("updateSizeAndPosition sizeHint:", self.sizeHint().height(), "self.height()", self.height())
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - self.edge_padding, screen_geometry.height() - self.sizeHint().height() - self.edge_padding)
        self.resize(self.width(), self.sizeHint().height())



    # MARK: animateWindowOpen()
    def animateWindowOpen(self):
        # screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        # start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        # end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - self.edge_padding, self.width(), self.sizeHint().height())
        end_rect = QRect(screen_geometry.width() - self.width() - self.edge_padding, screen_geometry.height() - self.sizeHint().height() - self.edge_padding, self.width(), self.sizeHint().height())
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        
        self.animation.start()
        self.opacity_animation.start()

    # MARK: animateWindowClose()
    def animateWindowClose(self):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        start_rect = QRect(screen_geometry.width() - self.width() - self.edge_padding, screen_geometry.height() - self.sizeHint().height() - self.edge_padding, self.width(), self.sizeHint().height())
        current_rect = self.geometry()
        end_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - self.edge_padding, self.width(), self.sizeHint().height())
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(1)
        self.opacity_animation.setEndValue(0)
        
        self.animation.finished.connect(self.hide) # hide window after animation is done
        self.animation.start()
        self.opacity_animation.start()




    # MARK: openSettingsWindow()
    def openSettingsWindow(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        if self.settings_window.isMinimized():
            self.settings_window.showNormal()
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()




if __name__ == "__main__":

    # Check if another instance is already running
    if getattr(sys, 'frozen', False):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex = kernel32.CreateMutexW(None, False, "MoniTune")
        if not mutex: # Помилка створення м'ютекса
            print(f"Error code: {ctypes.get_last_error()}")
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS (м'ютекс вже є)
            print("Another instance is already running")
            sys.exit(1)

    app = QApplication([])

    # print(QStyleFactory.keys())
    # app.setStyle("windows11")

    window = MainWindow()
    window.show()
    app.exec()