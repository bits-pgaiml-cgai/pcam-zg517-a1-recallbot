from __future__ import annotations

import time
from typing import Dict, List, Tuple

from src.config import WINDOW_K
from src.logging_util import log_call
from src.tokens import count_tokens


def format_history(turns: List[Dict]) -> str:
    lines = []
    for t in turns:
        lines.append(f"{t['role'].upper()}: {t['text']}")
    return "\n".join(lines)


def select_history(
    history: List[Dict],
    strategy: str,
    *,
    config: str,
    user: str,
    session: str,
    turn: int,
    summary_state: Dict,
) -> Tuple[str, Dict]:
    """Return history text for the prompt under full | trim | summary."""
    if strategy == "full":
        return format_history(history), summary_state
    if strategy == "trim":
        return format_history(history[-WINDOW_K:]), summary_state
    if strategy == "summary":
        older = history[:-2] if len(history) > 2 else []
        recent = history[-2:]
        if older:
            start = time.time()
            bullet = "; ".join(f"{t['role']}:{t['text'][:60]}" for t in older[-10:])
            summary_state["summary"] = f"Earlier conversation summary: {bullet}"
            log_call(
                config=config,
                user=user,
                session=session,
                turn=turn,
                call_type="summary",
                model="rule-summary",
                input_tokens=count_tokens(format_history(older)),
                output_tokens=count_tokens(summary_state["summary"]),
                retrieved_tokens=0,
                start=start,
            )
        parts = []
        if summary_state.get("summary"):
            parts.append(summary_state["summary"])
        parts.append(format_history(recent))
        return "\n".join(parts), summary_state
    raise ValueError(f"Unknown STM strategy: {strategy}")
