$KeyDir = "$env:USERPROFILE\.config\sops\keys"
$KeyFile = Join-Path $KeyDir "age.key"

if (-not (Test-Path $KeyDir)) { New-Item -ItemType Directory -Path $KeyDir -Force }

if (Test-Path $KeyFile) {
    Write-Host "Age key already exists: $KeyFile"
} else {
    Write-Host "Generating Age key..."
    age-keygen -o $KeyFile
}

Write-Host "`n=== Public key ==="
age-keygen -y $KeyFile

Write-Host "`nPrivate key saved at $KeyFile"
Write-Host "Keep it safe! Do not share."

$env:SOPS_AGE_KEY_FILE = $KeyFile
[Environment]::SetEnvironmentVariable("SOPS_AGE_KEY_FILE", $KeyFile, "User")

Write-Host "`nEnvironment variable SOPS_AGE_KEY_FILE set to $KeyFile"
Write-Host "You may need to restart your terminal for the change to take effect in new sessions."