import os
import sys


# MARK: Constants

app_name = "MoniTune"

version = "0.1.5"

REGISTRY_PATH = r"Software\MoniTune\Settings"



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