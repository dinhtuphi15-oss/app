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

function Test-RealPython {
    # 'python'/'python3' co san trong PATH cua Windows thuong chi la
    # "App execution alias" (stub mo Microsoft Store), KHONG phai Python
    # that, nen phai kiem tra ky chu khong the chi dua vao Get-Command.
    if (Test-Cmd "py") {
        try {
            & py -3 --version *> $null
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch {}
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
        try {
            & python --version *> $null
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch {}
    }
    return $false
}

function Invoke-PythonVenv {
    if (Test-Cmd "py") {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

try {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  newsclip - Cai dat tu dong (chi chay 1 lan)" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "=== Kiem tra winget ===" -ForegroundColor Cyan
    if (-not (Test-Cmd "winget")) {
        Write-Host "Khong tim thay winget (Trinh cai dat ung dung cua Windows)." -ForegroundColor Red
        Write-Host "Hay cai 'App Installer' tu Microsoft Store roi chay lai file nay:" -ForegroundColor Red
        Write-Host "  https://apps.microsoft.com/detail/9nblggh4nns1" -ForegroundColor Yellow
        return
    }

    Write-Host "=== Cai Python (neu chua co that su) ===" -ForegroundColor Cyan
    if (-not (Test-RealPython)) {
        winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
        Refresh-Path
    } else {
        Write-Host "Da co Python that, bo qua."
    }

    Write-Host "=== Cai ffmpeg (neu chua co) ===" -ForegroundColor Cyan
    if (-not (Test-Cmd "ffmpeg")) {
        winget install -e --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
        Refresh-Path
    } else {
        Write-Host "Da co ffmpeg, bo qua."
    }

    if (-not (Test-RealPython)) {
        Write-Host ""
        Write-Host "Van chua thay Python that su sau khi cai." -ForegroundColor Yellow
        Write-Host "Nguyen nhan thuong gap: Windows co san 'App execution alias' gia cho python.exe." -ForegroundColor Yellow
        Write-Host "Cach sua thu cong (lam mot lan):" -ForegroundColor Yellow
        Write-Host "  1) Mo Settings > Apps > Advanced app settings > App execution aliases" -ForegroundColor Yellow
        Write-Host "  2) TAT 2 cong tac 'App Installer python.exe' va 'App Installer python3.exe'" -ForegroundColor Yellow
        Write-Host "  3) Dong cua so nay, mo lai, chay lai '1-cai-dat.bat'" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Neu van loi, tu cai Python thu cong tai https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "(nho tick 'Add python.exe to PATH' luc cai), roi chay lai file nay." -ForegroundColor Yellow
        return
    }

    Write-Host "=== Tao moi truong ao Python (.venv) ===" -ForegroundColor Cyan
    Invoke-PythonVenv
    if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
        throw "Khong tao duoc .venv (xem thong bao loi ngay ben tren)."
    }

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
}
catch {
    Write-Host ""
    Write-Host "=== CO LOI XAY RA ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Chup lai man hinh nay (hoac copy toan bo chu) gui lai de duoc ho tro sua." -ForegroundColor Yellow
}
finally {
    Write-Host ""
    Read-Host "Nhan Enter de dong cua so nay"
}
