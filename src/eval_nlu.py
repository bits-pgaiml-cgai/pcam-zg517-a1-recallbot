"""Report NLU accuracy on labelled utterances (Task 2a)."""

from __future__ import annotations

import json

from src.config import RESULTS_DIR
from src.nlu import LABELLED_UTTERANCES, classify_intent, nlu_accuracy
from src.state import STATE_FIELDS


def main():
    rows = []
    for text, gold in LABELLED_UTTERANCES:
        pred = classify_intent(text)
        rows.append({"text": text, "gold": gold, "pred": pred, "correct": int(pred == gold)})
    acc = nlu_accuracy(LABELLED_UTTERANCES)
    out = {
        "n": len(LABELLED_UTTERANCES),
        "accuracy": acc,
        "approach": "rule/regex hybrid NLU (intent + entity patterns)",
        "state_fields": STATE_FIELDS,
        "rows": rows,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "nlu_accuracy.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"NLU accuracy={acc:.3f} on {len(LABELLED_UTTERANCES)} utterances")
    print("Wrote", path)


if __name__ == "__main__":
    main()
