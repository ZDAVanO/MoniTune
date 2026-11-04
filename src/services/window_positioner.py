import logging
from PySide6.QtCore import QRect

logger = logging.getLogger(__name__)


def detect_taskbar_edge(full_rect: QRect, work_rect: QRect) -> str:
    """Detect which edge the taskbar is docked to by comparing work area to full screen."""
    if work_rect.top() > full_rect.top():
        return "top"
    elif work_rect.left() > full_rect.left():
        return "left"
    elif work_rect.right() < full_rect.right():
        return "right"
    else:
        return "bottom"


def calculate_window_rects(
    full_rect: QRect,
    work_rect: QRect,
    win_w: int,
    win_h: int,
    offset: int,
    is_popup: bool,
    popup_position: str = "bottom_right"
) -> tuple[str, QRect, QRect, QRect]:
    """
    Calculate target_rect, start_rect (slide-in start), and end_rect (slide-out end)
    for main window or popup.

    Returns:
        (taskbar_edge, target_rect, start_rect, end_rect)
    """
    taskbar_edge = detect_taskbar_edge(full_rect, work_rect)

    if not is_popup:
        # Standard main window anchored near taskbar / notification area
        if taskbar_edge == "top":
            target_x = work_rect.right() - win_w - offset + 1
            target_y = work_rect.top() + offset
        elif taskbar_edge == "left":
            target_x = work_rect.left() + offset
            target_y = work_rect.bottom() - win_h - offset + 1
        elif taskbar_edge == "right":
            target_x = work_rect.right() - win_w - offset + 1
            target_y = work_rect.bottom() - win_h - offset + 1
        else:  # bottom
            target_x = work_rect.right() - win_w - offset + 1
            target_y = work_rect.bottom() - win_h - offset + 1

        target_rect = QRect(target_x, target_y, win_w, win_h)

        if taskbar_edge in ("left", "right"):
            start_rect = QRect(target_x, work_rect.bottom() + 1, win_w, win_h)
            end_rect = QRect(target_x, work_rect.bottom() + 1, win_w, win_h)
        else:
            start_rect = QRect(work_rect.right() + 1, target_y, win_w, win_h)
            end_rect = QRect(work_rect.right() + 1, target_y, win_w, win_h)

        return taskbar_edge, target_rect, start_rect, end_rect

    # Popup mode: anchor in user-specified corner within work_rect
    pos = (popup_position or "bottom_right").lower()
    is_left = "left" in pos
    is_top = "top" in pos

    # Calculate target position inside work_rect (which naturally excludes the taskbar)
    target_x = (work_rect.left() + offset) if is_left else (work_rect.right() - win_w - offset + 1)
    target_y = (work_rect.top() + offset) if is_top else (work_rect.bottom() - win_h - offset + 1)
    target_rect = QRect(target_x, target_y, win_w, win_h)

    # Determine slide-in and slide-out animation vectors
    if is_left:
        if taskbar_edge == "left":
            # Taskbar on the left: slide along vertical axis
            if is_top:
                start_x, start_y = target_x, work_rect.top() - win_h - 1
            else:
                start_x, start_y = target_x, work_rect.bottom() + 1
        else:
            # Taskbar is bottom/top/right: slide horizontally from left screen edge
            start_x, start_y = work_rect.left() - win_w - 1, target_y
    else:  # right side
        if taskbar_edge == "right":
            # Taskbar on the right: slide along vertical axis
            if is_top:
                start_x, start_y = target_x, work_rect.top() - win_h - 1
            else:
                start_x, start_y = target_x, work_rect.bottom() + 1
        else:
            # Taskbar is bottom/top/left: slide horizontally from right screen edge
            start_x, start_y = work_rect.right() + 1, target_y

    start_rect = QRect(start_x, start_y, win_w, win_h)
    end_rect = QRect(start_x, start_y, win_w, win_h)

    return taskbar_edge, target_rect, start_rect, end_rect
