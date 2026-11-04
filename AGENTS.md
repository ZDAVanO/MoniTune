# MoniTune — Agent Guidelines

Windows tray utility for multi-monitor brightness, contrast, and refresh rate management via DDC/CI & WMI, featuring Power Saving limits, profile automation, and corner popups.

## Essential Commands

- **Run Application:** `uv run python src/MoniTune.py`
- **Run All Tests:** `uv run pytest`
- **Run Specific Test:** `uv run pytest tests/test_brightness_logic.py`
- **Install Dependency:** `uv pip install <package>`

## Architecture & Code Map

- `src/MoniTune.py`: Main PySide6 application window, system tray integration, window lifecycle, and popup orchestration.
- `src/settings_window.py`: Multi-tab configuration dialog (Profiles, Power Saving, DDC/CI, Brightness, Hotkeys).
- `src/services/`: Pure business logic decoupled from UI widgets:
  - `brightness_coordinator.py`: State machine for brightness resolution, Power Saving limits, linked slider deltas, and pre-saving recovery.
  - `settings_manager.py`: Typed configuration manager backed by Windows Registry (`HKCU\Software\MoniTune`) with Qt signal notifications.
  - `window_positioner.py`: Taskbar edge detection, corner targeting (top/bottom, left/right), and slide animation geometry.
- `src/utils/`: Hardware and Win32 OS bridges:
  - `monitor_utils.py`: DDC/CI (VCP) and WMI physical monitor discovery and control.
  - `power_detect.py`: Windows Energy Saver detection via `GetSystemPowerStatus`.
  - `reg_utils.py`: Low-level registry read/write wrappers.
  - `lock_detect.py` / `active_process.py`: Session lock detection and active window process listeners.
- `src/custom_widgets/`: Reusable PySide6 UI controls (sliders, frames, animated icons).
- `tests/`: Automated test suite with PySide6 fixture in `conftest.py`.

## Project-Specific Rules

1. **NO GIT COMMITS:** Never run `git commit`. The user commits manually. Leave all work as unstaged changes.
2. **Logic Decoupling:** Keep mathematical and algorithmic state logic in `src/services/` (unit-testable via `pytest`) rather than embedding complex calculations inside Qt UI callbacks.
