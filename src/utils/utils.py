import ctypes
import psutil
import subprocess
import re

import time

import logging
logger = logging.getLogger(__name__)

import requests
from packaging.version import Version



class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_time():
    """
    Returns:
        float: The time (in seconds) during which the PC has been idle.
               Returns -1 if there is an error retrieving the data.
    """
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
    """
    Returns:
        tuple: (AC timeout, DC timeout) in seconds.
    """

    result = subprocess.run(['powercfg', '/query'], 
                            capture_output=True, 
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)
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


# MARK: check_github_update_available()
def check_github_update_available(repo_api_url: str, current_version: str):
    """
    Checks if a newer version of the software is available on GitHub.

    Args:
        repo_api_url (str): The API URL of the GitHub repository.
        current_version (str): The current version of the software.

    Returns:
        tuple: A tuple containing:
               - bool: True if an update is available, False otherwise.
               - Version or None: The latest version if available, None otherwise.
    """
    try:
        response = requests.get(repo_api_url)
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = Version(latest_release["tag_name"].lstrip("v"))
            current_version = Version(current_version)

            # Compare versions
            if latest_version > current_version:
                logger.info(f"New version available: {latest_version}. Current version: {current_version}.")
                return True, latest_version
            else:
                logger.info(f"Current version {current_version} is up to date.")
                return False, latest_version
        else:
            logger.error(f"Error fetching release data: {response.status_code}")
            return False, None
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False, None



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='[%(asctime)s] [%(levelname)s] %(message)s', 
                        datefmt="%H:%M:%S")

    print("is_laptop:", is_laptop())
    print("is_on_battery:", is_on_battery())

    display_timeout_ac, display_timeout_dc = get_display_timeouts()
    print(f"Display Timeout on AC Power: {display_timeout_ac} seconds")
    print(f"Display Timeout on DC Power: {display_timeout_dc} seconds")

    # Example usage of check_github_update_available
    is_update_available, latest_version = check_github_update_available(
        current_version="0.3.7", 
        repo_api_url="https://api.github.com/repos/ZDAVanO/MoniTune/releases/latest"
    )

    while True:
        idle_seconds = get_idle_time()
        print(f"The computer has been idle for {idle_seconds:.2f} seconds")
        time.sleep(1)


