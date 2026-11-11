param([switch]$Fix)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskLocalModule = Join-Path $taskRoot '.tooling/PSScriptAnalyzer/1.24.0/PSScriptAnalyzer.psd1'
if (Test-Path -LiteralPath $taskLocalModule) {
    Import-Module $taskLocalModule -ErrorAction Stop
}
else {
    Import-Module PSScriptAnalyzer -RequiredVersion 1.24.0 -ErrorAction Stop
}
$taskSettings = Join-Path $taskRoot 'PSScriptAnalyzerSettings.psd1'
$taskScripts = @(Get-ChildItem -LiteralPath $taskRoot -File | Where-Object { $_.Extension -in '.ps1', '.psd1' })
foreach ($taskFolder in 'tools', 'packaging') {
    $taskScripts += @(Get-ChildItem -LiteralPath (Join-Path $taskRoot $taskFolder) -Recurse -File -Filter '*.ps1')
}
$taskProblems = @()
foreach ($taskScript in $taskScripts) {
    $taskText = [IO.File]::ReadAllText($taskScript.FullName)
    $taskNormalized = $taskText -replace '\r?\n', "`r`n"
    $taskFormatted = Invoke-Formatter -ScriptDefinition $taskNormalized -Settings $taskSettings
    $taskFormatted = $taskFormatted -replace '(?m)[ \t]+(?=\r?$)', ''
    $taskFormatted = ($taskFormatted -replace '\r?\n', "`r`n").TrimEnd() + "`r`n"
    if ($Fix) {
        [IO.File]::WriteAllText($taskScript.FullName, $taskFormatted, [Text.UTF8Encoding]::new($true))
    }
    else {
        $taskBytes = [IO.File]::ReadAllBytes($taskScript.FullName)
        $taskHasBom = $taskBytes.Length -ge 3 -and $taskBytes[0] -eq 239 -and $taskBytes[1] -eq 187 -and $taskBytes[2] -eq 191
        if ($taskText -cne $taskFormatted -or -not $taskHasBom) {
            $taskProblems += "Formatting/UTF-8 BOM: $($taskScript.Name)"
        }
    }
    $taskProblems += @(Invoke-ScriptAnalyzer -Path $taskScript.FullName -Settings $taskSettings)
}
if ($taskProblems.Count -gt 0) {
    $taskProblems | Out-String | Write-Output
    throw 'PowerShell style checks failed. Run tools/check_powershell.ps1 -Fix and review remaining diagnostics.'
}
Write-Output "$($taskScripts.Count) PowerShell files: formatting and analysis passed."
