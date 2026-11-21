from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.config import MEMORY_DIR
from src.embeddings import cosine_similarity, embed_texts
from src.logging_util import log_call


def importance_rule(text: str) -> int:
    t = text.lower()
    if any(x in t for x in ["book", "confirm", "complaint", "decided", "problem"]):
        return 8
    if any(x in t for x in ["allergy", "budget", "doctor"]):
        return 6
    if any(x in t for x in ["thanks", "bye", "weather", "hi", "hello"]):
        return 2
    return 4


class EpisodicMemory:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or (MEMORY_DIR / "episodic.jsonl")
        self.entries: List[Dict] = []
        self.load()

    def load(self) -> None:
        self.entries = []
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                self.entries.append(json.loads(line))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(e) + "\n")

    def add(
        self,
        user_id: str,
        text: str,
        turn: int,
        *,
        config: str,
        session: str,
        kind: str = "event",
    ) -> Dict:
        start = time.time()
        score = importance_rule(text)
        log_call(config, user_id, session, turn, "importance", "rule-importance", len(text.split()), 1, 0, start)
        vec = embed_texts([text], config=config, user=user_id, session=session, turn=turn, log=True)[0]
        entry = {
            "id": f"ep-{len(self.entries)+1}",
            "user": user_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "turn": turn,
            "session": session,
            "text": text,
            "importance": score,
            "kind": kind,
            "vector": vec.tolist(),
            "redacted": False,
        }
        self.entries.append(entry)
        self.save()
        return entry

    def reflect(
        self,
        user_id: str,
        *,
        config: str,
        session: str,
        turn: int,
    ) -> Dict:
        start = time.time()
        user_eps = [e for e in self.entries if e["user"] == user_id and not e.get("redacted")]
        summary = "Reflection: " + "; ".join(e["text"][:80] for e in user_eps[-5:])
        log_call(config, user_id, session, turn, "reflect", "rule-reflect", 50, len(summary.split()), 0, start)
        return self.add(user_id, summary, turn, config=config, session=session, kind="reflection")

    def score_entry(
        self,
        entry: Dict,
        query_vec: np.ndarray,
        now: Optional[datetime] = None,
        w_recency: float = 1.0,
        w_importance: float = 1.0,
        w_relevance: float = 1.0,
        half_life_hours: float = 24.0,
    ) -> float:
        now = now or datetime.now(timezone.utc)
        ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
        hours = max(0.0, (now - ts).total_seconds() / 3600.0)
        recency = math.exp(-hours / half_life_hours)
        importance = entry.get("importance", 1) / 10.0
        ev = np.asarray(entry["vector"], dtype=np.float32)
        relevance = cosine_similarity(query_vec, ev)
        return w_recency * recency + w_importance * importance + w_relevance * relevance

    def retrieve(
        self,
        user_id: str,
        query: str,
        top_k: int = 3,
        weights: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> List[Dict]:
        qv = embed_texts([query], log=False)[0]
        scored = []
        for e in self.entries:
            if e["user"] != user_id or e.get("redacted"):
                continue
            s = self.score_entry(e, qv, w_recency=weights[0], w_importance=weights[1], w_relevance=weights[2])
            item = {k: v for k, v in e.items() if k != "vector"}
            item["score"] = s
            scored.append(item)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def redact_mentioning(self, user_id: str, keyword: str) -> int:
        n = 0
        for e in self.entries:
            if e["user"] == user_id and keyword.lower() in e["text"].lower():
                e["redacted"] = True
                e["text"] = "[redacted]"
                n += 1
        self.save()
        return n
