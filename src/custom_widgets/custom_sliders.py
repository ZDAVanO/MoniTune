from typing import Optional
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QSlider, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QLabel,
)
from PySide6.QtCore import (
    Qt, 
    QPropertyAnimation, 
    QEasingCurve, 
    QTimer,
)
from PySide6.QtGui import (
    QWheelEvent, 
    QKeyEvent,
)

import time

import logging
logger = logging.getLogger(__name__)



class CustomSlider(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal, scrollStep=1, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)
        self.scrollStep = scrollStep

    def wheelEvent(self, event: QWheelEvent):
        value = self.value()
        if event.angleDelta().y() > 0:
            self.setValue(value + self.scrollStep)
        else:
            self.setValue(value - self.scrollStep)


class NoScrollSlider(QSlider):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()


class AnimatedSlider(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal, scrollStep=1, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)

        self.animation = None
        self.scrollStep = scrollStep

        self.setRange(0, 100)


    def animate_to(self, target_value, duration=1000, easing_curve=QEasingCurve.Type.OutCubic):
        distance = abs(target_value - self.value())
        duration = max(250, (duration * distance / 100)) # Scale duration based on distance
        # print(f"Animating to {target_value} in {duration} ms")

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(int(duration))
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(easing_curve)
        self.animation.start()
    
    def stop_animation(self):
        if self.animation:
            self.animation.stop()


    # Stop animation when user interacts with the slider
    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.setValue(self.value() + self.scrollStep)
        else:
            self.setValue(self.value() - self.scrollStep)
        self.stop_animation()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.stop_animation()

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.stop_animation()



class AnimatedSliderBS(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal, scrollStep=1, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)

        # self.setRange(0, 100)
        self.scrollStep = scrollStep
        self.max_limit: int = 100

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.finished.connect(lambda: self.blockSignals(False))

    def set_max_limit(self, limit: Optional[int] = None, snap: bool = True):
        self.max_limit = 100 if limit is None else max(0, min(100, int(limit)))
        if self.animation.state() == QPropertyAnimation.State.Running:
            if self.animation.endValue() > self.max_limit:
                self.stop_animation()
                if snap and self.value() > self.max_limit:
                    self.setValue(self.max_limit)
        elif snap and self.value() > self.max_limit:
            self.setValue(self.max_limit)

    def setValue(self, value: int):
        limit = getattr(self, "max_limit", 100)
        if self.animation.state() == QPropertyAnimation.State.Running and self.animation.endValue() <= limit:
            super().setValue(int(value))
        else:
            super().setValue(min(int(value), limit))

    def setSliderPosition(self, position: int):
        limit = getattr(self, "max_limit", 100)
        super().setSliderPosition(min(int(position), limit))

    def sliderChange(self, change):
        if change == QSlider.SliderChange.SliderValueChange:
            limit = getattr(self, "max_limit", 100)
            if self.animation.state() == QPropertyAnimation.State.Running and self.animation.endValue() <= limit:
                pass
            elif self.value() > limit:
                self.setValue(limit)
                return
        super().sliderChange(change)


    def animate_to(self, target_value, duration=1000, easing_curve=QEasingCurve.Type.OutCubic):
        # print(f"AnimatedSliderBS animate_to {self.value()}-{target_value}")

        limit = getattr(self, "max_limit", 100)
        target_value = min(int(target_value), limit)

        if self.animation.state() == QPropertyAnimation.State.Running:
            # logger.info("Animation is running, stopping it before starting a new one.")
            self.stop_animation() # This will also unblock signals

        current_value = self.value() # Get current value after any potential stop
        distance = abs(target_value - current_value)
        if distance == 0:
            # print("Animation distance is 0, skipping animation")
            return
        
        duration = max(250, (duration * distance / 100)) # Scale duration based on distance

        self.animation.setDuration(int(duration))
        self.animation.setStartValue(current_value) # Use current_value
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(easing_curve)

        self.blockSignals(True)  # Block signals during animation

        self.animation.start()
    
    def stop_animation(self):
        logger.info("AnimatedSliderBS stop_animation")
        
        self.animation.stop()
        self.blockSignals(False)  # Ensure signals are unblocked
        
        # self.animation.deleteLater()
        # self.animation = None
        

    # Stop animation when user interacts with the slider
    def wheelEvent(self, event: QWheelEvent):
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.stop_animation()

        limit = getattr(self, "max_limit", 100)
        step = self.scrollStep if event.angleDelta().y() > 0 else -self.scrollStep
        new_val = max(0, min(limit, self.value() + step))
        self.setValue(new_val)

    def mousePressEvent(self, event):
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.stop_animation()

        limit = getattr(self, "max_limit", 100)
        if limit < 100:
            self.blockSignals(True)
            super().mousePressEvent(event)
            self.blockSignals(False)
            if self.value() > limit:
                self.setValue(limit)
                self.setSliderPosition(limit)
            else:
                self.valueChanged.emit(self.value())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.stop_animation()

        limit = getattr(self, "max_limit", 100)
        if limit < 100:
            prev_val = self.value()
            self.blockSignals(True)
            super().mouseMoveEvent(event)
            self.blockSignals(False)
            if self.value() > limit:
                self.setSliderPosition(limit)
                if prev_val == limit:
                    self.blockSignals(True)
                    self.setValue(limit)
                    self.blockSignals(False)
                else:
                    self.setValue(limit)
            else:
                self.valueChanged.emit(self.value())
        else:
            super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.stop_animation()

        limit = getattr(self, "max_limit", 100)
        if limit < 100:
            self.blockSignals(True)
            super().keyPressEvent(event)
            self.blockSignals(False)
            if self.value() > limit:
                self.setValue(limit)
                self.setSliderPosition(limit)
            else:
                self.valueChanged.emit(self.value())
        else:
            super().keyPressEvent(event)



class SliderAnimationDemo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QSlider Animation")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()


        self.slider = AnimatedSlider()
        self.slider.setValue(15)

        self.button = QPushButton("Animate to 70")
        self.button.clicked.connect(lambda: self.slider.animate_to(70))

        self.button2 = QPushButton("Animate to 30")
        self.button2.clicked.connect(lambda: self.slider.animate_to(30))

        layout.addWidget(self.slider)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)


        self.sliders = [AnimatedSlider() for _ in range(5)]
        for slider in self.sliders:
            slider.setValue(0)

        self.button = QPushButton("Animate Sliders")
        self.button.clicked.connect(self.animate_sliders)

        for slider in self.sliders:
            layout.addWidget(slider)
        layout.addWidget(self.button)


        self.continuous_slider = AnimatedSlider()
        layout.addWidget(self.continuous_slider)
        self.continuous_slider.setValue(0)
        self.animate_continuous_slider()


        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)



    def animate_sliders(self):
        for i, slider in enumerate(self.sliders):
            QTimer.singleShot(i * 500, lambda s=slider: s.animate_to(100))

    def animate_continuous_slider(self):
        target_value = 100 if self.continuous_slider.value() == 0 else 0
        self.continuous_slider.animate_to(target_value, duration=2000)
        QTimer.singleShot(2000, self.animate_continuous_slider)



if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")

    app = QApplication([])
    window = SliderAnimationDemo()
    window.show()
    app.exec()
