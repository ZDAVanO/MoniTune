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

# from custom_widgets.custom_labels import BrightnessIcon
try:
    from custom_labels import BrightnessIcon
except ImportError:
    from custom_widgets.custom_labels import BrightnessIcon

import time

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
    def __init__(self, orientation=Qt.Orientation.Horizontal, scrollStep=1, icon : BrightnessIcon = None, label=None, callback=None, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)

        self.animation = None
        self.scrollStep = scrollStep

        self.icon = icon  # BrightnessIcon to update
        self.label = label  # QLabel to update
        self.callback = callback if callback else self.update_ui_elements  # Default to update_ui_elements

        self.setRange(0, 100)


    def animate_to(self, target_value, duration=1000, easing_curve=QEasingCurve.Type.OutCubic):
        distance = abs(target_value - self.value())
        if distance == 0:
            # print("Animation distance is 0, skipping animation")
            return
        duration = max(250, (duration * distance / 100)) # Scale duration based on distance
        # print(f"Animating to {target_value} in {duration} ms")

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(int(duration))
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(target_value)
        self.animation.setEasingCurve(easing_curve)

        self.blockSignals(True)  # Block signals during animation
        self.animation.finished.connect(lambda: self.blockSignals(False))

        self.animation.valueChanged.connect(self.update_ui_elements)
        # if self.callback:
        #     self.animation.valueChanged.connect(self.callback)  # Connect to custom callback

        if self.icon:
            self.icon.stop_animation()  # Stop any ongoing animation in the icon

        self.animation.start()
    
    def stop_animation(self):
        if self.animation:
            self.animation.stop()
            self.blockSignals(False)  # Ensure signals are unblocked
            self.animation.deleteLater()
            self.animation = None
            print("AnimatedSliderBS Animation stopped")

    def update_ui_elements(self, value):
        if self.label:
            self.label.setText(str(value))

        if self.icon:
            # self.icon.set_value(value, stop_animation=True)
            self.icon.set_value(value)

    # Stop animation when user interacts with the slider
    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.setValue(self.value() + self.scrollStep)
        else:
            self.setValue(self.value() - self.scrollStep)
        self.stop_animation()
        # self.update_ui_elements(self.value())
        self.valueChanged.emit(self.value())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            print("Mouse pressed")
            if self.animation and (self.animation.state() == QPropertyAnimation.State.Running):
                self.stop_animation()
                # self.update_ui_elements(self.value())
                self.valueChanged.emit(self.value())

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if self.animation and (self.animation.state() == QPropertyAnimation.State.Running):
            self.stop_animation()
            # self.update_ui_elements(self.value())
            self.valueChanged.emit(self.value())

    def add_icon(self, icon):
        self.icon = icon
        # self.valueChanged.connect(lambda value, ico=self.icon: ico.set_value(value))
        self.valueChanged.connect(lambda value, ico=self.icon: ico.animate_to(value))

    def add_label(self, label):
        self.label = label
        self.valueChanged.connect(lambda value, lbl=self.label: lbl.setText(str(value)))

    def setValueBS(self, value):

        if self.animation and (self.animation.state() == QPropertyAnimation.State.Running):
            self.stop_animation()

        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
        
        # self.update_ui_elements(value)
        # self.update_ui_elements_a(value)
        if self.label:
            self.label.setText(str(value))
        if self.icon:
            self.icon.animate_to(value)



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

        # Demonstration of AnimatedSliderBS with QLabel
        self.label_slider_label = QLabel("0")
        self.label_slider = AnimatedSliderBS(label=self.label_slider_label)
        self.label_slider.setValue(50)
        self.label_slider_button = QPushButton("Animate to 100")
        self.label_slider_button.clicked.connect(lambda: self.label_slider.animate_to(100))
        layout.addWidget(self.label_slider)
        layout.addWidget(self.label_slider_label)

        # Demonstration with BrightnessIcon
        self.br_icon = BrightnessIcon(icon_path="src/assets/icons/sun_dark.png")
        self.br_icon.set_value(50)
        self.label_slider.add_icon(self.br_icon)
        layout.addWidget(self.br_icon)

        layout.addWidget(self.label_slider_button)

        # Connect QLabel to slider's valueChanged signal
        self.label_slider.add_label(self.label_slider_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # QTimer.singleShot(1000, self.sleep)


    def animate_sliders(self):
        for i, slider in enumerate(self.sliders):
            QTimer.singleShot(i * 500, lambda s=slider: s.animate_to(100))

    def animate_continuous_slider(self):
        target_value = 100 if self.continuous_slider.value() == 0 else 0
        self.continuous_slider.animate_to(target_value, duration=2000)
        QTimer.singleShot(2000, self.animate_continuous_slider)

    def sleep(self):
        time.sleep(2)




if __name__ == "__main__":
    app = QApplication([])
    window = SliderAnimationDemo()
    window.show()
    app.exec()
