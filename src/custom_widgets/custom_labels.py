from PySide6.QtWidgets import (
    QLabel, 
    QApplication, 
    QVBoxLayout, 
    QWidget, 
    QSlider,
    QPushButton
)
from PySide6.QtGui import (
    QPixmap, 
    QIcon, 
    QTransform
)
from PySide6.QtCore import (
    Qt,
    QVariantAnimation
)

class BrightnessIcon(QLabel):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)

        self.value = 0

        self.icon_path = icon_path
        self.sun_icon = QIcon(self.icon_path)

        self.icon_size = 30
        self.min_size_percentage = 75  # Minimum size of the icon in percentage
        self.min_size = self.icon_size * (self.min_size_percentage / 100)
        # print("min_size:", self.min_size)

        self.rotation_range = 270  # Control the range of rotation

        self.setFixedSize(self.icon_size, self.icon_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPixmap(self.sun_icon.pixmap(self.icon_size, self.icon_size))

        self.animation = QVariantAnimation()
        self.animation.valueChanged.connect(self.set_value)


    def set_value(self, value):
        # print(f"BrightnessIcon set_value {value}")

        value = max(0, min(100, value))  # Ensure value is between 0 and 100
        self.value = value

        # Calculate the new icon size based on the slider value
        icon_size = self.min_size + (value / 100) * (self.icon_size - self.min_size)
        # print("icon_size:", icon_size)
        pixmap = self.sun_icon.pixmap(icon_size, icon_size)
        
        # Rotate the pixmap
        angle = (value - 50) * (self.rotation_range / 100)
        transform = QTransform().rotate(angle)
        rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        
        self.setPixmap(rotated_pixmap)

    
    def animate_to(self, target_value, step_duration=8, easing_curve=None):
        # print(f"BrightnessIcon animate_to {self.value}-{target_value}")

        self.stop_animation()  # Stop any ongoing animation before starting a new one

        target_value = max(0, min(100, target_value))  # Ensure target value is between 0 and 100
        distance = abs(target_value - self.value)
        duration = int(distance * step_duration)
        # print(f"distance: {distance}, duration: {duration}")

        # animation = QVariantAnimation()
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.value)
        self.animation.setEndValue(target_value)
        if easing_curve:
            self.animation.setEasingCurve(easing_curve)

        # animation.valueChanged.connect(self.set_value)
        self.animation.start()


    def stop_animation(self):
        """Stops the current animation if it is running."""
        if (self.animation.state() == QVariantAnimation.State.Running):
            # print("BrightnessIcon stop_animation")
            self.animation.stop()

            # self.animation.deleteLater()
            # self.animation = None



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout()
    # layout.setContentsMargins(0, 0, 0, 0)

    icon = BrightnessIcon(icon_path="src/assets/icons/sun_dark.png")
    # icon.set_value(100)
    icon.setStyleSheet("""
                       background-color: blue;
                       """)
    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, 100)
    slider.valueChanged.connect(lambda value: icon.set_value(value))

    layout.addWidget(icon)
    layout.addWidget(slider)

    # Demonstration of animation
    animate_button = QPushButton("Animate to 100")
    animate_button.clicked.connect(lambda: icon.animate_to(100))
    layout.addWidget(animate_button)

    animate_button_0 = QPushButton("Animate to 0")
    animate_button_0.clicked.connect(lambda: icon.animate_to(0))
    layout.addWidget(animate_button_0)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())
