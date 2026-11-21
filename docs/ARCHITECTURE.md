# RecallBot architecture (V31)

```text
User turn
   │
   ▼
NLU  src.nlu.parse_utterance / classify_intent + entities
   │
   ▼
State tracker  src.state.DialogueState.update_from_nlu
   │
   ▼
Dialogue manager  src.dialogue.DialogueManager.handle_turn
   ├─ SemanticMemory.extract_from_turn / retrieve / forget
   ├─ EpisodicMemory.add / retrieve / reflect / redact
   ├─ STM  src.stm.select_history  (full | trim k=5 | summary)
   ├─ Tools
   │    ├─ search_kb  → HybridIndex (dense + BM25 + RRF, time filter)
   │    ├─ get_appointment
   │    └─ book_slot  (only after confirm_yes)
   └─ NLG  src.nlg.generate_reply  (Ollama if available else template)
          + skills/system_prompt_v1.md + book_appointment_steps_v1.md
```

## Memory homes (CS5)

| Type | Store | Loaded |
|------|-------|--------|
| Short-term | Prompt history | Every turn (model-native) |
| Semantic | `memory/semantic_U1.json` + vectors | External |
| Episodic | `memory/episodic_U1.jsonl` | External |
| Procedural | `skills/*.md` | External → prompt |

## Twist B

Chunks and facts carry `valid_from` / `valid_to`. Retrieval filters expired items as of `AS_OF_DATE_DEFAULT` (2026-11-21). Superseded codes (WAIT-48→WAIT-24, RFD-7D→RFD-14D) are rewritten before search.
