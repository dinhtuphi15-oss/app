@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp02-chay.ps1"
echo.
echo (Neu cua so nay tu dong dong ngay sau dong tren, PowerShell co the chua chay duoc.)
pause
