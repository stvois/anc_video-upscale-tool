$ErrorActionPreference = 'Stop'
$Root = if ($env:VIDEO_UPSCALER_DATA_DIR) { $env:VIDEO_UPSCALER_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'VideoUpscalerAI' }
if (-not $env:VIDEO_UPSCALER_DATA_DIR -and $Root -match '[^\x00-\x7F]') { $Root = Join-Path $env:PUBLIC 'VideoUpscalerAI' }
$Precision = Join-Path $Root 'precision'
$Python = Join-Path $Precision 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    & py -3.10 -m venv $Precision
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 is required for precision engine setup.' }
}
& $Python -m pip install torch torchvision spandrel opencv-python-headless
if ($LASTEXITCODE -ne 0) { throw 'Precision dependencies installation failed.' }
$Models = Join-Path $Precision 'models'
New-Item -ItemType Directory -Force -Path $Models | Out-Null
foreach ($Name in @('realesr-animevideov3','RealESRGAN_x4plus')) {
    $Version = if ($Name -eq 'realesr-animevideov3') { 'v0.2.5.0' } else { 'v0.1.0' }
    $Target = Join-Path $Models ($Name + '.pth')
    if (-not (Test-Path -LiteralPath $Target)) {
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/xinntao/Real-ESRGAN/releases/download/$Version/$Name.pth" -OutFile ($Target + '.download')
        Move-Item -LiteralPath ($Target + '.download') -Destination $Target
    }
}
Write-Output '[DONE] Precision engine installed.'
