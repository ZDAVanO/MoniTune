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
    QTabWidget,  # Add these imports
    QPushButton,
    QDialog,
    QFrame,
    QComboBox,  # Add this import
    QGridLayout  # Add this import
)

from system_tray_icon import SystemTrayIcon
from settings_window import SettingsWindow 

import random

# from monitor_utils import get_monitors_info

edge_padding = 11










# MARK: MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MoniTune")
        self.resize(358, 231)


        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.installEventFilter(self)

        # This container holds the window contents, so we can style it.
        central_widget = QWidget()
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """
            #Container {
            background: #202020;
            border-radius: 9px;
            border: 1px solid #404040;
            }
            """
        )
        

        self.settings_window = None  # No settings window yet

        self.test_var = 5

        self.monitors_frame = QWidget()
        # self.monitors_frame.setStyleSheet("background-color: red;")
        # self.monitors_frame.setStyleSheet("border-radius: 9px; background-color: red")
        self.monitors_layout = QVBoxLayout(self.monitors_frame)
        self.monitors_layout.setContentsMargins(7, 7, 7, 0)
        # self.monitors_layout.setSpacing(0)

        self.bottom_frame = QWidget()
        # self.bottom_frame.setStyleSheet("background-color: green;") 
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
        # Clear old widgets
        while self.monitors_layout.count():
            child = self.monitors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


        # Add new frames with monitor information
        num_monitors = random.randint(1, 4)
        for i in range(num_monitors):
            
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
            label_hbox.setContentsMargins(5, 5, 5, 5)
            monitor_label = QLabel(f"Monitor {i+1}")
            monitor_label.setStyleSheet("""
                                        font-size: 16px; 
                                        font-weight: bold;
                                        """)
            label_hbox.addWidget(monitor_label)
            
            # res_combobox = QComboBox()
            # res_combobox.setStyleSheet("font-size: 14px; font-weight: bold;  padding-left: 7px;")
            # res_combobox.setFixedWidth(120)
            # res_combobox.setFixedHeight(32)
            # res_combobox.addItems(["1920x1080", "1280x720", "1024x768"])
            # label_hbox.addWidget(res_combobox)
            
            res_label = QLabel("1920x1080")
            res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            res_label.setFixedWidth(105)
            # res_label.setMinimumWidth(105)
            res_label.setStyleSheet("""
                                    font-size: 14px; font-weight: bold; 
                                    background-color: #373737; 
                                    border: 1px solid #3f3f3f; 
                                    border-radius: 6px; 
                                    padding: 3px;
                                    padding-bottom: 4px;
                                    """)
            label_hbox.addWidget(res_label)

            monitor_vbox.addWidget(label_frame)
            



            # Add refresh rate buttons
            rr_frame = QWidget()
            
            rr_grid = QGridLayout(rr_frame)
            rr_grid.setContentsMargins(5, 5, 5, 5)
            rr_grid.setSpacing(0)

            num_columns = 6

            rates = ["100 Hz", "2 Hz", "3 Hz", "4 Hz", "5 Hz", "6 Hz", "7 Hz", "8 Hz", "9 Hz", "10 Hz", "11 Hz", "12 Hz", "13 Hz", "14 Hz", "15 Hz", "16 Hz", "17 Hz", "18 Hz", "19 Hz", "20 Hz"]
            rates = ["100 Hz", "2 Hz", "3 Hz", "4 Hz", "5 Hz",]
            for idx, rate in enumerate(rates):
                rr_button = QPushButton(rate)
                rr_button.setCheckable(True)
                rr_button.setChecked(True) if rate == "20 Hz" else rr_button.setChecked(False)
                rr_button.setMinimumWidth(55)
                row = idx // num_columns
                col = idx % num_columns
                rr_grid.addWidget(rr_button, row, col)

            monitor_vbox.addWidget(rr_frame)
            




            br_frame = QWidget()
            
            br_hbox = QHBoxLayout(br_frame)
            br_hbox.setContentsMargins(5, 5, 5, 5)
            br_slider = QSlider(Qt.Orientation.Horizontal)
            br_slider.setMaximum(100)  # Set maximum value to 100

            br_label = QLabel("50")
            br_label.setStyleSheet("""
                                   font-size: 22px; 
                                   font-weight: bold; 
                                   padding-bottom: 4px;
                                   """)
            br_label.setFixedWidth(40) 
            br_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            br_slider.setValue(50)
            br_label.setText(str(br_slider.value()))
            br_slider.valueChanged.connect(lambda value, label=br_label: label.setText(str(value)))
            br_hbox.addWidget(br_slider)
            br_hbox.addWidget(br_label)

            monitor_vbox.addWidget(br_frame)
            
            self.monitors_layout.addWidget(monitor_frame)


            label_frame.setStyleSheet("background-color: red")
            rr_frame.setStyleSheet("background-color: green")
            br_frame.setStyleSheet("background-color: blue")
            



    # MARK: showEvent()
    def showEvent(self, event):
        print("showEvent")
        print(self.test_var)

        # monitors_info = get_monitors_info()
        # print("monitors_info", monitors_info)

        # self.adjustWindowPosition()

        self.updateFrameContents()  # Update frame contents each time the window is shown
        
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()

        self.move(screen_geometry.width(), screen_geometry.height())
        # self.animateWindowOpen()
        QTimer.singleShot(0, self.animateWindowOpen)
        # QTimer.singleShot(0, self.updateSizeAndPosition)

        # window_height = self.sizeHint().height()  # Use sizeHint().height() instead of self.height()
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - window_height - edge_padding)
        
        print("self.width()", self.width(), "self.height()", self.height())
        print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())
        # self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding)
        

        self.activateWindow()
        self.raise_()
        

        super().showEvent(event)
        
        print("self.height():", self.height(), "sizeHint:", self.sizeHint().height())






    def updateSizeAndPosition(self):
        print("updateSizeAndPosition sizeHint:", self.sizeHint().height(), "self.height()", self.height())
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding)
        self.resize(self.width(), self.sizeHint().height())


    # def adjustWindowPosition(self):
    #     # screen_geometry = QGuiApplication.primaryScreen().geometry()
    #     screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
    #     self.move(screen_geometry.width() - self.width(), screen_geometry.height() - self.height())

    # MARK: animateWindowOpen()
    def animateWindowOpen(self):
        # screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        # start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        # end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.height() - edge_padding, self.width(), self.height())
        start_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        end_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        
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
        start_rect = QRect(screen_geometry.width() - self.width() - edge_padding, screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        end_rect = QRect(screen_geometry.width(), screen_geometry.height() - self.sizeHint().height() - edge_padding, self.width(), self.sizeHint().height())
        
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

    print(QStyleFactory.keys())
    app.setStyle("windows11")

    window = MainWindow()
    window.show()
    app.exec()