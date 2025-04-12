from PySide6.QtWidgets import (
    QLabel, 
    QApplication, 
    QVBoxLayout, 
    QWidget, 
    QSlider
)
from PySide6.QtGui import (
    QPixmap, 
    QIcon, 
    QTransform
)
from PySide6.QtCore import Qt

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

    def set_value(self, value):
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
                           
                            """) # background-color: yellow;
    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, 100)
    slider.valueChanged.connect(lambda value: icon.set_value(value))

    layout.addWidget(icon)
    layout.addWidget(slider)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())
