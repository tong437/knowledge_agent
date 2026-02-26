Write-Host "=== Installing age and sops (Windows) ==="

# Check for scoop
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "Scoop not found. Installing scoop..."
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')
}

# Install age
Write-Host "=== Installing age ==="
if (-not (Get-Command age -ErrorAction SilentlyContinue)) {
    Write-Host "Installing age via scoop..."
    scoop bucket add extras
    scoop install age
}
else {
    Write-Host "age already installed"
}

# Install sops
Write-Host "=== Installing sops ==="
if (-not (Get-Command sops -ErrorAction SilentlyContinue)) {
    Write-Host "Installing sops via scoop..."
    scoop install sops
}
else {
    Write-Host "sops already installed"
}

Write-Host "=== Done. sops + age installed. ==="
