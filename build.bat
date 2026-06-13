@echo off
chcp 65001 >nul
echo ========================================
echo PaperDeck - Portable Build
echo ========================================
echo.

REM 使用 Python 3（系统默认 python 可能是 2.x）
set PY=py -3
where py >nul 2>nul || set PY=python

REM 配置代理（国内网络访问 GitHub/PyPI 必需）
set http_proxy=http://127.0.0.1:7897
set https_proxy=http://127.0.0.1:7897

%PY% build_portable.py
if errorlevel 1 (
    echo.
    echo [ERROR] 构建失败，请检查上方日志
    pause
    exit /b 1
)

echo.
echo ========================================
echo Done - dist\PaperDeck_v1.0_portable.zip
echo 用户只需解压后双击 启动.bat
echo ========================================
pause
