$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = $PSScriptRoot
$Python = $null

foreach ($Candidate in @(
    "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:SystemDrive\Python314\python.exe",
    "$env:SystemDrive\Python313\python.exe",
    "$env:SystemDrive\Python312\python.exe",
    "$env:SystemDrive\Python311\python.exe",
    "$env:SystemDrive\Python310\python.exe"
)) {
    if (Test-Path -LiteralPath $Candidate) {
        $Python = $Candidate
        break
    }
}

if (-not $Python) {
    throw "Python 3.10 or later was not found."
}

Write-Output "[INFO] Python: $Python"
& $Python -m pip install --disable-pip-version-check --upgrade "pyinstaller>=6.0,<7.0"

Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name "VideoUpscaler" `
        --add-data "setup_video_ai_engines.ps1;." `
        "video_upscaler_gui.py"

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    $Exe = Join-Path $ProjectRoot "dist\VideoUpscaler.exe"
    if (-not (Test-Path -LiteralPath $Exe)) {
        throw "EXE was not generated: $Exe"
    }

    $SizeMB = [math]::Round((Get-Item -LiteralPath $Exe).Length / 1MB, 1)
    Write-Output "[DONE] $Exe ($SizeMB MB)"
}
finally {
    Pop-Location
}

