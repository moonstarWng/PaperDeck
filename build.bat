@echo off
REM build.bat — PyInstaller 打包 paper2ppt GUI 为单个 exe
echo ========================================
echo Paper2PPT GUI — Build EXE
echo ========================================

echo.
echo [1/3] Installing dependencies...
pip install -r requirements-gui.txt -q

echo.
echo [2/3] Building exe with PyInstaller...
pyinstaller --onefile --windowed ^
  --name Paper2PPT ^
  --add-data "prompt-base.txt;." ^
  --add-data "agent-prompt.txt;." ^
  --add-data "scripts;scripts" ^
  --add-data "templates;templates" ^
  --hidden-import customtkinter ^
  --hidden-import pptx ^
  --hidden-import pypdf ^
  --hidden-import pdfplumber ^
  --hidden-import lxml ^
  --hidden-import PIL ^
  --hidden-import requests ^
  gui_app.py

echo.
echo [3/3] Done!
echo EXE located at: dist\Paper2PPT.exe
pause
