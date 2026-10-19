from typing import Callable, List, Optional
from PySide6.QtWidgets import QFrame, QGridLayout
from custom_widgets.custom_buttons import CheckLockButton
from utils.logger import get_logger

logger = get_logger(__name__)


# MARK: ButtonGridFrame
class ButtonGridFrame(QFrame):
    def __init__(self, values: List[int], active_value: int, callback: Optional[Callable[[int], bool]] = None):
        super().__init__()

        self.values = values
        self.active_value = active_value
        self.callback = callback

        self.buttons: List[CheckLockButton] = []

        self.setObjectName("ButtonGridFrame")

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)

        num_columns = 6
        for idx, value in enumerate(values):
            button = CheckLockButton(f"{value} Hz")
            button.setMinimumWidth(55)
            button.setFixedHeight(28)  # 26
            if value == self.active_value:
                button.setChecked(True)
            button.clicked.connect(
                lambda checked, r=value, btn=button: self.on_button_click(r, btn)
            )

            row = idx // num_columns
            col = idx % num_columns

            self.grid.addWidget(button, row, col)
            self.buttons.append(button)  # Store button

    # MARK: on_button_click()
    def on_button_click(self, value, button):
        logger.info(f"Button clicked: {value}")

        callback_result = self.callback(value) if self.callback else False

        if callback_result:
            # disable all other buttons for this monitor
            for btn in self.buttons:
                if btn != button:
                    btn.setChecked(False)
        else:
            button.setChecked(False)  # Revert the button state if callback fails
            # button.setStyleSheet("background-color: #ff3232;")
            # button.setStyleSheet(f"""
            #     QPushButton {{
            #         background-color: #ff4545;
            #     }}
            #     """)
            button.setToolTip("Failed to set refresh rate")
            button.setDisabled(True)
