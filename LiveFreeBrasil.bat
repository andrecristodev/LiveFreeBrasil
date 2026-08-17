@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

title LiveFreeBrasil CLI

:: Verifica se o Python esta instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Python nao encontrado. Instalando automaticamente...
    where winget >nul 2>nul
    if %errorlevel% equ 0 (
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements >nul 2>nul
    )
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe', '%TEMP%\python_installer.exe')"
        if exist "%TEMP%\python_installer.exe" (
            start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 SimpleInstall=1
            del /f /q "%TEMP%\python_installer.exe" >nul 2>nul
        )
    )
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    set "PATH=%ProgramFiles%\Python312;%ProgramFiles%\Python312\Scripts;%PATH%"
)

if "%~1"=="" (
    python "%~dp0livefreebrasil.py" --auto --kill
) else (
    python "%~dp0livefreebrasil.py" %*
)
