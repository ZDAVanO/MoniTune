import sys
import os
from ui import MT_App

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        icon_path_s = os.path.join(sys._MEIPASS, 'icon_color.ico')
    else:
        icon_path_s = 'icons/icon_color_dev.ico'

    app = MT_App(icon_path_s)
    app.run()