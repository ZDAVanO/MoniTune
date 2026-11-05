from typing import Callable, Optional
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)

from custom_widgets.custom_labels import BrightnessIcon
from custom_widgets.custom_sliders import AnimatedSliderBS
from utils.logger import get_logger

logger = get_logger(__name__)


# MARK: SliderFrame
class SliderFrame(QFrame):
    def __init__(self, main_window=None, icon_path="", value: int = 50, slider_callback: Optional[Callable[[int], None]] = None, disabled: bool = False):
        super().__init__()

        # self.main_window = main_window

        self.bg_color = 'transparent'
        self.border_radius = 6

        self.setObjectName("SliderFrame")
        # self.setStyleSheet(f"""
        #     #SliderFrame {{
        #         background-color: transparent;
        #         border-radius: 6px;
        #     }}
        #     #SliderFrame:hover {{
        #         background-color: {'rgba(0, 0, 0, 0.03)' if self.main_window.theme == "Light" else 'rgba(255, 255, 255, 0.03)'};
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
        
        self.slider = AnimatedSliderBS(
            Qt.Orientation.Horizontal, 
            scrollStep=1,  # step when scrolling with mouse wheel
            singleStep=1,  # step when pressing arrow keys
            pageStep=10,   # step when pressing page up/down keys
        )
        self.slider.setRange(0, 100)
        self.slider.setValue(value)
        
        self.label = QLabel()
        self.label.setFixedSize(39, 30)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(str(value))
        self.label.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            padding-bottom: 2px; 
        """)  # background-color: green;
        
        # add widgets to layout
        self.hbox.addWidget(self.icon)
        self.hbox.addItem(QSpacerItem(6, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.hbox.addWidget(self.slider)
        self.hbox.addItem(QSpacerItem(3, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.hbox.addWidget(self.label)

        self.slider.valueChanged.connect(self._on_slider_value_changed)
        self.slider.animation.valueChanged.connect(self.update_ui_elements)

        if disabled:
            self.setDisabled(True)

    def _on_slider_value_changed(self, value):
        limit = getattr(self.slider, "max_limit", 100)
        clamped = min(int(value), limit)
        self.label.setText(str(clamped))
        self.icon.animate_to(clamped)
        if self.slider_callback:
            self.slider_callback(clamped)

    def update_ui_elements(self, value):
        self.label.setText(str(value))
        self.icon.set_value(value)

    def set_max_limit(self, limit: Optional[int] = None, snap: bool = True):
        if hasattr(self.slider, "set_max_limit"):
            self.slider.set_max_limit(limit, snap=snap)
        if snap and self.slider.animation.state() != QPropertyAnimation.State.Running:
            actual_val = self.slider.value()
            self.label.setText(str(actual_val))
            self.icon.set_value(actual_val)

    def animate_to(self, target_value, duration=1000, easing_curve=QEasingCurve.Type.OutCubic):
        limit = getattr(self.slider, "max_limit", 100)
        clamped_target = min(int(target_value), limit)
        logger.info(f"SliderFrame animate_to {self.slider.value()}-{clamped_target}")
        self.icon.stop_animation()  # Stop any ongoing animation in the icon
        self.slider.animate_to(clamped_target, duration, easing_curve)

    def setValueBS(self, value):
        if self.slider.animation.state() == QPropertyAnimation.State.Running:
            self.slider.stop_animation()  # Stop any ongoing animation in the slider

        self.slider.blockSignals(True)  # Block signals during animation
        self.slider.setValue(value)
        self.slider.blockSignals(False)  # Unblock signals after setting value

        actual_val = self.slider.value()
        self.label.setText(str(actual_val))
        self.icon.animate_to(actual_val)

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
        
        limit = getattr(self.slider, "max_limit", self.slider.maximum())
        if delta > 0:
            new_value = min(self.slider.value() + step, limit)
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
