import ctypes
import psutil
import subprocess
import re

import time

import logging
logger = logging.getLogger(__name__)



class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_time():
    """Returns the time (in seconds) during which the PC has been idle."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        current_time = ctypes.windll.kernel32.GetTickCount()  # Time in milliseconds
        idle_time = (current_time - lii.dwTime) / 1000.0  # Convert to seconds
        return idle_time
    else:
        return -1  # Error retrieving data


def is_laptop():
    battery = psutil.sensors_battery()
    return battery is not None


def is_on_battery():
    battery = psutil.sensors_battery()
    if (battery is not None) and (not battery.power_plugged):
        return True
    return False


def get_display_timeouts():
    result = subprocess.run(['powercfg', '/query'], capture_output=True, text=True)
    output = result.stdout
    logger.debug(f"Powercfg output:\n {output}")

    # Find the block responsible for Display -> Turn off display after
    pattern = re.compile(
        r"Subgroup GUID: 7516b95f-f776-4464-8c53-06167f40cc99.*?"
        r"Power Setting GUID: 3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e.*?"
        r"Current AC Power Setting Index: 0x([0-9a-fA-F]+).*?"
        r"Current DC Power Setting Index: 0x([0-9a-fA-F]+)",
        re.DOTALL
    )

    display_timeout_ac = 0
    display_timeout_dc = 0

    match = pattern.search(output)
    if match:
        ac_hex = match.group(1)
        dc_hex = match.group(2)

        # Convert from hex to seconds
        display_timeout_ac = int(ac_hex, 16)
        display_timeout_dc = int(dc_hex, 16)

    return display_timeout_ac, display_timeout_dc



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")

    print("is_laptop:", is_laptop())
    print("is_on_battery:", is_on_battery())

    display_timeout_ac, display_timeout_dc = get_display_timeouts()
    print(f"Display Timeout on AC Power: {display_timeout_ac} seconds")
    print(f"Display Timeout on DC Power: {display_timeout_dc} seconds")

    while True:
        idle_seconds = get_idle_time()
        print(f"The computer has been idle for {idle_seconds:.2f} seconds")
        time.sleep(1)


