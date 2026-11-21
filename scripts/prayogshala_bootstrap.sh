#!/usr/bin/env bash
# BITS Prayogshala — Ubuntu VM ONLY (PCA MZG517 RecallBot V31)
# Portal: https://prayogshala.bits-pilani.ac.in
#
# Prayogshala provides Ubuntu VMs only. For local Windows development use:
#   scripts/local_windows_bootstrap.ps1
#
# Usage:
#   bash scripts/prayogshala_bootstrap.sh .
#   bash scripts/prayogshala_bootstrap.sh /path/to/workspace
#   SKIP_ABLATION=1 SKIP_HNSW=1 bash scripts/prayogshala_bootstrap.sh .

set -euo pipefail

REPO_URL="https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git"
REPO_NAME="pcam-zg517-a1-recallbot"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_FROM_SCRIPT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== RecallBot V31 · Prayogshala Ubuntu VM bootstrap ==="
echo "Host: $(uname -a)"
echo "Python: $(command -v python3 || true)"

if [[ "${1:-}" == "." ]]; then
  PROJECT_DIR="$(pwd)"
elif [[ -n "${1:-}" ]]; then
  ROOT_DIR="$1"
  mkdir -p "$ROOT_DIR"
  cd "$ROOT_DIR"
  if [[ ! -d "${REPO_NAME}/.git" ]]; then
    git clone "$REPO_URL"
  fi
  PROJECT_DIR="$(pwd)/${REPO_NAME}"
elif [[ -f "${REPO_FROM_SCRIPT}/requirements.txt" && -d "${REPO_FROM_SCRIPT}/src" ]]; then
  PROJECT_DIR="$REPO_FROM_SCRIPT"
else
  ROOT_DIR="${HOME}/Workspace/cgai-mp1"
  mkdir -p "$ROOT_DIR"
  cd "$ROOT_DIR"
  if [[ ! -d "${REPO_NAME}/.git" ]]; then
    git clone "$REPO_URL"
  fi
  PROJECT_DIR="$(pwd)/${REPO_NAME}"
fi

cd "$PROJECT_DIR"
echo "Project: $PROJECT_DIR"

if command -v apt-get >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -y || true
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 python3-venv python3-pip python3-dev \
      build-essential git curl \
      || true
  else
    echo "No sudo — assuming python3/venv already installed."
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found on this Ubuntu VM."
  exit 1
fi

export MPLBACKEND="${MPLBACKEND:-Agg}"
unset RECALLBOT_EMBED_BACKEND || true
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b-instruct}"
export RECALLBOT_LLM="${RECALLBOT_LLM:-auto}"
export TOKENIZERS_PARALLELISM=false
export HF_HUB_DISABLE_TELEMETRY=1

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
    nohup ollama serve >/tmp/ollama-recallbot.log 2>&1 &
    sleep 3
  fi
  ollama pull "$OLLAMA_MODEL" || echo "WARN: ollama pull failed; template NLG will be used."
else
  echo "Ollama not found — template NLG will be used."
  export RECALLBOT_LLM=template
fi

RUN_ARGS=(python scripts/run_all.py --fresh-logs)
if [[ "${SKIP_ABLATION:-0}" == "1" ]]; then
  RUN_ARGS+=(--skip-ablation)
fi
if [[ "${SKIP_HNSW:-0}" == "1" ]]; then
  RUN_ARGS+=(--skip-hnsw)
fi

"${RUN_ARGS[@]}"

echo
echo "=== Done (Prayogshala Ubuntu) ==="
echo "Artifacts under: $PROJECT_DIR"
echo "  logs/calls.jsonl  results/  memory/  index/  db/"
echo "Copy/zip those folders to ~/Workspace before ending the VM."
