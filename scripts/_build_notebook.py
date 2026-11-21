import json
from pathlib import Path


def md(src: str, cid: str):
    lines = src.strip("\n").split("\n")
    return {
        "cell_type": "markdown",
        "id": cid,
        "metadata": {},
        "source": [ln + "\n" for ln in lines],
    }


def code(src: str, cid: str):
    lines = src.strip("\n").split("\n")
    return {
        "cell_type": "code",
        "id": cid,
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [ln + "\n" for ln in lines],
    }


cells = []

cells.append(
    md(
        """
# RecallBot V31 — Clinic Appointment Desk

**Course:** PCA MZG517 Conversational Generative AI · **Mini Project 1**  
**Author:** Venkata Srinivasa Rao Tunuguntla · **Variant:** V31 (individual)

| Field | Value |
|-------|--------|
| Domain | Clinic appointment desk |
| Twist | B. Time-bound facts |
| Window k | 5 |
| Context window | 4,096 tokens |
| Scale | 5,000 daily users |

This notebook is a **walkthrough + evidence runner** for the `pcam-zg517-a1-recallbot` package. Core BM25, RRF, dialogue, and memory logic live in `src/` (not LangChain/LlamaIndex).

**Where to run**

| Environment | Notes |
|-------------|--------|
| **Google Colab** | Use the Colab bootstrap cell below (clone + pip). MiniLM usually works. Ollama is not available → template NLG. |
| **Prayogshala Ubuntu** | Preferred for LMS evidence; use `scripts/prayogshala_bootstrap.sh`. |
| **Local Windows** | If Hugging Face is blocked, set `RECALLBOT_EMBED_BACKEND=hash`. |
""",
        "c00",
    )
)

cells.append(
    md(
        """
## 0a. Google Colab bootstrap (run first on Colab only)

Skip this section on Prayogshala / local Jupyter if the repo is already checked out.

1. Runtime → **CPU** is enough (GPU optional).  
2. Run the next cell once per new runtime.  
3. It clones the public GitHub repo, installs deps, and `cd`s into the project root.  
4. Optional: mount Google Drive and copy `logs/`, `results/`, `memory/` out before the runtime disconnects.
""",
        "c01a",
    )
)

cells.append(
    code(
        """
# === Google Colab bootstrap ===
import os
import subprocess
import sys
from pathlib import Path

IN_COLAB = False
try:
    import google.colab  # noqa: F401
    IN_COLAB = True
except Exception:
    IN_COLAB = False

REPO_URL = "https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot.git"
REPO_NAME = "pcam-zg517-a1-recallbot"

if IN_COLAB:
    print("Detected Google Colab")
    os.chdir("/content")
    repo_dir = Path("/content") / REPO_NAME
    if not (repo_dir / "src").exists():
        subprocess.check_call(["git", "clone", REPO_URL])
    else:
        print("Repo already present — pull latest")
        subprocess.check_call(["git", "-C", str(repo_dir), "pull", "--ff-only"])
    os.chdir(repo_dir)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    # Colab has no Ollama — force template NLG
    os.environ["RECALLBOT_LLM"] = "template"
    # Prefer MiniLM on Colab (HF usually works). Uncomment only if download fails:
    # os.environ["RECALLBOT_EMBED_BACKEND"] = "hash"
    print("Installed requirements and moved into", repo_dir)
else:
    print("Not Colab — assuming repo checkout / Prayogshala / local Jupyter")

print("cwd =", Path.cwd().resolve())
""",
        "c01b",
    )
)

cells.append(
    code(
        """
# Optional on Colab: persist artifacts to Google Drive before runtime ends
# from google.colab import drive
# drive.mount("/content/drive")
# !mkdir -p /content/drive/MyDrive/RecallBot_V31_artifacts
# !cp -r logs results memory index db /content/drive/MyDrive/RecallBot_V31_artifacts/
""",
        "c01c",
    )
)

cells.append(
    md(
        """
## 0b. Project root + environment

Works after Colab bootstrap, or when the notebook is opened from the repo / `notebooks/`.
""",
        "c01",
    )
)

cells.append(
    code(
        """
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("RECALLBOT_LLM", os.environ.get("RECALLBOT_LLM", "template"))

# Local Windows / Zscaler only:
# os.environ["RECALLBOT_EMBED_BACKEND"] = "hash"

ROOT = Path.cwd()
candidates = [
    ROOT,
    ROOT.parent,
    Path("/content/pcam-zg517-a1-recallbot"),
    ROOT / "pcam-zg517-a1-recallbot",
]
for cand in candidates:
    if (cand / "src").exists() and (cand / "requirements.txt").exists():
        ROOT = cand
        os.chdir(ROOT)
        break

print("ROOT =", ROOT.resolve())
assert (ROOT / "src").exists(), "Repo root with src/ not found — run the Colab bootstrap cell first"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
""",
        "c02",
    )
)

cells.append(
    code(
        """
# Non-Colab optional install (Prayogshala/local venv usually already has deps):
# %pip -q install -r requirements.txt
print("Python", sys.version.split()[0], "| embed backend env =", os.environ.get("RECALLBOT_EMBED_BACKEND", "<auto MiniLM>"))
""",
        "c03",
    )
)

cells.append(
    md(
        """
## 1. Variant + architecture

Pipeline: **NLU → state tracker → dialogue manager → tools → memories → NLG**

- Tools: `search_kb` (hybrid), `get_appointment`, `book_slot` (confirm first)
- Twist B: filter by `valid_from` / `valid_to`
- For LMS integrity, Session B should be a **separate OS process**; this notebook also shows reload-from-disk
""",
        "c04",
    )
)

cells.append(
    code(
        """
from src.config import (
    VARIANT, DOMAIN, TWIST, WINDOW_K, CONTEXT_WINDOW, SCALE_DAILY_USERS,
    EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_POOLING, AS_OF_DATE_DEFAULT,
)
from src.embeddings import embed_backend

print({
    "variant": VARIANT,
    "domain": DOMAIN,
    "twist": TWIST,
    "window_k": WINDOW_K,
    "context_window": CONTEXT_WINDOW,
    "scale": SCALE_DAILY_USERS,
    "embedding_model": EMBEDDING_MODEL,
    "dim": EMBEDDING_DIM,
    "pooling": EMBEDDING_POOLING,
    "as_of": AS_OF_DATE_DEFAULT,
    "embed_backend": embed_backend(),
})
""",
        "c05",
    )
)

cells.append(
    md(
        """
## 2. Task 1 data + CS4 BM25 / RRF tests
""",
        "c06",
    )
)

cells.append(
    code(
        """
import subprocess
subprocess.check_call([sys.executable, "scripts/generate_task1_data.py"], cwd=ROOT)
subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=ROOT)

from src.bm25 import bm25_cs4_worked_example_score
from src.rrf import rrf_cs4_example
print("BM25 CS4 score ≈", round(bm25_cs4_worked_example_score(), 3))
print("RRF ranking:", [d for d, _ in rrf_cs4_example()])
""",
        "c07",
    )
)

cells.append(
    md(
        """
## 3. Chunking, indexing, hit rate@k
""",
        "c08",
    )
)

cells.append(
    code(
        """
from src.logging_util import set_run_id
from src.retrieval import build_all_indexes
from src.eval_retrieval import main as eval_retrieval_main

set_run_id("nb_index")
indexes = build_all_indexes(as_config="hybrid")
for size, idx in indexes.items():
    print(f"chunk_size={size} chunks={len(idx.chunks)}")
eval_retrieval_main()
""",
        "c09",
    )
)

cells.append(
    code(
        """
import pandas as pd
hr = pd.read_csv(ROOT / "results" / "hit_rate.csv")
summary = (
    hr.groupby(["method", "chunk_size", "k", "qtype"])["hit"]
      .mean()
      .reset_index()
      .rename(columns={"hit": "hit_rate"})
)
display(summary.sort_values(["chunk_size", "method", "k", "qtype"]).head(40))
""",
        "c10",
    )
)

cells.append(
    md(
        """
## 4. NLU accuracy + state fields (Task 2a)
""",
        "c11",
    )
)

cells.append(
    code(
        """
from src.eval_nlu import main as eval_nlu_main
from src.nlu import LABELLED_UTTERANCES, nlu_accuracy
from src.state import STATE_FIELDS

eval_nlu_main()
print("NLU accuracy:", round(nlu_accuracy(LABELLED_UTTERANCES), 3), "on", len(LABELLED_UTTERANCES))
print("State fields:", STATE_FIELDS)
""",
        "c12",
    )
)

cells.append(
    md(
        """
## 5. Session A (`hybrid_mem`)

Booking confirmation, user facts, KB questions, complaint episode, end-of-session reflection.
""",
        "c13",
    )
)

cells.append(
    code(
        """
import json
from src.tools import init_db
from src.dialogue import DialogueManager
from src.retrieval import load_index
from src.config import MEMORY_DIR, DATA_DIR, DB_DIR

for p in MEMORY_DIR.glob("*"):
    if p.name != ".gitkeep" and p.is_file():
        p.unlink()
db = DB_DIR / "clinic.sqlite"
if db.exists():
    db.unlink()
init_db()

set_run_id("nb_hm_A")
index = load_index(512)
dm = DialogueManager(
    index, config="hybrid_mem", stm_strategy="trim", user_id="U1",
    enable_rag=True, enable_semantic=True, enable_episodic=True,
)

conv = json.loads((DATA_DIR / "test_conversation.json").read_text(encoding="utf-8"))
lo, hi = conv["session_a_turns"]
user_turns = [t for t in conv["turns"] if t["role"] == "user" and lo <= t["turn"] <= hi]

for t in user_turns:
    out = dm.handle_turn(t["text"], session="A", turn=t["turn"])
    print(f"[{t['turn']}] USER: {t['text']}")
    print(f"[{t['turn']}] BOT : {out['reply'][:220]}")
    print()

ref = dm.end_session_reflection("A", turn=hi)
print("Reflection:", (ref or {}).get("text"))
""",
        "c14",
    )
)

cells.append(
    md(
        """
## 6. Session B — new DialogueManager (reload from disk)

Simulates a process restart by constructing a fresh manager that reads `memory/`.
For LMS logs, also run `python -m src.run_session --session B ...` in a separate shell.
""",
        "c15",
    )
)

cells.append(
    code(
        """
set_run_id("nb_hm_B")
dm_b = DialogueManager(
    load_index(512), config="hybrid_mem", stm_strategy="trim", user_id="U1",
    enable_rag=True, enable_semantic=True, enable_episodic=True,
)

lo, hi = conv["session_b_turns"]
user_turns_b = [t for t in conv["turns"] if t["role"] == "user" and lo <= t["turn"] <= hi]
show = {26, 28, 30, 32, 34, 36, 40}
for t in user_turns_b:
    if t["turn"] not in show:
        continue
    out = dm_b.handle_turn(t["text"], session="B", turn=t["turn"])
    print(f"[{t['turn']}] USER: {t['text']}")
    print(f"[{t['turn']}] BOT : {out['reply'][:240]}")
    print()

table = dm_b.context_assembly_table("What is the refund window for plan P-204?")
display(pd.DataFrame(table))
""",
        "c16",
    )
)

cells.append(
    md(
        """
## 7. Probes + semantic / episodic evals
""",
        "c17",
    )
)

cells.append(
    code(
        """
subprocess.check_call([sys.executable, "-m", "src.eval_probes", "--config", "hybrid_mem", "--run-id", "nb_probes"], cwd=ROOT)
subprocess.check_call([sys.executable, "-m", "src.eval_semantic"], cwd=ROOT)
subprocess.check_call([sys.executable, "-m", "src.eval_episodic_weights"], cwd=ROOT)

probes = pd.read_csv(ROOT / "results" / "probe_results_hybrid_mem.csv")
print("Probe accuracy:", probes["correct"].astype(int).mean())
display(probes[["probe_id", "category", "correct", "answer"]].head(20))
""",
        "c18",
    )
)

cells.append(
    md(
        """
## 8. Short-term memory strategies (demo)
""",
        "c19",
    )
)

cells.append(
    code(
        """
for cfg in ("full", "trim", "summary"):
    set_run_id(f"nb_{cfg}_A")
    dm_stm = DialogueManager(
        load_index(512), config=cfg, stm_strategy=cfg, user_id="U1",
        enable_rag=True, enable_semantic=True, enable_episodic=True,
    )
    for t in user_turns[:8]:
        dm_stm.handle_turn(t["text"], session="A", turn=t["turn"])
    print("Finished STM strategy:", cfg)

subprocess.check_call([sys.executable, "-m", "src.plot_tokens"], cwd=ROOT)
from IPython.display import Image, display
plot_path = ROOT / "results" / "plots" / "stm_tokens.png"
if plot_path.exists():
    display(Image(filename=str(plot_path)))
""",
        "c20",
    )
)

cells.append(
    md(
        """
## 9. Task 5 — cost + flat vs HNSW
""",
        "c21",
    )
)

cells.append(
    code(
        """
subprocess.check_call([sys.executable, "-m", "src.cost_scale"], cwd=ROOT)
cost = json.loads((ROOT / "results" / "cost_scale.json").read_text(encoding="utf-8"))
print(json.dumps(cost, indent=2)[:2500])
""",
        "c22",
    )
)

cells.append(
    md(
        """
## 10. Twist B — time-bound retrieval check
""",
        "c23",
    )
)

cells.append(
    code(
        """
idx = load_index(512)
q = "What is the refund window for plan P-204?"
print("as_of 2026 →", [(h["doc_id"], h.get("version")) for h in idx.hybrid_rank(q, top_k=3, as_of="2026-11-21")])
print("as_of 2025 →", [(h["doc_id"], h.get("version")) for h in idx.hybrid_rank(q, top_k=3, as_of="2025-06-01")])
q2 = "Is WAIT-48 still the new-patient wait target?"
print("WAIT-48@2026 →", [(h["doc_id"], h.get("version")) for h in idx.hybrid_rank(q2, top_k=3, as_of="2026-11-21")])
""",
        "c24",
    )
)

cells.append(
    md(
        """
## 11. LMS CLI reminder + surprise probes

```bash
python -m src.run_session --session A --config hybrid_mem --run-id r_hm_A
python -m src.run_session --session B --config hybrid_mem --run-id r_hm_B
python -m src.eval_probes --config hybrid_mem --probes surprise_probes.json --run-id r_surprise
```

Fill `data/surprise_probes.json` after the LMS release on 24/11/2026.
""",
        "c25",
    )
)

cells.append(
    code(
        """
print("Notebook complete. Artifact check:")
for rel in [
    "logs/calls.jsonl",
    "results/hit_rate.csv",
    "results/probe_results.csv",
    "results/cost_scale.json",
    "memory/semantic_U1.json",
    "memory/episodic_U1.jsonl",
]:
    p = ROOT / rel
    print(" ", "OK" if p.exists() else "MISSING", rel)
""",
        "c26",
    )
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "cells": cells,
}

out = Path(__file__).resolve().parents[1] / "notebooks" / "RecallBot_V31_Clinic_Desk.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("Wrote", out, "cells=", len(cells))
