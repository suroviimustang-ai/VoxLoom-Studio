param([string]$Python = "$PSScriptRoot\.venv311\Scripts\python.exe")
$ErrorActionPreference = 'Stop'
& $Python "$PSScriptRoot\main.py"
exit $LASTEXITCODE
