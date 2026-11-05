import ctypes
import winreg
import win32api
import win32event
import time
from utils.logger import get_logger

logger = get_logger(__name__)

kernel32 = ctypes.windll.kernel32


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_byte),
        ('BatteryFlag', ctypes.c_byte),
        ('BatteryLifePercent', ctypes.c_byte),
        ('SystemStatusFlag', ctypes.c_byte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong),
    ]


def is_energy_saver_active() -> bool:
    """
    Returns True if Windows 10/11 Energy Saver / Battery Saver is currently active.
    Works for both AC and DC on Windows 11 as well as battery saver on laptops.
    """
    # 1. Check Windows 11 EnergySaverState in registry (works on AC and DC)
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power") as key:
            val, _ = winreg.QueryValueEx(key, "EnergySaverState")
            if val == 1:
                return True
    except Exception:
        pass

    # 2. Check Win32 GetSystemPowerStatus (standard battery saver on DC)
    try:
        status = SYSTEM_POWER_STATUS()
        if kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            if status.SystemStatusFlag == 1:
                return True
    except Exception:
        pass

    return False


class PowerDetect:
    """
    Background listener that continuously monitors Energy Saver changes:
    - Uses RegNotifyChangeKeyValue on the Power registry key to detect changes instantly.
    - Re-registers only upon event signal to avoid kernel registration accumulation.
    - Calls callback(is_active: bool) whenever the state changes.
    """
    def __init__(self, callback):
        self.callback = callback
        self._last_state = is_energy_saver_active()
        self._running = True

    def run(self):
        reg_key = None
        event = None
        registered = False
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power")
            event = win32event.CreateEvent(None, 0, 0, None)
        except Exception as e:
            logger.debug(f"Could not initialize registry notification for power: {e}")

        while self._running:
            try:
                if reg_key and event:
                    if not registered:
                        win32api.RegNotifyChangeKeyValue(
                            reg_key, False, win32api.REG_NOTIFY_CHANGE_LAST_SET, event, True
                        )
                        registered = True

                    wait_res = win32event.WaitForSingleObject(event, 1000)
                    if wait_res == win32event.WAIT_OBJECT_0:
                        registered = False  # Re-arm on next loop
                else:
                    time.sleep(1.0)

                current_state = is_energy_saver_active()
                if current_state != self._last_state:
                    self._last_state = current_state
                    logger.info(f"Energy Saver state changed to: {current_state}")
                    try:
                        self.callback(current_state)
                    except Exception as cb_err:
                        logger.error(f"Error in PowerDetect callback: {cb_err}")
            except Exception as e:
                logger.error(f"Error in PowerDetect watcher loop: {e}")
                registered = False
                time.sleep(1.0)

        if event:
            try:
                win32api.CloseHandle(event)
            except Exception:
                pass
        if reg_key:
            try:
                winreg.CloseKey(reg_key)
            except Exception:
                pass

    def stop(self):
        self._running = False
