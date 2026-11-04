import pytest
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QMouseEvent
from custom_widgets.custom_sliders import AnimatedSliderBS
from custom_widgets.slider_frame import SliderFrame


def test_animated_slider_maintains_full_range_and_clamps(qapp):
    slider = AnimatedSliderBS(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    assert slider.maximum() == 100

    slider.setValue(60)
    assert slider.value() == 60

    # Apply limit: should clamp value without changing maximum range
    slider.set_max_limit(25)
    assert slider.maximum() == 100
    assert slider.value() == 25

    # Attempt to set beyond limit
    slider.setValue(80)
    assert slider.value() == 25

    # Attempt to set slider position (e.g. mouse drag) beyond limit
    slider.setSliderPosition(90)
    assert slider.sliderPosition() == 25
    assert slider.value() == 25

    # Setting below limit works normally
    slider.setValue(10)
    assert slider.value() == 10

    # Releasing limit to 100 allows moving above 25 again
    slider.set_max_limit(100)
    slider.setValue(85)
    assert slider.value() == 85


def test_slider_frame_set_max_limit(qapp):
    frame = SliderFrame(value=50)
    assert frame.slider.maximum() == 100
    assert frame.slider.value() == 50
    assert frame.label.text() == "50"

    # Enforce power saving limit
    frame.set_max_limit(15)
    assert frame.slider.maximum() == 100
    assert frame.slider.value() == 15
    assert frame.label.text() == "15"

    # setValueBS clamps to limit
    frame.setValueBS(70)
    assert frame.slider.value() == 15
    assert frame.label.text() == "15"

    # Release limit
    frame.set_max_limit(100)
    frame.setValueBS(70)
    assert frame.slider.value() == 70
    assert frame.label.text() == "70"


def test_slider_frame_mouse_interaction_never_exceeds_limit(qapp):
    observed_callback_values = []
    frame = SliderFrame(
        value=50,
        slider_callback=lambda val: observed_callback_values.append(val),
    )
    frame.resize(250, 40)
    frame.show()
    frame.set_max_limit(15)

    assert frame.label.text() == "15"

    # Click far to the right (at x=220) where 100% would be
    press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(220, 15),
        QPointF(220, 15),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    frame.slider.mousePressEvent(press)

    # Value, label, and callback must stay clamped to 15
    assert frame.slider.value() == 15
    assert frame.slider.sliderPosition() == 15
    assert frame.label.text() == "15"
    assert frame.icon.value == 15
    for val in observed_callback_values:
        assert val <= 15

    # Drag further to x=240
    drag = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(240, 15),
        QPointF(240, 15),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    frame.slider.mouseMoveEvent(drag)

    assert frame.slider.value() == 15
    assert frame.label.text() == "15"
    for val in observed_callback_values:
        assert val <= 15


def test_slider_frame_animation_down_and_up(qapp):
    frame = SliderFrame(value=40)
    frame.resize(250, 40)
    frame.show()

    # Enter power saving without snapping, then animate
    frame.set_max_limit(15, snap=False)
    frame.animate_to(15, duration=100)

    emitted_down = []
    frame.slider.animation.valueChanged.connect(lambda v: emitted_down.append(v))

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(qapp.quit)
    timer.start(350)
    qapp.exec()

    assert frame.slider.value() == 15
    assert frame.label.text() == "15"
    assert any(15 < v < 40 for v in emitted_down)

    # Exit power saving: release limit and animate up
    frame.set_max_limit(100)
    frame.animate_to(40, duration=100)

    emitted_up = []
    frame.slider.animation.valueChanged.connect(lambda v: emitted_up.append(v))

    timer2 = QTimer()
    timer2.setSingleShot(True)
    timer2.timeout.connect(qapp.quit)
    timer2.start(350)
    qapp.exec()

    assert frame.slider.value() == 40
    assert frame.label.text() == "40"
    assert any(15 < v < 40 for v in emitted_up)
