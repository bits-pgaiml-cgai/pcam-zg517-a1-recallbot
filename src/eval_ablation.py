"""Summarise ablation configs from calls.jsonl + probe_results (Task 4a)."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from src.config import LOGS_DIR, RESULTS_DIR


CONFIGS = ["no_rag", "hybrid", "hybrid_sem", "hybrid_mem"]


def _latency_and_tokens():
    path = LOGS_DIR / "calls.jsonl"
    stats = {c: {"inputs": [], "latencies": [], "total_tokens": 0} for c in CONFIGS}
    if not path.exists():
        return stats
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        cfg = rec.get("config")
        if cfg not in stats:
            continue
        if rec.get("call_type") == "chat":
            stats[cfg]["inputs"].append(rec.get("input_tokens", 0))
        stats[cfg]["latencies"].append(rec.get("latency_ms", 0))
        stats[cfg]["total_tokens"] += rec.get("input_tokens", 0) + rec.get("output_tokens", 0)
    return stats


def _median(xs):
    if not xs:
        return None
    ys = sorted(xs)
    mid = len(ys) // 2
    return ys[mid] if len(ys) % 2 else 0.5 * (ys[mid - 1] + ys[mid])


def main():
    stats = _latency_and_tokens()
    probe_path = RESULTS_DIR / "probe_results.csv"
    by_cfg_cat = defaultdict(lambda: defaultdict(list))
    if probe_path.exists():
        with open(probe_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                by_cfg_cat[row["config"]][row["category"]].append(int(row["correct"]))

    table = []
    for cfg in CONFIGS:
        cats = {
            cat: (sum(vals) / len(vals) if vals else None)
            for cat, vals in by_cfg_cat.get(cfg, {}).items()
        }
        overall = None
        flat = [v for vals in by_cfg_cat.get(cfg, {}).values() for v in vals]
        if flat:
            overall = sum(flat) / len(flat)
        inputs = stats[cfg]["inputs"]
        table.append(
            {
                "config": cfg,
                "accuracy_overall": overall,
                "accuracy_by_category": cats,
                "mean_input_tokens_per_chat_turn": (sum(inputs) / len(inputs)) if inputs else None,
                "median_latency_ms": _median(stats[cfg]["latencies"]),
                "total_tokens_logged": stats[cfg]["total_tokens"],
            }
        )

    out = {
        "table": table,
        "notes": (
            "Run Session A/B for each config, then eval_probes per config, before relying on this table. "
            "Rubric scores (coherence/relevance/groundedness/safety) can be added manually or via LLM judge."
        ),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "ablation_summary.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("Wrote", path)


if __name__ == "__main__":
    main()
