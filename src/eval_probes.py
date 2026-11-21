"""Run probes against a fresh DialogueManager (expects memory already from Session A if needed)."""

from __future__ import annotations

import argparse
import csv
import json
import re

from src.config import DATA_DIR, RESULTS_DIR
from src.dialogue import DialogueManager
from src.logging_util import set_run_id
from src.retrieval import load_index


def judge(answer: str, expected: str) -> int:
    a = answer.lower()
    e = expected.lower()
    if "does not know" in e or "not on file" in e or "fallback" in e:
        return int(
            "do not have" in a
            or "not have" in a
            or "not on file" in a
            or "do not know" in a
        )
    tokens = [t for t in re.split(r"[^a-z0-9\-]+", e) if len(t) > 2][:4]
    return int(any(t in a for t in tokens) or e[:20] in a)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="hybrid_mem")
    parser.add_argument("--run-id", default="r_probes")
    parser.add_argument("--chunk-size", type=int, default=512)
    args = parser.parse_args()
    set_run_id(args.run_id)

    probes = json.loads((DATA_DIR / "probes.json").read_text(encoding="utf-8"))
    index = load_index(args.chunk_size)

    flags = {
        "no_rag": (False, False, False),
        "hybrid": (True, False, False),
        "hybrid_sem": (True, True, False),
        "hybrid_mem": (True, True, True),
        "full": (True, True, True),
        "trim": (True, True, True),
        "summary": (True, True, True),
    }
    rag, sem, epi = flags.get(args.config, (True, True, True))
    stm = args.config if args.config in {"full", "trim", "summary"} else "trim"

    dm = DialogueManager(
        index,
        config=args.config,
        stm_strategy=stm,
        enable_rag=rag,
        enable_semantic=sem,
        enable_episodic=epi,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, p in enumerate(probes, start=1):
        out = dm.handle_turn(p["question"], session=p.get("session", "B"), turn=900 + i)
        correct = judge(out["reply"], p["expected"])
        rows.append(
            {
                "run_id": args.run_id,
                "config": args.config,
                "probe_id": p["probe_id"],
                "category": p["category"],
                "expected": p["expected"],
                "answer": out["reply"],
                "correct": correct,
                "judged_by": "manual",
            }
        )
        print(p["probe_id"], correct, out["reply"][:100])

    out_path = RESULTS_DIR / "probe_results.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "config",
                "probe_id",
                "category",
                "expected",
                "answer",
                "correct",
                "judged_by",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    acc = sum(r["correct"] for r in rows) / len(rows)
    print(f"accuracy={acc:.3f} wrote {out_path}")


if __name__ == "__main__":
    main()
