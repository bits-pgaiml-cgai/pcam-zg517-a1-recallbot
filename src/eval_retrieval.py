"""Compute hit rate@k for dense, BM25, hybrid at both chunk sizes."""

from __future__ import annotations

import csv
import json

from src.config import AS_OF_DATE_DEFAULT, DATA_DIR, RESULTS_DIR
from src.logging_util import set_run_id
from src.retrieval import load_index


def hit(chunk_text: str, gold_span: str) -> int:
    return int(gold_span.lower() in chunk_text.lower())


def eval_method(index, questions, method: str, k_values=(1, 3, 5), as_of=AS_OF_DATE_DEFAULT):
    rows = []
    for q in questions:
        if method == "dense":
            ranked = index.dense_rank(q["question"], top_k=max(k_values), as_of=as_of)
            chunks = [index.chunks[i] for i, _ in ranked]
        elif method == "bm25":
            ranked = index.bm25_rank(q["question"], top_k=max(k_values), as_of=as_of)
            chunks = [index.chunks[i] for i, _ in ranked]
        else:
            chunks = index.hybrid_rank(q["question"], top_k=max(k_values), as_of=as_of)
        for k in k_values:
            top = chunks[:k]
            is_hit = any(hit(c["text"], q["gold_span"]) or c.get("doc_id") == q["doc_id"] for c in top)
            rows.append(
                {
                    "method": method,
                    "chunk_size": index.chunk_size,
                    "k": k,
                    "question_id": q["question_id"],
                    "qtype": q.get("type", ""),
                    "hit": int(is_hit),
                }
            )
    return rows


def main():
    set_run_id("r_hitrate")
    questions = json.loads((DATA_DIR / "kb_questions.json").read_text(encoding="utf-8"))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for size in (128, 512):
        index = load_index(size)
        for method in ("dense", "bm25", "hybrid"):
            all_rows.extend(eval_method(index, questions, method))

    out = RESULTS_DIR / "hit_rate.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["method", "chunk_size", "k", "question_id", "qtype", "hit"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary print
    from collections import defaultdict

    agg = defaultdict(list)
    for r in all_rows:
        key = (r["method"], r["chunk_size"], r["k"], r["qtype"])
        agg[key].append(r["hit"])
    print("method chunk k qtype hit_rate")
    for key, vals in sorted(agg.items()):
        print(key, sum(vals) / len(vals))
    print("Wrote", out)


if __name__ == "__main__":
    main()
