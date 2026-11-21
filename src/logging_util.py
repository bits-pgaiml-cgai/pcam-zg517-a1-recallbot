import datetime
import json
import time
from pathlib import Path

from src.config import LOGS_DIR

RUN_ID = "r01"
_LOG_PATH = LOGS_DIR / "calls.jsonl"


def set_run_id(run_id: str) -> None:
    global RUN_ID
    RUN_ID = run_id


def log_call(
    config,
    user,
    session,
    turn,
    call_type,
    model,
    input_tokens,
    output_tokens,
    retrieved_tokens,
    start,
):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.datetime.now().astimezone().isoformat(),
        "run_id": RUN_ID,
        "config": config,
        "user": user,
        "session": session,
        "turn": turn,
        "call_type": call_type,
        "model": model,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "retrieved_tokens": int(retrieved_tokens),
        "latency_ms": int((time.time() - start) * 1000),
    }
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec
