# First-run setup for Windows: writes .env and creates workspace/tools with the hello tool.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path .env) {
    Write-Host ".env already exists; leaving it alone. Delete it to run setup again."
} else {
    $ollama = Read-Host "Ollama URL (blank to run a model on this machine instead)"
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $secret = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
    $image = if ($env:LAB_IMAGE) { $env:LAB_IMAGE } else { "ghcr.io/dsumjham/remap:latest" }
    $lines = @("LAB_IMAGE=$image", "LAB_UID=1000", "LAB_GID=1000", "WEBUI_SECRET_KEY=$secret")
    if ([string]::IsNullOrWhiteSpace($ollama)) {
        $lines += "OLLAMA_BASE_URL=http://ollama:11434"
        $lines += "COMPOSE_PROFILES=local-model"
    } else {
        $lines += "OLLAMA_BASE_URL=$ollama"
    }
    Set-Content -Path .env -Value $lines -Encoding ascii
    Write-Host "Wrote .env"
}

New-Item -ItemType Directory -Force workspace/tools | Out-Null
if (-not (Test-Path workspace/tools/hello.py)) { Copy-Item tools/hello.py workspace/tools/hello.py }
Write-Host "Next: docker compose up -d, then open http://localhost:8501 (panel) and http://localhost:3000 (chat)."
