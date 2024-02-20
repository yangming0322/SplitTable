@echo off
rem 更改当前代码页为 UTF-8
chcp 65001 > nul


setlocal enabledelayedexpansion

rem 定义变量存储 Anaconda 的快捷方式路径
set "SHORTCUT_PATH="

echo 正在全局“开始”菜单中查找 Anaconda 快捷方式...
for /r "%ProgramData%\Microsoft\Windows\Start Menu\Programs" %%F in (*Anaconda*.lnk) do (
    echo 找到快捷方式: %%F
    set "SHORTCUT_PATH=%%F"
    goto processShortcut
)

echo 正在用户个人的“开始”菜单中查找 Anaconda 快捷方式...
for /r "%APPDATA%\Microsoft\Windows\Start Menu\Programs" %%F in (*Anaconda*.lnk) do (
    echo 找到快捷方式: %%F
    set "SHORTCUT_PATH=%%F"
    goto processShortcut
)

if "!SHORTCUT_PATH!"=="" (
    echo 未找到 Anaconda 的快捷方式。
    goto endScript
)

:processShortcut
rem 使用 PowerShell 获取快捷方式的目标路径
for /f "delims=" %%i in ('powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\""!SHORTCUT_PATH!\""); $Shortcut.TargetPath"') do set "ANACONDA_INSTALL_PATH=%%i"

rem 从安装路径提取 Anaconda 的 Scripts 目录
for %%a in ("!ANACONDA_INSTALL_PATH!") do set "ANACONDA_SCRIPTS_DIR=%%~dpaScripts"

echo 找到 Anaconda 的 Scripts 目录：!ANACONDA_SCRIPTS_DIR!

rem 启动 Anaconda 默认环境
echo 正在激活 Anaconda 默认环境...
call "!ANACONDA_SCRIPTS_DIR!\activate.bat" base

rem 激活myenv环境
echo  激活myenv环境
conda activate myenv


rem 运行SL脚本
echo  运行SL脚本
streamlit run SplitTable.py


:endScript
pause