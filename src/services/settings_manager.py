import copy
import logging
import platform
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal

# Support running both directly from root and when src is in sys.path
try:
    import config as cfg
    from utils.reg_utils import (
        delete_reg_key,
        reg_read_bool,
        reg_read_dict,
        reg_read_int,
        reg_read_list,
        reg_write_bool,
        reg_write_dict,
        reg_write_int,
        reg_write_list,
        reg_read_str,
        reg_write_str,
    )
except ImportError:
    from src import config as cfg
    from src.utils.reg_utils import (
        delete_reg_key,
        reg_read_bool,
        reg_read_dict,
        reg_read_int,
        reg_read_list,
        reg_write_bool,
        reg_write_dict,
        reg_write_int,
        reg_write_list,
        reg_read_str,
        reg_write_str,
    )

logger = logging.getLogger(__name__)


def _read_tray_icon(reg_path: str) -> str:
    """Read tray icon name from registry stored as a list."""
    icons = reg_read_list(reg_path, "TrayIcon")
    return icons[0] if icons else "monitune"


def _write_tray_icon(reg_path: str, value: str) -> None:
    """Write tray icon name to registry as a list."""
    reg_write_list(reg_path, "TrayIcon", [str(value)])


@dataclass(frozen=True)
class SettingSpec:
    """Definition for an individual application setting."""
    name: str
    reg_name: str
    val_type: type
    default_factory: Callable[[], Any]
    custom_read: Optional[Callable[[str], Any]] = None
    custom_write: Optional[Callable[[str, Any], None]] = None


# MARK: Setting Specifications Registry
_SPECS: List[SettingSpec] = [
    # General tab
    SettingSpec("launch_on_startup", "LaunchOnStartup", bool, lambda: False),
    SettingSpec("enable_window_animation", "EnableWindowAnimation", bool, lambda: True),
    SettingSpec(
        "enable_rounded_corners",
        "EnableRoundedCorners",
        bool,
        lambda: platform.release() == "11",
    ),
    SettingSpec("show_resolution", "ShowResolution", bool, lambda: True),
    SettingSpec("enable_fusion_theme", "EnableFusionTheme", bool, lambda: False),
    SettingSpec("enable_logging", "EnableLogging", bool, lambda: False),
    SettingSpec("enable_break_reminders", "EnableBreakReminders", bool, lambda: False),
    SettingSpec(
        "enable_idle_detection",
        "EnableIdleDetection",
        bool,
        lambda: getattr(cfg, "enable_idle_detection", True),
    ),
    SettingSpec(
        "break_idle_threshold",
        "BreakIdleThreshold",
        int,
        lambda: getattr(cfg, "break_idle_threshold", 10),
    ),
    SettingSpec(
        "break_notification_interval",
        "BreakNotificationInterval",
        int,
        lambda: getattr(cfg, "break_notification_interval", 30),
    ),
    SettingSpec("hidden_displays", "HiddenDisplays", list, list),
    SettingSpec("custom_monitor_names", "CustomMonitorNames", dict, dict),
    SettingSpec("monitors_order", "MonitorsOrder", list, list),
    SettingSpec(
        "tray_icon_name",
        "TrayIcon",
        str,
        lambda: "monitune",
        custom_read=_read_tray_icon,
        custom_write=_write_tray_icon,
    ),

    # Refresh rates tab
    SettingSpec("show_refresh_rates", "ShowRefreshRates", bool, lambda: True),
    SettingSpec("excluded_rates", "ExcludedHzRates", dict, dict),

    # Brightness tab
    SettingSpec("restore_last_brightness", "RestoreLastBrightness", bool, lambda: True),
    SettingSpec("show_brightness_popup", "ShowBrightnessPopup", bool, lambda: False),
    SettingSpec("skip_popup_if_unchanged", "SkipPopupIfUnchanged", bool, lambda: True),
    SettingSpec("popup_position", "PopupPosition", str, lambda: "bottom_right"),
    SettingSpec("brightness_values", "BrightnessValues", dict, dict),
    SettingSpec("manual_brightness_values", "ManualBrightnessValues", dict, dict),
    SettingSpec("enable_time_adjustment", "EnableTimeAdjustment", bool, lambda: False),
    SettingSpec("time_adjustment_startup", "TimeAdjustmentStartup", bool, lambda: True),
    SettingSpec("time_adjustment_data", "TimeAdjustmentData", dict, dict),
    SettingSpec("link_brightness", "LinkBrightness", bool, lambda: False),

    # DDC/CI tab
    SettingSpec("show_contrast_sliders", "ShowContrastSliders", bool, lambda: False),
    SettingSpec("contrast_values", "ContrastValues", dict, dict),

    # Profiles tab
    SettingSpec("enable_profiles", "EnableProfiles", bool, lambda: False),
    SettingSpec("profiles_data", "ProfilesData", dict, dict),
    SettingSpec("ignored_processes", "IgnoredProcesses", list, lambda: ["EarTrumpet.exe"]),
    SettingSpec("profile_switch_delay_ms", "ProfileSwitchDelayMs", int, lambda: 350),

    # Power Saving tab
    SettingSpec("enable_power_saving_limits", "EnablePowerSavingLimits", bool, lambda: True),
    SettingSpec("sync_windows_energy_saver", "SyncWindowsEnergySaver", bool, lambda: True),
    SettingSpec("power_saving_manual_state", "PowerSavingManualState", bool, lambda: False),
    SettingSpec("power_saving_limits", "PowerSavingLimits", dict, dict),
]

_SPECS_BY_NAME: Dict[str, SettingSpec] = {spec.name: spec for spec in _SPECS}
# Alias for backwards compatibility
if "tray_icon_name" in _SPECS_BY_NAME:
    _SPECS_BY_NAME["tray_icon"] = _SPECS_BY_NAME["tray_icon_name"]
_SPECS_BY_REG_NAME: Dict[str, SettingSpec] = {spec.reg_name: spec for spec in _SPECS}


# MARK: SettingsManager
class SettingsManager(QObject):
    """
    Centralized, reactive configuration manager for MoniTune.

    Features:
    - In-memory cache for ultra-fast reads.
    - Synchronized persistence to Windows Registry (backward compatible).
    - Qt Signal emission on setting change (`setting_changed(name, value)`).
    - Key-specific observer subscriptions (`subscribe(name, callback)`).
    - Pythonic property-like access (`settings.show_resolution = True`).
    - Reset to defaults and bulk update support.
    """

    setting_changed = Signal(str, object)
    settings_reset = Signal()

    def __init__(self, reg_path: Optional[str] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._reg_path = reg_path or cfg.REGISTRY_PATH
        self._cache: Dict[str, Any] = {}
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._load_all()

    # MARK: Internal I/O
    def _read_spec_from_registry(self, spec: SettingSpec) -> Any:
        default_val = spec.default_factory()

        if spec.custom_read is not None:
            return spec.custom_read(self._reg_path)

        if spec.val_type is bool:
            return reg_read_bool(self._reg_path, spec.reg_name, default_val)
        elif spec.val_type is int:
            return reg_read_int(self._reg_path, spec.reg_name, default_val)
        elif spec.val_type is list:
            val = reg_read_list(self._reg_path, spec.reg_name, default=default_val)
            return val if val is not None else default_val
        elif spec.val_type is dict:
            val = reg_read_dict(self._reg_path, spec.reg_name)
            return val if val else default_val
        elif spec.val_type is str:
            return reg_read_str(self._reg_path, spec.reg_name, default_val)
        return default_val

    def _write_spec_to_registry(self, spec: SettingSpec, value: Any) -> None:
        if spec.custom_write is not None:
            spec.custom_write(self._reg_path, value)
            return

        if spec.val_type is bool:
            reg_write_bool(self._reg_path, spec.reg_name, bool(value))
        elif spec.val_type is int:
            reg_write_int(self._reg_path, spec.reg_name, int(value))
        elif spec.val_type is list:
            reg_write_list(self._reg_path, spec.reg_name, list(value))
        elif spec.val_type is dict:
            reg_write_dict(self._reg_path, spec.reg_name, dict(value))
        elif spec.val_type is str:
            reg_write_str(self._reg_path, spec.reg_name, str(value))

    def _load_all(self) -> None:
        """Load all configured settings from registry into cache."""
        for spec in _SPECS:
            try:
                self._cache[spec.name] = self._read_spec_from_registry(spec)
            except Exception as e:
                logger.error(f"Error loading setting {spec.name} from registry: {e}")
                self._cache[spec.name] = spec.default_factory()

    # MARK: Public Accessors
    def get(self, name: str, default: Any = None) -> Any:
        """Get setting value by its Pythonic attribute name."""
        if name in self._cache:
            return self._cache[name]
        if name in _SPECS_BY_REG_NAME:
            return self.get_by_reg_name(name, default)
        return default

    def get_by_reg_name(self, reg_name: str, default: Any = None) -> Any:
        """Get setting value using its Windows Registry key name."""
        spec = _SPECS_BY_REG_NAME.get(reg_name)
        if spec:
            return self._cache.get(spec.name, default)
        return default

    def set(self, name: str, value: Any, save: bool = True, force: bool = False) -> None:
        """
        Update setting value, persist to registry, and notify subscribers.

        Args:
            name: Setting name (either Python attribute name or Registry key name).
            value: The new value.
            save: Whether to persist immediately to registry (defaults to True).
            force: Persist and notify even if value equals old_value (useful for mutated dicts).
        """
        spec = _SPECS_BY_NAME.get(name) or _SPECS_BY_REG_NAME.get(name)
        if not spec:
            raise KeyError(f"Unknown setting '{name}'")

        old_value = self._cache.get(spec.name)
        if not force and old_value == value:
            return

        # Store in cache
        self._cache[spec.name] = value

        # Persist to registry
        if save:
            try:
                self._write_spec_to_registry(spec, value)
            except Exception as e:
                logger.error(f"Failed to persist setting '{spec.name}' to registry: {e}")

        # Emit Qt signal
        self.setting_changed.emit(spec.name, value)

        # Notify key-specific subscribers
        if spec.name in self._subscribers:
            for callback in list(self._subscribers[spec.name]):
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in subscriber callback for '{spec.name}': {e}", exc_info=True)

    def set_by_reg_name(self, reg_name: str, value: Any, save: bool = True) -> None:
        """Convenience method to set a setting using its Registry name."""
        spec = _SPECS_BY_REG_NAME.get(reg_name)
        if not spec:
            raise KeyError(f"Unknown registry setting name '{reg_name}'")
        self.set(spec.name, value, save=save)

    def save(self, name: str) -> None:
        """
        Explicitly persist current in-memory value of a setting to registry.
        Useful when modifying mutable objects (e.g. dicts) in-place.
        """
        spec = _SPECS_BY_NAME.get(name) or _SPECS_BY_REG_NAME.get(name)
        if not spec:
            raise KeyError(f"Unknown setting '{name}'")
        try:
            self._write_spec_to_registry(spec, self._cache.get(spec.name))
        except Exception as e:
            logger.error(f"Failed to persist setting '{spec.name}' to registry: {e}")

    # MARK: Subscriptions
    def subscribe(self, name: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        """
        Subscribe a callback to changes of a specific setting.
        Returns an unsubscribe callable.
        """
        spec = _SPECS_BY_NAME.get(name) or _SPECS_BY_REG_NAME.get(name)
        setting_key = spec.name if spec else name

        if setting_key not in self._subscribers:
            self._subscribers[setting_key] = []
        self._subscribers[setting_key].append(callback)

        def unsubscribe() -> None:
            if setting_key in self._subscribers and callback in self._subscribers[setting_key]:
                self._subscribers[setting_key].remove(callback)

        return unsubscribe

    # MARK: Utilities
    def reload(self) -> None:
        """Re-read all values from registry and refresh in-memory cache."""
        self._load_all()

    def reset_to_defaults(self) -> None:
        """Clear registry storage and reset all settings to defaults."""
        try:
            delete_reg_key(self._reg_path)
            logger.info("Registry settings deleted.")
        except Exception as e:
            logger.error(f"Error clearing registry settings: {e}")

        for spec in _SPECS:
            default_val = spec.default_factory()
            self._cache[spec.name] = default_val
            self.setting_changed.emit(spec.name, default_val)

        self.settings_reset.emit()

    def to_dict(self) -> Dict[str, Any]:
        """Return deep copy of current settings as a dict."""
        return copy.deepcopy(self._cache)

    # MARK: Attribute Access Magic
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or name == "staticMetaObject":
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in self._cache:
            return self._cache[name]
        if name in _SPECS_BY_NAME:
            return _SPECS_BY_NAME[name].default_factory()
        raise AttributeError(f"Setting '{name}' not found in {type(self).__name__}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in ("staticMetaObject",):
            super().__setattr__(name, value)
            return
        if name in _SPECS_BY_NAME:
            self.set(name, value)
        else:
            super().__setattr__(name, value)


# MARK: Singleton Accessor
_GLOBAL_SETTINGS: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Access the global SettingsManager singleton instance."""
    global _GLOBAL_SETTINGS
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = SettingsManager()
    return _GLOBAL_SETTINGS
