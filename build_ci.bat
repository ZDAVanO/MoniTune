@echo off
cd /d "%~dp0"
echo Generating QRC resource file...
python generate_qrc.py

echo Compiling resources...
pyside6-rcc src/resources.qrc -o src/resources_rc.py

echo Building MoniTune executable...
pyinstaller MoniTune.spec
