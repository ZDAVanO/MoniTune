import os
import sys


# MARK: Constants

app_name = "MoniTune"

version = "0.3.5"

timer_interval = 60  # seconds
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
border_color_light = "#bebebe"
border_color_dark = "#404040"

bg_color_light = "#f3f3f3"
bg_color_dark = "#202020"


fr_color_light = "#fbfbfb"  
fr_color_dark = "#2b2b2b"

fr_border_color_light = "#e5e5e5"
fr_border_color_dark = "#1d1d1d"


rr_border_color_light = "#ececec"
rr_border_color_dark = "#3f3f3f"

rr_fg_color_light = "#fefefe"
rr_fg_color_dark = "#373737"

rr_hover_color_light = "#f0f0f0"
rr_hover_color_dark = "#2c2c2c"


separator_color_light = "#d2d2d2" # #dcdcdc bebebe
separator_color_dark = "#555555" # 5f5f5f





# MARK: Paths
if getattr(sys, 'frozen', False):
    # Якщо програма запущена як EXE, шлях до іконки відносно до виконуваного файлу
    app_icon_path = os.path.join(sys._MEIPASS, 'icon_color.ico')
    
    settings_icon_light_path = os.path.join(sys._MEIPASS, 'setting_light.png')
    settings_icon_dark_path = os.path.join(sys._MEIPASS, 'setting_dark.png')

    tray_icon_light_fluent_path = os.path.join(sys._MEIPASS, 'tray-icons/light/fluent.ico')
    tray_icon_dark_fluent_path = os.path.join(sys._MEIPASS, 'tray-icons/dark/fluent.ico')

    tray_icon_light_mdl2_path = os.path.join(sys._MEIPASS, 'tray-icons/light/mdl2.ico')
    tray_icon_dark_mdl2_path = os.path.join(sys._MEIPASS, 'tray-icons/dark/mdl2.ico')


    monitor_icon_light_path = os.path.join(sys._MEIPASS, 'monitor_light.png')
    monitor_icon_dark_path = os.path.join(sys._MEIPASS, 'monitor_dark.png')

    laptop_icon_light_path = os.path.join(sys._MEIPASS, 'laptop_light.png')
    laptop_icon_dark_path = os.path.join(sys._MEIPASS, 'laptop_dark.png')

    sun_icon_light_path = os.path.join(sys._MEIPASS, 'sun_light.png')
    sun_icon_dark_path = os.path.join(sys._MEIPASS, 'sun_dark.png')

    down_arrow_icon_light_path = os.path.join(sys._MEIPASS, 'down_arrow_light.png')
    down_arrow_icon_dark_path = os.path.join(sys._MEIPASS, 'down_arrow_dark.png')

    eye_icon_light_path = os.path.join(sys._MEIPASS, 'eye_light.png')
    eye_icon_dark_path = os.path.join(sys._MEIPASS, 'eye_dark.png')

    contrast_icon_light_path = os.path.join(sys._MEIPASS, 'contrast_light.png')
    contrast_icon_dark_path = os.path.join(sys._MEIPASS, 'contrast_dark.png')

    link_icon_light_path = os.path.join(sys._MEIPASS, 'link_light.png')
    link_icon_dark_path = os.path.join(sys._MEIPASS, 'link_dark.png')


else:
    # Якщо програма запущена з Python, використовуємо поточну директорію
    app_icon_path = 'src/assets/icons/icon_color_dev.ico'

    settings_icon_light_path = 'src/assets/icons/setting_light.png'
    settings_icon_dark_path = 'src/assets/icons/setting_dark.png'

    tray_icon_light_fluent_path = 'src/assets/tray-icons/light/fluent.ico'
    tray_icon_dark_fluent_path = 'src/assets/tray-icons/dark/fluent.ico'

    tray_icon_light_mdl2_path = 'src/assets/tray-icons/light/mdl2.ico'
    tray_icon_dark_mdl2_path = 'src/assets/tray-icons/dark/mdl2.ico'

    
    monitor_icon_light_path = 'src/assets/icons/monitor_light.png'
    monitor_icon_dark_path = 'src/assets/icons/monitor_dark.png'
    
    laptop_icon_light_path = 'src/assets/icons/laptop_light.png'
    laptop_icon_dark_path = 'src/assets/icons/laptop_dark.png'

    sun_icon_light_path = 'src/assets/icons/sun_light.png'
    sun_icon_dark_path = 'src/assets/icons/sun_dark.png'

    down_arrow_icon_light_path = 'src/assets/icons/down_arrow_light.png'
    down_arrow_icon_dark_path = 'src/assets/icons/down_arrow_dark.png'

    eye_icon_light_path = 'src/assets/icons/eye_light.png'
    eye_icon_dark_path = 'src/assets/icons/eye_dark.png'

    contrast_icon_light_path = 'src/assets/icons/contrast_light.png'
    contrast_icon_dark_path = 'src/assets/icons/contrast_dark.png'

    link_icon_light_path = 'src/assets/icons/link_light.png'
    link_icon_dark_path = 'src/assets/icons/link_dark.png'


# MARK: Tray Icons
tray_icons = {
    "monitune": {
        "Light": app_icon_path,
        "Dark": app_icon_path
    },
    "mdl2": {
        "Light": tray_icon_light_mdl2_path,
        "Dark": tray_icon_dark_mdl2_path
    },
    "fluent": {
        "Light": tray_icon_light_fluent_path,
        "Dark": tray_icon_dark_fluent_path
    }
}