#!/usr/bin/env bash
set -euo pipefail

# BITS Prayogshala bootstrap for PCA MZG517 Mini Project 1 (RecallBot V31)
# Portal: https://prayogshala.bits-pilani.ac.in

ROOT_DIR="${1:-$HOME/Workspace/cgai-mp1}"
REPO_URL="https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git"

mkdir -p "$ROOT_DIR"
cd "$ROOT_DIR"

if [ ! -d pcam-zg517-a1-recallbot/.git ]; then
  git clone "$REPO_URL"
fi
cd pcam-zg517-a1-recallbot

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Prefer real MiniLM on Prayogshala (usually has Hugging Face access).
unset RECALLBOT_EMBED_BACKEND || true

# Optional Ollama NLG
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b-instruct}"
export RECALLBOT_LLM="${RECALLBOT_LLM:-auto}"

if command -v ollama >/dev/null 2>&1; then
  (ollama serve >/tmp/ollama-recallbot.log 2>&1 &) || true
  sleep 2
  ollama pull "$OLLAMA_MODEL" || true
else
  echo "Ollama not found — template NLG will be used (still valid for retrieval/memory evidence)."
fi

python scripts/run_all.py

echo
echo "Done. Key outputs:"
echo "  logs/calls.jsonl"
echo "  results/hit_rate.csv results/probe_results.csv results/cost_scale.json"
echo "  memory/ (after hybrid_mem Session B)"
