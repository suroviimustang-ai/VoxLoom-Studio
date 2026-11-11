param([string]$Python = "$PSScriptRoot\.venv311\Scripts\python.exe", [switch]$SkipTests)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not $SkipTests) {
        $taskTestDirectory = Join-Path $PSScriptRoot ('artifacts\pytest-' + [guid]::NewGuid().ToString('N'))
        & $Python -m pytest -q --basetemp $taskTestDirectory
        if ($LASTEXITCODE -ne 0) {
            throw 'Tests failed'
        }
    }
    & "$PSScriptRoot/build-flexsed.ps1" -Python $Python
}
finally {
    Pop-Location
}
