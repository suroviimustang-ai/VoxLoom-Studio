param([string]$Python = "$PSScriptRoot\.venv311\Scripts\python.exe", [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Push-Location -LiteralPath $PSScriptRoot
try {
    New-Item -ItemType Directory -Path artifacts -Force | Out-Null
    if (-not (Test-Path -LiteralPath 'models/flexsed/manifest.json')) {
        throw 'Run tools/prepare_flexsed.py first'
    }
    if (-not $SkipBuild) {
        & $Python tools/collect_licenses.py
        if ($LASTEXITCODE -ne 0) {
            throw 'License collection failed'
        }
        & $Python -m PyInstaller VoxLoom.spec --noconfirm --distpath dist-flexsed --workpath build-flexsed
        if ($LASTEXITCODE -ne 0) {
            throw 'Packaging failed'
        }
    }
    & $Python tools/check_qt_imports.py --root dist-flexsed/VoxLoom/_internal
    if ($LASTEXITCODE -ne 0) {
        throw 'Qt DLL validation failed'
    }
    & "$PSScriptRoot/tools/prepare_speech_fixture.ps1"
    & $Python tools/check_startup.py
    if ($LASTEXITCODE -ne 0) {
        throw 'Display checks failed'
    }
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:HF_HUB_OFFLINE = '1'
    $env:TRANSFORMERS_OFFLINE = '1'
    $taskExecutable = Join-Path $PSScriptRoot 'dist-flexsed/VoxLoom/VoxLoom.exe'
    $taskSmoke = Start-Process -FilePath $taskExecutable -ArgumentList '--smoke-test', 'artifacts/speech_fixture.wav', 'artifacts/packaged-flexsed-smoke' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -Wait -PassThru
    if ($taskSmoke.ExitCode -ne 0) {
        throw 'Packaged smoke test failed'
    }
    $taskReport = Get-Content -LiteralPath 'artifacts/packaged-flexsed-smoke/release-smoke.json' -Raw | ConvertFrom-Json
    if (-not $taskReport.ok -or 'flexsed-offline-events' -notin $taskReport.checks) {
        throw 'FlexSED packaged smoke report failed'
    }
    & $Python tools/verify_release.py $taskExecutable
    if ($LASTEXITCODE -ne 0) {
        throw 'Packaged codecs and offline models failed'
    }
    & 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' packaging/VoxLoom-FlexSED.iss
    if ($LASTEXITCODE -ne 0) {
        throw 'Installer build failed'
    }
    $taskVersion = & $Python -c 'from voxloom import __version__; print(__version__)'
    Get-FileHash -LiteralPath "release/VoxLoom-Studio-Setup-$taskVersion-Offline-win-x64.exe" -Algorithm SHA256 | Format-List
}
finally {
    Pop-Location
}
