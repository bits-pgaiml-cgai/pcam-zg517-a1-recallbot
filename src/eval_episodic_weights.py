"""Compare two episodic retrieval weightings on E probes (Task 3d)."""

from __future__ import annotations

import json

from src.config import DATA_DIR, MEMORY_DIR, RESULTS_DIR
from src.memory.episodic import EpisodicMemory


def score_probes(weights, probes, mem: EpisodicMemory):
    hits = 0
    details = []
    for p in probes:
        ranked = mem.retrieve("U1", p["question"], top_k=3, weights=weights)
        text = " ".join(e.get("text", "") for e in ranked).lower()
        expected_bits = [t for t in p["expected"].lower().replace(",", " ").split() if len(t) > 3][:3]
        ok = any(b in text for b in expected_bits) if expected_bits else False
        hits += int(ok)
        details.append({"probe_id": p["probe_id"], "hit": int(ok), "top": [e.get("text", "")[:80] for e in ranked]})
    return hits / max(1, len(probes)), details


def main():
    probes = [
        p
        for p in json.loads((DATA_DIR / "probes.json").read_text(encoding="utf-8"))
        if p.get("category") == "E"
    ]
    mem = EpisodicMemory(MEMORY_DIR / "episodic_U1.jsonl")
    w_balanced = (1.0, 1.0, 1.0)
    w_relevance = (0.5, 0.5, 2.0)
    acc_b, det_b = score_probes(w_balanced, probes, mem)
    acc_r, det_r = score_probes(w_relevance, probes, mem)
    keep = "relevance-heavy" if acc_r >= acc_b else "balanced"
    out = {
        "balanced_weights": w_balanced,
        "relevance_heavy_weights": w_relevance,
        "balanced_accuracy": acc_b,
        "relevance_heavy_accuracy": acc_r,
        "kept": keep,
        "justification": (
            "Keep relevance-heavy when E probes need semantic match to bookings/complaints; "
            "otherwise keep balanced so recent high-importance events still surface."
            if keep == "relevance-heavy"
            else "Balanced weights recover recent high-importance episodes without over-fitting query wording."
        ),
        "balanced_details": det_b,
        "relevance_details": det_r,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "episodic_weights.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in out if "details" not in k}, indent=2))
    print("Wrote", path)


if __name__ == "__main__":
    main()
