# Run RecallBot on BITS Prayogshala

Portal: https://prayogshala.bits-pilani.ac.in  
Repo: https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot  
Variant: **V31** clinic appointment desk · Twist B time-bound facts

Use Prayogshala when local Hugging Face / Ollama downloads fail (Zscaler TLS).

## Quick path (Linux VM)

```bash
mkdir -p ~/Workspace/cgai-mp1 && cd ~/Workspace/cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
bash scripts/prayogshala_bootstrap.sh
```

## Quick path (Windows VM)

```powershell
mkdir D:\cgai-mp1 -Force
cd D:\cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
powershell -ExecutionPolicy Bypass -File scripts/prayogshala_bootstrap.ps1
```

## What the bootstrap runs

1. `pytest` BM25/RRF CS4 tests  
2. Rebuild MiniLM indexes (128 & 512)  
3. Session A → **new process** Session B (`hybrid_mem`)  
4. STM `full` / `trim` / `summary` + token plot  
5. Ablation `no_rag` → `hybrid_mem` + probe CSVs  
6. Task 5 cost + flat vs HNSW on 100k vectors  

## Environment knobs

| Variable | Meaning |
|----------|---------|
| unset `RECALLBOT_EMBED_BACKEND` | Use `sentence-transformers/all-MiniLM-L6-v2` (Prayogshala default) |
| `RECALLBOT_EMBED_BACKEND=hash` | Offline hashing fallback (local Zscaler) |
| `RECALLBOT_LLM=auto` | Try Ollama chat; else template NLG |
| `RECALLBOT_LLM=template` | Force template NLG |
| `OLLAMA_MODEL` | e.g. `qwen2.5:1.5b-instruct` or `qwen3:1.7b` |

## Integrity reminders for viva

- Session B is a **separate process** (`python -m src.run_session --session B ...`).
- Do not hand-edit `logs/calls.jsonl`.
- `python -m pytest tests/` must pass before zip.

## After the run — copy out before ending the VM

Zip at least:

- `logs/calls.jsonl`
- `results/`
- `memory/`
- `index/`
- `db/`

Save under **Workspace** (Linux) or **D:\\** (Windows).
