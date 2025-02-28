@echo off
pyinstaller --onefile --windowed --add-data "src/assets/icons/setting_light.png;." --add-data "src/assets/icons/setting_dark.png;." --add-data "src/assets/icons/icon_color.ico;." --add-data "src/assets/tray-icons/light/mdl2.ico;./tray-icons/light" --add-data "src/assets/tray-icons/dark/mdl2.ico;./tray-icons/dark" --add-data "src/assets/tray-icons/light/fluent.ico;./tray-icons/light" --add-data "src/assets/tray-icons/dark/fluent.ico;./tray-icons/dark" --icon="src/assets/icons/icon_color.png" "src/MoniTune.py"
pause


