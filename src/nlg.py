from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from src.config import CHAT_MODEL, FALLBACK_SENTENCE, SKILLS_DIR
from src.llm import chat_ollama
from src.logging_util import log_call
from src.tokens import count_tokens


def load_system_prompt() -> str:
    path = SKILLS_DIR / "system_prompt_v1.md"
    return path.read_text(encoding="utf-8") if path.exists() else "You are RecallBot."


def load_task_steps() -> str:
    path = SKILLS_DIR / "book_appointment_steps_v1.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def generate_reply(
    *,
    user_text: str,
    intent: str,
    state: Dict,
    kb_chunks: List[Dict],
    semantic_facts: List[Dict],
    episodes: List[Dict],
    history_text: str,
    config: str,
    user: str,
    session: str,
    turn: int,
    retrieved_tokens: int,
) -> str:
    system = load_system_prompt()
    ctx_bits = []
    for c in kb_chunks[:3]:
        ctx_bits.append(f"[{c.get('chunk_id')}] {c.get('text', '')[:400]}")
    for f in semantic_facts[:5]:
        ctx_bits.append(f"FACT {f.get('key')}={f.get('value')}")
    for e in episodes[:3]:
        ctx_bits.append(f"EPISODE {e.get('text', '')[:200]}")
    rag_block = "\n".join(ctx_bits)
    ollama_prompt = (
        f"History:\n{history_text}\n\nContext:\n{rag_block}\n\n"
        f"User: {user_text}\nIntent: {intent}\n"
        f"If answer unknown, reply exactly: {FALLBACK_SENTENCE}"
    )
    llm_reply = chat_ollama(
        ollama_prompt,
        system=system,
        config=config,
        user=user,
        session=session,
        turn=turn,
        temperature=0.0 if intent in {"confirm_yes", "kb_question", "provide_slot"} else 0.3,
        retrieved_tokens=retrieved_tokens,
    )
    if llm_reply:
        return llm_reply

    start = time.time()
    reply = _template_reply(
        user_text=user_text,
        intent=intent,
        state=state,
        kb_chunks=kb_chunks,
        semantic_facts=semantic_facts,
        episodes=episodes,
    )
    prompt_proxy = history_text + user_text + reply
    log_call(
        config=config,
        user=user,
        session=session,
        turn=turn,
        call_type="chat",
        model=CHAT_MODEL,
        input_tokens=count_tokens(prompt_proxy),
        output_tokens=count_tokens(reply),
        retrieved_tokens=retrieved_tokens,
        start=start,
    )
    return reply


def _template_reply(
    user_text: str,
    intent: str,
    state: Dict,
    kb_chunks: List[Dict],
    semantic_facts: List[Dict],
    episodes: List[Dict],
) -> str:
    t = user_text.lower()

    if intent == "greet":
        return "Hello! I am RecallBot for ClinicCare appointments. How can I help?"

    if intent == "forget_fact":
        return "I removed the requested fact from your profile and related episode mentions."

    if intent == "confirm_yes":
        if state.get("awaiting_confirm") or state.get("just_booked"):
            pb = state.get("pending_booking") or {}
            return (
                f"Booked appointment {state.get('booked_appointment_id', 'APT-1001')} "
                f"for {pb.get('day') or state.get('day')} {pb.get('time') or state.get('time')} "
                f"at {pb.get('location') or state.get('location')}."
            )
        return (
            "I need a pending booking to confirm. Please provide day, time and location first, "
            "then say yes to write."
        )
    if intent == "provide_slot":
        pb = state.get("pending_booking") or {}
        if state.get("awaiting_confirm") and pb:
            return (
                f"I can offer {pb.get('day')} {pb.get('time')} {pb.get('slot_code', 'SLOT-GEN')} "
                f"at {pb.get('location')}. Reply yes to confirm the write."
            )
        return f"Noted {state.get('day') or 'the day'}. Tell me the time and location to finish the booking."

    if intent == "state_followup":
        loc = state.get("location") or "LOC-HYD"
        if "saturday" in t:
            return f"Saturday follows weekday hours 08:00 to 20:00 at {loc}. I can offer a Saturday SLOT-GEN if you want to book."
        return f"Continuing from our last topic about {state.get('last_topic') or 'your appointment'} at {loc}."

    if "pet" in t or "passport" in t or ("old address" in t):
        return FALLBACK_SENTENCE

    if "allergy" in t and not any(f.get("key") == "allergy" for f in semantic_facts):
        return "I do not have an allergy on file for you."

    if "specialty" in t:
        for f in semantic_facts:
            if f["key"] == "specialty":
                return f"You asked for {f['value']}."

    if "city" in t or "which city" in t:
        for f in semantic_facts:
            if f["key"] == "city":
                return f"You said {f['value']}."
        return FALLBACK_SENTENCE

    if "budget" in t:
        for f in semantic_facts:
            if f["key"] == "budget":
                return f"Your current budget is {f['value']} rupees."
        if intent in {"provide_fact", "update_fact", "kb_question"}:
            return FALLBACK_SENTENCE

    if "preferred doctor" in t or "doctor now" in t or (
        "doctor" in t and ("what" in t or "who" in t)
    ):
        for f in semantic_facts:
            if f["key"] == "preferred_doctor":
                return f"Your preferred doctor is {f['value']}."

    if intent in {"provide_fact", "update_fact"}:
        return "Noted and saved to your profile."

    if "book last time" in t or "what did i book" in t or "problem with it" in t:
        bits = [e["text"] for e in episodes[:3]]
        if bits:
            return "From prior sessions: " + " | ".join(bits)
        return FALLBACK_SENTENCE

    if kb_chunks:
        top = kb_chunks[0]
        cite = top.get("chunk_id") or top.get("doc_id")
        span = top["text"][:280].replace("\n", " ")
        return f"Based on [{cite}] (version {top.get('version')}): {span}"

    if intent == "book_start" or state.get("awaiting_confirm"):
        pb = state.get("pending_booking") or {}
        if pb:
            return (
                f"Confirm booking: {pb.get('name')}, {pb.get('specialty')}, "
                f"{pb.get('day')} {pb.get('time')}, {pb.get('location')}. Reply yes to write."
            )
        missing = [k for k in ["name", "specialty", "day", "location"] if not state.get(k)]
        if missing:
            return f"To book I still need: {', '.join(missing)}. Which should we set first?"
        return "I can help you book a SLOT-GEN appointment."

    if intent == "complaint":
        return "I logged your complaint as an episode for future visits."

    if intent == "chitchat":
        return "Glad to help. Anything else for your clinic visit?"

    return FALLBACK_SENTENCE
