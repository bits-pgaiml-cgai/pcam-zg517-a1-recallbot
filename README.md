# pcam-zg517-a1-recallbot

**BITS Pilani WILP · PGAIML · PCA MZG517 Conversational Generative AI**  
**Mini Project 1 · Variant V31 · Individual**  
**Domain:** Clinic appointment desk  
**Twist:** B. Time-bound facts  
**Window k:** 5 turns · **Context window:** 4,096 tokens · **Scale:** 5,000 daily users

**Author:** Venkata Srinivasa Rao Tunuguntla (`venkat-tunuguntla`)  
**GitHub:** [bits-pgaiml-cgai/pcam-zg517-a1-recallbot](https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot)

RecallBot is a task-oriented assistant that answers from a clinic knowledge base with hybrid retrieval (dense + BM25 + RRF), completes an appointment booking via slot filling, and remembers a returning user across Session A and Session B with semantic and episodic memory.

## Variant constraints

| Item | Value |
|------|--------|
| Domain | Clinic appointment desk |
| Twist | Time-bound facts (validity dates on docs and user facts) |
| Trim window `k` | 5 |
| Context window | 4,096 tokens |
| Daily users (Task 5) | 5,000 |

## Repository layout

```text
pcam-zg517-a1-recallbot/
  README.md
  requirements.txt
  src/                 # dialogue pipeline, retrieval, memory
  skills/              # procedural memory (system prompt, task steps)
  tests/               # BM25 and RRF CS4 worked-example tests
  data/kb/             # domain knowledge-base documents
  data/test_conversation.json
  data/kb_questions.json
  data/probes.json
  data/surprise_probes.json
  db/                  # SQLite / JSON back-end
  index/               # KB vector index
  memory/              # semantic + episodic stores (persist across sessions)
  logs/calls.jsonl
  results/probe_results.csv
  results/hit_rate.csv
  results/plots/
  docs/
  report.pdf           # at most 8 pages + appendices (submission)
  video_link.txt
```

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## Reproduce runs

Commands will be filled as modules land. Planned entry points:

```bash
# BM25 / RRF unit tests (CS4 examples)
python -m pytest tests/

# Session A / B with a config: full | trim | summary | no_rag | hybrid | hybrid_sem | hybrid_mem
python -m src.run_session --session A --config hybrid_mem --user U1

# Hit-rate table
python -m src.eval_retrieval

# Probe evaluation
python -m src.eval_probes --config hybrid_mem
```

## Integrity notes

- Session B must run as a **separate process**; memory is loaded from disk under `memory/`.
- Every LLM, embedding, and tool call appends one line to `logs/calls.jsonl` (never hand-edited).
- Core BM25, RRF, episodic scoring, and memory CRUD are implemented in this repo (no LangChain/LlamaIndex memory or hybrid search).

## LMS zip name

`<BITS_ID>_V31_MP1.zip`
