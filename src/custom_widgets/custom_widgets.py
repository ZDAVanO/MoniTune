from PySide6.QtCore import (
    Qt, 
)
from PySide6.QtGui import (
    QIcon, 
    QGuiApplication, 
)
from PySide6.QtWidgets import (
    QStyleFactory,
    QFrame,
)



# MARK: SeparatorLine
class SeparatorLine(QFrame):
    def __init__(self, color: str = None, line_width: int = 1, parent=None):
        super().__init__(parent)

        fusion_style = QStyleFactory.create("Fusion")

        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyle(fusion_style)
        if color:
            self.setStyleSheet(f"color: {color};")
        self.setLineWidth(line_width)


