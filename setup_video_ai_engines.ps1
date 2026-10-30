$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

if ($env:VIDEO_UPSCALER_DATA_DIR) {
    $DataRoot = $env:VIDEO_UPSCALER_DATA_DIR
}
elseif ((Join-Path $env:LOCALAPPDATA "VideoUpscalerAI") -match '[^\x00-\x7F]') {
    $DataRoot = Join-Path $env:PUBLIC "VideoUpscalerAI"
}
else {
    $DataRoot = Join-Path $env:LOCALAPPDATA "VideoUpscalerAI"
}
$ToolRoot = Join-Path $DataRoot "tools"
New-Item -ItemType Directory -Force -Path $ToolRoot | Out-Null

function Install-GitHubReleaseTool {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$ExecutableName,
        [Parameter(Mandatory = $true)][string]$DestinationName,
        [Parameter(Mandatory = $true)][string]$AssetPattern,
        [string]$RequiredFile,
        [switch]$SearchRecentReleases
    )

    $Destination = Join-Path $ToolRoot $DestinationName
    $Existing = Get-ChildItem -LiteralPath $Destination -Filter $ExecutableName -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    $Required = if ($RequiredFile) { Get-ChildItem -LiteralPath $Destination -Filter $RequiredFile -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 } else { $true }
    if ($Existing -and $Required) {
        Write-Output "[READY] $ExecutableName"
        return
    }

    Write-Output "[INFO] Checking the Windows release for $Repository."
    $Headers = @{ "User-Agent" = "Local-Video-Upscaler" }
    if ($SearchRecentReleases) {
        $Releases = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/repos/$Repository/releases?per_page=20"
        $Asset = $Releases.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
    }
    else {
        $Release = Invoke-RestMethod -Headers $Headers -Uri "https://api.github.com/repos/$Repository/releases/latest"
        $Asset = $Release.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
    }
    if (-not $Asset) {
        throw "No matching Windows ZIP asset was found for $Repository."
    }

    $TempDir = Join-Path $ToolRoot (".install-" + [Guid]::NewGuid().ToString("N"))
    $ZipPath = Join-Path $TempDir $Asset.name
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    try {
        Write-Output "[DOWNLOAD] $($Asset.name)"
        Invoke-WebRequest -Headers $Headers -Uri $Asset.browser_download_url -OutFile $ZipPath -UseBasicParsing
        Write-Output "[EXTRACT] $Destination"
        Expand-Archive -LiteralPath $ZipPath -DestinationPath $Destination -Force
        $Installed = Get-ChildItem -LiteralPath $Destination -Filter $ExecutableName -File -Recurse | Select-Object -First 1
        if (-not $Installed) {
            throw "Installation validation failed for $ExecutableName."
        }
        Write-Output "[OK] $($Installed.FullName)"
    }
    finally {
        if (Test-Path -LiteralPath $TempDir) {
            Remove-Item -LiteralPath $TempDir -Recurse -Force
        }
    }
}

Install-GitHubReleaseTool -Repository "xinntao/Real-ESRGAN" -ExecutableName "realesrgan-ncnn-vulkan.exe" -DestinationName "realesrgan" -AssetPattern "realesrgan-ncnn-vulkan.*windows.*\.zip$" -RequiredFile "realesrgan-x4plus.param" -SearchRecentReleases
Install-GitHubReleaseTool -Repository "nihui/rife-ncnn-vulkan" -ExecutableName "rife-ncnn-vulkan.exe" -DestinationName "rife" -AssetPattern "windows.*\.zip$" -RequiredFile "flownet.param"

Write-Output "[DONE] AI video engines are installed."
