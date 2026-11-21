"""Run Session A or B from test_conversation.json as a separate process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import DATA_DIR, MEMORY_DIR
from src.dialogue import DialogueManager
from src.logging_util import set_run_id
from src.retrieval import load_index
from src.tools import init_db


def config_flags(config: str):
    if config in {"full", "trim", "summary"}:
        return dict(
            stm_strategy=config,
            enable_rag=True,
            enable_semantic=True,
            enable_episodic=True,
            dm_config=config,
        )
    mapping = {
        "no_rag": dict(stm_strategy="trim", enable_rag=False, enable_semantic=False, enable_episodic=False),
        "hybrid": dict(stm_strategy="trim", enable_rag=True, enable_semantic=False, enable_episodic=False),
        "hybrid_sem": dict(stm_strategy="trim", enable_rag=True, enable_semantic=True, enable_episodic=False),
        "hybrid_mem": dict(stm_strategy="trim", enable_rag=True, enable_semantic=True, enable_episodic=True),
    }
    flags = mapping[config]
    flags["dm_config"] = config
    return flags


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", choices=["A", "B"], required=True)
    parser.add_argument("--config", default="hybrid_mem")
    parser.add_argument("--user", default="U1")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--chunk-size", type=int, default=512)
    args = parser.parse_args()

    run_id = args.run_id or f"r_{args.config}_{args.session}"
    set_run_id(run_id)
    init_db()

    conv = json.loads((DATA_DIR / "test_conversation.json").read_text(encoding="utf-8"))
    lo, hi = conv["session_a_turns"] if args.session == "A" else conv["session_b_turns"]
    user_turns = [
        t for t in conv["turns"] if t["role"] == "user" and lo <= t["turn"] <= hi
    ]

    flags = config_flags(args.config)
    index = load_index(args.chunk_size)
    dm = DialogueManager(
        index,
        config=flags["dm_config"],
        stm_strategy=flags["stm_strategy"],
        user_id=args.user,
        enable_rag=flags["enable_rag"],
        enable_semantic=flags["enable_semantic"],
        enable_episodic=flags["enable_episodic"],
    )

    print(f"RUN {run_id} session={args.session} config={args.config} turns={len(user_turns)}")
    for t in user_turns:
        out = dm.handle_turn(t["text"], session=args.session, turn=t["turn"])
        print(f"[{t['turn']}] USER: {t['text']}")
        print(f"[{t['turn']}] BOT : {out['reply']}")
        print(f"         intent={out['intent']} kb={out['kb_chunks'][:1]}")

    if args.session == "A" and flags["enable_episodic"]:
        ref = dm.end_session_reflection("A", turn=hi)
        print("Reflection:", ref.get("text") if ref else None)

    if args.session == "B":
        table = dm.context_assembly_table(user_turns[0]["text"] if user_turns else "hello")
        out_path = MEMORY_DIR / "context_assembly_session_b.json"
        out_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
        print("Wrote", out_path)

    print("Memory dir:", MEMORY_DIR)


if __name__ == "__main__":
    main()
