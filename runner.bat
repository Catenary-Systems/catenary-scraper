@echo off
:: BatchGotAdmin - check for admin privileges
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: If not admin, relaunch as admin
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Optional: Change to the directory containing this script
cd /d "%~dp0"

:: Run the Python GUI
start "" pythonw.exe gui.py

:: Hide the batch window
exit
