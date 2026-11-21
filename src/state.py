from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DialogueState:
    user_id: str = "U1"
    intent: str = ""
    name: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    specialty: Optional[str] = None
    day: Optional[str] = None
    time: Optional[str] = None
    doctor_id: Optional[str] = None
    budget: Optional[str] = None
    allergy: Optional[str] = None
    time_preference: Optional[str] = None
    pending_booking: Dict[str, Any] = field(default_factory=dict)
    awaiting_confirm: bool = False
    last_topic: Optional[str] = None
    last_kb_doc: Optional[str] = None
    booked_appointment_id: Optional[str] = None
    clarification_asked: Optional[str] = None

    def update_from_nlu(self, parsed: Dict) -> None:
        self.intent = parsed.get("intent", "")
        ents = parsed.get("entities", {})
        for key in (
            "name",
            "city",
            "location",
            "day",
            "time",
            "doctor_id",
            "budget",
            "allergy",
        ):
            if key in ents:
                setattr(self, key, ents[key])
        text = parsed.get("text", "").lower()
        if "general physician" in text or "gp" in text:
            self.specialty = "general physician"
        if "morning" in text:
            self.time_preference = "morning"
        if self.intent in {"book_start", "provide_slot"} or (
            self.intent in {"provide_fact", "update_fact"} and self.day and self.location
        ):
            self._refresh_pending()
        if self.intent == "state_followup":
            self.last_topic = self.last_topic or "hours_or_slot"
        if self.day and not self.last_topic:
            self.last_topic = "appointment_day"

    def _refresh_pending(self) -> None:
        if self.name and self.specialty and self.day and (self.time or self.time_preference) and self.location:
            self.pending_booking = {
                "name": self.name,
                "specialty": self.specialty,
                "day": self.day,
                "time": self.time or ("09:00" if self.time_preference == "morning" else "16:00"),
                "location": self.location,
                "slot_code": "SLOT-GEN",
            }
            self.awaiting_confirm = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueState":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "DialogueState":
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


STATE_FIELDS = [
    "user_id",
    "intent",
    "name",
    "city",
    "location",
    "specialty",
    "day",
    "time",
    "doctor_id",
    "budget",
    "allergy",
    "time_preference",
    "pending_booking",
    "awaiting_confirm",
    "last_topic",
    "last_kb_doc",
    "booked_appointment_id",
    "clarification_asked",
]
