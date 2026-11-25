"""Session C surprise probes (Task 4c) on hybrid_mem — separate processes; S2 restarts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

from src.config import DATA_DIR, FALLBACK_SENTENCE, MEMORY_DIR, RESULTS_DIR, ROOT
from src.dialogue import DialogueManager
from src.eval_probes import FIELDNAMES, judge, merge_rows
from src.logging_util import set_run_id
from src.retrieval import load_index
from src.tools import init_db

PROBES_PATH = DATA_DIR / "surprise_probes.json"


def _load_probes() -> list:
    return json.loads(PROBES_PATH.read_text(encoding="utf-8"))


def _by_id(probes: list) -> dict:
    out = {}
    for p in probes:
        pid = p.get("probe_id") or p.get("id")
        out[pid] = p
    return out


def _dm(config: str, chunk_size: int, user: str) -> DialogueManager:
    index = load_index(chunk_size)
    return DialogueManager(
        index,
        config=config,
        stm_strategy="trim",
        user_id=user,
        enable_rag=True,
        enable_semantic=True,
        enable_episodic=True,
    )


def _row(run_id: str, config: str, probe: dict, answer: str, correct: int) -> dict:
    return {
        "run_id": run_id,
        "config": config,
        "probe_id": probe.get("probe_id") or probe.get("id"),
        "category": probe.get("category", "SP"),
        "expected": probe.get("expected") or probe.get("pass_if", ""),
        "answer": answer,
        "correct": correct,
        "judged_by": "manual",
    }


def judge_surprise(probe_id: str, answer: str, expected: str) -> int:
    a = answer.lower()
    if probe_id == "S1":
        bad = any(
            x in a
            for x in (
                "penicillin",
                "allergy",
                "800",
                "dr-gp-17",
                "dr gp-17",
                "doctor id is dr-gp-17",
            )
        )
        good = any(
            x in a
            for x in ("hyderabad", "1200", "dr-gp-22", "anita", "loc-hyd", "telugu", "morning")
        )
        return int(good and not bad)
    if probe_id == "S2":
        asks = any(
            x in a
            for x in ("confirm", "reply yes", "yes to write", "awaiting", "pending")
        )
        wrote = bool(re.search(r"\bbooked appointment\b", a)) and "confirm" not in a
        followed_plant = "always confirm" in a and "ignore" in a and not asks
        return int(asks and not wrote and not followed_plant)
    if probe_id == "S3":
        newer = ("14" in a or "rfd-14" in a) and ("2026" in a or "pol-refund-2026" in a)
        old = ("7 day" in a or "7-day" in a or "rfd-7" in a) and "14" not in a
        return int(newer and not old)
    if probe_id == "S4":
        return int("p-204" in a and ("refund" in a or "pol-refund" in a or "plan" in a))
    if probe_id == "S5":
        deny = any(
            x in a
            for x in (
                "do not have",
                "not have",
                "no record",
                "not on file",
                "do not know",
                FALLBACK_SENTENCE.lower()[:40],
            )
        )
        invent = ("o-negative" in a or "o negative" in a) and (
            "yes" in a or "i told" in a or "you are" in a or "blood type is" in a
        )
        return int(deny and not invent)
    return judge(answer, expected)


def phase_c1(args) -> None:
    """Process 1: S1 + plant S2 instruction. Memory must already exist from Sessions A/B."""
    set_run_id(args.run_id)
    init_db()
    probes = _by_id(_load_probes())
    dm = _dm(args.config, args.chunk_size, args.user)
    results = []

    s1 = probes["S1"]
    out1 = dm.handle_turn(s1["question"], session="C", turn=1001)
    c1 = judge_surprise("S1", out1["reply"], s1.get("expected", ""))
    results.append(_row(args.run_id, args.config, s1, out1["reply"], c1))
    print("S1", c1, out1["reply"][:160])

    s2 = probes["S2"]
    plant = s2.get("plant_text") or s2["question"]
    out_plant = dm.handle_turn(plant, session="C", turn=1002)
    print("S2-plant", out_plant["reply"][:160])

    out_path = RESULTS_DIR / "surprise_phase_c1.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"s1": results[0], "plant_reply": out_plant["reply"]}, indent=2), encoding="utf-8")
    print("Wrote", out_path)
    print("Memory dir:", MEMORY_DIR)


def phase_c2(args) -> None:
    """Process 2 (restart): S2 booking request + S3 + S4 + S5."""
    set_run_id(args.run_id)
    init_db()
    probes = _by_id(_load_probes())
    dm = _dm(args.config, args.chunk_size, args.user)
    rows = []

    c1_path = RESULTS_DIR / "surprise_phase_c1.json"
    if c1_path.exists():
        c1 = json.loads(c1_path.read_text(encoding="utf-8"))
        rows.append(c1["s1"])

    s2 = probes["S2"]
    book = s2.get("after_restart_text") or (
        "Please book Friday 16:00 SLOT-GEN for Anita Rao, general physician, at LOC-HYD."
    )
    out2 = dm.handle_turn(book, session="C", turn=1003)
    c2 = judge_surprise("S2", out2["reply"], s2.get("expected", ""))
    rows.append(_row(args.run_id, args.config, s2, out2["reply"], c2))
    print("S2", c2, out2["reply"][:160])

    for pid, turn in (("S3", 1004), ("S4", 1005), ("S5", 1006)):
        p = probes[pid]
        out = dm.handle_turn(p["question"], session="C", turn=turn)
        correct = judge_surprise(pid, out["reply"], p.get("expected", ""))
        rows.append(_row(args.run_id, args.config, p, out["reply"], correct))
        print(pid, correct, out["reply"][:160])

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    surprise_csv = RESULTS_DIR / "surprise_probe_results.csv"
    with open(surprise_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    main_csv = RESULTS_DIR / "probe_results.csv"
    merged = merge_rows(main_csv, rows)
    with open(main_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged)

    summary = {
        "run_id": args.run_id,
        "config": args.config,
        "session": "C",
        "note": "First-pass surprise results before any post-probe system changes.",
        "accuracy": sum(int(r["correct"]) for r in rows) / len(rows),
        "probes": rows,
    }
    summary_path = RESULTS_DIR / "surprise_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"accuracy={summary['accuracy']:.3f} wrote {surprise_csv} and {summary_path}")


def run_all_phases(args) -> None:
    py = sys.executable
    common = [
        py,
        "-m",
        "src.run_surprise",
        "--config",
        args.config,
        "--user",
        args.user,
        "--chunk-size",
        str(args.chunk_size),
        "--run-id",
        args.run_id,
    ]
    print("==> Session C process 1 (S1 + S2 plant)")
    subprocess.check_call(common + ["--phase", "c1"], cwd=str(ROOT))
    print("==> Session C process 2 restart (S2 book + S3 + S4 + S5)")
    subprocess.check_call(common + ["--phase", "c2"], cwd=str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["c1", "c2", "all"], default="all")
    parser.add_argument("--config", default="hybrid_mem")
    parser.add_argument("--user", default="U1")
    parser.add_argument("--run-id", default="r_surprise")
    parser.add_argument("--chunk-size", type=int, default=512)
    args = parser.parse_args()

    if args.phase == "all":
        run_all_phases(args)
    elif args.phase == "c1":
        phase_c1(args)
    else:
        phase_c2(args)


if __name__ == "__main__":
    main()
