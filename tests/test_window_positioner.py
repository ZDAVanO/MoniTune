import pytest
from PySide6.QtCore import QRect
from services.window_positioner import detect_taskbar_edge, calculate_window_rects


def test_detect_taskbar_edge():
    full = QRect(0, 0, 1920, 1080)

    # Bottom taskbar
    assert detect_taskbar_edge(full, QRect(0, 0, 1920, 1032)) == "bottom"
    # Top taskbar
    assert detect_taskbar_edge(full, QRect(0, 48, 1920, 1032)) == "top"
    # Left taskbar
    assert detect_taskbar_edge(full, QRect(60, 0, 1860, 1080)) == "left"
    # Right taskbar
    assert detect_taskbar_edge(full, QRect(0, 0, 1860, 1080)) == "right"


def test_main_window_bottom_taskbar():
    full = QRect(0, 0, 1920, 1080)
    work = QRect(0, 0, 1920, 1032)
    win_w, win_h = 350, 400
    offset = 12

    edge, target, start, end = calculate_window_rects(
        full, work, win_w, win_h, offset, is_popup=False
    )
    assert edge == "bottom"
    assert target.x() == work.right() - win_w - offset + 1
    assert target.y() == work.bottom() - win_h - offset + 1
    assert target.width() == win_w
    assert target.height() == win_h

    # Slides in/out from right edge
    assert start.x() == work.right() + 1
    assert start.y() == target.y()
    assert end == start


def test_main_window_left_taskbar():
    full = QRect(0, 0, 1920, 1080)
    work = QRect(60, 0, 1860, 1080)
    win_w, win_h = 350, 400
    offset = 12

    edge, target, start, end = calculate_window_rects(
        full, work, win_w, win_h, offset, is_popup=False
    )
    assert edge == "left"
    assert target.x() == work.left() + offset
    assert target.y() == work.bottom() - win_h - offset + 1

    # Vertical slide from bottom
    assert start.x() == target.x()
    assert start.y() == work.bottom() + 1
    assert end == start


@pytest.mark.parametrize("position,expected_left,expected_top", [
    ("bottom_right", False, False),
    ("top_right", False, True),
    ("bottom_left", True, False),
    ("top_left", True, True),
])
def test_popup_corners_bottom_taskbar(position, expected_left, expected_top):
    full = QRect(0, 0, 1920, 1080)
    work = QRect(0, 0, 1920, 1032)
    win_w, win_h = 350, 400
    offset = 10

    edge, target, start, end = calculate_window_rects(
        full, work, win_w, win_h, offset, is_popup=True, popup_position=position
    )

    assert edge == "bottom"

    if expected_left:
        assert target.x() == work.left() + offset
        # Slides from left
        assert start.x() == work.left() - win_w - 1
        assert start.y() == target.y()
    else:
        assert target.x() == work.right() - win_w - offset + 1
        # Slides from right
        assert start.x() == work.right() + 1
        assert start.y() == target.y()

    if expected_top:
        assert target.y() == work.top() + offset
    else:
        assert target.y() == work.bottom() - win_h - offset + 1


def test_popup_side_taskbars():
    full = QRect(0, 0, 1920, 1080)
    win_w, win_h = 350, 400
    offset = 10

    # Right taskbar
    work_right = QRect(0, 0, 1860, 1080)
    _, target_tr, start_tr, _ = calculate_window_rects(
        full, work_right, win_w, win_h, offset, is_popup=True, popup_position="top_right"
    )
    # Slides from top
    assert start_tr.x() == target_tr.x()
    assert start_tr.y() == work_right.top() - win_h - 1

    _, target_br, start_br, _ = calculate_window_rects(
        full, work_right, win_w, win_h, offset, is_popup=True, popup_position="bottom_right"
    )
    # Slides from bottom
    assert start_br.x() == target_br.x()
    assert start_br.y() == work_right.bottom() + 1

    # Left taskbar
    work_left = QRect(60, 0, 1860, 1080)
    _, target_tl, start_tl, _ = calculate_window_rects(
        full, work_left, win_w, win_h, offset, is_popup=True, popup_position="top_left"
    )
    # Slides from top
    assert start_tl.x() == target_tl.x()
    assert start_tl.y() == work_left.top() - win_h - 1

    _, target_bl, start_bl, _ = calculate_window_rects(
        full, work_left, win_w, win_h, offset, is_popup=True, popup_position="bottom_left"
    )
    # Slides from bottom
    assert start_bl.x() == target_bl.x()
    assert start_bl.y() == work_left.bottom() + 1
