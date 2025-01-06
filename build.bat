@echo off
pyinstaller --noconfirm --onedir --windowed --add-data "icons/icon_color.ico;." --add-data "C:\Users\Oleh Ivaniuk\AppData\Local\Programs\Python\Python313\Lib\site-packages/customtkinter;customtkinter/" --icon="icons/icon_color.png" "MoniTune.py"
pause