@echo off
setlocal
cd /d "%~dp0"

title Desativar LiveFreeBrasil - Restaurar Discord Normal

:: Executa o LiveFreeBrasil com a flag de restauracao/desativacao
python "%~dp0livefreebrasil.py" --disable

if %errorlevel% neq 0 (
    echo.
    echo Ocorreu um problema ao restaurar o Discord normal.
    pause
)
