from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication
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

        self.window_open = False
        self.brightness_sync_thread = None

        self.brightness_values = {}
        # self.load_brightness_values_from_registry()
        brightness_data = reg_read_dict(config.REGISTRY_PATH, "BrightnessValues")
        print(f"brightness_data {brightness_data}")
        for monitor_serial, br_level in brightness_data.items():
            self.brightness_values[monitor_serial] = {'brightness': int(br_level), 'slider': None, 'label': None}
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
        # self.monitors_layout.setSpacing(0)

        self.bottom_frame = QWidget()
        # self.bottom_frame.setStyleSheet("""
        #     background-color: green;
        #     border-bottom-left-radius: 9px;
        #     border-bottom-right-radius: 9px;
        # """)
        self.bottom_frame.setFixedHeight(60)
        self.bottom_frame.installEventFilter(self)
        self.bottom_hbox = QHBoxLayout(self.bottom_frame)
        name_title = QLabel("Scroll to adjust brightness")
        name_title.setStyleSheet("""
                                 font-size: 14px; 
                                 padding-left: 5px;
                                 """)
        settings_button = QPushButton("Settings")
        settings_button.setFixedWidth(70)
        settings_button.setFixedHeight(40)
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



        self.createTrayIcon()



        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.bottom_frame.setStyleSheet("background-color: green;") 





    def createTrayIcon(self):
        self.tray_icon = SystemTrayIcon(self)


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
            if delta > 0:
                print("scroll up")
            else:
                print("scroll down")
        
        return super().eventFilter(source, event)



    # MARK: updateFrameContents()
    def updateFrameContents(self):

        start_time = time.time()


        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()





        monitors_info = get_monitors_info()
        # print(f"monitors_info {monitors_info}")
        # monitors_info.reverse()  # Invert the order of monitors

        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.monitors_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]






        num_monitors = random.randint(1, 4)
        # for i in range(num_monitors):
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
                    label_hbox.addWidget(res_combobox)

                    # res_combobox.set(monitor["Resolution"])
                    # res_combobox.configure(command=lambda value, ms=monitor_serial, frame=label_frame: self.on_resolution_select(ms, value, frame))
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

                rr_frame = QWidget()
                rr_grid = QGridLayout(rr_frame)
                rr_grid.setContentsMargins(5, 0, 5, 0)
                rr_grid.setSpacing(0)

                num_columns = 6

                
                for idx, rate in enumerate(refresh_rates):
                    rr_button = QPushButton(f"{rate} Hz")
                    # rr_button.setFixedHeight(26)
                    print(f"rate {rate}, monitor['RefreshRate'] {monitor['RefreshRate']}")
                    rr_button.setCheckable(True)
                    if rate == monitor["RefreshRate"]:
                        rr_button.setChecked(True)
                    
                    rr_button.setMinimumWidth(55)
                    row = idx // num_columns
                    col = idx % num_columns
                    rr_grid.addWidget(rr_button, row, col)

                monitor_vbox.addWidget(rr_frame)
            




            br_frame = QWidget()
            
            br_hbox = QHBoxLayout(br_frame)
            br_hbox.setContentsMargins(7, 7, 7, 7)


            if self.restore_last_brightness and monitor['serial'] in self.brightness_values:
                br_level = int(self.brightness_values[monitor['serial']]['brightness'])
            else:
                br_level = sbc.get_brightness(display=monitor['serial'])[0]


            br_slider = QSlider(Qt.Orientation.Horizontal)
            br_slider.setMaximum(100)  # Set maximum value to 100
            br_slider.setValue(br_level)
            
            br_label = QLabel()
            br_label.setText(str(br_level))
            br_label.setStyleSheet("""
                                   font-size: 22px; 
                                   font-weight: bold; 
                                   padding-bottom: 4px;
                                   background-color: green;
                                   """)
            br_label.setFixedWidth(50) 
            br_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            br_slider.valueChanged.connect(lambda value, label=br_label: label.setText(str(value)))
            
            br_hbox.addWidget(br_slider)
            br_hbox.addWidget(br_label)

            monitor_vbox.addWidget(br_frame)
            
            self.monitors_layout.addWidget(monitor_frame)


            label_frame.setStyleSheet("background-color: red")
            if self.show_refresh_rates: rr_frame.setStyleSheet("background-color: green")
            br_frame.setStyleSheet("background-color: blue")
            br_slider.setStyleSheet("background-color: red")

        end_time = time.time()
        print(f"load_ui took {end_time - start_time:.4f} seconds")
            



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
        

        super().showEvent(event)
        
        # print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())






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
        end_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - self.edge_padding, self.width(), self.sizeHint().height())
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(1)
        self.opacity_animation.setEndValue(0)
        
        self.animation.finished.connect(self.hide)
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
    app = QApplication([])

    # print(QStyleFactory.keys())
    # app.setStyle("windows11")

    window = MainWindow()
    window.show()

    # Theme change listener
    def on_theme_change(theme: str):
        print(f"Theme changed to: {theme}")
    def theme_listener():
        darkdetect.listener(on_theme_change)
    # Run the theme listener in a separate thread
    threading.Thread(target=theme_listener, daemon=True).start()


    app.exec()