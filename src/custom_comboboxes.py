from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QComboBox, QStyleFactory
from PySide6.QtGui import QWheelEvent



class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        # fusion_style = QStyleFactory.create("Fusion")
        # self.setStyle(fusion_style)  # Встановлюємо стиль Fusion

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()  # Ігноруємо прокрутку



if __name__ == "__main__":
    app = QApplication([])
    
    resolutions = [
        "800x600", "1024x768", "1280x720", "1366x768", "1440x900", 
        "1600x900", "1920x1080", "2560x1440", "3200x1800", "3840x2160"
    ]
    reversed_resolutions = resolutions[::-1]
    
    window = QWidget()
    layout = QVBoxLayout()
    
    combo = NoScrollComboBox()
    combo.addItems(reversed_resolutions)
    combo.setCurrentText("3840x2160")
    
    layout.addWidget(combo)
    window.setLayout(layout)
    window.setWindowTitle("No Scroll ComboBox")
    
    window.show()
    app.exec()
