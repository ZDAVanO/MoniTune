from unittest.mock import patch, MagicMock
from services.settings_manager import SettingsManager


def test_settings_manager_defaults(qapp):
    """Verify that SettingsManager initializes with defaults when registry is empty."""
    with patch("services.settings_manager.reg_read_bool", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_int", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_dict", return_value={}), \
         patch("services.settings_manager.reg_read_list", return_value=[]), \
         patch("services.settings_manager.reg_read_str", side_effect=lambda path, name, default: default):
        
        settings = SettingsManager(reg_path=r"Software\TestMoniTune")
        
        assert settings.enable_power_saving_limits is True
        assert settings.sync_windows_energy_saver is True
        assert settings.power_saving_mode == "windows"
        assert settings.power_saving_manual_state is False
        assert settings.power_saving_limits == {}
        assert settings.brightness_values == {}
        assert settings.popup_position == "bottom_right"
        assert settings.profile_switch_delay_ms == 350


def test_settings_manager_set_and_signal(qapp):
    """Verify that changing a setting updates cache and emits setting_changed signal."""
    with patch("services.settings_manager.reg_read_bool", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_int", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_dict", return_value={}), \
         patch("services.settings_manager.reg_read_list", return_value=[]), \
         patch("services.settings_manager.reg_read_str", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_write_str") as mock_write_str:

        settings = SettingsManager(reg_path=r"Software\TestMoniTune")

        received_signals = []
        settings.setting_changed.connect(lambda name, val: received_signals.append((name, val)))

        settings.power_saving_mode = "manual"

        assert settings.power_saving_mode == "manual"
        mock_write_str.assert_called_once_with(r"Software\TestMoniTune", "PowerSavingMode", "manual")
        assert received_signals == [("power_saving_mode", "manual")]


def test_settings_manager_subscribe(qapp):
    """Verify observer subscription and unsubscription."""
    with patch("services.settings_manager.reg_read_bool", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_int", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_dict", return_value={}), \
         patch("services.settings_manager.reg_read_list", return_value=[]), \
         patch("services.settings_manager.reg_read_str", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_write_bool"):

        settings = SettingsManager(reg_path=r"Software\TestMoniTune")

        observed_values = []
        unsubscribe = settings.subscribe("power_saving_manual_state", lambda val: observed_values.append(val))

        settings.power_saving_manual_state = True
        assert observed_values == [True]

        unsubscribe()
        settings.power_saving_manual_state = False
        assert observed_values == [True]  # Did not receive False after unsubscribing


def test_settings_manager_ignored_processes(qapp):
    """Verify that ignored_processes defaults and updates correctly."""
    with patch("services.settings_manager.reg_read_bool", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_int", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_read_dict", return_value={}), \
         patch("services.settings_manager.reg_read_list", side_effect=lambda path, name, default=None: default if default is not None else []), \
         patch("services.settings_manager.reg_read_str", side_effect=lambda path, name, default: default), \
         patch("services.settings_manager.reg_write_list") as mock_write_list:

        settings = SettingsManager(reg_path=r"Software\TestMoniTune")
        assert settings.ignored_processes == ["EarTrumpet.exe"]

        settings.ignored_processes = ["EarTrumpet.exe", "overlay.exe"]
        mock_write_list.assert_called_once_with(
            r"Software\TestMoniTune", "IgnoredProcesses", ["EarTrumpet.exe", "overlay.exe"]
        )
        assert settings.ignored_processes == ["EarTrumpet.exe", "overlay.exe"]

