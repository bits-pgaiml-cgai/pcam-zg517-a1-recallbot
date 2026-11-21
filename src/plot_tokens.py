"""Plot input tokens per turn for full/trim/summary from calls.jsonl."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.config import LOGS_DIR, RESULTS_DIR


def main():
    path = LOGS_DIR / "calls.jsonl"
    if not path.exists():
        print("No logs yet")
        return
    by = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("call_type") != "chat":
            continue
        if rec.get("config") in {"full", "trim", "summary"}:
            by[rec["config"]].append((rec["turn"], rec["input_tokens"]))

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 4))
    for cfg, pts in sorted(by.items()):
        pts = sorted(pts)
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=cfg)
    plt.xlabel("turn")
    plt.ylabel("input_tokens")
    plt.title("STM strategies: input tokens per turn")
    plt.legend()
    out = RESULTS_DIR / "plots" / "stm_tokens.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out)
    print("Wrote", out)


if __name__ == "__main__":
    main()
