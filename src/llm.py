"""Optional chat LLM via Ollama; falls back to template NLG when unavailable."""

from __future__ import annotations

import os
import time
from typing import Optional

import requests

from src.config import OLLAMA_HOST, OLLAMA_MODEL
from src.logging_util import log_call
from src.tokens import count_tokens


def ollama_available(host: Optional[str] = None) -> bool:
    host = host or os.environ.get("OLLAMA_HOST", OLLAMA_HOST)
    try:
        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def chat_ollama(
    prompt: str,
    *,
    system: str = "",
    config: str = "hybrid_mem",
    user: str = "U1",
    session: str = "A",
    turn: int = 0,
    temperature: float = 0.0,
    retrieved_tokens: int = 0,
) -> Optional[str]:
    if os.environ.get("RECALLBOT_LLM", "auto").lower() in {"off", "0", "false", "template"}:
        return None
    host = os.environ.get("OLLAMA_HOST", OLLAMA_HOST)
    model = os.environ.get("OLLAMA_MODEL", OLLAMA_MODEL)
    if not ollama_available(host):
        return None
    start = time.time()
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [],
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})
    try:
        r = requests.post(f"{host.rstrip('/')}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        text = (data.get("message") or {}).get("content") or ""
        usage = data.get("prompt_eval_count"), data.get("eval_count")
        in_tok = usage[0] if usage[0] is not None else count_tokens(system + prompt)
        out_tok = usage[1] if usage[1] is not None else count_tokens(text)
        log_call(
            config=config,
            user=user,
            session=session,
            turn=turn,
            call_type="chat",
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            retrieved_tokens=retrieved_tokens,
            start=start,
        )
        return text.strip()
    except Exception as exc:
        print(f"[llm] Ollama chat failed ({exc}); using template NLG")
        return None
