import os
import sys



is_exe = getattr(sys, 'frozen', False)


# MARK: Constants

app_name = "MoniTune"

version = "0.3.7"

timer_interval = 20  # seconds
break_notification_interval = 30  # minutes

REGISTRY_PATH = r"Software\MoniTune\Settings"

WIN11_WINDOW_CORNER_RADIUS = 9
WIN11_WINDOW_OFFSET = 11

UPDATE_CHECK_URL = "https://api.github.com/repos/ZDAVanO/MoniTune/releases/latest"
LATEST_RELEASE_URL = "https://github.com/ZDAVanO/MoniTune/releases/latest"
LEARN_MORE_URL = "https://github.com/ZDAVanO/MoniTune"

DISPLAY_SETTINGS_URL = "ms-settings:display"
NIGHT_LIGHT_SETTINGS_URL = "ms-settings:nightlight"


# MARK: Colors
colors = {
    # main window background color
    "main_bg": {
        "Light": "#f3f3f3",
        "Dark": "#202020"  # 141414
    },
    # main window border color
    "main_border": {
        "Light": "#bebebe",
        "Dark": "#404040"
    },
    # monitor_frame, placeholder_frame background color
    "frame_bg": {
        "Light": "#fbfbfb",
        "Dark": "#2b2b2b"
    },
    # monitor_frame, placeholder_frame border color
    "frame_border": {
        "Light": "#e5e5e5",
        "Dark": "#1d1d1d"
    },
    "frame_hover": {
        "Light": "rgba(0, 0, 0, 0.05)",
        "Dark": "rgba(255, 255, 255, 0.07)"
    },
    # res_combobox background color
    "combobox_bg": {
        "Light": "#fefefe",
        "Dark": "#373737"
    },
    # separator color
    "separator": {
        "Light": "#d2d2d2", # #dcdcdc #bebebe
        "Dark": "#555555" # #5f5f5f
    }
}


def get_icon_path(relative_path):
    if is_exe:
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join('src/assets', relative_path)


# MARK: Icons
icons = {
    "monitune": {
        "Light": get_icon_path('icons/icon_color.ico' if is_exe else 'icons/icon_color_dev.ico'), # src/assets/icons/icon_color.ico
        "Dark": get_icon_path('icons/icon_color.ico' if is_exe else 'icons/icon_color_dev.ico')  # src/assets/icons/icon_color_dev.ico
    },
    "settings": {
        "Light": get_icon_path('icons/setting_light.png'), # src/assets/icons/setting_light.png
        "Dark": get_icon_path('icons/setting_dark.png') # src/assets/icons/setting_dark.png
    },
    "monitor": {
        "Light": get_icon_path('icons/monitor_light.png'), # src/assets/icons/monitor_light.png
        "Dark": get_icon_path('icons/monitor_dark.png') # src/assets/icons/monitor_dark.png
    },
    "laptop": {
        "Light": get_icon_path('icons/laptop_light.png'), # src/assets/icons/laptop_light.png
        "Dark": get_icon_path('icons/laptop_dark.png') # src/assets/icons/laptop_dark.png
    },
    "sun": {
        "Light": get_icon_path('icons/sun_light.png'), # src/assets/icons/sun_light.png
        "Dark": get_icon_path('icons/sun_dark.png') # src/assets/icons/sun_dark.png
    },
    "down_arrow": {
        "Light": get_icon_path('icons/down_arrow_light.png'), # src/assets/icons/down_arrow_light.png
        "Dark": get_icon_path('icons/down_arrow_dark.png') # src/assets/icons/down_arrow_dark.png
    },
    "eye": {
        "Light": get_icon_path('icons/eye_light.png'), # src/assets/icons/eye_light.png
        "Dark": get_icon_path('icons/eye_dark.png') # src/assets/icons/eye_dark.png
    },
    "contrast": {
        "Light": get_icon_path('icons/contrast_light.png'), # src/assets/icons/contrast_light.png
        "Dark": get_icon_path('icons/contrast_dark.png') # src/assets/icons/contrast_dark.png
    },
    "link": {
        "Light": get_icon_path('icons/link_light.png'), # src/assets/icons/link_light.png
        "Dark": get_icon_path('icons/link_dark.png') # src/assets/icons/link_dark.png
    },
    "shutdown": {
        "Light": get_icon_path('icons/shutdown_light.png'), # src/assets/icons/shutdown_light.png
        "Dark": get_icon_path('icons/shutdown_dark.png') # src/assets/icons/shutdown_dark.png
    }
}


# MARK: Tray Icons
tray_icons = {
    "monitune": {
        "Light": get_icon_path('icons/icon_color.ico' if is_exe else 'icons/icon_color_dev.ico'), # src/assets/icons/icon_color.ico
        "Dark": get_icon_path('icons/icon_color.ico' if is_exe else 'icons/icon_color_dev.ico') # src/assets/icons/icon_color_dev.ico
    },
    "mdl2": {
        "Light": get_icon_path('tray-icons/light/mdl2.ico'), # src/assets/tray-icons/light/mdl2.ico
        "Dark": get_icon_path('tray-icons/dark/mdl2.ico') # src/assets/tray-icons/dark/mdl2.ico
    },
    "fluent": {
        "Light": get_icon_path('tray-icons/light/fluent.ico'), # src/assets/tray-icons/light/fluent.ico
        "Dark": get_icon_path('tray-icons/dark/fluent.ico') # src/assets/tray-icons/dark/fluent.ico
    }
}


