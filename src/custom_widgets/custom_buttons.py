from PySide6.QtWidgets import QPushButton, QWidget, QGridLayout, QVBoxLayout, QApplication

class RRButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(55)
        self.setFixedHeight(28)
        # self.setFixedHeight(26)
        self.setCheckable(True)

    def mousePressEvent(self, event):
        if not self.isChecked():
            super().mousePressEvent(event)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    
    button = RRButton("Click Me")
    layout.addWidget(button)
    
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())

