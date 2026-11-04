"""
BrightnessCoordinator - Centralized, pure business-logic engine for MoniTune brightness decisions.

This module is completely decoupled from Qt widgets, Win32 API, and DDC/CI hardware calls.
It evaluates inputs on-demand, resolving target brightness values and enforcing safety limits
with 0% idle CPU overhead.
"""

from typing import Dict, Optional


class BrightnessCoordinator:
    def __init__(self) -> None:
        self.pre_saving_brightness: Dict[str, int] = {}
        self.active_limits: Dict[str, int] = {}
        self.is_power_saving: bool = False

    # MARK: Power Saving Evaluation
    @staticmethod
    def is_power_saving_effective(
        enable_limits: bool,
        mode: str,
        manual_state: bool,
        is_windows_energy_saver: bool,
    ) -> bool:
        """Determines whether power saving brightness limits should be enforced."""
        if not enable_limits:
            return False
        if mode == "manual":
            return bool(manual_state)
        return bool(is_windows_energy_saver)

    # MARK: Priority Resolution
    @staticmethod
    def resolve_brightness(
        enable_profiles: bool,
        profile_value: Optional[int],
        enable_schedule: bool,
        schedule_value: Optional[int],
        manual_value: Optional[int],
        is_power_saving: bool,
        power_saving_limit: Optional[int] = 100,
    ) -> int:
        """
        Resolves the winning brightness value according to the priority hierarchy:
        1. Active App Profile (if enabled & present)
        2. Schedule Time Adjustment (if enabled & present)
        3. Manual Brightness (fallback)
        Final: Clamped by Power Saving limit (if active)
        """
        if enable_profiles and profile_value is not None:
            val = profile_value
        elif enable_schedule and schedule_value is not None:
            val = schedule_value
        else:
            val = manual_value if manual_value is not None else 50

        if is_power_saving:
            limit = power_saving_limit if power_saving_limit is not None else 100
            val = min(val, limit)

        return max(0, min(100, int(val)))

    # MARK: Linked Monitors Delta Calculation
    @staticmethod
    def calculate_linked_change(
        master_serial: str,
        new_master_value: int,
        current_values: Dict[str, int],
        limits: Optional[Dict[str, int]] = None,
        is_power_saving: bool = False,
    ) -> Dict[str, int]:
        """
        Calculates synchronized brightness changes for linked monitors.
        Preserves offsets between sliders while strictly respecting individual limits.
        """
        limits = limits or {}
        master_limit = limits.get(master_serial, 100) if is_power_saving else 100
        effective_master_val = max(0, min(master_limit, new_master_value))

        prev_master_val = current_values.get(master_serial, 0)
        delta = effective_master_val - prev_master_val

        result: Dict[str, int] = dict(current_values)
        result[master_serial] = effective_master_val

        for serial, val in current_values.items():
            if serial == master_serial:
                continue
            limit = limits.get(serial, 100) if is_power_saving else 100
            new_val = max(0, min(limit, val + delta))
            result[serial] = int(new_val)

        return result

    # MARK: Startup Resolution
    @staticmethod
    def resolve_startup_brightness(
        restore_last_brightness: bool,
        time_adjustment_startup: bool,
        schedule_value: Optional[int],
        saved_manual_value: Optional[int],
        is_power_saving: bool,
        power_saving_limit: Optional[int] = 100,
    ) -> int:
        """Resolves target brightness on MoniTune application launch."""
        if time_adjustment_startup and schedule_value is not None:
            val = schedule_value
        elif restore_last_brightness and saved_manual_value is not None:
            val = saved_manual_value
        else:
            val = 50

        if is_power_saving:
            limit = power_saving_limit if power_saving_limit is not None else 100
            val = min(val, limit)

        return max(0, min(100, int(val)))

    # MARK: Power Saving Lifecycle Management
    def enter_power_saving(
        self,
        current_brightness: Optional[Dict[str, int]] = None,
        limits: Optional[Dict[str, int]] = None,
        fallback_brightness: Optional[Dict[str, int]] = None,
        live_brightness: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """
        Enters power saving state: preserves initial brightness and clamps targets.
        Prefers live active brightness over stale manual/saved brightness.
        Returns the new clamped brightness values for each monitor.
        """
        self.is_power_saving = True
        limits = limits or {}
        self.active_limits = dict(limits)

        # live brightness can be passed as live_brightness or current_brightness
        live = live_brightness if live_brightness is not None else (current_brightness or {})
        fallback = fallback_brightness or {}
        target_values: Dict[str, int] = {}

        all_serials = set(live.keys()) | set(limits.keys()) | set(fallback.keys())
        for serial in all_serials:
            val = live.get(serial)
            if val is None:
                val = fallback.get(serial, 50)

            if serial not in self.pre_saving_brightness:
                self.pre_saving_brightness[serial] = val

            limit = limits.get(serial, 100)
            target_values[serial] = min(self.pre_saving_brightness[serial], limit)

        return target_values

    def exit_power_saving(self) -> Dict[str, int]:
        """
        Exits power saving state: releases limits and returns pre-saving brightness.
        """
        self.is_power_saving = False
        self.active_limits.clear()
        restored = dict(self.pre_saving_brightness)
        self.pre_saving_brightness.clear()
        return restored

    def clamp_value(self, serial: str, value: int, limit: Optional[int] = None) -> int:
        """Clamps a brightness value to the monitor's limit if power saving is active."""
        if self.is_power_saving or limit is not None:
            active_limit = limit if limit is not None else self.active_limits.get(serial, 100)
            return max(0, min(active_limit, int(value)))
        return max(0, min(100, int(value)))

    def get_active_limit(self, serial: str) -> int:
        """Gets active limit for monitor, defaulting to 100."""
        return self.active_limits.get(serial, 100)

    def get_pre_saving_brightness(self, serial: str) -> Optional[int]:
        """Gets stored pre-saving brightness for monitor."""
        return self.pre_saving_brightness.get(serial)
