from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSlider, QPushButton, QApplication, QMainWindow, QHBoxLayout, QComboBox, QFrame, QCheckBox, QScrollArea
from PySide6.QtCore import QEvent, QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
import random

class SettingsWindow(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("Settings")
        self.resize(600, 450)
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)  # Make it a regular window with minimize and maximize buttons

        self.tab_widget = QTabWidget()
        tab_layout = QVBoxLayout()
        # for i in range(1, 6):
        #     tab = QWidget()
        #     tab_layout = QVBoxLayout()
        #     tab_layout.addWidget(QLabel(f"Content for Tab {i}"))
        #     tab.setLayout(tab_layout)
        #     self.tab_widget.addTab(tab, f"Tab {i}")

        tab_layout.addWidget(self.tab_widget)

        # Add button to show parent window
        self.show_parent_button = QPushButton("Show Parent Window")
        self.show_parent_button.clicked.connect(self.show_parent_window)
        tab_layout.addWidget(self.show_parent_button)

        # Add button to change parent window's test_var
        self.change_var_button = QPushButton("Change Parent Variable")
        self.change_var_button.clicked.connect(self.change_parent_var)
        tab_layout.addWidget(self.change_var_button)

        self.setLayout(tab_layout)
        

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # self.close()

    def showEvent(self, event):
        print("Settings window is now visible")
        self.updateLayout()
        super().showEvent(event)

    def updateLayout(self):
        # Clear old widgets
        print("removed tabs:", self.tab_widget.count())
        while self.tab_widget.count():
            self.tab_widget.removeTab(0)

        # Add new tabs
        # num_tabs = random.randint(1, 1)
        # for i in range(num_tabs):
        #     tab = QWidget()
        #     tab_layout = QVBoxLayout()
        #     tab_layout.addWidget(QLabel(f"Content for Tab {i}"))

        #     # Add four sliders to each tab
        #     for _ in range(4):
        #         slider = QSlider(Qt.Orientation.Horizontal)
        #         slider.setRange(0, 100)
        #         slider.setValue(random.randint(0, 100))
        #         tab_layout.addWidget(slider)

        #     tab.setLayout(tab_layout)
        #     self.tab_widget.addTab(tab, f"Tab {i}")


        general_tab = QWidget()
        # general_tab.setStyleSheet("background-color: blue")
        general_layout = QVBoxLayout(general_tab)
        general_layout.setAlignment(Qt.AlignTop)
        rounded_corners_checkbox = QCheckBox("Rounded Corners")
        general_layout.addWidget(rounded_corners_checkbox)
        self.tab_widget.addTab(general_tab, "General")
        
        resolution_tab = QWidget()
        resolution_layout = QVBoxLayout(resolution_tab)
        resolution_layout.setAlignment(Qt.AlignTop)
        show_resolution_checkbox = QCheckBox("Show Resolutions")
        allow_res_change_checkbox = QCheckBox("Allow Resolution Change")
        resolution_layout.addWidget(show_resolution_checkbox)
        resolution_layout.addWidget(allow_res_change_checkbox)
        self.tab_widget.addTab(resolution_tab, "Resolution")
        
        refresh_rate_tab = QWidget()
        refresh_rate_layout = QVBoxLayout(refresh_rate_tab)
        refresh_rate_layout.setAlignment(Qt.AlignTop)
        show_refresh_rates_checkbox = QCheckBox("Show Refresh Rates")
        refresh_rate_layout.addWidget(show_refresh_rates_checkbox)
        
        exclude_rr_frame = QFrame()
        exclude_rr_layout = QVBoxLayout(exclude_rr_frame)
        exclude_rr_label = QLabel("Exclude Refresh Rates")
        exclude_rr_layout.addWidget(exclude_rr_label)
        
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        for rate in ["60 Hz", "75 Hz", "120 Hz"]:
            rate_checkbox = QCheckBox(rate)
            scroll_layout.addWidget(rate_checkbox)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        exclude_rr_layout.addWidget(scroll_area)
        
        refresh_rate_layout.addWidget(exclude_rr_frame)
        self.tab_widget.addTab(refresh_rate_tab, "Refresh Rate")
        
        brightness_tab = QWidget()
        brightness_layout = QVBoxLayout(brightness_tab)
        brightness_layout.setAlignment(Qt.AlignTop)
        restore_last_brightness_checkbox = QCheckBox("Restore Last Brightness")
        brightness_layout.addWidget(restore_last_brightness_checkbox)
        self.tab_widget.addTab(brightness_tab, "Brightness")
        
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setAlignment(Qt.AlignTop)
        about_label = QLabel("MonitorTuneApp v1.0")
        check_update_button = QPushButton("Check for Updates")
        about_layout.addWidget(about_label)
        about_layout.addWidget(check_update_button)
        self.tab_widget.addTab(about_tab, "About")
        

    def show_parent_window(self):
        self.parent_window.show()

    def change_parent_var(self):
        self.parent_window.test_var = 100









