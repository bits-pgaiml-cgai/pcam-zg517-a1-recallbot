# Run RecallBot on BITS Prayogshala (Ubuntu VM only)

Portal: https://prayogshala.bits-pilani.ac.in  
Repo: https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot  
Variant: **V31** clinic appointment desk · Twist B time-bound facts

**Prayogshala provides Ubuntu VMs only** (no Windows VM).  
Your local PC may be Windows — for that use [`scripts/local_windows_bootstrap.ps1`](../scripts/local_windows_bootstrap.ps1) and keep MiniLM evidence runs on Prayogshala when Hugging Face is blocked at home.

Persist work under **`~/Workspace`** before ending the lab session.

---

## Ubuntu Prayogshala — one-shot

```bash
mkdir -p ~/Workspace/cgai-mp1 && cd ~/Workspace/cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
chmod +x scripts/prayogshala_bootstrap.sh
bash scripts/prayogshala_bootstrap.sh .
```

### Faster smoke (skip ablation + 100k HNSW)

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

unset RECALLBOT_EMBED_BACKEND   # use MiniLM on Prayogshala
export MPLBACKEND=Agg
export RECALLBOT_LLM=auto       # or template
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:1.5b-instruct

python scripts/run_all.py --fresh-logs
```

### Ubuntu notes

| Topic | Detail |
|-------|--------|
| OS | Ubuntu only on Prayogshala |
| Python | `python3` / `python3 -m venv` |
| Display | Headless → `MPLBACKEND=Agg` |
| Embeddings | Leave `RECALLBOT_EMBED_BACKEND` unset (MiniLM) |
| Persist | Copy `logs/ results/ memory/ index/ db/` → `~/Workspace` |

---

## Local Windows PC (not Prayogshala)

```powershell
cd <path>\pcam-zg517-a1-recallbot
powershell -ExecutionPolicy Bypass -File scripts\local_windows_bootstrap.ps1
```

Local default uses `RECALLBOT_EMBED_BACKEND=hash` when Hugging Face/Zscaler blocks MiniLM. Prefer graded MiniLM runs on the Ubuntu Prayogshala VM.

---

## What `run_all.py` executes

1. Task 1 data  
2. `pytest` BM25/RRF tests  
3. Indexes 128 & 512  
4. Session A → separate process Session B (`hybrid_mem`)  
5. STM `full` / `trim` / `summary` + plot  
6. Ablation (unless skipped)  
7. Cost + HNSW (unless skipped)  

## Environment knobs

| Variable | Meaning |
|----------|---------|
| unset `RECALLBOT_EMBED_BACKEND` | MiniLM (Prayogshala) |
| `RECALLBOT_EMBED_BACKEND=hash` | Offline hashing (local Windows) |
| `RECALLBOT_LLM=auto` / `template` | Ollama vs template NLG |
| `MPLBACKEND=Agg` | Headless plots |
| `SKIP_ABLATION=1` / `SKIP_HNSW=1` | Shorter bootstrap |

## Integrity

- Session B = **separate process**  
- Do not hand-edit `logs/calls.jsonl`  
- `python3 -m pytest tests/` must pass  
