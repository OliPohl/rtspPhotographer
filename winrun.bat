@echo off

REM Check if python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed, please install Python 3.x to continue.
    pause
)

REM Check if pip is installed
where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo Pip is not installed, please install Pip to continue.
    pause
)

REM Check if the .venv directory exists
if not exist ".venv" (
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

python -m rtspPhotographer
