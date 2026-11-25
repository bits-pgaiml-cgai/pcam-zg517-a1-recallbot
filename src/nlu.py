from __future__ import annotations

import re
import time
from typing import Dict, List, Tuple

from src.logging_util import log_call

INTENTS = [
    "greet",
    "provide_fact",
    "update_fact",
    "forget_fact",
    "recall_profile",
    "kb_question",
    "book_start",
    "provide_slot",
    "confirm_yes",
    "confirm_no",
    "state_followup",
    "complaint",
    "chitchat",
    "unknown",
]


def _entities(text: str) -> Dict[str, str]:
    ents = {}
    m = re.search(r"\b(LOC-[A-Z]+)\b", text, re.I)
    if m:
        ents["location"] = m.group(1).upper()
    m = re.search(r"\b(DR-[A-Z0-9-]+)\b", text, re.I)
    if m:
        ents["doctor_id"] = m.group(1).upper()
    m = re.search(r"\b(P-\d+|E-\d+|RFD-\w+|CXL-\w+|WAIT-\d+|FU-\d+|LAB-\w+|IMG-\w+|VAX-\w+|SLOT-\w+)\b", text, re.I)
    if m:
        ents["code"] = m.group(1).upper()
    m = re.search(r"budget.*?(\d{3,5})", text, re.I)
    if m:
        ents["budget"] = m.group(1)
    m = re.search(r"allergic to ([a-zA-Z]+)", text, re.I)
    if m:
        ents["allergy"] = m.group(1).lower()
    m = re.search(r"(Hyderabad|Bengaluru|Bangalore|Chennai|Mumbai)", text, re.I)
    if m:
        ents["city"] = m.group(1)
    m = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", text, re.I)
    if m:
        ents["day"] = m.group(1)
    m = re.search(r"(\d{1,2}:\d{2})", text)
    if m:
        ents["time"] = m.group(1)
    m = re.search(r"my name is ([A-Za-z ]+)", text, re.I)
    if m:
        ents["name"] = m.group(1).strip()
    if "name" not in ents:
        m = re.search(r"\bfor ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
        if m:
            ents["name"] = m.group(1).strip()
    return ents


def classify_intent(text: str) -> str:
    t = text.lower().strip()
    if re.search(r"\b(hi|hello|hey)\b", t) and "?" not in text and "which" not in t:
        return "greet"
    if "forget" in t or "remove my" in t or "delete my" in t:
        return "forget_fact"
    if "remember about me" in t or "list everything you currently remember" in t or (
        "list everything" in t and "remember" in t
    ):
        return "recall_profile"
    if re.search(r"\b(actually|change|update|instead)\b", t) and (
        "budget" in t or "doctor" in t or "prefer" in t or "sms" in t
    ):
        return "update_fact"
    if re.search(r"\bwhat is my\b", t) and any(
        k in t for k in ("budget", "city", "allergy", "doctor", "sms")
    ):
        return "provide_fact"
    if t in {"yes", "yes, confirm the booking.", "confirm", "yes confirm"} or t.startswith("yes,"):
        return "confirm_yes"
    if t in {"no", "cancel"}:
        return "confirm_no"
    if t.startswith("and for ") or t == "and for saturday?":
        return "state_followup"
    if "book" in t or "appointment" in t:
        return "book_start"
    if re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", t) and (
        "works" in t or "afternoon" in t or "morning" in t or re.search(r"\d{1,2}:\d{2}", t)
    ):
        return "provide_slot"
    if "complaint" in t or "crowded" in t or "problem" in t:
        return "complaint"
    if "?" in text or re.search(
        r"\b(what|how|where|when|which|refund|window|mean|policy|code|wait)\b", t
    ):
        return "kb_question"
    if any(k in t for k in ["live in", "prefer", "allergic", "budget", "my name", "doctor"]):
        return "provide_fact"
    if any(k in t for k in ["thanks", "thank you", "bye", "nice weather", "ok bye"]):
        return "chitchat"
    return "unknown"


def parse_utterance(
    text: str,
    *,
    config: str,
    user: str,
    session: str,
    turn: int,
) -> Dict:
    start = time.time()
    intent = classify_intent(text)
    ents = _entities(text)
    log_call(
        config=config,
        user=user,
        session=session,
        turn=turn,
        call_type="nlu",
        model="rule-nlu",
        input_tokens=len(text.split()),
        output_tokens=1,
        retrieved_tokens=0,
        start=start,
    )
    return {"intent": intent, "entities": ents, "text": text}


def nlu_accuracy(labelled: List[Tuple[str, str]]) -> float:
    correct = sum(1 for text, gold in labelled if classify_intent(text) == gold)
    return correct / max(1, len(labelled))


LABELLED_UTTERANCES = [
    ("Hi there", "greet"),
    ("Hello", "greet"),
    ("I live in Hyderabad", "provide_fact"),
    ("My budget for consults is 800 rupees", "provide_fact"),
    ("I am allergic to penicillin", "provide_fact"),
    ("Actually my budget is now 1200 rupees", "update_fact"),
    ("Actually change preferred doctor to DR-GP-22", "update_fact"),
    ("Please forget my allergy", "forget_fact"),
    ("Please forget my old address if any, and forget my allergy", "forget_fact"),
    ("What is the refund window for plan P-204?", "kb_question"),
    ("What does E-4021 mean?", "kb_question"),
    ("What is WAIT-24?", "kb_question"),
    ("Please book a clinic appointment", "book_start"),
    ("I want to book an appointment", "book_start"),
    ("Friday afternoon works", "provide_slot"),
    ("Yes, confirm the booking", "confirm_yes"),
    ("yes", "confirm_yes"),
    ("And for Saturday?", "state_followup"),
    ("The waiting area was crowded last time; please note my complaint", "complaint"),
    ("Thanks for your help so far", "chitchat"),
    ("nice weather today", "chitchat"),
    ("ok bye", "chitchat"),
]
