# LiveFreeBrasil CLI - PowerShell Wrapper
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\livefreebrasil.py" @args
