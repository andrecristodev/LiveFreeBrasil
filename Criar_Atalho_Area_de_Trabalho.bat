@echo off
setlocal
cd /d "%~dp0"

title Criar Atalho LiveFreeBrasil na Area de Trabalho

set SCRIPT_PATH=%~dp0LiveFreeBrasil.bat
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Discord (LiveFreeBrasil).lnk

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Iniciar Discord com LiveFreeBrasil Desbloqueado'; $s.Save()"

echo.
echo [OK] Atalho criado na sua Area de Trabalho com sucesso!
echo Local: %USERPROFILE%\Desktop\Discord (LiveFreeBrasil).lnk
echo.
timeout /t 3 /nobreak >nul
