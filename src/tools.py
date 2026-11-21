from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.config import AS_OF_DATE_DEFAULT, DB_DIR
from src.logging_util import log_call
from src.retrieval import HybridIndex, load_index
from src.tokens import count_tokens

DB_PATH = DB_DIR / "clinic.sqlite"


def init_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            specialty TEXT,
            day TEXT,
            time TEXT,
            location TEXT,
            slot_code TEXT,
            status TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _tool_log(config, user, session, turn, start):
    log_call(
        config=config,
        user=user,
        session=session,
        turn=turn,
        call_type="tool",
        model="tool",
        input_tokens=0,
        output_tokens=0,
        retrieved_tokens=0,
        start=start,
    )


def search_kb(
    query: str,
    index: HybridIndex,
    *,
    top_k: int = 3,
    as_of: str = AS_OF_DATE_DEFAULT,
    apply_time_filter: bool = True,
    config: str = "hybrid",
    user: str = "U1",
    session: str = "A",
    turn: int = 0,
) -> List[Dict]:
    start = time.time()
    hits = index.hybrid_rank(
        query, top_k=top_k, as_of=as_of, apply_time_filter=apply_time_filter
    )
    _tool_log(config, user, session, turn, start)
    return hits


def get_appointment(
    appointment_id: str,
    *,
    config: str,
    user: str,
    session: str,
    turn: int,
) -> Optional[Dict]:
    start = time.time()
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    _tool_log(config, user, session, turn, start)
    if not row:
        return None
    return dict(zip(cols, row))


def book_slot(
    booking: Dict,
    *,
    confirmed: bool,
    config: str,
    user: str,
    session: str,
    turn: int,
) -> Dict:
    start = time.time()
    if not confirmed:
        _tool_log(config, user, session, turn, start)
        return {"status": "blocked", "reason": "confirmation_required"}
    init_db()
    appt_id = booking.get("id") or "APT-1001"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT OR REPLACE INTO appointments
        (id, user_id, name, specialty, day, time, location, slot_code, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            appt_id,
            user,
            booking.get("name"),
            booking.get("specialty"),
            booking.get("day"),
            booking.get("time"),
            booking.get("location"),
            booking.get("slot_code", "SLOT-GEN"),
            "confirmed",
        ),
    )
    conn.commit()
    conn.close()
    _tool_log(config, user, session, turn, start)
    return {"status": "ok", "id": appt_id, **booking}


def retrieved_token_total(chunks: List[Dict]) -> int:
    return sum(count_tokens(c.get("text", "")) for c in chunks)
