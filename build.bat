@echo off
REM build.bat — 一键构建 PaperDeck 便携包并自动解压
echo ========================================
echo PaperDeck — 便携包构建
echo ========================================
echo.
python build_portable.py
echo.
echo 解压完成 — dist\PaperDeck_v1.0_portable\
echo 双击 启动.bat 即可运行
pause
