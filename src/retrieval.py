from __future__ import annotations

import json
import pickle
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.bm25 import BM25, tokenize
from src.chunker import chunk_text
from src.config import (
    AS_OF_DATE_DEFAULT,
    BM25_B,
    BM25_K1,
    CHUNK_OVERLAP_RATIO,
    CHUNK_SIZES,
    INDEX_DIR,
    KB_DIR,
    RRF_K,
)
from src.embeddings import cosine_similarity, embed_texts
from src.rrf import reciprocal_rank_fusion
from src.tokens import count_tokens


def _parse_front_matter(text: str) -> Dict[str, str]:
    meta = {}
    for line in text.splitlines()[:12]:
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def load_kb_documents() -> List[Dict]:
    docs = []
    for path in sorted(KB_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta = _parse_front_matter(raw)
        body = raw.split("\n\n", 1)[-1]
        docs.append(
            {
                "doc_id": meta.get("doc_id", path.stem),
                "version": meta.get("version", ""),
                "valid_from": meta.get("valid_from", ""),
                "valid_to": meta.get("valid_to", ""),
                "section": meta.get("section", ""),
                "text": body,
            }
        )
    return docs


def _parse_ymd(s: str) -> Optional[date]:
    if not s:
        return None
    try:
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def is_valid_on(chunk: Dict, as_of: str) -> bool:
    as_of_d = _parse_ymd(as_of) or _parse_ymd(AS_OF_DATE_DEFAULT)
    vf = _parse_ymd(chunk.get("valid_from", ""))
    vt = _parse_ymd(chunk.get("valid_to", ""))
    if vf and as_of_d < vf:
        return False
    if vt and as_of_d > vt:
        return False
    return True


class HybridIndex:
    def __init__(self, chunk_size: int):
        self.chunk_size = chunk_size
        self.chunks: List[Dict] = []
        self.vectors: Optional[np.ndarray] = None
        self.bm25: Optional[BM25] = None

    def build(self, docs: List[Dict], *, config: str = "hybrid") -> None:
        self.chunks = []
        for doc in docs:
            self.chunks.extend(
                chunk_text(
                    doc["text"],
                    chunk_size=self.chunk_size,
                    overlap_ratio=CHUNK_OVERLAP_RATIO,
                    doc_id=doc["doc_id"],
                    section=doc.get("section", ""),
                    version=doc.get("version", ""),
                    valid_from=doc.get("valid_from", ""),
                    valid_to=doc.get("valid_to", ""),
                )
            )
        texts = [c["text"] for c in self.chunks]
        self.vectors = embed_texts(texts, config=config, log=True) if texts else np.zeros((0, 384))
        tokenized = [tokenize(t) for t in texts]
        self.bm25 = BM25(tokenized, k1=BM25_K1, b=BM25_B)

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / f"chunks_{self.chunk_size}.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f)
        np.save(directory / f"vectors_{self.chunk_size}.npy", self.vectors)
        with open(directory / f"bm25_{self.chunk_size}.pkl", "wb") as f:
            pickle.dump(self.bm25, f)

    def load(self, directory: Path) -> None:
        with open(directory / f"chunks_{self.chunk_size}.json", encoding="utf-8") as f:
            self.chunks = json.load(f)
        self.vectors = np.load(directory / f"vectors_{self.chunk_size}.npy")
        with open(directory / f"bm25_{self.chunk_size}.pkl", "rb") as f:
            self.bm25 = pickle.load(f)

    def dense_rank(self, query: str, top_k: int = 10, as_of: Optional[str] = None) -> List[tuple]:
        qv = embed_texts([query], log=False)[0]
        scores = []
        for i, vec in enumerate(self.vectors):
            if as_of and not is_valid_on(self.chunks[i], as_of):
                continue
            scores.append((i, cosine_similarity(qv, vec)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def bm25_rank(self, query: str, top_k: int = 10, as_of: Optional[str] = None) -> List[tuple]:
        q = tokenize(query)
        scored = []
        for i in range(len(self.chunks)):
            if as_of and not is_valid_on(self.chunks[i], as_of):
                continue
            scored.append((i, self.bm25.score(q, i)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def hybrid_rank(
        self,
        query: str,
        top_k: int = 10,
        as_of: Optional[str] = None,
        apply_time_filter: bool = True,
    ) -> List[Dict]:
        if as_of is None and apply_time_filter:
            as_of = AS_OF_DATE_DEFAULT
        as_of_val = as_of if apply_time_filter else None
        # Twist B: rewrite superseded codes toward current equivalents before search.
        q_search = query
        if as_of_val and as_of_val >= "2026-01-01":
            q_search = (
                query.replace("WAIT-48", "WAIT-24 replaces WAIT-48")
                .replace("RFD-7D", "RFD-14D")
                .replace("CXL-24H", "CXL-12H")
            )
        dense = self.dense_rank(q_search, top_k=top_k * 2, as_of=as_of_val)
        sparse = self.bm25_rank(q_search, top_k=top_k * 2, as_of=as_of_val)
        dense_ids = [self.chunks[i]["chunk_id"] for i, _ in dense]
        sparse_ids = [self.chunks[i]["chunk_id"] for i, _ in sparse]
        by_id = {c["chunk_id"]: c for c in self.chunks}
        # Exact codes/IDs: trust BM25 order (dense hashing/embeddings often dilute rare codes).
        if CODE_RE.search(query or "") and sparse and sparse[0][1] > 1.0:
            fused = [(self.chunks[i]["chunk_id"], s) for i, s in sparse]
        else:
            fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=RRF_K)
        out = []
        for cid, score in fused[:top_k]:
            item = dict(by_id[cid])
            item["score"] = score
            item["retrieved_tokens"] = count_tokens(item["text"])
            out.append(item)
        return out


def build_all_indexes(as_config: str = "hybrid") -> Dict[int, HybridIndex]:
    docs = load_kb_documents()
    indexes = {}
    for size in CHUNK_SIZES:
        idx = HybridIndex(size)
        idx.build(docs, config=as_config)
        idx.save(INDEX_DIR)
        indexes[size] = idx
    return indexes


def load_index(chunk_size: int = 512) -> HybridIndex:
    idx = HybridIndex(chunk_size)
    idx.load(INDEX_DIR)
    return idx


CODE_RE = re.compile(r"\b([A-Z]{1,5}-\d{1,4}[A-Z]?|[A-Z]{2,}-\d+[A-Z]?|[A-Z]{3,}-\w+)\b")
