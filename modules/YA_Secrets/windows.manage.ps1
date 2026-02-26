$SopsConfigFiles = @(".sops.yaml")
$SopsConfig = $SopsConfigFiles | ForEach-Object { Join-Path (Get-Location) $_ } | Where-Object { Test-Path $_ }

if (-not $SopsConfig) {
    Write-Host "No sops config file found (.sops.yaml)."
    Write-Host "Please copy the config file from submodule before running this script."
    exit 1
}

$File = "env.yaml"

$FileExists = Test-Path $File

if (-not $FileExists) {
    $Template = @"
secrets:
  api_key: value
  database_password: value
"@
    $Template | Set-Content $File -Encoding UTF8
    Write-Host "Created $File"
}

$Temp = [System.IO.Path]::GetTempFileName()
$TempYaml = [System.IO.Path]::ChangeExtension($Temp, ".yaml")
Rename-Item -Path $Temp -NewName $TempYaml
$Temp = $TempYaml

if ($FileExists) {
    sops -d --output $Temp $File
    $content = Get-Content -Path $Temp -Raw
}

if (-not $FileExists) {
    $content = Get-Content -Path $File -Raw
}

$content | Set-Content -Path $Temp -Encoding UTF8

$codeExists = Get-Command code -ErrorAction SilentlyContinue
if ($codeExists) {
    & code --wait $Temp
}
else {
    Start-Process -FilePath "notepad" -ArgumentList $Temp -Wait
}

sops -e -i $Temp
Move-Item -Force $Temp $File

Write-Host "Saved and encrypted $File"
