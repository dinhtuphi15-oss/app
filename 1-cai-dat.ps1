$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Refresh-Path {
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  newsclip - Cai dat tu dong (chi chay 1 lan)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== Kiem tra winget ===" -ForegroundColor Cyan
if (-not (Test-Cmd "winget")) {
    Write-Host "Khong tim thay winget (Trinh cai dat ung dung cua Windows)." -ForegroundColor Red
    Write-Host "Hay cai 'App Installer' tu Microsoft Store roi chay lai file nay:" -ForegroundColor Red
    Write-Host "  https://apps.microsoft.com/detail/9nblggh4nns1" -ForegroundColor Yellow
    Read-Host "Nhan Enter de dong"
    exit 1
}

Write-Host "=== Cai Python (neu chua co) ===" -ForegroundColor Cyan
if (-not (Test-Cmd "python")) {
    winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "Da co Python, bo qua."
}

Write-Host "=== Cai ffmpeg (neu chua co) ===" -ForegroundColor Cyan
if (-not (Test-Cmd "ffmpeg")) {
    winget install -e --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "Da co ffmpeg, bo qua."
}

Refresh-Path

if (-not (Test-Cmd "python")) {
    Write-Host ""
    Write-Host "Khong thay lenh 'python' sau khi cai." -ForegroundColor Yellow
    Write-Host "Hay DONG cua so nay, roi chay lai '1-cai-dat.bat' (Windows can nap lai PATH)." -ForegroundColor Yellow
    Read-Host "Nhan Enter de dong"
    exit 1
}

Write-Host "=== Tao moi truong ao Python (.venv) ===" -ForegroundColor Cyan
python -m venv .venv

Write-Host "=== Cai thu vien Python (co the mat vai phut) ===" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  CAI DAT XONG!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Buoc tiep theo (khuyen nghi, giup ket qua chinh xac hon nhieu):"
Write-Host "  1. Mo file .env bang Notepad (trong thu muc nay), dan ANTHROPIC_API_KEY vao."
Write-Host "     (Lay key mien phi tai: https://console.anthropic.com)"
Write-Host "  2. Double-click '2-chay.bat' de bat dau dung cong cu."
Write-Host ""
Read-Host "Nhan Enter de dong cua so nay"
