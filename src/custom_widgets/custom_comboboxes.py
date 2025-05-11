from PySide6.QtWidgets import (
    QApplication, 
    QVBoxLayout, 
    QWidget, 
    QComboBox, 
    QStyleFactory
)
from PySide6.QtGui import QWheelEvent

import os

import logging
logger = logging.getLogger(__name__)



class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()  # ignore the wheel event to prevent scrolling


class StyledComboBox(NoScrollComboBox):
    def __init__(self, parent, down_arrow: str, bg_color: str = None):
        super().__init__(parent)
        
        absolute_icon_path = os.path.abspath(down_arrow).replace('\\', '/')
        logger.debug(f"StyledComboBox down_arrow: {down_arrow}")
        logger.debug(f"StyledComboBox absolute_icon_path: {absolute_icon_path}")

        self.setStyleSheet(f"""
                            /* Basic QComboBox style */
                            QComboBox {{
                                font-size: 14px; font-weight: bold;
                                padding-left: 7px;
                                {f"background-color: {bg_color};" if bg_color else ""}
                            }}
                            /* Dropdown list style */
                            QComboBox QAbstractItemView {{
                                padding: 0px;
                            }}
                            QComboBox::drop-down {{
                                border: 0px;
                            }}
                            QComboBox::down-arrow {{
                                image: url('{absolute_icon_path}');
                                width: 11px;
                                height: 11px;
                                margin-right: 10px;
                                }}
                            """)



if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")


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
