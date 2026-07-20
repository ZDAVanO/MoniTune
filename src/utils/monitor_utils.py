import ctypes
import logging
import threading
import time

from ctypes import wintypes

import screen_brightness_control as sbc
import win32api, win32con

logger = logging.getLogger(__name__)



VCP_CODES = {
    # 0-100, called 'brightness' on the OSD
    "Luminance": 0x10,

    # 0-100
    "Contrast": 0x12,
    
    # 0x01: power on, 0x04: standby (screenoff + blinking led), 0x05: power off
    "Power Mode": 0xD6,
}

METHOD_MAP = {
    sbc.windows.WMI: "WMI",
    sbc.windows.VCP: "VCP",
}

ORIENTATION = {
    'landscape': 0,
    'portrait': 1,
    'landscape_flipped': 2,
    'portrait_flipped': 3,
}

PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128

class _PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [('hPhysicalMonitor', wintypes.HANDLE),
                ('szPhysicalMonitorDescription',
                           wintypes.WCHAR * PHYSICAL_MONITOR_DESCRIPTION_SIZE)]


# MARK: Monitor
class Monitor:
    def __init__(self, index, hMonitor, sbc_monitor_info):
        self.index = index

        win_monitor_info = win32api.GetMonitorInfo(hMonitor)
        self.device_name = win_monitor_info.get("Device", None)

        self.hMonitor = hMonitor
        self.hPhysicalMonitor = self._get_physical_monitor_handle()

        devmode = win32api.EnumDisplaySettings(self.device_name,
                                               win32con.ENUM_CURRENT_SETTINGS)
        
        self.resolution = (devmode.PelsWidth, devmode.PelsHeight)
        self.refresh_rate = devmode.DisplayFrequency
        self.available_resolutions, self.available_refresh_rates = self._get_available_resolutions_and_refresh_rates()

        self.name = sbc_monitor_info["name"]
        self.model = sbc_monitor_info["model"]

        self.serial = sbc_monitor_info["serial"] or self.index
        if not sbc_monitor_info["serial"]:
            logger.warning(f"Monitor {self.index} does not have a serial number, using index as serial")
        
        self.manufacturer = sbc_monitor_info["manufacturer"]
        self.manufacturer_id = sbc_monitor_info["manufacturer_id"]

        self.method = METHOD_MAP.get(sbc_monitor_info["method"], 
                                     sbc_monitor_info["method"]) # "VCP", "WMI"

        self.display_name = f"DISPLAY {self.index + 1}"
        if self.manufacturer:
            self.display_name = f"{self.manufacturer} ({self.index + 1})"

        logger.debug(
            f"Monitor init: "
            f"index={self.index}, "
            f"device_name='{self.device_name}', "

            f"hMonitor={self.hMonitor}, "
            f"hPhysicalMonitor={self.hPhysicalMonitor}, "

            f"resolution={self.resolution}, "
            f"available_resolutions={self.available_resolutions}, "
            f"refresh_rate={self.refresh_rate}, "
            f"available_refresh_rates={self.available_refresh_rates}, "

            f"name='{self.name}', "
            f"model='{self.model}', "
            f"serial='{self.serial}', "
            f"manufacturer='{self.manufacturer}', "
            f"manufacturer_id='{self.manufacturer_id}', "
            f"method='{self.method}', "
            
            f"display_name='{self.display_name}'"
        )


    # MARK: __repr__()
    def __repr__(self):
        return (
            f"<Monitor(name='{self.display_name}', "
            f"serial='{self.serial}', "
            f"method='{self.method}', "
            f"hpm={self.hPhysicalMonitor})>"
        )

    # MARK: _get_physical_monitor_handle()
    def _get_physical_monitor_handle(self):
        try:
            # start_time = time.time()
            monitor_number = wintypes.DWORD()
            if not ctypes.windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(
                int(self.hMonitor), ctypes.byref(monitor_number)
            ):
                return None

            physical_monitor_array = (_PHYSICAL_MONITOR * monitor_number.value)()
            if not ctypes.windll.dxva2.GetPhysicalMonitorsFromHMONITOR(
                int(self.hMonitor), monitor_number, physical_monitor_array
            ):
                return None

            # logger.info(f"_get_physical_monitor_handle took {time.time() - start_time:.4f} seconds for hMonitor {self.hMonitor}")
            return physical_monitor_array[0].hPhysicalMonitor  # Return first handle
        except Exception:
            return None

    # MARK: _get_available_resolutions_and_refresh_rates()
    def _get_available_resolutions_and_refresh_rates(self):
        # start_time = time.time()
        resolutions = set()
        refresh_rates = set()
        i = 0
        while True:
            try:
                devmode = win32api.EnumDisplaySettings(self.device_name, i)
                if devmode.PelsWidth >= 800 and devmode.PelsHeight >= 600:
                    resolutions.add((devmode.PelsWidth, devmode.PelsHeight))
                refresh_rates.add(devmode.DisplayFrequency)
                i += 1
            except win32api.error:
                break
        # logger.info(f"_get_available_resolutions_and_refresh_rates took {time.time() - start_time:.4f} seconds for device {self.device_name}")
        return sorted(resolutions, reverse=True), sorted(refresh_rates)

    # MARK: _get_vcp_feature_retry()
    def _get_vcp_feature_retry(self, code, retries=1, delay=0.05):
        for attempt in range(retries):
            try:
                current_value = wintypes.DWORD()
                maximum_value = wintypes.DWORD()
                if not ctypes.windll.dxva2.GetVCPFeatureAndVCPFeatureReply(
                    self.hPhysicalMonitor, 
                    wintypes.BYTE(code), 
                    None,
                    ctypes.byref(current_value), 
                    ctypes.byref(maximum_value)
                ):
                    raise ctypes.WinError()
                return current_value.value
            except Exception as e:
                logger.info(f"Attempt {attempt + 1} failed to get VCP feature {hex(code)}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to get VCP feature {hex(code)} after {retries} attempts.")
                    return None
                time.sleep(delay)

    # MARK: _set_vcp_feature_retry()
    def _set_vcp_feature_retry(self, code, value, retries=1, delay=0.05):
        for attempt in range(retries):
            try:
                if not ctypes.windll.dxva2.SetVCPFeature(
                    self.hPhysicalMonitor, wintypes.BYTE(code), wintypes.DWORD(value)
                ):
                    raise ctypes.WinError()
                return True
            except Exception as e:
                logger.info(f"Attempt {attempt + 1} failed to set VCP feature {hex(code)}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to set VCP feature {hex(code)} after {retries} attempts.")
                    return False
                time.sleep(delay)


    # MARK: get_brightness()
    def get_brightness(self, retries=1):
        logger.debug(f"Getting brightness for {self}")
        if self.method == "VCP":
            return self._get_vcp_feature_retry(VCP_CODES["Luminance"], retries=retries)
        elif self.method == "WMI":
            try:
                # sbc.get_brightness returns a list, take the first element
                # return sbc.get_brightness(display=self.index)[0] # Using index for WMI
                return sbc.get_brightness(display=self.serial)[0]
            except Exception as e:
                logger.warning(f"Failed to get brightness for display {self.serial} (index {self.index}): {e}")
                return None
        logger.warning(f"Unknown method {self.method} for getting brightness of {self}")
        return None

    # MARK: set_brightness()
    def set_brightness(self, value, retries=1):
        logger.debug(f"Setting brightness for {self} to {value}")
        value = int(max(0, min(100, value))) # Ensure value is between 0 and 100
        if self.method == "VCP":
            return self._set_vcp_feature_retry(VCP_CODES["Luminance"], value, retries=retries)
        elif self.method == "WMI":
            try:
                # sbc.set_brightness(value, display=self.index) # Using index for WMI
                sbc.set_brightness(value, display=self.serial)
                return True
            except Exception as e:
                logger.warning(f"Failed to set brightness for display {self} to {value}: {e}")
                return False
        logger.warning(f"Unknown method {self.method} for setting brightness of {self}")
        return False


    # MARK: get_contrast()
    def get_contrast(self, retries=1):
        if self.method == "VCP":
            return self._get_vcp_feature_retry(VCP_CODES["Contrast"], retries=retries)
        logger.debug(f"Contrast not supported via {self.method} for {self}")
        return None

    # MARK: set_contrast()
    def set_contrast(self, value, retries=1):
        value = int(max(0, min(100, value))) # Ensure value is between 0 and 100
        if self.method == "VCP":
            return self._set_vcp_feature_retry(VCP_CODES["Contrast"], value, retries=retries)
        logger.debug(f"Contrast not supported via {self.method} for {self}")
        return False


    # MARK: get_power_mode()
    def get_power_mode(self, retries=1):
        if self.method == "VCP":
            return self._get_vcp_feature_retry(VCP_CODES["Power Mode"], retries=retries)
        logger.debug(f"Power mode not supported via {self.method} for {self}")
        return None

    # MARK: set_power_mode()
    def set_power_mode(self, value, retries=1):
        # 0x01: power on, 0x04: standby, 0x05: power off
        valid_power_modes = [0x01, 0x04, 0x05]
        if value not in valid_power_modes:
            logger.error(f"Invalid power mode value for {self}: {value}. Must be one of {valid_power_modes}.")
            return False
        if self.method == "VCP":
            return self._set_vcp_feature_retry(VCP_CODES["Power Mode"], value, retries=retries)
        logger.debug(f"Power mode not supported via {self.method} for {self}")
        return False


    # MARK: set_resolution()
    def set_resolution(self, width, height):

        if (width, height) not in self.available_resolutions:
            logger.error(f"Resolution {width}x{height} is not supported by {self}")
            return False
        
        logger.info(f"Setting resolution for {self} to {width}x{height}")
        
        devmode = win32api.EnumDisplaySettings(self.device_name, win32con.ENUM_CURRENT_SETTINGS)
        devmode.PelsWidth = width
        devmode.PelsHeight = height
        # devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT # Закоментовано, бо може викликати помилки, якщо інші поля не валідні
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        try:
            # result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode, 0) # Додано 0 як останній аргумент (dwflags)
            # result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode)
            result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode, Flags=win32con.CDS_UPDATEREGISTRY)

            if result == win32con.DISP_CHANGE_SUCCESSFUL:
                logger.info(f"Successfully changed resolution for {self} to {width}x{height}")
                self.resolution = (width, height)
                return True
            else:
                logger.error(f"Failed to change resolution for {self} to {width}x{height}. Result code: {result}")
                return False
        except Exception as e:
            logger.error(f"Exception changing resolution for {self} to {width}x{height}: {e}")
            return False

    # MARK: set_refresh_rate()
    def set_refresh_rate(self, rate):

        if rate not in self.available_refresh_rates:
            logger.error(f"Refresh rate {rate}Hz is not supported by {self}")
            return False
        
        logger.info(f"Setting refresh rate for {self} to {rate}Hz")
        
        devmode = win32api.EnumDisplaySettings(self.device_name, win32con.ENUM_CURRENT_SETTINGS)
        devmode.DisplayFrequency = rate
        # devmode.Fields = win32con.DM_DISPLAYFREQUENCY # Закоментовано
        try:
            # result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode, 0) # Додано 0 як останній аргумент (dwflags)
            # result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode)
            result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode, Flags=win32con.CDS_UPDATEREGISTRY)
            if result == win32con.DISP_CHANGE_SUCCESSFUL:
                logger.info(f"Successfully changed refresh rate for {self} to {rate}Hz")
                self.refresh_rate = rate
                return True
            else:
                logger.error(f"Failed to change refresh rate for {self} to {rate}Hz. Result code: {result}")
                return False
        except Exception as e:
            logger.error(f"Exception changing refresh rate for {self} to {rate}Hz: {e}")
            return False

    # MARK: set_orientation()
    def set_orientation(self, orientation):
        devmode = win32api.EnumDisplaySettings(self.device_name, win32con.ENUM_CURRENT_SETTINGS)

        # Change orientation
        devmode.DisplayOrientation = orientation

        # Swap width and height if orientation is vertical
        if orientation in [1, 3]:
            devmode.PelsWidth, devmode.PelsHeight = devmode.PelsHeight, devmode.PelsWidth

        # Apply changes
        result = win32api.ChangeDisplaySettingsEx(self.device_name, devmode,)

        if result == win32con.DISP_CHANGE_SUCCESSFUL:
            logger.info(f"Successfully changed orientation for {self} to {orientation}")
            return True
        else:
            logger.error(f"Failed to change orientation for {self} to {orientation}. Result code: {result}")
            return False


# MARK: find_sbc_info()
def find_sbc_info(device_id, sbc_monitors):
    """Matches a Win32 monitor DeviceID with screen_brightness_control monitor info."""
    if not device_id:
        return None
    parts = device_id.upper().split('#')
    if len(parts) < 3:
        return None
    instance_id = parts[2] # e.g. '5&19396927&1d&UID256'

    # Try exact match on serial (WMI laptop monitors use instance_id as serial)
    for sbc_item in sbc_monitors:
        sbc_serial = (sbc_item.get('serial') or '').upper()
        if sbc_serial == instance_id:
            return sbc_item

    # Try matching UID
    for sbc_item in sbc_monitors:
        sbc_uid = sbc_item.get('uid')
        if sbc_uid:
            uid_str = f"UID{sbc_uid}".upper()
            if uid_str in instance_id:
                return sbc_item

    return None


# MARK: get_monitors()
def get_monitors():
    """Returns a list of Monitor objects for each detected monitor."""
    start_time = time.time()
    monitors_objects = []

    try:
        sbc_monitors_info = sbc.list_monitors_info()
        logger.debug("sbc_info:\n" + "\n".join(f"{monitor}" for monitor in sbc_monitors_info))

        for index, (hMonitor, hdcMonitor, rect) in enumerate(win32api.EnumDisplayMonitors()):
            try:
                # print(f"Processing monitor {index}: hMonitor={hMonitor}, hdcMonitor={hdcMonitor}, rect={rect}")
                logger.debug(f"Processing monitor {index}: hMonitor={hMonitor}, hdcMonitor={hdcMonitor}, rect={rect}")
                
                # Get the DeviceID
                win_monitor_info = win32api.GetMonitorInfo(hMonitor)
                device_name = win_monitor_info.get("Device", None)
                try:
                    dev = win32api.EnumDisplayDevices(device_name, 0, 1)
                    device_id = dev.DeviceID
                except Exception as e:
                    logger.warning(f"Failed to get DisplayDevices for {device_name}: {e}")
                    device_id = ""

                sbc_match = find_sbc_info(device_id, sbc_monitors_info)
                if sbc_match is None:
                    logger.warning(f"Monitor {device_name} (DeviceID: '{device_id}') has no matching SBC info, skipping.")
                    continue

                monitors_objects.append(Monitor(index, int(hMonitor), sbc_match))
            except Exception as e:
                logger.error(f"Failed to create Monitor object for index {index}: {e}")

    except Exception as e:
        logger.error(f"Error in get_monitors: {e}")

    logger.info(f"get_monitors took {time.time() - start_time:.4f} seconds")
    return monitors_objects


# MARK: get_monitor_device_names()
def get_monitor_device_names():
    """Returns a list of monitor device names (e.g. '\\\\.\\DISPLAY1')."""
    device_names = []
    try:
        monitors_enum = win32api.EnumDisplayMonitors()
        for i, m_info in enumerate(monitors_enum):
            monitor_info = win32api.GetMonitorInfo(m_info[0]) # {'Monitor': (0, 0, 1920, 1080), 'Work': (0, 0, 1920, 1032), 'Flags': 1, 'Device': '\\\\.\\DISPLAY1'}
            device = monitor_info['Device']
            device_names.append(device)
    except Exception as e:
        logger.error(f"Error enumerating display monitors: {e}")
    return device_names



# MARK: main
if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")
    
    print(f"get_monitor_device_names: {get_monitor_device_names()}")

    # sbc_info = sbc.list_monitors_info()
    # print(f"sbc_info: {sbc_info}")

    monitors_info = get_monitors()
    print(f"monitors_info: {monitors_info}")

    print(sbc.list_monitors())

    # get_monitors()
    # get_monitors()
    # get_monitors()

    # set_brightness_sbc(1, 0)

    # print(get_contrast_vcp(monitors_info[1]["hPhysicalMonitor"]))
    # set_contrast_vcp(monitors_info[1]["hPhysicalMonitor"], 100)

    # rotate_display('\\\\.\\DISPLAY2', ORIENTATION['landscape'])

    # for monitor in monitors_info:
    #     if monitor['method'] == "VCP":
    #         while True:
    #             start_time = time.time()

    #             print(f"Monitor {monitor['serial']} - Brightness: {get_brightness_vcp(monitor['hPhysicalMonitor'], retries=5)}")
    #             # print(f"Monitor {monitor['serial']} - Contrast: {get_contrast_vcp(monitor['hPhysicalMonitor'], retries=5)}")
    #             # print(f"Monitor {monitor['serial']} - Power Mode: {get_power_mode_vcp(monitor['hPhysicalMonitor'], retries=5)}")
                
    #             # set_power_mode_vcp(monitor['hPhysicalMonitor'], 4, retries=5)

    #             # set contrast
    #             # set_contrast_vcp(monitor['hPhysicalMonitor'], 75, retries=5)
    #             # print(f"contrast set to 75")
                
    #             # print("trying to set_brightness")
    #             # set_brightness(monitor['serial'], 50)

    #             # print(f"Monitor {monitor['serial']} - Brightness: {sbc.get_brightness(monitor['serial'])}")

                
    #             print(f"Execution time for get_monitors(): {time.time() - start_time:.2f} seconds")
                
    #             # time.sleep(0.2)




