@echo off
echo Magic Wound - Starting GUI Version
echo.

REM Check if dependencies are installed
python -c "import pygame" 2>nul
if errorlevel 1 (
    echo [Warning] pygame not detected, installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Check if placeholder images are generated
if not exist "assets\cards\madposion.png" (
    echo [Info] First run, generating placeholder images...
    python generate_placeholders.py
    echo.
)

echo Starting game...
python main_gui.py

pause
