@echo off
pyinstaller ^
    --onefile ^
    --add-data "src/assets/icons/setting_light.png;./icons" ^
    --add-data "src/assets/icons/setting_dark.png;./icons" ^
    --add-data "src/assets/icons/monitor_light.png;./icons" ^
    --add-data "src/assets/icons/monitor_dark.png;./icons" ^
    --add-data "src/assets/icons/laptop_light.png;./icons" ^
    --add-data "src/assets/icons/laptop_dark.png;./icons" ^
    --add-data "src/assets/icons/sun_light.png;./icons" ^
    --add-data "src/assets/icons/sun_dark.png;./icons" ^
    --add-data "src/assets/icons/down_arrow_light.png;./icons" ^
    --add-data "src/assets/icons/down_arrow_dark.png;./icons" ^
    --add-data "src/assets/icons/eye_light.png;./icons" ^
    --add-data "src/assets/icons/eye_dark.png;./icons" ^
    --add-data "src/assets/icons/contrast_light.png;./icons" ^
    --add-data "src/assets/icons/contrast_dark.png;./icons" ^
    --add-data "src/assets/icons/link_light.png;./icons" ^
    --add-data "src/assets/icons/link_dark.png;./icons" ^
    --add-data "src/assets/icons/shutdown_light.png;./icons" ^
    --add-data "src/assets/icons/shutdown_dark.png;./icons" ^
    --add-data "src/assets/tray-icons/light/mdl2.ico;./tray-icons/light" ^
    --add-data "src/assets/tray-icons/dark/mdl2.ico;./tray-icons/dark" ^
    --add-data "src/assets/tray-icons/light/fluent.ico;./tray-icons/light" ^
    --add-data "src/assets/tray-icons/dark/fluent.ico;./tray-icons/dark" ^
    --add-data "src/assets/icons/icon_color.ico;./icons" ^
    --icon="src/assets/icons/icon_color.png" "src/MoniTune.py"
pause


