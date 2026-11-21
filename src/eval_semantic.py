"""Semantic memory extraction precision/recall against Task 1 planted facts."""

from __future__ import annotations

import json

from src.config import DATA_DIR, MEMORY_DIR, RESULTS_DIR
from src.memory.semantic import SemanticMemory


def main():
    conv = json.loads((DATA_DIR / "test_conversation.json").read_text(encoding="utf-8"))
    gold = conv.get("facts", [])
    mem = SemanticMemory(MEMORY_DIR / "semantic_U1.json")
    precision, recall = mem.precision_recall(gold, user_id="U1")
    out = {
        "precision": precision,
        "recall": recall,
        "active_facts": mem.active_facts("U1"),
        "gold_count": len([g for g in gold if g.get("value") is not None and not g.get("forget")]),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "semantic_precision_recall.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("precision", "recall", "gold_count")}, indent=2))
    print("Wrote", path)


if __name__ == "__main__":
    main()
