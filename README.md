# pcam-zg517-a1-recallbot

**BITS Pilani WILP · PGAIML · PCA MZG517 Conversational Generative AI**  
**Mini Project 1 · Variant V31 · Individual**  
**Domain:** Clinic appointment desk  
**Twist:** B. Time-bound facts  
**Window k:** 5 turns · **Context window:** 4,096 tokens · **Scale:** 5,000 daily users

**Author:** Venkata Srinivasa Rao Tunuguntla (`venkat-tunuguntla`)  
**GitHub:** [bits-pgaiml-cgai/pcam-zg517-a1-recallbot](https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot)

RecallBot answers clinic policy/FAQ questions with hybrid retrieval (own BM25 + dense + RRF), completes appointment booking with confirm-before-write, and remembers a returning user across Session A → process restart → Session B.

## Variant

| Item | Value |
|------|--------|
| Domain | Clinic appointment desk |
| Twist | Time-bound facts (`valid_from` / `valid_to`) |
| Trim window `k` | 5 |
| Context window | 4,096 tokens |
| Daily users (Task 5) | 5,000 |
| Embedding | `all-MiniLM-L6-v2`, dim 384, mean pooling (hash fallback if HF blocked) |
| Index | flat NumPy + FAISS HNSW experiment (`src.cost_scale`) |

## Where to run

| Environment | OS | Script |
|-------------|----|--------|
| **Prayogshala** (graded MiniLM runs) | **Ubuntu VM only** | `scripts/prayogshala_bootstrap.sh` |
| **Local PC** (dev / Zscaler) | **Windows** | `scripts/local_windows_bootstrap.ps1` |

Full Prayogshala guide: [`docs/PRAYOGSHALA_SETUP.md`](docs/PRAYOGSHALA_SETUP.md).

### Prayogshala (Ubuntu VM)

```bash
mkdir -p ~/Workspace/cgai-mp1 && cd ~/Workspace/cgai-mp1
git clone https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git
cd pcam-zg517-a1-recallbot
chmod +x scripts/prayogshala_bootstrap.sh
bash scripts/prayogshala_bootstrap.sh .
```

Faster smoke:

```bash
SKIP_ABLATION=1 SKIP_HNSW=1 bash scripts/prayogshala_bootstrap.sh .
```

### Local Windows PC

```powershell
cd <path>\pcam-zg517-a1-recallbot
powershell -ExecutionPolicy Bypass -File scripts\local_windows_bootstrap.ps1
```

Local default uses `RECALLBOT_EMBED_BACKEND=hash` when Hugging Face is blocked. Prefer Prayogshala Ubuntu for MiniLM evidence.

## Reproduce runs (manual)

```bash
python scripts/generate_task1_data.py
python -m pytest tests/ -q
python -m src.build_index
python -m src.eval_nlu
python -m src.eval_retrieval

# Session A then Session B as SEPARATE processes
python -m src.run_session --session A --config hybrid_mem --run-id r_hm_A
python -m src.run_session --session B --config hybrid_mem --run-id r_hm_B
python -m src.eval_probes --config hybrid_mem --run-id r_hm_probes
python -m src.eval_semantic
python -m src.eval_episodic_weights

# STM strategies
python -m src.run_session --session A --config full --run-id r_full_A
python -m src.run_session --session A --config trim --run-id r_trim_A
python -m src.run_session --session A --config summary --run-id r_sum_A
python -m src.plot_tokens

# Ablation
python -m src.run_session --session A --config no_rag --run-id r_nr_A
python -m src.run_session --session B --config no_rag --run-id r_nr_B
python -m src.eval_probes --config no_rag --run-id r_nr_probes
# ... hybrid, hybrid_sem, hybrid_mem similarly
python -m src.eval_ablation

# Task 5
python -m src.cost_scale

# Surprise probes (after 24/11/2026 LMS release)
python -m src.eval_probes --config hybrid_mem --probes surprise_probes.json --run-id r_surprise
```

## Notebook

Walkthrough + evidence runner:

[`notebooks/RecallBot_V31_Clinic_Desk.ipynb`](notebooks/RecallBot_V31_Clinic_Desk.ipynb)

**Google Colab:** open the notebook (or upload it), run the **Colab bootstrap** cell first (clones the public repo + installs deps). Keep `RECALLBOT_LLM=template` (no Ollama on Colab). Copy `logs/ results/ memory/` to Drive before the runtime ends.

```bash
# Ubuntu Prayogshala
source .venv/bin/activate
jupyter notebook notebooks/RecallBot_V31_Clinic_Desk.ipynb
```

```powershell
# Local Windows
.\.venv\Scripts\Activate.ps1
jupyter notebook notebooks\RecallBot_V31_Clinic_Desk.ipynb
```

## Architecture (function map)

NLU `src.nlu.parse_utterance` → state `DialogueState.update_from_nlu` → dialogue manager `DialogueManager.handle_turn` → tools `search_kb` / `get_appointment` / `book_slot` → memories `SemanticMemory` / `EpisodicMemory` → NLG `generate_reply` (Ollama if up, else template).

Procedural memory: `skills/system_prompt_v1.md`, `skills/book_appointment_steps_v1.md`.

## Decoding

| Turn type | Setting |
|-----------|---------|
| Task / booking / KB | temperature 0 (greedy) |
| Open chitchat | temperature 0.3 |

## Integrity

- Session B is a **separate process**; memory loads from `memory/`.
- `logs/calls.jsonl` is append-only from code.
- BM25, RRF, episodic score, chunker, state tracker, DM, and memory CRUD are implemented here (no LangChain/LlamaIndex memory/hybrid).

## LMS zip

`<BITS_ID>_V31_MP1.zip`
