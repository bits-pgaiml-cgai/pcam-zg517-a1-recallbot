from __future__ import annotations

import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.config import AS_OF_DATE_DEFAULT, MEMORY_DIR
from src.embeddings import cosine_similarity, embed_texts
from src.logging_util import log_call


class SemanticMemory:
    """Keyed user fact notebook with supersede + forget (Twist B: validity dates)."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (MEMORY_DIR / "semantic.json")
        self.records: List[Dict] = []
        self.vectors: Optional[np.ndarray] = None
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self.records = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.records = []
        self._reindex()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")
        vec_path = self.path.with_suffix(".npy")
        if self.vectors is not None and len(self.records):
            np.save(vec_path, self.vectors)

    def _reindex(self) -> None:
        active = [r for r in self.records if r.get("status") == "active"]
        if not active:
            self.vectors = np.zeros((0, 384), dtype=np.float32)
            return
        texts = [f"{r['key']}: {r['value']}" for r in active]
        self.vectors = embed_texts(texts, log=False)

    def extract_from_turn(
        self,
        user_id: str,
        text: str,
        turn: int,
        *,
        config: str,
        session: str,
        as_of: str = AS_OF_DATE_DEFAULT,
    ) -> List[Dict]:
        start = time.time()
        created = []
        patterns = [
            (r"I live in ([A-Za-z]+)", "city"),
            (r"prefer (LOC-[A-Z]+)", "preferred_location"),
            (r"My name is ([A-Za-z ]+)", "name"),
            (r"budget.*?(\d{3,5})", "budget"),
            (r"allergic to ([A-Za-z]+)", "allergy"),
            (r"preferred doctor(?:\s+ID)?(?:\s+is)?\s+(DR-[A-Z0-9-]+)", "preferred_doctor"),
            (r"change preferred doctor to (DR-[A-Z0-9-]+)", "preferred_doctor"),
            (r"\b(DR-[A-Z0-9-]+)\b", "preferred_doctor"),
            (r"prefer (morning|evening) slots", "time_preference"),
            (r"prefer ([A-Za-z]+) for SMS", "sms_language"),
            (r"General physician", "specialty"),
        ]
        low = text.lower()
        filler = any(x in low for x in ["thanks", "bye", "nice weather", "ok bye", "great thanks"])
        if filler and "forget" not in low:
            log_call(config, user_id, session, turn, "extract", "rule-extract", len(text.split()), 0, 0, start)
            return []

        if "forget" in low and "allergy" in low:
            self.forget(user_id, "allergy")
            log_call(config, user_id, session, turn, "extract", "rule-extract", len(text.split()), 1, 0, start)
            return [{"key": "allergy", "action": "forget"}]

        for pat, key in patterns:
            m = re.search(pat, text, re.I)
            if not m:
                continue
            value = m.group(1).strip() if m.lastindex else "general physician"
            if key == "specialty":
                value = "general physician"
            rec = self.upsert(
                user_id=user_id,
                key=key,
                value=value,
                source_turn=turn,
                as_of=as_of,
            )
            created.append(rec)
        log_call(config, user_id, session, turn, "extract", "rule-extract", len(text.split()), len(created), 0, start)
        return created

    def upsert(
        self,
        user_id: str,
        key: str,
        value: str,
        source_turn: int,
        as_of: str = AS_OF_DATE_DEFAULT,
    ) -> Dict:
        for r in self.records:
            if r["user"] == user_id and r["key"] == key and r.get("status") == "active":
                r["status"] = "superseded"
                r["superseded_on"] = as_of
        rec = {
            "user": user_id,
            "key": key,
            "value": value,
            "source_turn": source_turn,
            "date": as_of,
            "valid_from": as_of,
            "valid_to": "2099-12-31",
            "status": "active",
        }
        self.records.append(rec)
        self._reindex()
        self.save()
        return rec

    def forget(self, user_id: str, key: str) -> int:
        removed = 0
        kept = []
        for r in self.records:
            if r["user"] == user_id and r["key"] == key:
                removed += 1
                continue
            kept.append(r)
        self.records = kept
        self._reindex()
        self.save()
        return removed

    def active_facts(
        self,
        user_id: str,
        as_of: str = AS_OF_DATE_DEFAULT,
    ) -> List[Dict]:
        out = []
        for r in self.records:
            if r["user"] != user_id or r.get("status") != "active":
                continue
            if r.get("valid_to") and as_of > r["valid_to"]:
                continue
            if r.get("valid_from") and as_of < r["valid_from"]:
                continue
            out.append(r)
        return out

    def retrieve(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        as_of: str = AS_OF_DATE_DEFAULT,
    ) -> List[Dict]:
        facts = self.active_facts(user_id, as_of=as_of)
        if not facts:
            return []
        texts = [f"{r['key']}: {r['value']}" for r in facts]
        vecs = embed_texts(texts, log=False)
        qv = embed_texts([query], log=False)[0]
        scored = [(cosine_similarity(qv, v), r) for v, r in zip(vecs, facts)]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def precision_recall(self, gold_facts: List[Dict], user_id: str = "U1") -> Tuple[float, float]:
        gold_pairs = {
            (f["key"], str(f["value"]))
            for f in gold_facts
            if f.get("value") is not None and not f.get("forget")
        }
        pred_pairs = {(r["key"], str(r["value"])) for r in self.active_facts(user_id)}
        if not pred_pairs:
            return 0.0, 0.0
        tp = len(gold_pairs & pred_pairs)
        precision = tp / len(pred_pairs)
        recall = tp / max(1, len(gold_pairs))
        return precision, recall
