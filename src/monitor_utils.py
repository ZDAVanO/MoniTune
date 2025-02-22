import win32api, win32con

import time
import threading

import ctypes
from ctypes import wintypes

import screen_brightness_control as sbc


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
                "RefreshRate": devmode.DisplayFrequency,
                "AvailableRefreshRates": available_refresh_rates,
                "Resolution": f"{devmode.PelsWidth}x{devmode.PelsHeight}",
                "AvailableResolutions": available_resolutions
            })
        return True

    # Define the callback type
    MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

    # Load the function from user32.dll
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    enum_display_monitors = user32.EnumDisplayMonitors
    enum_display_monitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), MonitorEnumProc, wintypes.LPARAM]
    enum_display_monitors.restype = wintypes.BOOL

    # Call EnumDisplayMonitors
    enum_display_monitors(None, None, MonitorEnumProc(monitor_enum_proc), 0)

    sbc_info = sbc.list_monitors_info()
    for index, monitor in enumerate(monitors):
        monitor["name"] = sbc_info[index]["name"]
        monitor["model"] = sbc_info[index]["model"]
        monitor["serial"] = sbc_info[index]["serial"]
        monitor["manufacturer"] = sbc_info[index]["manufacturer"]
        monitor["manufacturer_id"] = sbc_info[index]["manufacturer_id"]

        if monitor["manufacturer"] is None:
            monitor["display_name"] = f"DISPLAY{index + 1}"
        else:
            monitor["display_name"] = f"{monitor['manufacturer']} ({index + 1})"

    # for monitor in monitors:
    #     print(monitor)
    # print("get_monitors_info()")

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
def set_refresh_rate_br(monitor, refresh_rate, refresh=False):
    
    brightness_before = sbc.get_brightness(display=monitor["name"])
    # print(f"Current brightness of {monitor['name']}: {brightness_before}")

    set_refresh_rate(monitor, refresh_rate)

    # Refresh the icon menu
    if refresh:
        pass
        # icon.menu = pystray.Menu(*create_menu(get_monitors_info()))

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







def set_brightness(monitor_serial, br_value):
        # monitor_serial = get_monitors_info()[monitor_index]['serial']
        sbc.set_brightness(int(br_value), display=monitor_serial)









# MARK: set_resolution()
def set_resolution(device, width, height):
    devmode = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS)
    devmode.PelsWidth = width
    devmode.PelsHeight = height
    devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT

    result = win32api.ChangeDisplaySettingsEx(device, devmode)
    if result != win32con.DISP_CHANGE_SUCCESSFUL:
        raise Exception(f"Failed to change resolution to {width}x{height} for device {device}")







# MARK: main
if __name__ == "__main__":

    monitors_info = get_monitors_info()

    for monitor in monitors_info:
        print(monitor)


    # if monitors_info:
    #     first_monitor = monitors_info[0]
    #     device = first_monitor["Device"]
    #     set_resolution(device, 1920, 1080)
