from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtCore import Qt
import sys

class BrightnessControl(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Brightness Control")
        self.setGeometry(100, 100, 400, 400)
        
        layout = QVBoxLayout(self)
        
        # Завантажуємо іконку сонця
        self.sun_icon = QPixmap("src/assets/icons/sun_dark.png")  # Переконайтесь, що sun.png є в тій же папці
        self.icon_label = QLabel()
        self.icon_label.setPixmap(self.sun_icon)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Створюємо слайдер
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.update_icon)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.slider)
        
        self.rotation_range = 90  # Контроль діапазону обертання
    
    def update_icon(self, value):
        angle = (value - 50) * (self.rotation_range / 50)  # Використання змінної для обертання
        scale_factor = 0.5 + (value / 100)  # Масштабування від 0.5 до 1.5
        
        transform = QTransform().rotate(angle).scale(scale_factor, scale_factor)
        transformed_pixmap = self.sun_icon.transformed(transform, Qt.SmoothTransformation)
        self.icon_label.setPixmap(transformed_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrightnessControl()
    window.show()
    sys.exit(app.exec())
