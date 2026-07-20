@echo off
echo ===================================================
echo [1/3] Generating QRC resource file...
.venv\Scripts\python generate_qrc.py

echo [2/3] Compiling resources...
.venv\Scripts\pyside6-rcc src/resources.qrc -o src/resources_rc.py

echo [3/3] Building MoniTune executable...
.venv\Scripts\pyinstaller MoniTune.spec

echo ===================================================
echo Build completed successfully.
pause
