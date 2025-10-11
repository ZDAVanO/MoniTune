from PySide6.QtWidgets import (
    QPushButton, 
    QWidget, 
    QGridLayout, 
    QVBoxLayout, 
    QApplication
)
from PySide6.QtGui import (
    QIcon, 
)

class CheckLockButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)

    def mousePressEvent(self, event):
        if not self.isChecked():
            super().mousePressEvent(event)


class HoverIconButton(QPushButton):
    def __init__(self, icon_path, hover_icon_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.default_icon = QIcon(icon_path)
        self.hover_icon = QIcon(hover_icon_path)

        self.setIcon(self.default_icon)
        self.active_def_icon = True

    def enterEvent(self, event):
        if self.isEnabled():
            self.setIcon(self.hover_icon)
            self.active_def_icon = False
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled() and self.active_def_icon:
            self.setIcon(self.default_icon)
            self.active_def_icon = True
        super().leaveEvent(event)

    def applyDefaultIcon(self):
        self.setIcon(self.default_icon)
        self.active_def_icon = True

    def applyHoverIcon(self):
        self.setIcon(self.hover_icon)
        self.active_def_icon = False



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    
    button = CheckLockButton("Click Me")
    layout.addWidget(button)
    
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())

