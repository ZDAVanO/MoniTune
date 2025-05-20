from PySide6.QtCore import (
    Qt, 
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QIcon, 
    QGuiApplication, 
)
from PySide6.QtWidgets import (
    QStyleFactory,
    QFrame,
    QWidget,
    QVBoxLayout,
    QGraphicsOpacityEffect,
    QApplication,
    QLabel,
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



# MARK: FadingWidget
class FadingWidget(QWidget):
    def __init__(self, fade_opacity: float = 0.5, duration: int = 500):
        super().__init__()

        # self.setStyleSheet("background-color: red;")

        self.fade_opacity = fade_opacity
        self.duration = duration

        # Adding a transparency effect to widget
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(self.fade_opacity)

        # Transparency animation
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(self.duration)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Setting up the layout
        self.box_layout = QVBoxLayout()
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.box_layout)

    def enterEvent(self, event):
        self.animate_opacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_opacity(self.fade_opacity)
        super().leaveEvent(event)

    def animate_opacity(self, target_opacity):
        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(target_opacity)
        self.anim.start()



if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    window.resize(300, 200)
    layout = QVBoxLayout()



    # Example usage of SeparatorLine
    separator = SeparatorLine(color="red")
    layout.addWidget(separator)

    # Example usage of FadingWidget
    label = QLabel("TEST TEXT")
    label.setStyleSheet("font-size: 24px;")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    fw_widget = FadingWidget(fade_opacity=0.3)
    fw_widget.box_layout.addWidget(label)
    layout.addWidget(fw_widget)



    window.setLayout(layout)
    window.setWindowTitle("No Scroll ComboBox")
    
    window.show()
    app.exec()