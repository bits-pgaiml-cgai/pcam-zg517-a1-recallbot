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
| Embedding | `all-MiniLM-L6-v2`, dim 384, mean pooling |
| Index | flat NumPy cosine (corpus small; HNSW optional later) |

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## Reproduce runs

```bash
# 1) Task 1 data (KB + conversation + probes)
python scripts/generate_task1_data.py

# 2) BM25 / RRF CS4 tests
python -m pytest tests/ -q

# 3) Build chunk indexes (128 and 512)
python -m src.build_index

# 4) Hit-rate table
python -m src.eval_retrieval

# 5) Session A then Session B as SEPARATE processes (hybrid_mem)
python -m src.run_session --session A --config hybrid_mem --run-id r_hm_A
python -m src.run_session --session B --config hybrid_mem --run-id r_hm_B

# 6) STM strategies on Session A
python -m src.run_session --session A --config full --run-id r_full_A
python -m src.run_session --session A --config trim --run-id r_trim_A
python -m src.run_session --session A --config summary --run-id r_sum_A
python -m src.plot_tokens

# 7) Ablation configs (A then B each)
python -m src.run_session --session A --config no_rag --run-id r_nr_A
python -m src.run_session --session B --config no_rag --run-id r_nr_B
python -m src.run_session --session A --config hybrid --run-id r_hy_A
python -m src.run_session --session B --config hybrid --run-id r_hy_B
python -m src.run_session --session A --config hybrid_sem --run-id r_hs_A
python -m src.run_session --session B --config hybrid_sem --run-id r_hs_B

# 8) Probes
python -m src.eval_probes --config hybrid_mem --run-id r_probes
```

## Architecture (function map)

NLU `src.nlu.parse_utterance` → state `DialogueState.update_from_nlu` → dialogue manager `DialogueManager.handle_turn` → tools `search_kb` / `get_appointment` / `book_slot` → memories `SemanticMemory` / `EpisodicMemory` → NLG `generate_reply`.

Procedural memory lives in `skills/` and is loaded at run time.

## Integrity

- Session B is a separate process; memory loads from `memory/`.
- `logs/calls.jsonl` is append-only from code.
- BM25, RRF, episodic score, chunker, state tracker, DM, and memory CRUD are implemented here (no LangChain/LlamaIndex memory/hybrid).

## LMS zip

`<BITS_ID>_V31_MP1.zip`
