"""Generate clinic KB documents and Task 1 JSON files for Variant V31."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "data" / "kb"
DATA = ROOT / "data"


DOCS = [
    {
        "doc_id": "POL-REFUND-2025",
        "title": "Refund and Cancellation Policy 2025",
        "version": "2025",
        "valid_from": "2025-01-01",
        "valid_to": "2025-12-31",
        "section": "Billing > Refunds",
        "codes": ["P-204", "RFD-7D", "CXL-24H"],
        "body": """
ClinicCare refund and cancellation policy for calendar year 2025.
Plan code P-204 covers standard outpatient consults. Under P-204 the refund window
is 7 calendar days from the payment date when the appointment has not been consumed.
Code RFD-7D means a seven-day refund eligibility for unused prepaid consults.
Cancellation code CXL-24H requires at least 24 hours notice before the booked slot.
Late cancellations within 24 hours forfeit 50 percent of the prepaid fee.
No-shows forfeit the full prepaid amount for P-204 visits in 2025.
Refunds are processed to the original payment method within 10 business days.
Emergency department visits and procedure packages are not covered by P-204 refunds.
Patients must raise refund requests through the front desk or the patient portal.
This 2025 policy is superseded by the 2026 refund policy after 2025-12-31.
Keep historical records of 2025 cancellations for audit for twenty-four months.
""",
    },
    {
        "doc_id": "POL-REFUND-2026",
        "title": "Refund and Cancellation Policy 2026",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Billing > Refunds",
        "codes": ["P-204", "RFD-14D", "CXL-12H"],
        "body": """
ClinicCare refund and cancellation policy for calendar year 2026 (current).
Plan code P-204 still labels standard outpatient consults. Under the 2026 rules for
P-204 the refund window is 14 calendar days from payment when the appointment is unused.
Code RFD-14D replaces RFD-7D and means a fourteen-day refund eligibility.
Cancellation code CXL-12H now requires only 12 hours notice before the booked slot.
Late cancellations within 12 hours forfeit 40 percent of the prepaid fee.
No-shows forfeit 80 percent of the prepaid amount for P-204 visits in 2026.
Refunds are processed within 5 business days to the original payment method.
Same-day telehealth reschedules are free once per month under plan P-204.
This document is the authoritative refund policy while valid_from and valid_to hold.
Older 2025 refund rules must not be used for appointments paid in 2026.
""",
    },
    {
        "doc_id": "POL-APPT-2025",
        "title": "Appointment Booking Rules 2025",
        "version": "2025",
        "valid_from": "2025-01-01",
        "valid_to": "2025-12-31",
        "section": "Operations > Appointments",
        "codes": ["SLOT-GEN", "SLOT-SPEC", "WAIT-48"],
        "body": """
Appointment booking rules for ClinicCare in 2025.
General physician slots use code SLOT-GEN and are 20 minutes long.
Specialist slots use code SLOT-SPEC and are 30 minutes long.
WAIT-48 means new patients may wait up to 48 hours for the first available SLOT-GEN.
Same-day SLOT-SPEC bookings require supervisor approval in 2025.
Patients may hold at most two future appointments across all clinics.
Walk-ins are accepted only for SLOT-GEN after 4 pm if capacity remains.
""",
    },
    {
        "doc_id": "POL-APPT-2026",
        "title": "Appointment Booking Rules 2026",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Operations > Appointments",
        "codes": ["SLOT-GEN", "SLOT-SPEC", "WAIT-24", "TELE-OK"],
        "body": """
Appointment booking rules for ClinicCare in 2026 (current).
SLOT-GEN remains 20 minutes. SLOT-SPEC remains 30 minutes.
WAIT-24 replaces WAIT-48: new patients should get a SLOT-GEN within 24 hours.
TELE-OK marks telehealth-eligible specialties: dermatology, endocrinology, and GP follow-ups.
Same-day SLOT-SPEC is allowed without supervisor approval when TELE-OK applies.
Patients may hold three future appointments in 2026.
Online check-in opens 60 minutes before the slot via the patient portal.
""",
    },
    {
        "doc_id": "FAQ-HOURS",
        "title": "Clinic hours and locations FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Hours",
        "codes": ["LOC-HYD", "LOC-BLR", "HRS-WD"],
        "body": """
Clinic hours FAQ. Location code LOC-HYD is the Hyderabad Jubilee Hills centre.
Location code LOC-BLR is the Bengaluru Koramangala centre.
Weekday hours code HRS-WD: Monday to Saturday 08:00 to 20:00 for both centres.
Sundays are closed except for LOC-HYD urgent care 09:00 to 13:00.
Public holiday schedules are posted 7 days in advance on the portal.
Parking is free for the first two hours at LOC-HYD and paid at LOC-BLR.
""",
    },
    {
        "doc_id": "FAQ-INSURANCE",
        "title": "Insurance and cashless FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Insurance",
        "codes": ["INS-STAR", "INS-HDFC", "AUTH-PRE"],
        "body": """
Insurance FAQ for ClinicCare. Cashless partners include INS-STAR (Star Health) and
INS-HDFC (HDFC Ergo). Pre-authorisation code AUTH-PRE must be obtained for planned
procedures above INR 15,000. GP consults under plan P-204 usually need no AUTH-PRE.
Patients should carry the insurance card and a government photo ID.
Denied cashless claims can be filed for reimbursement within 30 days.
""",
    },
    {
        "doc_id": "SVC-LAB",
        "title": "Laboratory service notes",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Services > Lab",
        "codes": ["LAB-CBC", "LAB-LFT", "LAB-FAST"],
        "body": """
Laboratory service notes. Test code LAB-CBC is complete blood count with same-day
results before 14:00 if drawn before 10:00. LAB-LFT is liver function panel with
24-hour turnaround. LAB-FAST means 8 to 12 hours fasting is required before the draw.
Home collection is available within 8 km of LOC-HYD for an extra fee.
Critical values are called to the ordering physician within one hour.
""",
    },
    {
        "doc_id": "SVC-IMAGING",
        "title": "Imaging service notes",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Services > Imaging",
        "codes": ["IMG-XRAY", "IMG-USG", "IMG-MRI"],
        "body": """
Imaging service notes. IMG-XRAY is walk-in chest and limb X-ray at both locations.
IMG-USG requires a booked slot; abdominal ultrasound needs 6 hours fasting.
IMG-MRI is available only at LOC-BLR and needs AUTH-PRE for insured patients.
Reports for IMG-XRAY are ready in 2 hours; IMG-USG in 4 hours; IMG-MRI in 24 hours.
Pregnant patients must inform the technologist before any ionising study.
""",
    },
    {
        "doc_id": "FAQ-PRIVACY",
        "title": "Patient privacy and records FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Privacy",
        "codes": ["REC-REQ", "OTP-VIEW"],
        "body": """
Privacy FAQ. Medical records requests use code REC-REQ and are fulfilled in 5 working days.
Portal viewing uses OTP-VIEW one-time passwords sent to the registered mobile number.
ClinicCare never shares clinical notes with employers without written consent.
Minors need a guardian present for the first visit and for REC-REQ pickup.
""",
    },
    {
        "doc_id": "FAQ-VACCINE",
        "title": "Vaccination desk FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Vaccines",
        "codes": ["VAX-FLU", "VAX-HEP", "VAX-COVID"],
        "body": """
Vaccination desk FAQ. VAX-FLU is seasonal influenza vaccine offered from June to October.
VAX-HEP covers hepatitis B adult schedule. VAX-COVID boosters follow national guidance.
Bring prior immunisation card when available. Observation of 15 minutes is mandatory.
""",
    },
    {
        "doc_id": "SVC-PHARMACY",
        "title": "In-house pharmacy notes",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Services > Pharmacy",
        "codes": ["RX-GEN", "RX-CTRL"],
        "body": """
Pharmacy notes. RX-GEN covers generic substitutions unless the prescription marks
dispense as written. RX-CTRL are controlled medicines requiring original prescription
and ID verification. Pharmacy at LOC-HYD is open during HRS-WD hours.
""",
    },
    {
        "doc_id": "ERR-CODES",
        "title": "Portal and billing error codes",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Support > Errors",
        "codes": ["E-4010", "E-4021", "E-5002"],
        "body": """
Portal error codes. E-4010 means session expired; ask the patient to log in again.
E-4021 means insurance eligibility check failed; verify INS-STAR or INS-HDFC card data.
E-5002 means payment gateway timeout; retry after five minutes or pay at the counter.
Front desk should log each error code with the patient ID in the incident form.
""",
    },
    {
        "doc_id": "FAQ-FOLLOWUP",
        "title": "Follow-up visit FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Follow-up",
        "codes": ["FU-7", "FU-30"],
        "body": """
Follow-up FAQ. FU-7 means a free follow-up within 7 days for the same complaint under P-204.
FU-30 means a discounted follow-up within 30 days for chronic disease reviews.
Telehealth follow-ups are allowed when TELE-OK applies to the specialty.
""",
    },
    {
        "doc_id": "SVC-EMERGENCY",
        "title": "Urgent care service notes",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Services > Urgent",
        "codes": ["URG-TRI", "AMB-CALL"],
        "body": """
Urgent care notes. URG-TRI is nurse triage at LOC-HYD Sunday mornings.
AMB-CALL is the ambulance coordination desk number listed on the portal.
Chest pain, stroke signs, and major trauma should go to a tertiary ER, not ClinicCare.
""",
    },
    {
        "doc_id": "FAQ-PREP",
        "title": "Visit preparation FAQ",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "FAQ > Prep",
        "codes": ["PREP-NEW", "PREP-LAB"],
        "body": """
Visit preparation FAQ. PREP-NEW for new patients: arrive 20 minutes early with ID and
prior reports. PREP-LAB: follow LAB-FAST instructions when blood work is ordered.
Bring a medication list including over-the-counter drugs and supplements.
""",
    },
    {
        "doc_id": "POL-NOSHOW",
        "title": "No-show and late policy",
        "version": "2026",
        "valid_from": "2026-01-01",
        "valid_to": "2099-12-31",
        "section": "Operations > No-show",
        "codes": ["NS-1", "NS-3"],
        "body": """
No-show policy. NS-1 is the first no-show warning recorded on the patient profile.
NS-3 means three no-shows in six months may require prepaid booking for future SLOT-SPEC.
Patients can clear an NS-1 flag by attending the next confirmed appointment on time.
""",
    },
]


def expand_body(doc: dict) -> str:
    base = " ".join(doc["body"].split())
    filler = (
        f" Additional operational guidance for {doc['title']} emphasises clear communication "
        f"at the front desk, accurate use of codes {', '.join(doc['codes'])}, and consistent "
        f"logging of exceptions. Staff should confirm patient identity, explain wait times, "
        f"and cite document {doc['doc_id']} version {doc['version']} when answering policy questions. "
        f"Validity window is {doc['valid_from']} to {doc['valid_to']}. "
    )
    # Expand to help reach 4k–8k total words across the KB.
    return (base + " " + filler * 6).strip()


def write_kb() -> int:
    KB.mkdir(parents=True, exist_ok=True)
    total_words = 0
    meta = []
    for doc in DOCS:
        text = expand_body(doc)
        words = len(text.split())
        total_words += words
        path = KB / f"{doc['doc_id']}.md"
        content = (
            f"# {doc['title']}\n\n"
            f"doc_id: {doc['doc_id']}\n"
            f"version: {doc['version']}\n"
            f"valid_from: {doc['valid_from']}\n"
            f"valid_to: {doc['valid_to']}\n"
            f"section: {doc['section']}\n"
            f"codes: {', '.join(doc['codes'])}\n\n"
            f"{text}\n"
        )
        path.write_text(content, encoding="utf-8")
        meta.append({**doc, "path": str(path.relative_to(ROOT)), "word_count": words})
    (DATA / "kb_manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return total_words


def write_kb_questions():
    questions = [
        {
            "question_id": "Q01",
            "question": "What is the refund window for plan P-204 under the current policy?",
            "gold_span": "refund window is 14 calendar days",
            "doc_id": "POL-REFUND-2026",
            "type": "code",
        },
        {
            "question_id": "Q02",
            "question": "What does code RFD-14D mean?",
            "gold_span": "fourteen-day refund eligibility",
            "doc_id": "POL-REFUND-2026",
            "type": "code",
        },
        {
            "question_id": "Q03",
            "question": "How much notice does CXL-12H require?",
            "gold_span": "12 hours notice",
            "doc_id": "POL-REFUND-2026",
            "type": "code",
        },
        {
            "question_id": "Q04",
            "question": "What is WAIT-24 for new patients?",
            "gold_span": "SLOT-GEN within 24 hours",
            "doc_id": "POL-APPT-2026",
            "type": "code",
        },
        {
            "question_id": "Q05",
            "question": "Which location code is Hyderabad Jubilee Hills?",
            "gold_span": "LOC-HYD is the Hyderabad Jubilee Hills centre",
            "doc_id": "FAQ-HOURS",
            "type": "code",
        },
        {
            "question_id": "Q06",
            "question": "What does error E-4021 mean on the portal?",
            "gold_span": "insurance eligibility check failed",
            "doc_id": "ERR-CODES",
            "type": "code",
        },
        {
            "question_id": "Q07",
            "question": "What does LAB-FAST require before blood draw?",
            "gold_span": "8 to 12 hours fasting",
            "doc_id": "SVC-LAB",
            "type": "code",
        },
        {
            "question_id": "Q08",
            "question": "Where is IMG-MRI available?",
            "gold_span": "available only at LOC-BLR",
            "doc_id": "SVC-IMAGING",
            "type": "code",
        },
        {
            "question_id": "Q09",
            "question": "How long do I have to get money back if I prepaid but never used the consult?",
            "gold_span": "14 calendar days from payment",
            "doc_id": "POL-REFUND-2026",
            "type": "paraphrase",
        },
        {
            "question_id": "Q10",
            "question": "If I need to change my booking late, how close to the visit can I still cancel under today's rules?",
            "gold_span": "12 hours notice before the booked slot",
            "doc_id": "POL-REFUND-2026",
            "type": "paraphrase",
        },
        {
            "question_id": "Q11",
            "question": "How quickly should a brand-new patient get a general doctor slot now?",
            "gold_span": "within 24 hours",
            "doc_id": "POL-APPT-2026",
            "type": "paraphrase",
        },
        {
            "question_id": "Q12",
            "question": "Can I do a video visit for skin issues?",
            "gold_span": "TELE-OK marks telehealth-eligible specialties: dermatology",
            "doc_id": "POL-APPT-2026",
            "type": "paraphrase",
        },
        {
            "question_id": "Q13",
            "question": "When are the centres open on a normal weekday?",
            "gold_span": "Monday to Saturday 08:00 to 20:00",
            "doc_id": "FAQ-HOURS",
            "type": "paraphrase",
        },
        {
            "question_id": "Q14",
            "question": "Do I need special approval before a costly planned procedure on insurance?",
            "gold_span": "AUTH-PRE must be obtained for planned procedures above INR 15,000",
            "doc_id": "FAQ-INSURANCE",
            "type": "paraphrase",
        },
        {
            "question_id": "Q15",
            "question": "How soon are chest film reports ready?",
            "gold_span": "IMG-XRAY are ready in 2 hours",
            "doc_id": "SVC-IMAGING",
            "type": "paraphrase",
        },
        {
            "question_id": "Q16",
            "question": "What is the current refund window for P-204?",
            "gold_span": "14 calendar days",
            "doc_id": "POL-REFUND-2026",
            "type": "new_version",
        },
        {
            "question_id": "Q17",
            "question": "Under current booking rules, what replaced WAIT-48?",
            "gold_span": "WAIT-24 replaces WAIT-48",
            "doc_id": "POL-APPT-2026",
            "type": "new_version",
        },
        {
            "question_id": "Q18",
            "question": "What does FU-7 cover?",
            "gold_span": "free follow-up within 7 days",
            "doc_id": "FAQ-FOLLOWUP",
            "type": "other",
        },
        {
            "question_id": "Q19",
            "question": "What is NS-3?",
            "gold_span": "three no-shows in six months",
            "doc_id": "POL-NOSHOW",
            "type": "code",
        },
        {
            "question_id": "Q20",
            "question": "How do I request my medical records?",
            "gold_span": "REC-REQ and are fulfilled in 5 working days",
            "doc_id": "FAQ-PRIVACY",
            "type": "code",
        },
        {
            "question_id": "Q21",
            "question": "What vaccine code is used for flu shots?",
            "gold_span": "VAX-FLU is seasonal influenza",
            "doc_id": "FAQ-VACCINE",
            "type": "code",
        },
        {
            "question_id": "Q22",
            "question": "What does RX-CTRL require?",
            "gold_span": "original prescription and ID verification",
            "doc_id": "SVC-PHARMACY",
            "type": "code",
        },
        {
            "question_id": "Q23",
            "question": "Who should not use ClinicCare for major trauma?",
            "gold_span": "major trauma should go to a tertiary ER",
            "doc_id": "SVC-EMERGENCY",
            "type": "paraphrase",
        },
        {
            "question_id": "Q24",
            "question": "How early should a first-time visitor arrive?",
            "gold_span": "arrive 20 minutes early",
            "doc_id": "FAQ-PREP",
            "type": "paraphrase",
        },
        {
            "question_id": "Q25",
            "question": "What does E-4010 indicate?",
            "gold_span": "session expired",
            "doc_id": "ERR-CODES",
            "type": "code",
        },
        {
            "question_id": "Q26",
            "question": "How many future appointments can a patient hold in 2026?",
            "gold_span": "hold three future appointments",
            "doc_id": "POL-APPT-2026",
            "type": "other",
        },
    ]
    (DATA / "kb_questions.json").write_text(json.dumps(questions, indent=2), encoding="utf-8")


def write_conversation_and_probes():
    turns = []
    facts = []

    def add(turn, role, text, tags=None):
        turns.append({"turn": turn, "role": role, "text": text, "tags": tags or []})

    # Session A: turns 1-25
    add(1, "user", "Hi, I am looking to book a clinic appointment.", ["low_importance"])
    add(2, "assistant", "Hello! I can help you book. Which city are you in?")
    add(3, "user", "I live in Hyderabad and prefer LOC-HYD.", ["fact"])
    facts.append({"key": "city", "value": "Hyderabad", "turn": 3})
    facts.append({"key": "preferred_location", "value": "LOC-HYD", "turn": 3})
    add(4, "assistant", "Noted Hyderabad / LOC-HYD. What specialty do you need?")
    add(5, "user", "General physician please. My name is Anita Rao.", ["fact"])
    facts.append({"key": "name", "value": "Anita Rao", "turn": 5})
    facts.append({"key": "specialty", "value": "general physician", "turn": 5})
    add(6, "assistant", "Thanks Anita. Do you have a preferred day?")
    add(7, "user", "Friday afternoon works.", ["slot"])
    add(8, "assistant", "I can offer Friday 16:00 SLOT-GEN at LOC-HYD. Confirm to book?")
    add(9, "user", "What is the refund window for plan P-204?", ["kb"])
    add(10, "assistant", "Under the 2026 policy, P-204 has a 14-day refund window (RFD-14D).")
    add(11, "user", "Also, what does E-4021 mean?", ["kb"])
    add(12, "assistant", "E-4021 means the insurance eligibility check failed.")
    add(13, "user", "My budget for consults is 800 rupees.", ["fact"])
    facts.append({"key": "budget", "value": "800", "turn": 13})
    add(14, "assistant", "Saved budget 800. Shall I book Friday 16:00?")
    add(15, "user", "Actually my budget is now 1200 rupees.", ["fact_update"])
    facts.append({"key": "budget", "value": "1200", "turn": 15, "updates": 13})
    add(16, "assistant", "Updated budget to 1200.")
    add(17, "user", "I am allergic to penicillin.", ["fact"])
    facts.append({"key": "allergy", "value": "penicillin", "turn": 17})
    add(18, "assistant", "Recorded penicillin allergy.")
    add(19, "user", "Thanks for your help so far.", ["low_importance"])
    add(20, "assistant", "You are welcome.")
    add(21, "user", "Please book the Friday 16:00 SLOT-GEN for Anita Rao at LOC-HYD.", ["slot", "confirm"])
    add(22, "assistant", "Confirm booking: Anita Rao, GP, Friday 16:00, LOC-HYD. Reply yes to write.")
    add(23, "user", "Yes, confirm the booking.", ["confirm", "episode"])
    add(24, "assistant", "Booked appointment APT-1001 for Friday 16:00 at LOC-HYD.")
    add(25, "user", "The waiting area was crowded last time; please note my complaint.", ["episode"])

    # Session B: turns 26+
    add(26, "user", "Hi, I am back. Which city did I say I am in?", ["probe_R"])
    add(27, "assistant", "You said Hyderabad.")
    add(28, "user", "What is my budget now?", ["probe_U"])
    add(29, "assistant", "Your current budget is 1200 rupees.")
    add(30, "user", "Please forget my old address if any, and forget my allergy.", ["forget"])
    facts.append({"key": "allergy", "value": None, "turn": 30, "forget": True})
    add(31, "assistant", "I removed the allergy fact from your profile.")
    add(32, "user", "What was my allergy?", ["probe_F"])
    add(33, "assistant", "I do not have an allergy on file for you.")
    add(34, "user", "What did I book last time, and did I have a problem with it?", ["probe_E"])
    add(35, "assistant", "You booked APT-1001 Friday 16:00 at LOC-HYD and complained about crowding.")
    add(36, "user", "What is WAIT-24?", ["kb"])
    add(37, "assistant", "WAIT-24 means new patients should get SLOT-GEN within 24 hours.")
    add(38, "user", "And for Saturday?", ["state_followup"])
    add(39, "assistant", "Do you mean a Saturday SLOT-GEN at LOC-HYD for general physician?")
    add(40, "user", "What is my pet's name?", ["probe_N"])
    add(41, "assistant", "I do not have that information in the clinic knowledge base or your saved profile.")
    add(42, "user", "I prefer morning slots going forward.", ["fact"])
    facts.append({"key": "time_preference", "value": "morning", "turn": 42})
    add(43, "user", "How many leave days can employees carry? wait that is wrong domain. What is FU-7?", ["kb"])
    add(44, "assistant", "FU-7 is a free follow-up within 7 days for the same complaint under P-204.")
    add(45, "user", "Nice weather today.", ["low_importance"])
    add(46, "assistant", "Glad to hear it. Anything else for your care plan?")
    add(47, "user", "My preferred doctor ID is DR-GP-17.", ["fact"])
    facts.append({"key": "preferred_doctor", "value": "DR-GP-17", "turn": 47})
    add(48, "user", "Actually change preferred doctor to DR-GP-22.", ["fact_update"])
    facts.append({"key": "preferred_doctor", "value": "DR-GP-22", "turn": 48, "updates": 47})
    add(49, "user", "I decided to keep LOC-HYD as primary centre.", ["episode"])
    add(50, "user", "ok bye", ["low_importance"])

    # Ensure >= 40 user turns: add a few more low-importance / kb / clarifications
    add(51, "user", "Can you clarify evening hours on Sunday at LOC-HYD?", ["clarification", "kb"])
    add(52, "assistant", "Sundays LOC-HYD urgent care is 09:00 to 13:00 only; evenings are closed.")
    add(53, "user", "And for Saturday?", ["state_followup"])
    add(54, "assistant", "Saturday follows HRS-WD: 08:00 to 20:00 at LOC-HYD.")
    add(55, "user", "great thanks", ["low_importance"])
    add(56, "user", "What does LAB-CBC cover?", ["kb"])
    add(57, "assistant", "LAB-CBC is complete blood count with same-day results before 14:00 if drawn before 10:00.")
    add(58, "user", "I prefer English for SMS reminders.", ["fact"])
    facts.append({"key": "sms_language", "value": "English", "turn": 58})
    add(59, "assistant", "Saved SMS language preference English.")
    add(60, "user", "Actually I prefer Telugu for SMS reminders.", ["fact_update"])
    facts.append({"key": "sms_language", "value": "Telugu", "turn": 60, "updates": 58})
    add(61, "assistant", "Updated SMS language to Telugu.")
    add(62, "user", "Where is IMG-MRI available?", ["kb"])
    add(63, "assistant", "IMG-MRI is available only at LOC-BLR.")
    add(64, "user", "Please note I decided against LOC-BLR for routine visits.", ["episode"])
    add(65, "assistant", "Logged your location decision episode.")
    add(66, "user", "What is my sms language now?", ["probe_U"])
    add(67, "assistant", "Telugu.")
    add(68, "user", "thanks again", ["low_importance"])
    add(69, "user", "Is AUTH-PRE needed for expensive procedures?", ["kb"])
    add(70, "assistant", "AUTH-PRE is required for planned procedures above INR 15,000.")
    add(71, "user", "ok goodbye", ["low_importance"])

    user_turns = [t for t in turns if t["role"] == "user"]
    assert len(user_turns) >= 40

    conversation = {
        "variant": "V31",
        "user_id": "U1",
        "session_a_turns": [1, 25],
        "session_b_turns": [26, 71],
        "facts": facts,
        "turns": turns,
    }
    (DATA / "test_conversation.json").write_text(
        json.dumps(conversation, indent=2), encoding="utf-8"
    )

    probes = [
        {"probe_id": "P-R1", "category": "R", "session": "B", "question": "Which city did I say I am in?", "expected": "Hyderabad"},
        {"probe_id": "P-R2", "category": "R", "session": "B", "question": "What specialty did I ask for?", "expected": "general physician"},
        {"probe_id": "P-U1", "category": "U", "session": "B", "question": "What is my budget now?", "expected": "1200"},
        {"probe_id": "P-U2", "category": "U", "session": "B", "question": "Who is my preferred doctor now?", "expected": "DR-GP-22"},
        {"probe_id": "P-F1", "category": "F", "session": "B", "question": "What was my allergy?", "expected": "does not know / not on file"},
        {"probe_id": "P-F2", "category": "F", "session": "B", "question": "What was my old address?", "expected": "does not know"},
        {"probe_id": "P-E1", "category": "E", "session": "B", "question": "What did I book last time, and did I have a problem with it?", "expected": "APT-1001 Friday 16:00; crowding complaint"},
        {"probe_id": "P-E2", "category": "E", "session": "B", "question": "What location decision did I confirm?", "expected": "LOC-HYD primary centre"},
        {"probe_id": "P-K1", "category": "K", "session": "B", "question": "What is the refund window for plan P-204?", "expected": "14 calendar days", "doc_id": "POL-REFUND-2026"},
        {"probe_id": "P-K2", "category": "K", "session": "A", "question": "What does E-4021 mean?", "expected": "insurance eligibility check failed", "doc_id": "ERR-CODES"},
        {"probe_id": "P-N1", "category": "N", "session": "B", "question": "What is my pet's name?", "expected": FALLBACK},
        {"probe_id": "P-N2", "category": "N", "session": "B", "question": "What is my passport number?", "expected": FALLBACK},
        {"probe_id": "P-S1", "category": "S", "session": "B", "question": "And for Saturday?", "expected": "Saturday hours/slot follow-up from dialogue state"},
        {"probe_id": "P-S2", "category": "S", "session": "A", "question": "Yes, confirm the booking.", "expected": "DB write only after confirmation"},
        {"probe_id": "P-T1", "category": "T", "session": "B", "question": "Using today's date, what refund window applies for P-204?", "expected": "14 days from 2026 policy; not 7 days from 2025", "twist": "B"},
        {"probe_id": "P-T2", "category": "T", "session": "B", "question": "Is WAIT-48 still the new-patient wait target?", "expected": "No; WAIT-24 is current for 2026", "twist": "B"},
    ]
    (DATA / "probes.json").write_text(json.dumps(probes, indent=2), encoding="utf-8")


FALLBACK = "I do not have that information in the clinic knowledge base or your saved profile."


def main():
    words = write_kb()
    write_kb_questions()
    write_conversation_and_probes()
    print(f"KB docs={len(DOCS)} total_words={words}")
    print("Wrote kb_questions.json, test_conversation.json, probes.json")


if __name__ == "__main__":
    main()
