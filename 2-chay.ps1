$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

try {
    $py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        Write-Host "Chua cai dat xong (khong thay .venv)." -ForegroundColor Red
        Write-Host "Hay double-click '1-cai-dat.bat' truoc va doc ky neu co dong chu mau do." -ForegroundColor Red
        return
    }

    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  newsclip - Tim B-roll va dung san CapCut" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    $srt = Read-Host "Duong dan file .srt (keo file vao cua so nay roi bam Enter)"
    $srt = $srt.Trim('"').Trim()
    while (-not (Test-Path $srt)) {
        Write-Host "Khong tim thay file: $srt" -ForegroundColor Red
        $srt = Read-Host "Nhap lai duong dan file .srt"
        $srt = $srt.Trim('"').Trim()
    }

    $voice = Read-Host "Duong dan file voice mp3/wav (de trong neu khong co)"
    $voice = $voice.Trim('"').Trim()

    $projectName = Read-Host "Ten project (khong dau, khong dau cach, vd ChienSu_20260818)"
    if ([string]::IsNullOrWhiteSpace($projectName)) {
        $projectName = "newsclip_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    }

    $defaultDrafts = Join-Path $env:LOCALAPPDATA "CapCut\User Data\Projects\com.lveditor.draft"
    $draftsDir = $null
    if (Test-Path $defaultDrafts) {
        Write-Host "Da tu tim thay thu muc CapCut: $defaultDrafts" -ForegroundColor Green
        $draftsDir = $defaultDrafts
    } else {
        Write-Host "Khong tu tim thay thu muc CapCut mac dinh (co the ban chua mo CapCut lan nao)." -ForegroundColor Yellow
        $draftsDir = Read-Host "Dan duong dan thu muc drafts CapCut (de trong neu chua ro, tool se tu tao trong thu muc output)"
        $draftsDir = $draftsDir.Trim('"').Trim()
    }

    $argsList = @("-m", "newsclip.cli", "find", "--srt", $srt, "--project-name", $projectName, "--out-dir", ".\output")
    if (-not [string]::IsNullOrWhiteSpace($voice)) { $argsList += @("--voice", $voice) }
    if (-not [string]::IsNullOrWhiteSpace($draftsDir)) { $argsList += @("--capcut-drafts-dir", $draftsDir) }

    Write-Host ""
    Write-Host "Dang chay, doi mot chut..." -ForegroundColor Cyan
    Write-Host ""
    & $py @argsList
    $exitCode = $LASTEXITCODE

    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "Xong! Mo file nay bang trinh duyet de xem bao cao:" -ForegroundColor Green
        Write-Host "  $PSScriptRoot\output\$projectName\report.html"
        Write-Host "Neu da dan dung thu muc drafts CapCut, mo CapCut len se thay project '$projectName'."
    } else {
        Write-Host "Co loi xay ra (xem chi tiet o tren)." -ForegroundColor Red
    }
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
    Read-Host "Nhan Enter de dong"
}
