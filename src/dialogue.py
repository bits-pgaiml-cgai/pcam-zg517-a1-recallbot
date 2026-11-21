from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import AS_OF_DATE_DEFAULT, CONTEXT_WINDOW, FALLBACK_SENTENCE, MEMORY_DIR
from src.memory.episodic import EpisodicMemory
from src.memory.semantic import SemanticMemory
from src.nlg import generate_reply, load_system_prompt, load_task_steps
from src.nlu import parse_utterance
from src.retrieval import HybridIndex
from src.state import DialogueState
from src.stm import select_history
from src.tokens import count_tokens
from src.tools import book_slot, retrieved_token_total, search_kb


class DialogueManager:
    def __init__(
        self,
        index: HybridIndex,
        *,
        config: str = "hybrid_mem",
        stm_strategy: str = "trim",
        user_id: str = "U1",
        enable_rag: bool = True,
        enable_semantic: bool = True,
        enable_episodic: bool = True,
        as_of: str = AS_OF_DATE_DEFAULT,
    ):
        self.index = index
        self.config = config
        self.stm_strategy = stm_strategy
        self.user_id = user_id
        self.enable_rag = enable_rag
        self.enable_semantic = enable_semantic
        self.enable_episodic = enable_episodic
        self.as_of = as_of
        self.state = DialogueState(user_id=user_id)
        self.history: List[Dict] = []
        self.summary_state: Dict = {}
        self.semantic = SemanticMemory(MEMORY_DIR / f"semantic_{user_id}.json")
        self.episodic = EpisodicMemory(MEMORY_DIR / f"episodic_{user_id}.jsonl")

    def handle_turn(self, text: str, session: str, turn: int) -> Dict:
        parsed = parse_utterance(
            text, config=self.config, user=self.user_id, session=session, turn=turn
        )
        self.state.update_from_nlu(parsed)
        intent = parsed["intent"]

        if self.enable_semantic:
            self.semantic.extract_from_turn(
                self.user_id, text, turn, config=self.config, session=session, as_of=self.as_of
            )
            if intent == "forget_fact" and "allergy" in text.lower():
                self.episodic.redact_mentioning(self.user_id, "allergy")

        kb_chunks: List[Dict] = []
        if self.enable_rag and intent in {"kb_question", "state_followup", "unknown"}:
            kb_chunks = search_kb(
                text,
                self.index,
                top_k=3,
                as_of=self.as_of,
                apply_time_filter=True,
                config=self.config,
                user=self.user_id,
                session=session,
                turn=turn,
            )
            if kb_chunks:
                self.state.last_kb_doc = kb_chunks[0].get("doc_id")
                self.state.last_topic = "kb"

        semantic_facts = []
        if self.enable_semantic:
            semantic_facts = self.semantic.retrieve(self.user_id, text, as_of=self.as_of)
            # Prefer exact profile keys for "what is my ..." recall probes.
            active = self.semantic.active_facts(self.user_id, as_of=self.as_of)
            key_map = {
                "city": "city",
                "budget": "budget",
                "allergy": "allergy",
                "doctor": "preferred_doctor",
                "specialty": "specialty",
                "sms": "sms_language",
                "language": "sms_language",
            }
            low = text.lower()
            for tip, key in key_map.items():
                if tip in low:
                    matched = [f for f in active if f["key"] == key]
                    if matched:
                        semantic_facts = matched + [f for f in semantic_facts if f["key"] != key]

        episodes = (
            self.episodic.retrieve(self.user_id, text)
            if self.enable_episodic
            else []
        )

        just_booked = False
        if intent == "confirm_yes" and self.state.awaiting_confirm:
            result = book_slot(
                {**self.state.pending_booking, "id": "APT-1001"},
                confirmed=True,
                config=self.config,
                user=self.user_id,
                session=session,
                turn=turn,
            )
            self.state.booked_appointment_id = result.get("id")
            just_booked = True
            if self.enable_episodic:
                self.episodic.add(
                    self.user_id,
                    f"Booked {result.get('id')} {self.state.pending_booking}",
                    turn,
                    config=self.config,
                    session=session,
                    kind="booking",
                )
            self.state.awaiting_confirm = False

        if intent == "complaint" and self.enable_episodic:
            self.episodic.add(
                self.user_id, text, turn, config=self.config, session=session, kind="complaint"
            )

        if "decided" in text.lower() and self.enable_episodic:
            self.episodic.add(
                self.user_id, text, turn, config=self.config, session=session, kind="decision"
            )

        history_text, self.summary_state = select_history(
            self.history,
            self.stm_strategy if self.config in {"full", "trim", "summary"} else "trim",
            config=self.config,
            user=self.user_id,
            session=session,
            turn=turn,
            summary_state=self.summary_state,
        )

        retrieved_tokens = retrieved_token_total(kb_chunks)
        retrieved_tokens += sum(
            count_tokens(f"{f['key']}:{f['value']}") for f in semantic_facts
        )
        retrieved_tokens += sum(count_tokens(e.get("text", "")) for e in episodes)

        state_for_nlg = self.state.to_dict()
        if just_booked:
            state_for_nlg["awaiting_confirm"] = True
            state_for_nlg["just_booked"] = True
        reply = generate_reply(
            user_text=text,
            intent=intent,
            state=state_for_nlg,
            kb_chunks=kb_chunks,
            semantic_facts=semantic_facts,
            episodes=episodes,
            history_text=history_text,
            config=self.config,
            user=self.user_id,
            session=session,
            turn=turn,
            retrieved_tokens=retrieved_tokens,
        )

        self.history.append({"role": "user", "text": text, "turn": turn})
        self.history.append({"role": "assistant", "text": reply, "turn": turn})
        self.state.save(MEMORY_DIR / f"state_{self.user_id}.json")
        self.semantic.save()
        self.episodic.save()

        return {
            "reply": reply,
            "intent": intent,
            "state": self.state.to_dict(),
            "kb_chunks": [
                {"chunk_id": c.get("chunk_id"), "doc_id": c.get("doc_id"), "score": c.get("score")}
                for c in kb_chunks
            ],
            "retrieved_tokens": retrieved_tokens,
        }

    def end_session_reflection(self, session: str, turn: int) -> Optional[Dict]:
        if not self.enable_episodic:
            return None
        return self.episodic.reflect(
            self.user_id, config=self.config, session=session, turn=turn
        )

    def context_assembly_table(self, current_user_text: str) -> List[Dict]:
        system = load_system_prompt() + "\n" + load_task_steps()
        history_text, _ = select_history(
            self.history,
            "trim",
            config=self.config,
            user=self.user_id,
            session="B",
            turn=0,
            summary_state=dict(self.summary_state),
        )
        facts = self.semantic.active_facts(self.user_id, as_of=self.as_of)
        episodes = self.episodic.retrieve(self.user_id, current_user_text, top_k=2)
        kb = search_kb(
            current_user_text,
            self.index,
            top_k=2,
            as_of=self.as_of,
            config=self.config,
            user=self.user_id,
            session="B",
            turn=0,
        ) if self.enable_rag else []
        rows = [
            {"part": "system+skills", "memory_type": "procedural", "home": "external→prompt", "tokens": count_tokens(system)},
            {"part": "tools schema", "memory_type": "procedural", "home": "model-native", "tokens": 80},
            {"part": "semantic facts", "memory_type": "semantic", "home": "external", "tokens": sum(count_tokens(f"{f['key']}:{f['value']}") for f in facts)},
            {"part": "episodic", "memory_type": "episodic", "home": "external", "tokens": sum(count_tokens(e['text']) for e in episodes)},
            {"part": "history", "memory_type": "short-term", "home": "model-native", "tokens": count_tokens(history_text)},
            {"part": "retrieved kb", "memory_type": "semantic-domain", "home": "external", "tokens": retrieved_token_total(kb)},
            {"part": "current user", "memory_type": "short-term", "home": "model-native", "tokens": count_tokens(current_user_text)},
            {"part": "reply headroom", "memory_type": "n/a", "home": "reserved", "tokens": 256},
        ]
        total = sum(r["tokens"] for r in rows)
        rows.append({"part": "TOTAL", "memory_type": "-", "home": "-", "tokens": total, "fits_window": total <= CONTEXT_WINDOW, "fallback": FALLBACK_SENTENCE})
        return rows
