import win32api, win32con
import ctypes
from ctypes import wintypes
import time
import threading

import screen_brightness_control as sbc

from monitorcontrol import get_monitors, VCPError



VCP_CONTRAST_CODE = 0x12
PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128



# MARK: get_available_refresh_rates()
def get_available_refresh_rates(device):
    refresh_rates = set()
    i = 0
    while True:
        try:
            devmode = win32api.EnumDisplaySettings(device, i)
            refresh_rates.add(devmode.DisplayFrequency)
            i += 1
        except Exception:
            break
    return sorted(refresh_rates)



# MARK: get_available_resolutions()
def get_available_resolutions(device):
    resolutions = set()
    i = 0
    while True:
        try:
            devmode = win32api.EnumDisplaySettings(device, i)
            if devmode.PelsWidth >= 800 and devmode.PelsHeight >= 600:
                resolutions.add((devmode.PelsWidth, devmode.PelsHeight))
            i += 1
        except Exception:
            break
    return sorted(resolutions)



class _PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [('hPhysicalMonitor', wintypes.HANDLE), 
                ('szPhysicalMonitorDescription', 
                           wintypes.WCHAR * PHYSICAL_MONITOR_DESCRIPTION_SIZE)]
    
# MARK: get_monitors_info()
def get_monitors_info():

    monitors = []

    # Callback function for EnumDisplayMonitors
    def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
        monitor_info = win32api.GetMonitorInfo(hMonitor)
        device = monitor_info.get('Device', None)

        if device:
            devmode = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS)
            available_refresh_rates = get_available_refresh_rates(device)
            available_resolutions = get_available_resolutions(device)
            monitors.append({
                "Device": device,
                "hMonitor": hMonitor,
                "RefreshRate": devmode.DisplayFrequency,
                "AvailableRefreshRates": available_refresh_rates,
                "Resolution": f"{devmode.PelsWidth}x{devmode.PelsHeight}",
                "AvailableResolutions": available_resolutions
            })
        return True

    # Define the callback type
    MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, 
                                         wintypes.HMONITOR, 
                                         wintypes.HDC, 
                                         ctypes.POINTER(wintypes.RECT), 
                                         wintypes.LPARAM)

    # Load the function from user32.dll
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    enum_display_monitors = user32.EnumDisplayMonitors
    enum_display_monitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), MonitorEnumProc, wintypes.LPARAM]
    enum_display_monitors.restype = wintypes.BOOL

    # Call EnumDisplayMonitors
    enum_display_monitors(None, None, MonitorEnumProc(monitor_enum_proc), 0)

    sbc_info = sbc.list_monitors_info()
    monitorcontrol_monitors = get_monitors()
    for index, monitor in enumerate(monitors):
        monitor["index"] = index
        monitor["name"] = sbc_info[index]["name"]
        monitor["model"] = sbc_info[index]["model"]
        monitor["serial"] = sbc_info[index]["serial"]
        monitor["manufacturer"] = sbc_info[index]["manufacturer"]
        monitor["manufacturer_id"] = sbc_info[index]["manufacturer_id"]

        if sbc_info[index]["method"] == sbc.windows.WMI:
            monitor["method"] = "WMI"
        elif sbc_info[index]["method"] == sbc.windows.VCP:
            monitor["method"] = "VCP"
        else:
            monitor["method"] = sbc_info[index]["method"]
        
        if monitor["manufacturer"] is None:
            monitor["display_name"] = f"DISPLAY{index + 1}"
        else:
            monitor["display_name"] = f"{monitor['manufacturer']} ({index + 1})"
        
        monitor_number = wintypes.DWORD()
        if not ctypes.windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(
                                         monitor["hMonitor"], ctypes.byref(monitor_number)):
            raise ctypes.WinError()
        physical_monitor_array = (_PHYSICAL_MONITOR * monitor_number.value)()
        if not ctypes.windll.dxva2.GetPhysicalMonitorsFromHMONITOR(
                               monitor["hMonitor"], monitor_number, physical_monitor_array):
            raise ctypes.WinError()
        for physical_monitor in physical_monitor_array:
            monitor["hPhysicalMonitor"] = physical_monitor.hPhysicalMonitor

        monitor["mc_obj"] = monitorcontrol_monitors[index]

    return monitors



# MARK: set_refresh_rate()
def set_refresh_rate(monitor, refresh_rate):

    # if refresh_rate == monitor["RefreshRate"]:
    #     print(f"Monitor {monitor['Device']} is already set to {refresh_rate} Hz.")
    #     return

    device = monitor["Device"]

    devmode = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS)
    devmode.DisplayFrequency = refresh_rate
    result = win32api.ChangeDisplaySettingsEx(device, devmode)

    if result == win32con.DISP_CHANGE_SUCCESSFUL:
        print(f"Successfully changed the refresh rate of {device} to {refresh_rate} Hz.")
    else:
        print(f"Failed to change the refresh rate of {device}.")



# MARK: set_refresh_rate_br()
def set_refresh_rate_br(monitor, refresh_rate):
    # Refresh monitor data
    monitors_info = get_monitors_info()
    monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

    updated_monitor = monitors_dict.get(monitor['serial'], None)
    if not updated_monitor:
        print(f"Monitor {monitor['Device']} not found")
        return
    
    if updated_monitor and updated_monitor["RefreshRate"] == refresh_rate:
        print(f"Monitor {monitor['Device']} is already set to {refresh_rate} Hz.")
        return

    brightness_before = sbc.get_brightness(display=monitor["name"])
    # print(f"Current brightness of {monitor['name']}: {brightness_before}")

    set_refresh_rate(monitor, refresh_rate)

    # Restore brightness in a separate thread
    def restore_brightness():
        time.sleep(5)
        brightness_after = sbc.get_brightness(display=monitor["name"])
        if brightness_after != brightness_before:
            sbc.set_brightness(*brightness_before, display=monitor["name"])
            print(f"Restored brightness of {monitor['name']} from {brightness_after} to {brightness_before}")
        else:
            print(f"Did not need to restore brightness of {monitor['name']}")

    threading.Thread(target=restore_brightness).start()



# MARK: set_brightness()
def set_brightness(monitor_serial, br_value):
        # monitor_serial = get_monitors_info()[monitor_index]['serial']
        sbc.set_brightness(int(br_value), display=monitor_serial)


# MARK: get_brightness()
def get_brightness(display):
    return sbc.get_brightness(display=display)



# MARK: set_resolution()
def set_resolution(device, width, height):
    devmode = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS)
    devmode.PelsWidth = width
    devmode.PelsHeight = height
    devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT

    result = win32api.ChangeDisplaySettingsEx(device, devmode)
    if result != win32con.DISP_CHANGE_SUCCESSFUL:
        raise Exception(f"Failed to change resolution to {width}x{height} for device {device}")



def get_vcf_feature_and_vcf_feature_reply(handle, code):
        """Get current and maximun values for continuous VCP codes"""
        current_value = wintypes.DWORD()
        maximum_value = wintypes.DWORD()
        if not ctypes.windll.dxva2.GetVCPFeatureAndVCPFeatureReply(
                                       handle, wintypes.BYTE(code), None, 
                                       ctypes.byref(current_value), 
                                       ctypes.byref(maximum_value)):
            raise ctypes.WinError()
        return current_value.value, maximum_value.value

def set_vcp_feature(handle, code, value):
        """Set 'code' to 'value'"""
        if not ctypes.windll.dxva2.SetVCPFeature(handle, 
                                    wintypes.BYTE(code), wintypes.DWORD(value)):
            raise ctypes.WinError()
        

def get_contrast_vcp(handle):
    try:
        return get_vcf_feature_and_vcf_feature_reply(handle, VCP_CONTRAST_CODE)[0]
    except Exception as e:
        print(f"Failed to get contrast: {e}")
        return None

def set_contrast_vcp(handle, value):
        # current, max = get_vcf_feature_and_vcf_feature_reply(handle, VCP_CONTRAST_CODE)
        # if value == current:
        #     return
        # if value > max:
        #     value = max
        # elif value < 0:
        #     value = 0

        if value > 100:
            value = 100
        elif value < 0:
            value = 0

        set_vcp_feature(handle, VCP_CONTRAST_CODE, value)

def set_contrast_s(serial, contrast_value):
    monitors_info = get_monitors_info()
    for monitor in monitors_info:
        if monitor["serial"] == serial:
            set_contrast_vcp(monitor["hPhysicalMonitor"], contrast_value)
            return
    print(f"set_contrast_s: Monitor with serial '{serial}' not found")



# MARK: print_mi()
def print_mi(monitors_info):
    print("Monitors Info:")
    for monitor in monitors_info:
        print(f"    Display: {monitor['display_name']} ({monitor['serial']})")
        for key, value in monitor.items():
            print(f"        {key}: {value}")



# MARK: main
if __name__ == "__main__":

    start_time = time.time()

    # monitors_info = get_monitors_info()
    # print_mi(monitors_info)

    # sbc_info = sbc.list_monitors_info()
    # print(f"sbc_info: {sbc_info}")

    # mc_monitors = get_monitors()
    # print(f"mc_monitors: {mc_monitors}")


    # with mc_monitors[1]:
    #     try:
    #         print(f"contrast: {mc_monitors[1].get_contrast()}")
    #     except VCPError as e:
    #         print(f"Failed to get contrast for monitor: {e}")
    
    
    # print(get_contrast_vcp(monitors_info[1]["hPhysicalMonitor"]))
    # set_contrast_vcp(monitors_info[1]["hPhysicalMonitor"], 100)

    # for monitor in monitors_info:
    #     if monitor['method'] == sbc.windows.WMI:
    #         print(f"Monitor {monitor['name']} використовує WMI для управління яскравістю.")
    #     elif monitor['method'] == sbc.windows.VCP:
    #         print(f"Monitor {monitor['name']} використовує VCP для управління яскравістю.")

    # set_contrast_s("H4TN602437", 34)




    end_time = time.time()
    print(f"Execution time for get_monitors_info(): {end_time - start_time:.2f} seconds")

    # print_mi(monitors_info)

