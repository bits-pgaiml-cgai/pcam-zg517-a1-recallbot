# BITS Prayogshala — Windows VM bootstrap for RecallBot V31 (PCA MZG517)
# Portal: https://prayogshala.bits-pilani.ac.in
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\prayogshala_bootstrap.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\prayogshala_bootstrap.ps1 -RootDir D:\cgai-mp1
#   powershell -ExecutionPolicy Bypass -File scripts\prayogshala_bootstrap.ps1 -InPlace
#   $env:SKIP_ABLATION=1; $env:SKIP_HNSW=1; ...

param(
  [string]$RootDir = "D:\cgai-mp1",
  [switch]$InPlace
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git"
$RepoName = "pcam-zg517-a1-recallbot"

Write-Host "=== RecallBot V31 · Prayogshala Windows bootstrap ==="
Write-Host "Host: $([System.Environment]::OSVersion.VersionString)"

if ($InPlace) {
  $ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} elseif (Test-Path (Join-Path $PSScriptRoot "..\requirements.txt")) {
  # Script lives inside a checkout — prefer that unless -RootDir was explicitly meant for clone.
  $ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
  New-Item -ItemType Directory -Force -Path $RootDir | Out-Null
  Set-Location $RootDir
  if (-not (Test-Path "$RepoName\.git")) {
    git clone $RepoUrl
  }
  $ProjectDir = Join-Path $RootDir $RepoName
}

Set-Location $ProjectDir
Write-Host "Project: $ProjectDir"

$Py = $null
foreach ($c in @("python", "py")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) { throw "Python not found on PATH. Install Python 3.10+ on this Windows VM." }

& $Py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

Remove-Item Env:RECALLBOT_EMBED_BACKEND -ErrorAction SilentlyContinue
$env:MPLBACKEND = if ($env:MPLBACKEND) { $env:MPLBACKEND } else { "Agg" }
$env:OLLAMA_HOST = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "http://127.0.0.1:11434" }
$env:OLLAMA_MODEL = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen2.5:1.5b-instruct" }
$env:RECALLBOT_LLM = if ($env:RECALLBOT_LLM) { $env:RECALLBOT_LLM } else { "auto" }
$env:TOKENIZERS_PARALLELISM = "false"
$env:HF_HUB_DISABLE_TELEMETRY = "1"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
  try {
    Invoke-WebRequest -Uri "$($env:OLLAMA_HOST)/api/tags" -UseBasicParsing -TimeoutSec 2 | Out-Null
  } catch {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
  }
  ollama pull $env:OLLAMA_MODEL
} else {
  Write-Host "Ollama not found — template NLG will be used."
  $env:RECALLBOT_LLM = "template"
}

$runArgs = @("scripts/run_all.py", "--fresh-logs")
if ($env:SKIP_ABLATION -eq "1") { $runArgs += "--skip-ablation" }
if ($env:SKIP_HNSW -eq "1") { $runArgs += "--skip-hnsw" }

python @runArgs

Write-Host ""
Write-Host "=== Done (Windows) ==="
Write-Host "Artifacts under: $ProjectDir"
Write-Host "  logs\ results\ memory\ index\ db\"
Write-Host "Copy/zip those folders to D:\ before ending the VM."
