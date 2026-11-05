"""
BrightnessCoordinator - Centralized, pure business-logic engine for MoniTune brightness decisions.

This module is completely decoupled from Qt widgets, Win32 API, and DDC/CI hardware calls.
It evaluates inputs on-demand, resolving target brightness values and enforcing safety limits
with 0% idle CPU overhead.
"""

from typing import Dict, Iterable, Optional


class BrightnessCoordinator:
    def __init__(self) -> None:
        self.pre_saving_brightness: Dict[str, int] = {}
        self.active_limits: Dict[str, int] = {}
        self.is_power_saving: bool = False

    # MARK: Power Saving Evaluation
    @staticmethod
    def is_power_saving_effective(
        enable_limits: bool,
        sync_windows: bool = True,
        manual_state: bool = False,
        is_windows_energy_saver: bool = False,
        mode: Optional[str] = None,
    ) -> bool:
        """Determines whether power saving brightness limits should be enforced."""
        if not enable_limits:
            return False
        if mode == "manual":
            return bool(manual_state)
        if mode == "windows":
            return bool(is_windows_energy_saver)
        if sync_windows:
            return bool(is_windows_energy_saver)
        return bool(manual_state)

    # MARK: Priority Resolution
    @staticmethod
    def resolve_brightness(
        active_serials: Iterable[str],
        profile_data: Optional[Dict[str, int]] = None,
        schedule_data: Optional[Dict[str, int]] = None,
        manual_data: Optional[Dict[str, int]] = None,
        enable_profiles: bool = True,
        enable_schedule: bool = True,
        restore_last_brightness: bool = True,
        is_power_saving: bool = False,
        limits: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """
        Resolves target brightness for active monitors according to priority:
        1. Active App Profile (if enable_profiles=True and serial in profile_data)
        2. Schedule Time Adjustment (if enable_schedule=True and serial in schedule_data)
        3. Saved Manual Brightness (if restore_last_brightness=True and serial in manual_data)
        4. Untouched (if monitor has no target in 1, 2, or 3, it is omitted from the result)
        Final: Clamped by Power Saving limit (if is_power_saving=True, capped to monitor's limit)

        Returns:
            Dict[serial, target_brightness] containing only monitors with resolved targets.
        """
        limits = limits or {}
        manual_data = manual_data or {}
        schedule_data = schedule_data or {}
        profile_data = profile_data or {}
        resolved: Dict[str, int] = {}

        for serial in active_serials:
            val: Optional[int] = None
            if enable_profiles and serial in profile_data:
                val = profile_data[serial]
            elif enable_schedule and serial in schedule_data:
                val = schedule_data[serial]
            elif restore_last_brightness and serial in manual_data:
                val = manual_data[serial]

            if val is not None:
                if is_power_saving:
                    limit = limits.get(serial, 100)
                    val = min(val, limit)
                resolved[serial] = max(0, min(100, int(val)))

        return resolved

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
                val = fallback.get(serial)
            if val is None:
                continue

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

    def record_pre_saving_brightness(self, serial: str, value: int) -> None:
        """Stores pre-saving brightness for a monitor if not already recorded."""
        if serial not in self.pre_saving_brightness:
            self.pre_saving_brightness[serial] = int(value)

    def remove_monitor(self, serial: str) -> None:
        """Cleans up internal state when a monitor is disconnected."""
        self.pre_saving_brightness.pop(serial, None)
        self.active_limits.pop(serial, None)

    @staticmethod
    def get_recent_task_time(task_times: Iterable[str], current_time: str) -> Optional[str]:
        """
        Finds the most recent schedule slot matching current_time ("HH:mm").
        If current_time is earlier than all slots, wraps around to the latest slot of the previous day.
        """
        times = [t for t in task_times if t]
        if not times:
            return None
        past = [t for t in times if t <= current_time]
        if past:
            return max(past)
        return max(times)
