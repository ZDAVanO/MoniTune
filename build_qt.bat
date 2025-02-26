@echo off
pyinstaller --onefile --add-data "src/assets/icons/setting_light.png;." --add-data "src/assets/icons/setting_dark.png;." --add-data "src/assets/icons/icon_color.ico;." --icon="src/assets/icons/icon_color.png" "src/MoniTune.py"
pause