# BITS Prayogshala (Windows VM) bootstrap for RecallBot V31
# Portal: https://prayogshala.bits-pilani.ac.in

param(
  [string]$RootDir = "D:\cgai-mp1"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $RootDir | Out-Null
Set-Location $RootDir

if (-not (Test-Path "pcam-zg517-a1-recallbot\.git")) {
  git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
}
Set-Location pcam-zg517-a1-recallbot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Remove-Item Env:RECALLBOT_EMBED_BACKEND -ErrorAction SilentlyContinue
$env:OLLAMA_HOST = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "http://127.0.0.1:11434" }
$env:OLLAMA_MODEL = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen2.5:1.5b-instruct" }
$env:RECALLBOT_LLM = if ($env:RECALLBOT_LLM) { $env:RECALLBOT_LLM } else { "auto" }

if (Get-Command ollama -ErrorAction SilentlyContinue) {
  Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
  Start-Sleep -Seconds 2
  ollama pull $env:OLLAMA_MODEL
} else {
  Write-Host "Ollama not found — template NLG will be used."
}

python scripts/run_all.py

Write-Host "Done. See logs/, results/, memory/"
