# Run RecallBot on BITS Prayogshala (Ubuntu + Windows)

Portal: https://prayogshala.bits-pilani.ac.in  
Repo: https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot  
Variant: **V31** clinic appointment desk · Twist B time-bound facts

Prayogshala Virtual Lab VMs are commonly **Ubuntu**. Some courses also offer **Windows** VMs. Both are supported.

Persist work under **`~/Workspace`** (Ubuntu) or **`D:\`** (Windows) before ending the session.

---

## A) Ubuntu VM (recommended / typical)

### One-shot after Connect

```bash
mkdir -p ~/Workspace/cgai-mp1 && cd ~/Workspace/cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
chmod +x scripts/prayogshala_bootstrap.sh
bash scripts/prayogshala_bootstrap.sh .
```

Or from any directory (script clones into `~/Workspace/cgai-mp1` by default):

```bash
bash /path/to/pcam-zg517-a1-recallbot/scripts/prayogshala_bootstrap.sh
```

### Faster smoke run (skip ablation + 100k HNSW)

```bash
cd ~/Workspace/cgai-mp1/pcam-zg517-a1-recallbot
SKIP_ABLATION=1 SKIP_HNSW=1 bash scripts/prayogshala_bootstrap.sh .
```

### Manual Ubuntu steps

```bash
cd ~/Workspace/cgai-mp1/pcam-zg517-a1-recallbot
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Prefer MiniLM (do NOT set hash on Prayogshala)
unset RECALLBOT_EMBED_BACKEND
export MPLBACKEND=Agg
export RECALLBOT_LLM=auto          # or template
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:1.5b-instruct

# Optional LLM
# curl -fsSL https://ollama.com/install.sh | sh
# ollama serve &
# ollama pull qwen2.5:1.5b-instruct

python scripts/run_all.py --fresh-logs
```

### Ubuntu notes

| Topic | Detail |
|-------|--------|
| Python | Use `python3` / `python3 -m venv` |
| Display | Headless → `MPLBACKEND=Agg` (set by bootstrap) |
| Packages | Bootstrap tries `sudo apt-get install python3-venv python3-pip python3-dev build-essential` when sudo exists |
| Persist | Copy `logs/ results/ memory/ index/ db/` to `~/Workspace` |

---

## B) Windows VM

```powershell
mkdir D:\cgai-mp1 -Force
cd D:\cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
powershell -ExecutionPolicy Bypass -File scripts\prayogshala_bootstrap.ps1 -InPlace
```

Faster smoke:

```powershell
$env:SKIP_ABLATION="1"; $env:SKIP_HNSW="1"
powershell -ExecutionPolicy Bypass -File scripts\prayogshala_bootstrap.ps1 -InPlace
```

Manual Windows:

```powershell
cd D:\cgai-mp1\pcam-zg517-a1-recallbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Remove-Item Env:RECALLBOT_EMBED_BACKEND -ErrorAction SilentlyContinue
$env:MPLBACKEND="Agg"
python scripts\run_all.py --fresh-logs
```

Persist under **`D:\`** before ending the VM.

---

## What bootstrap / `run_all.py` executes

1. Regenerate Task 1 data  
2. `pytest` BM25/RRF CS4 tests  
3. Build MiniLM (or hash) indexes 128 & 512  
4. Session A → **separate process** Session B (`hybrid_mem`)  
5. STM `full` / `trim` / `summary` + token plot  
6. Ablation `no_rag` → `hybrid_mem` + probes (unless `SKIP_ABLATION=1`)  
7. Task 5 cost + flat vs HNSW (unless `SKIP_HNSW=1`)  

---

## Environment knobs (both OS)

| Variable | Meaning |
|----------|---------|
| unset `RECALLBOT_EMBED_BACKEND` | `sentence-transformers/all-MiniLM-L6-v2` (Prayogshala default) |
| `RECALLBOT_EMBED_BACKEND=hash` | Offline hashing (use on local Zscaler only) |
| `RECALLBOT_LLM=auto` | Try Ollama; else template NLG |
| `RECALLBOT_LLM=template` | Force template NLG |
| `OLLAMA_MODEL` | e.g. `qwen2.5:1.5b-instruct` or `qwen3:1.7b` |
| `MPLBACKEND=Agg` | Headless matplotlib (Ubuntu) |
| `SKIP_ABLATION=1` | Skip ablation loop in bootstrap |
| `SKIP_HNSW=1` | Skip 100k HNSW timing |

---

## Integrity reminders

- Session B must be a **separate process**.  
- Do not hand-edit `logs/calls.jsonl`.  
- `python -m pytest tests/` (Ubuntu: `python3 -m pytest tests/`) must pass.

## After the run

Zip and keep:

- `logs/calls.jsonl`
- `results/`
- `memory/`
- `index/`
- `db/`
