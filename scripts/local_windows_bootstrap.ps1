# Local Windows PC bootstrap for RecallBot V31 (PCA MZG517)
# Use this on your home/office Windows machine — NOT on Prayogshala.
# Prayogshala VMs are Ubuntu only; use scripts/prayogshala_bootstrap.sh there.
#
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\local_windows_bootstrap.ps1
#   $env:SKIP_ABLATION="1"; $env:SKIP_HNSW="1"
#   powershell -ExecutionPolicy Bypass -File scripts\local_windows_bootstrap.ps1

param(
  [switch]$InPlace
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git"
$RepoName = "pcam-zg517-a1-recallbot"

Write-Host "=== RecallBot V31 · Local Windows bootstrap ==="
Write-Host "Host: $([System.Environment]::OSVersion.VersionString)"
Write-Host "Note: For Prayogshala (Ubuntu VM), use scripts/prayogshala_bootstrap.sh instead."

if ($InPlace -or (Test-Path (Join-Path $PSScriptRoot "..\requirements.txt"))) {
  $ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
  $RootDir = Join-Path $PWD $RepoName
  if (-not (Test-Path "$RepoName\.git")) {
    git clone $RepoUrl
  }
  $ProjectDir = (Resolve-Path $RepoName).Path
}

Set-Location $ProjectDir
Write-Host "Project: $ProjectDir"

$Py = $null
foreach ($c in @("python", "py")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) { throw "Python not found on PATH. Install Python 3.10+." }

& $Py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Local Windows often blocks Hugging Face (Zscaler) — default to hash embeddings.
if (-not $env:RECALLBOT_EMBED_BACKEND) {
  $env:RECALLBOT_EMBED_BACKEND = "hash"
  Write-Host "RECALLBOT_EMBED_BACKEND=hash (local default). Unset this on Prayogshala Ubuntu."
}

$env:MPLBACKEND = if ($env:MPLBACKEND) { $env:MPLBACKEND } else { "Agg" }
$env:OLLAMA_HOST = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "http://127.0.0.1:11434" }
$env:OLLAMA_MODEL = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen2.5:1.5b-instruct" }
$env:RECALLBOT_LLM = if ($env:RECALLBOT_LLM) { $env:RECALLBOT_LLM } else { "template" }
$env:TOKENIZERS_PARALLELISM = "false"
$env:HF_HUB_DISABLE_TELEMETRY = "1"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
  try {
    Invoke-WebRequest -Uri "$($env:OLLAMA_HOST)/api/tags" -UseBasicParsing -TimeoutSec 2 | Out-Null
    $env:RECALLBOT_LLM = "auto"
  } catch {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $env:RECALLBOT_LLM = "auto"
  }
  try { ollama pull $env:OLLAMA_MODEL } catch { Write-Host "ollama pull failed; using template NLG." }
} else {
  Write-Host "Ollama not found — template NLG will be used."
}

$runArgs = @("scripts/run_all.py", "--fresh-logs", "--embed-backend", $env:RECALLBOT_EMBED_BACKEND)
if ($env:SKIP_ABLATION -eq "1") { $runArgs += "--skip-ablation" }
if ($env:SKIP_HNSW -eq "1") { $runArgs += "--skip-hnsw" }

python @runArgs

Write-Host ""
Write-Host "=== Done (local Windows) ==="
Write-Host "Artifacts: logs\ results\ memory\ index\ db\"
Write-Host "For graded MiniLM runs, use Prayogshala Ubuntu: bash scripts/prayogshala_bootstrap.sh ."
