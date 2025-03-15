@echo off
pyinstaller ^
    --onefile ^
    --add-data "src/assets/icons/setting_light.png;." ^
    --add-data "src/assets/icons/setting_dark.png;." ^
    --add-data "src/assets/icons/monitor_light.png;." ^
    --add-data "src/assets/icons/monitor_dark.png;." ^
    --add-data "src/assets/icons/laptop_light.png;." ^
    --add-data "src/assets/icons/laptop_dark.png;." ^
    --add-data "src/assets/icons/sun_light.png;." ^
    --add-data "src/assets/icons/sun_dark.png;." ^
    --add-data "src/assets/icons/down_arrow_light.png;." ^
    --add-data "src/assets/icons/down_arrow_dark.png;." ^
    --add-data "src/assets/tray-icons/light/mdl2.ico;./tray-icons/light" ^
    --add-data "src/assets/tray-icons/dark/mdl2.ico;./tray-icons/dark" ^
    --add-data "src/assets/tray-icons/light/fluent.ico;./tray-icons/light" ^
    --add-data "src/assets/tray-icons/dark/fluent.ico;./tray-icons/dark" ^
    --add-data "src/assets/icons/icon_color.ico;." ^
    --icon="src/assets/icons/icon_color.png" "src/MoniTune.py"
pause


