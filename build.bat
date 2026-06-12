@echo off
chcp 65001 >nul
echo ========================================
echo PaperDeck - Portable Build
echo ========================================
echo.
python build_portable.py
echo.
echo Done - dist\PaperDeck_v1.0_portable\
echo Double-click start.bat to launch
pause
