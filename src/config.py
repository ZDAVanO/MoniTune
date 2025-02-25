import os
import sys


# MARK: Constants

app_name = "MoniTune"

version = "0.2.0"

REGISTRY_PATH = r"Software\MoniTune\Settings"




# MARK: Theme
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






# MARK: Paths
if getattr(sys, 'frozen', False):
    # Якщо програма запущена як EXE, шлях до іконки відносно до виконуваного файлу
    app_icon_path = os.path.join(sys._MEIPASS, 'icon_color.ico')
    # if is_dark_theme():
    #     icon_path = os.path.join(sys._MEIPASS, 'icon_light.ico')
    # else:
    #     icon_path = os.path.join(sys._MEIPASS, 'icon_dark.ico')
    settings_icon_light_path = os.path.join(sys._MEIPASS, 'setting_light.png')
    settings_icon_dark_path = os.path.join(sys._MEIPASS, 'setting_dark.png')

else:
    # Якщо програма запущена з Python, використовуємо поточну директорію
    app_icon_path = 'src/assets/icons/icon_color_dev.ico'
    # if is_dark_theme():
    #     icon_path = 'icons/icon_light.ico' 
    # else:
    #     icon_path = 'icons/icon_dark.ico'
    settings_icon_light_path = 'src/assets/icons/setting_light.png'
    settings_icon_dark_path = 'src/assets/icons/setting_dark.png'