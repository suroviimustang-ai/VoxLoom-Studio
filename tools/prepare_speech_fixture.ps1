$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskOutput = Join-Path $taskRoot 'artifacts/speech_fixture.wav'
if (Test-Path -LiteralPath $taskOutput) {
    return
}
New-Item -ItemType Directory -Path (Split-Path -Parent $taskOutput) -Force | Out-Null
$taskVoice = New-Object -ComObject SAPI.SpVoice
$taskEnglish = @($taskVoice.GetVoices() | Where-Object { $_.GetAttribute('Language') -match '(^|;)409(;|$)' })
if ($taskEnglish.Count -eq 0) {
    throw 'Install an English Windows voice to generate the release speech fixture.'
}
$taskStream = New-Object -ComObject SAPI.SpFileStream
try {
    $taskVoice.Voice = $taskEnglish[0]
    $taskStream.Open($taskOutput, 3, $false)
    $taskVoice.AudioOutputStream = $taskStream
    [void]$taskVoice.Speak('This is a test recording for speech restoration. The original audio must remain unchanged. We can find speech, remove background noise, and transcribe the selected fragment.')
}
finally {
    $taskStream.Close()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($taskVoice)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($taskStream)
}
