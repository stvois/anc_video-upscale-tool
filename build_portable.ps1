$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = $PSScriptRoot
$DistRoot = Join-Path $ProjectRoot "dist"
$PortableRoot = Join-Path $DistRoot "VideoUpscaler-Portable"
$PortableZip = Join-Path $DistRoot "VideoUpscaler-Portable.zip"
$ExeSource = Join-Path $DistRoot "VideoUpscaler.exe"

function Remove-SafeDirectory {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$AllowedParent)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $ResolvedPath = [IO.Path]::GetFullPath($Path)
    $ResolvedParent = [IO.Path]::GetFullPath($AllowedParent).TrimEnd('\') + '\'
    if (-not $ResolvedPath.StartsWith($ResolvedParent, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe cleanup target: $ResolvedPath"
    }
    Remove-Item -LiteralPath $ResolvedPath -Recurse -Force
}

if (-not (Test-Path -LiteralPath $ExeSource)) {
    Write-Output "[INFO] Building VideoUpscaler.exe first."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "build_exe.ps1")
    if ($LASTEXITCODE -ne 0) { throw "EXE build failed." }
}

Write-Output "[INFO] Ensuring AI engines are installed."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "setup_video_ai_engines.ps1")
if ($LASTEXITCODE -ne 0) { throw "AI engine setup failed." }

if ($env:VIDEO_UPSCALER_DATA_DIR) {
    $DataRoot = $env:VIDEO_UPSCALER_DATA_DIR
}
elseif ((Join-Path $env:LOCALAPPDATA "VideoUpscalerAI") -match '[^\x00-\x7F]') {
    $DataRoot = Join-Path $env:PUBLIC "VideoUpscalerAI"
}
else {
    $DataRoot = Join-Path $env:LOCALAPPDATA "VideoUpscalerAI"
}

$InstalledTools = Join-Path $DataRoot "tools"
$RealExe = Get-ChildItem -LiteralPath (Join-Path $InstalledTools "realesrgan") -Filter "realesrgan-ncnn-vulkan.exe" -File -Recurse | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.Directory.FullName "models\realesrgan-x4plus.param")
} | Select-Object -First 1
$RifeExe = Get-ChildItem -LiteralPath (Join-Path $InstalledTools "rife") -Filter "rife-ncnn-vulkan.exe" -File -Recurse | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.Directory.FullName "rife-v4.6")
} | Select-Object -First 1

if (-not $RealExe) { throw "Installed Real-ESRGAN executable was not found." }
if (-not $RifeExe) { throw "Installed RIFE executable was not found." }

New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
Remove-SafeDirectory -Path $PortableRoot -AllowedParent $DistRoot
New-Item -ItemType Directory -Force -Path $PortableRoot | Out-Null

Copy-Item -LiteralPath $ExeSource -Destination (Join-Path $PortableRoot "VideoUpscaler.exe")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "PORTABLE_README.txt") -Destination $PortableRoot

Write-Output "[INFO] Copying selected Real-ESRGAN models."
$RealDest = Join-Path $PortableRoot "tools\realesrgan"
$RealModelDest = Join-Path $RealDest "models"
New-Item -ItemType Directory -Force -Path $RealModelDest | Out-Null
foreach ($Name in @("realesrgan-ncnn-vulkan.exe", "vcomp140.dll", "vcomp140d.dll", "LICENSE", "README.md")) {
    $Source = Join-Path $RealExe.Directory.FullName $Name
    if (Test-Path -LiteralPath $Source) { Copy-Item -LiteralPath $Source -Destination $RealDest }
}
foreach ($Pattern in @("realesrgan-x4plus.*", "realesr-animevideov3-x2.*", "realesr-animevideov3-x4.*")) {
    Get-ChildItem -LiteralPath (Join-Path $RealExe.Directory.FullName "models") -File -Filter $Pattern |
        Copy-Item -Destination $RealModelDest
}

Write-Output "[INFO] Copying selected RIFE models."
$RifeDest = Join-Path $PortableRoot "tools\rife"
New-Item -ItemType Directory -Force -Path $RifeDest | Out-Null
foreach ($Name in @("rife-ncnn-vulkan.exe", "vcomp140.dll", "LICENSE", "README.md")) {
    $Source = Join-Path $RifeExe.Directory.FullName $Name
    if (Test-Path -LiteralPath $Source) { Copy-Item -LiteralPath $Source -Destination $RifeDest }
}
foreach ($Model in @("rife-v4.6", "rife-anime")) {
    Copy-Item -LiteralPath (Join-Path $RifeExe.Directory.FullName $Model) -Destination $RifeDest -Recurse
}

$TempRoot = Join-Path $env:TEMP ("VideoUpscalerPortable-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
try {
    Write-Output "[INFO] Downloading the latest FFmpeg Windows GPL shared build."
    $Headers = @{ "User-Agent" = "VideoUpscaler-Portable-Builder" }
    $Release = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
    $Asset = $Release.assets | Where-Object { $_.name -eq "ffmpeg-master-latest-win64-gpl-shared.zip" } | Select-Object -First 1
    if (-not $Asset) { throw "FFmpeg GPL shared Windows asset was not found." }
    $Archive = Join-Path $TempRoot $Asset.name
    Invoke-WebRequest -Headers $Headers -Uri $Asset.browser_download_url -OutFile $Archive -UseBasicParsing
    $Extracted = Join-Path $TempRoot "ffmpeg"
    Expand-Archive -LiteralPath $Archive -DestinationPath $Extracted -Force
    $FfmpegRoot = Get-ChildItem -LiteralPath $Extracted -Directory | Select-Object -First 1
    if (-not $FfmpegRoot -or -not (Test-Path -LiteralPath (Join-Path $FfmpegRoot.FullName "bin\ffmpeg.exe"))) {
        throw "Extracted FFmpeg build is invalid."
    }
    $FfmpegDest = Join-Path $PortableRoot "ffmpeg"
    New-Item -ItemType Directory -Force -Path $FfmpegDest | Out-Null
    Copy-Item -LiteralPath (Join-Path $FfmpegRoot.FullName "bin") -Destination $FfmpegDest -Recurse
    $ThirdParty = Join-Path $PortableRoot "third_party\ffmpeg"
    New-Item -ItemType Directory -Force -Path $ThirdParty | Out-Null
    foreach ($Name in @("LICENSE.txt", "README.txt")) {
        $Source = Join-Path $FfmpegRoot.FullName $Name
        if (Test-Path -LiteralPath $Source) { Copy-Item -LiteralPath $Source -Destination $ThirdParty }
    }
}
finally {
    Remove-SafeDirectory -Path $TempRoot -AllowedParent $env:TEMP
}

if (Test-Path -LiteralPath $PortableZip) { Remove-Item -LiteralPath $PortableZip -Force }
Write-Output "[INFO] Creating portable ZIP."
Compress-Archive -LiteralPath $PortableRoot -DestinationPath $PortableZip -CompressionLevel Optimal

$FolderBytes = (Get-ChildItem -LiteralPath $PortableRoot -File -Recurse | Measure-Object Length -Sum).Sum
$ZipBytes = (Get-Item -LiteralPath $PortableZip).Length
Write-Output ("[DONE] Folder: {0} MB" -f [math]::Round($FolderBytes / 1MB, 1))
Write-Output ("[DONE] ZIP: {0} MB" -f [math]::Round($ZipBytes / 1MB, 1))
Write-Output "[DONE] $PortableZip"

