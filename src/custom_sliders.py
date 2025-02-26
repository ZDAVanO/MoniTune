from PySide6.QtWidgets import QApplication, QMainWindow, QSlider, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QWheelEvent, QKeyEvent

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

        self.setMinimum(0)
        self.setMaximum(100)


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

        QTimer.singleShot(1000, self.sleep)


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
