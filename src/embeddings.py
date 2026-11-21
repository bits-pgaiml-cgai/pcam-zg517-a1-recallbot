import hashlib
import os
import time
from typing import List

import numpy as np

from src.config import EMBEDDING_DIM, EMBEDDING_MODEL, EMBEDDING_POOLING
from src.logging_util import log_call
from src.tokens import count_tokens

_MODEL = None
_BACKEND = None


def _hashing_embed(texts: List[str], dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Offline dense-ish vectors via feature hashing (no network)."""
    out = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        for tok in (text or "").lower().split():
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            out[i, idx] += sign
        norm = np.linalg.norm(out[i]) + 1e-12
        out[i] /= norm
    return out


def _get_model():
    global _MODEL, _BACKEND
    if _MODEL is not None or _BACKEND == "hash":
        return _MODEL
    if os.environ.get("RECALLBOT_EMBED_BACKEND", "").lower() == "hash":
        _BACKEND = "hash"
        return None
    try:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(EMBEDDING_MODEL)
        _BACKEND = "sentence-transformers"
        return _MODEL
    except Exception as exc:
        print(f"[embeddings] falling back to hashing embedder ({exc.__class__.__name__})")
        _BACKEND = "hash"
        _MODEL = None
        return None


def embed_backend() -> str:
    _get_model()
    return _BACKEND or "hash"


def embed_texts(
    texts: List[str],
    *,
    config: str = "hybrid",
    user: str = "U1",
    session: str = "A",
    turn: int = 0,
    log: bool = True,
) -> np.ndarray:
    start = time.time()
    model = _get_model()
    if model is None:
        arr = _hashing_embed(texts, EMBEDDING_DIM)
        model_name = "hashing-md5-384"
    else:
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        arr = np.asarray(vectors, dtype=np.float32)
        model_name = EMBEDDING_MODEL
    if log:
        log_call(
            config=config,
            user=user,
            session=session,
            turn=turn,
            call_type="embed",
            model=model_name,
            input_tokens=sum(count_tokens(t) for t in texts),
            output_tokens=0,
            retrieved_tokens=0,
            start=start,
        )
    _ = EMBEDDING_POOLING
    return arr


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
