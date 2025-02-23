from PySide6.QtWidgets import QApplication, QSlider, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

class CustomSlider(QWidget):
    def __init__(self):
        super().__init__()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 120px;
                
            }
            QSlider::handle:horizontal {
                image: url('src/assets/icons/sun_dark.png');
                width: 150px;
                height: 150px;
                                  background: green;
            }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(self.slider)

if __name__ == "__main__":
    app = QApplication([])
    window = CustomSlider()
    window.show()
    app.exec()
