param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv-win")) {
    py -3.11 -m venv .venv-win
}

$Python = Join-Path $ProjectRoot ".venv-win\Scripts\python.exe"
$Pip = Join-Path $ProjectRoot ".venv-win\Scripts\pip.exe"

& $Python -m pip install --upgrade pip
& $Pip install -r requirements.txt

if (-not (Test-Path "assets\ffmpeg\ffmpeg.exe")) {
    throw "Не найден assets\ffmpeg\ffmpeg.exe"
}

if (-not (Test-Path "assets\ffmpeg\ffprobe.exe")) {
    throw "Не найден assets\ffmpeg\ffprobe.exe"
}

if ($Clean) {
    Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
}

& $Python -m PyInstaller build.spec --noconfirm

Write-Host ""
Write-Host "Windows build finished:"
Write-Host "  $ProjectRoot\dist\MP4Converter.exe"
