from unittest.mock import patch, MagicMock
from utils.power_detect import is_energy_saver_active


def test_energy_saver_active_from_registry():
    """Verify that EnergySaverState == 1 in registry returns True."""
    with patch("winreg.OpenKey"), patch("winreg.QueryValueEx", return_value=(1, 4)):
        assert is_energy_saver_active() is True


def test_energy_saver_inactive_when_all_zero():
    """Verify returns False when registry is 0 and Win32 status flag is 0."""
    with patch("winreg.OpenKey"), patch("winreg.QueryValueEx", return_value=(0, 4)):
        with patch("utils.power_detect.kernel32.GetSystemPowerStatus") as mock_status:
            # Fake SYSTEM_POWER_STATUS with SystemStatusFlag = 0
            mock_status.side_effect = lambda ptr: setattr(ptr._obj, "SystemStatusFlag", 0) or 1
            assert is_energy_saver_active() is False


def test_energy_saver_active_from_battery_saver_flag():
    """Verify returns True if registry key missing, but SystemStatusFlag == 1."""
    with patch("winreg.OpenKey", side_effect=FileNotFoundError):
        with patch("utils.power_detect.kernel32.GetSystemPowerStatus") as mock_status:
            mock_status.side_effect = lambda ptr: setattr(ptr._obj, "SystemStatusFlag", 1) or 1
            assert is_energy_saver_active() is True


def test_energy_saver_inactive_on_exception():
    """Verify returns False gracefully when both checks raise exceptions."""
    with patch("winreg.OpenKey", side_effect=Exception("Reg failure")):
        with patch("utils.power_detect.kernel32.GetSystemPowerStatus", side_effect=Exception("Win32 failure")):
            assert is_energy_saver_active() is False
