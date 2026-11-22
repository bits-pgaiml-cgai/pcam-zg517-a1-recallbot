"""Task 5: token economics and vector-index sizing / HNSW vs flat latency."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.config import (
    EMBEDDING_DIM,
    LOGS_DIR,
    RESULTS_DIR,
    SCALE_DAILY_USERS,
    WINDOW_K,
)
from src.tokens import count_tokens

# CS3 price table (May 2025 indicative), USD per 1M tokens.
PRICE_TABLE = {
    "GPT-4o": {"input": 2.50, "output": 10.00, "cached_input": 1.25, "min_cache_tokens": 1024},
    "Claude Haiku 5.5": {"input": 0.10, "output": 0.50, "cached_input": 0.01, "min_cache_tokens": 1024},
    "Gemini 3.8 Flash": {"input": 0.75, "output": 3.75, "cached_input": 0.075, "min_cache_tokens": 1024},
}
DEFAULT_PRICE_ROW = "GPT-4o"


def _mean_chat_tokens(config: str):
    path = LOGS_DIR / "calls.jsonl"
    if not path.exists():
        return None
    by_turn = defaultdict(lambda: {"in": 0, "out": 0})
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("config") != config or rec.get("call_type") != "chat":
            continue
        t = rec["turn"]
        by_turn[t]["in"] += rec.get("input_tokens", 0)
        by_turn[t]["out"] += rec.get("output_tokens", 0)
    if not by_turn:
        return None
    n = len(by_turn)
    return {
        "turns": n,
        "mean_input": sum(v["in"] for v in by_turn.values()) / n,
        "mean_output": sum(v["out"] for v in by_turn.values()) / n,
    }


def estimate_monthly_cost(
    config: str,
    price_row: str = DEFAULT_PRICE_ROW,
    daily_users: int = SCALE_DAILY_USERS,
    prefix_tokens: int = 450,
):
    stats = _mean_chat_tokens(config)
    if not stats:
        # Fallback illustrative means if logs missing for that config.
        stats = {"turns": 40, "mean_input": 900.0 if config == "hybrid_mem" else 600.0, "mean_output": 80.0}
        stats["assumed"] = True
    prices = PRICE_TABLE[price_row]
    turns = stats["turns"]
    days = 30
    convos = daily_users * days
    in_tok = stats["mean_input"] * turns * convos
    out_tok = stats["mean_output"] * turns * convos

    cost_no_cache = (in_tok / 1e6) * prices["input"] + (out_tok / 1e6) * prices["output"]

    # With caching: fixed prefix at cached rate; remainder of measured input at full rate.
    # If logged mean_input < prefix (template NLG under-counts full prompt), bill
    # prefix + max(0, mean_input) so the cache case never exceeds a full-prefix bill.
    cacheable = prefix_tokens >= prices["min_cache_tokens"]
    if cacheable:
        billed_input = max(float(stats["mean_input"]), float(prefix_tokens))
        dynamic_per_turn = max(0.0, billed_input - prefix_tokens)
        cached_in = prefix_tokens * turns * convos
        dynamic_in = dynamic_per_turn * turns * convos
        cost_cache = (
            (cached_in / 1e6) * prices["cached_input"]
            + (dynamic_in / 1e6) * prices["input"]
            + (out_tok / 1e6) * prices["output"]
        )
        # Comparable no-cache bill when prefix would be present in a real LLM prompt.
        in_tok_full = billed_input * turns * convos
        cost_no_cache = (in_tok_full / 1e6) * prices["input"] + (out_tok / 1e6) * prices["output"]
    else:
        cost_cache = None

    return {
        "config": config,
        "price_row": price_row,
        "daily_users": daily_users,
        "turns_per_convo": turns,
        "mean_input_tokens": stats["mean_input"],
        "mean_output_tokens": stats["mean_output"],
        "prefix_tokens": prefix_tokens,
        "prefix_reaches_min_cache": cacheable,
        "min_cache_tokens": prices["min_cache_tokens"],
        "monthly_cost_no_cache_usd": round(cost_no_cache, 2),
        "monthly_cost_with_cache_usd": None if cost_cache is None else round(cost_cache, 2),
        "assumed_tokens": bool(stats.get("assumed")),
        "note_if_prefix_short": (
            None
            if cacheable
            else "Prefix below 1024 tokens; lengthen system prompt + few-shot examples to enable caching."
        ),
    }


def flat_memory_bytes(n: int, dim: int = EMBEDDING_DIM) -> int:
    return n * dim * 4


def hnsw_memory_bytes(n: int, dim: int = EMBEDDING_DIM, m: int = 16) -> int:
    # CS3: d*4 + layer(1) + ~2M*4 links at layer 0 (+ small upper-layer).
    per = dim * 4 + 1 + (2 * m * 4)
    return n * per


def estimate_year_vectors(
    daily_users: int = SCALE_DAILY_USERS,
    kb_chunks: int = 32,
    semantic_per_user_year: int = 20,
    episodic_per_user_year: int = 40,
) -> dict:
    users = daily_users  # treat scale as active user base for yearly memory growth
    semantic = users * semantic_per_user_year
    episodic = users * episodic_per_user_year
    total = kb_chunks + semantic + episodic
    return {
        "kb_chunks": kb_chunks,
        "semantic": semantic,
        "episodic": episodic,
        "total": total,
        "flat_bytes": flat_memory_bytes(total),
        "hnsw_m16_bytes": hnsw_memory_bytes(total, m=16),
        "flat_gb": round(flat_memory_bytes(total) / (1024**3), 3),
        "hnsw_m16_gb": round(hnsw_memory_bytes(total, m=16) / (1024**3), 3),
    }


def measure_flat_vs_hnsw(n: int = 100_000, dim: int = EMBEDDING_DIM, queries: int = 50, m: int = 16, ef: int = 64):
    rng = np.random.default_rng(42)
    base = rng.standard_normal((max(32, min(n, 512)), dim), dtype=np.float32)
    # Pad with random vectors to n.
    if n > len(base):
        pad = rng.standard_normal((n - len(base), dim), dtype=np.float32)
        mat = np.vstack([base, pad])
    else:
        mat = base[:n]
    mat /= np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    q = mat[:queries]

    # Flat
    t0 = time.perf_counter()
    for qi in q:
        _ = np.dot(mat, qi)
    flat_ms = (time.perf_counter() - t0) * 1000 / queries

    hnsw_ms = None
    recall = None
    try:
        import faiss

        index = faiss.IndexHNSWFlat(dim, m)
        index.hnsw.efSearch = ef
        index.add(mat)
        # Flat reference top-1
        flat_top = []
        for qi in q:
            scores = np.dot(mat, qi)
            flat_top.append(int(np.argmax(scores)))
        t0 = time.perf_counter()
        _, idx = index.search(q, 1)
        hnsw_ms = (time.perf_counter() - t0) * 1000 / queries
        hits = sum(1 for i, j in enumerate(idx[:, 0]) if int(j) == flat_top[i])
        recall = hits / queries
    except Exception as exc:
        return {
            "n": n,
            "dim": dim,
            "flat_latency_ms": round(flat_ms, 3),
            "hnsw_latency_ms": None,
            "hnsw_recall_at_1": None,
            "m": m,
            "ef_search": ef,
            "error": str(exc),
            "recommend": "Install faiss-cpu; for V31 scale prefer HNSW M=16 ef_search=64–100.",
        }

    return {
        "n": n,
        "dim": dim,
        "flat_latency_ms": round(flat_ms, 3),
        "hnsw_latency_ms": round(hnsw_ms, 3),
        "hnsw_recall_at_1": round(recall, 4),
        "m": m,
        "ef_search": ef,
        "recommend": (
            "At year-1 vectors for 5k users, prefer HNSW M=16, ef_search=64 "
            "(good recall/latency). Flat is fine only while N << 100k."
        ),
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    from src.nlg import load_system_prompt, load_task_steps

    prefix = count_tokens(load_system_prompt() + "\n" + load_task_steps())
    report = {
        "window_k": WINDOW_K,
        "token_economics": [
            estimate_monthly_cost("trim", prefix_tokens=prefix),
            estimate_monthly_cost("hybrid_mem", prefix_tokens=prefix),
        ],
        "year_vectors": estimate_year_vectors(),
        "latency": measure_flat_vs_hnsw(n=100_000),
        "price_table_source": "CS3 Session-3 Token Economics table (May 2025 indicative)",
    }
    out = RESULTS_DIR / "cost_scale.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Wrote", out)


if __name__ == "__main__":
    main()
