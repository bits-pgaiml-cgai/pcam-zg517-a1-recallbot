"""Generate report.pdf for Mini Project 1 (V31)."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report.pdf"
RESULTS = ROOT / "results"
LOGS = ROOT / "logs"
MEMORY = ROOT / "memory"
SKILLS = ROOT / "skills"
PLOTS = RESULTS / "plots"


def load_json(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def hit_rate_table():
    rows = list(csv.DictReader((RESULTS / "hit_rate.csv").open(encoding="utf-8")))
    agg = defaultdict(list)
    by_type = defaultdict(list)
    for r in rows:
        key = (r["method"], r["chunk_size"], r["k"])
        agg[key].append(int(r["hit"]))
        by_type[(r["method"], r["chunk_size"], r["k"], r["qtype"])].append(int(r["hit"]))

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    data = [["method", "chunk", "@1", "@3", "@5", "code@5", "para@5"]]
    for method in ("dense", "bm25", "hybrid"):
        for cs in ("128", "512"):
            data.append(
                [
                    method,
                    cs,
                    f"{mean(agg[(method, cs, '1')]):.3f}",
                    f"{mean(agg[(method, cs, '3')]):.3f}",
                    f"{mean(agg[(method, cs, '5')]):.3f}",
                    f"{mean(by_type[(method, cs, '5', 'code')]):.3f}",
                    f"{mean(by_type[(method, cs, '5', 'paraphrase')]):.3f}",
                ]
            )
    return data


def mean_tokens_for_runs(config: str, run_ids: set[str]):
    by = defaultdict(lambda: {"in": 0, "out": 0})
    path = LOGS / "calls.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("config") != config or r.get("call_type") != "chat":
            continue
        if r.get("run_id") not in run_ids:
            continue
        t = r["turn"]
        by[t]["in"] += r.get("input_tokens", 0)
        by[t]["out"] += r.get("output_tokens", 0)
    n = len(by)
    if not n:
        return None
    return {
        "turns": n,
        "mean_input": sum(v["in"] for v in by.values()) / n,
        "mean_output": sum(v["out"] for v in by.values()) / n,
        "total_tokens": sum(v["in"] + v["out"] for v in by.values()),
    }


def stm_totals():
    totals = defaultdict(int)
    for line in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        cfg = r.get("config")
        if cfg in {"full", "trim", "summary"} and r.get("run_id") in {
            "r_full_A",
            "r_trim_A",
            "r_summary_A",
        }:
            totals[cfg] += r.get("input_tokens", 0) + r.get("output_tokens", 0)
    return dict(totals)


def styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "T",
            parent=base["Title"],
            fontSize=14,
            leading=18,
            spaceAfter=6,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=10,
            leading=12,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "B",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=11,
            alignment=TA_JUSTIFY,
            spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "S",
            parent=base["BodyText"],
            fontSize=7.5,
            leading=9.5,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "mono": ParagraphStyle(
            "M",
            parent=base["Code"],
            fontSize=6.5,
            leading=8,
            fontName="Courier",
        ),
        "caption": ParagraphStyle(
            "C",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#333333"),
        ),
    }
    return styles


def table(data, col_widths=None, font_size=7):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def build():
    st = styles()
    story = []
    ablation = load_json("ablation_summary.json")
    cost = load_json("cost_scale.json")
    nlu = load_json("nlu_accuracy.json")
    sem = load_json("semantic_precision_recall.json")
    epi = load_json("episodic_weights.json")
    ctx = json.loads((MEMORY / "context_assembly_session_b.json").read_text(encoding="utf-8"))
    stm_tok = stm_totals()
    trim_stats = mean_tokens_for_runs("trim", {"r_trim_A"})
    hm_stats = mean_tokens_for_runs("hybrid_mem", {"r_hm_A", "r_hm_B"})
    if not hm_stats:
        hm_stats = mean_tokens_for_runs("hybrid_mem", {"r_hybrid_mem_A2", "r_hybrid_mem_B2"})
    prefix = cost["token_economics"][0]["prefix_tokens"]
    prices = {"input": 2.50, "output": 10.00, "cached_input": 1.25}

    def monthly(stats):
        days, users = 30, 5000
        convos = users * days
        turns = stats["turns"]
        mi = max(stats["mean_input"], prefix)
        mo = stats["mean_output"]
        in_tok = mi * turns * convos
        out_tok = mo * turns * convos
        no = (in_tok / 1e6) * prices["input"] + (out_tok / 1e6) * prices["output"]
        cache = (
            (prefix * turns * convos / 1e6) * prices["cached_input"]
            + (max(0.0, mi - prefix) * turns * convos / 1e6) * prices["input"]
            + (out_tok / 1e6) * prices["output"]
        )
        return round(no, 2), round(cache, 2)

    story.append(Paragraph("RecallBot Mini Project 1 Report — Variant V31", st["title"]))
    story.append(
        Paragraph(
            "PCA MZG517 Conversational Generative AI · Venkata Srinivasa Rao Tunuguntla · "
            "Clinic appointment desk · Twist B (time-bound facts) · k=5 · ctx=4096 · scale=5,000",
            st["caption"],
        )
    )

    # §1 Variant / stack
    story.append(Paragraph("1. Variant, models and hardware", st["h1"]))
    story.append(
        Paragraph(
            "Variant <b>V31</b>: ClinicCare appointment desk; Twist <b>B. Time-bound facts</b> "
            "(chunks/facts carry <font face='Courier'>valid_from</font>/<font face='Courier'>valid_to</font>; "
            "as-of date 2026-11-21). Trim window <b>k=5</b>; context window <b>4,096</b> tokens; "
            "Task-5 scale <b>5,000</b> daily users. Chat NLG: Ollama "
            "<font face='Courier'>qwen2.5:1.5b-instruct</font> (<font face='Courier'>RECALLBOT_LLM=auto</font>; "
            "template fallback if Ollama is down). "
            "Embedding: <font face='Courier'>sentence-transformers/all-MiniLM-L6-v2</font>, dim 384, "
            "mean pooling — evidence tables in this report are from a local MiniLM run "
            "(hash backend remains available when Hugging Face SSL is blocked). "
            "KB index: flat NumPy cosine for production path; FAISS HNSW experiment in Task 5b. "
            "Hardware: Windows 11 laptop, CPU, no GPU required.",
            st["body"],
        )
    )

    # §2 Architecture
    story.append(Paragraph("2. Architecture", st["h1"]))
    arch = """User turn
  -> NLU  src.nlu.parse_utterance / classify_intent + entities
  -> State tracker  src.state.DialogueState.update_from_nlu
  -> Dialogue manager  src.dialogue.DialogueManager.handle_turn
       |- SemanticMemory.extract_from_turn / retrieve / forget
       |- EpisodicMemory.add / retrieve / reflect / redact
       |- STM  src.stm.select_history  (full | trim k=5 | summary)
       |- Tools: search_kb | get_appointment | book_slot (confirm-before-write)
       +- NLG  src.nlg.generate_reply  + skills/*.md procedural memory
Hybrid retrieval: dense + own BM25 + RRF (k=60), then Twist-B time filter."""
    story.append(Preformatted(arch, st["mono"]))
    story.append(
        Paragraph(
            "Memory homes (CS5): STM = model-native prompt history; semantic = "
            "<font face='Courier'>memory/semantic_U1.json</font> + vectors; episodic = "
            "<font face='Courier'>memory/episodic_U1.jsonl</font>; procedural = "
            "<font face='Courier'>skills/system_prompt_v1.md</font>, "
            "<font face='Courier'>book_appointment_steps_v1.md</font>. "
            "Session B is always a <b>separate process</b> that reloads disk stores.",
            st["body"],
        )
    )

    # Task 1
    story.append(Paragraph("3. Tasks 1–5", st["h1"]))
    story.append(Paragraph("Task 1 — Test data and probes", st["h2"]))
    story.append(
        Paragraph(
            "<b>data/test_conversation.json</b>: 71 turns (Session A turns 1–25; Session B 26–71), "
            "≥8 planted facts, budget/doctor/SMS updates, allergy forget, booking APT-1001 + complaint + "
            "LOC decisions, chitchat filler, state follow-ups (“And for Saturday?”), clarification, "
            "and ≥5 KB questions. <b>data/kb/</b>: 16 ClinicCare docs (~6,182 words) with codes "
            "(P-204, RFD-14D/7D, WAIT-24/48, E-4021, LOC-HYD, …) and 2025/2026 policy pairs. "
            "<b>data/kb_questions.json</b>: 26 gold-span questions (code / paraphrase / new_version). "
            "<b>data/probes.json</b>: 16 probes covering R,U,F,E,K,N,S plus twist probes P-T1/P-T2. "
            "Surprise probes remain placeholders until LMS release on 24/11/2026.",
            st["body"],
        )
    )

    # Task 2
    story.append(Paragraph("Task 2 — Dialogue pipeline and short-term memory", st["h2"]))
    story.append(
        Paragraph(
            "<b>2(a)</b> NLU is rule/regex hybrid (intent + entity patterns). Accuracy on 22 labelled "
            f"utterances: <b>{nlu['accuracy']:.0%}</b> (<font face='Courier'>results/nlu_accuracy.json</font>). "
            f"State fields ({len(nlu['state_fields'])}): "
            + ", ".join(nlu["state_fields"][:10])
            + ", … (full list in JSON). Procedural memory loaded at run time from "
            "<font face='Courier'>skills/</font>: persona, scope, error handling, exact fallback sentence, "
            "and booking step list. Decoding: temperature 0 for task/KB/confirm turns; 0.3 for open chitchat.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            f"<b>2(b)</b> Session A STM runs <font face='Courier'>r_full_A</font>, "
            f"<font face='Courier'>r_trim_A</font>, <font face='Courier'>r_summary_A</font>. "
            f"Total tokens from those run_ids (incl. summary calls): "
            f"full={stm_tok.get('full',0)}, trim={stm_tok.get('trim',0)}, "
            f"summary={stm_tok.get('summary',0)}. Plot: <font face='Courier'>results/plots/stm_tokens.png</font>.",
            st["body"],
        )
    )
    if (PLOTS / "stm_tokens.png").exists():
        img = Image(str(PLOTS / "stm_tokens.png"), width=14 * cm, height=5.5 * cm)
        story.append(img)
        story.append(Paragraph("Figure 1. Input tokens per turn for full / trim / summary (from calls.jsonl).", st["caption"]))

    story.append(
        Paragraph(
            "<b>2(c)</b> With state tracker always on, Session A booking and KB answers succeed under all three "
            "STM strategies; differences appear when history-only recall is required. "
            f"<b>Trim cut-off:</b> with k=5, turns older than the last 5 history messages are dropped — "
            f"facts stated before turn ~{25 - 5} in a long Session A are no longer in the prompt under trim "
            "(e.g. early city/name turns leave the window once later booking turns accumulate). "
            "State follow-up “And for Saturday?” resolves via <font face='Courier'>last_topic</font>/location "
            "in dialogue state (probe P-S1). Clarification asks for missing time/location before confirm. "
            "DB write <font face='Courier'>book_slot</font> runs only after <font face='Courier'>confirm_yes</font> "
            "(probe P-S2; Session A turn 23). Failures under history-only configs are deferred to Task 4 ablation "
            "(no_rag misses R/U/K; hybrid misses R/U without semantic store).",
            st["body"],
        )
    )

    # Task 3
    story.append(Paragraph("Task 3 — Retrieval and long-term memory", st["h2"]))
    story.append(
        Paragraph(
            "<b>3(a)</b> Chunk sizes 128 and 512 tokens with 15% overlap (tokenizer-counted). "
            "Metadata: doc_id, section, version, valid_from/valid_to, codes. Flat NumPy index chosen for "
            "the small KB (~32 chunks at 512); HNSW reserved for year-1 scale (Task 5b).",
            st["body"],
        )
    )
    story.append(Paragraph("<b>3(b)</b> Hit rate@k on 26 KB questions (own BM25 + RRF; pytest passes CS4 examples):", st["body"]))
    story.append(table(hit_rate_table(), col_widths=[1.6 * cm, 1.2 * cm, 1.4 * cm, 1.4 * cm, 1.4 * cm, 1.6 * cm, 1.6 * cm]))
    story.append(
        Paragraph(
            "With MiniLM, dense@5 rises to match BM25/hybrid (~0.96). "
            "<b>Fixed vs hash-dense:</b> paraphrase and code neighbours improve under MiniLM cosine; "
            "hybrid still protects exact IDs via BM25+RRF (e.g. P-204 / E-4021). "
            "<b>Residual miss:</b> a few paraphrases (e.g. Q12-class) can still miss @1/@5 when gold span "
            "wording diverges; inspect ranked lists in the retrieval debugger for those question IDs.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            f"<b>3(c)</b> Semantic fact notebook: keyed records with validity metadata. After hybrid_mem "
            f"Session B: precision={sem['precision']:.2f}, recall={sem['recall']:.2f} vs 12 gold facts "
            f"({len(sem['active_facts'])} active). Updates supersede (budget 800→1200; doctor DR-GP-17→DR-GP-22). "
            "Forget deletes allergy from store+index (P-F1).",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            f"<b>3(d)</b> Episodic stream with rule importance (bookings/complaints=8; chitchat=2). "
            f"Score = recency decay × importance × relevance (cosine). Weightings compared on E probes: "
            f"balanced {epi['balanced_weights']} acc={epi['balanced_accuracy']:.0%}; "
            f"relevance-heavy {epi['relevance_heavy_weights']} acc={epi['relevance_heavy_accuracy']:.0%}; "
            f"kept <b>{epi['kept']}</b>. Session A reflection written to stream and used in Session B (P-E1). "
            "Forget redacts allergy mentions after restart.",
            st["body"],
        )
    )
    story.append(Paragraph("<b>3(e)</b> Context assembly for one Session B turn (fits 4096):", st["body"]))
    ctx_rows = [["part", "memory type", "home", "tokens"]]
    for r in ctx:
        if r["part"] == "TOTAL":
            ctx_rows.append([r["part"], "-", "-", str(r["tokens"])])
        else:
            ctx_rows.append([r["part"], r["memory_type"], r["home"], str(r["tokens"])])
    story.append(table(ctx_rows, col_widths=[3.2 * cm, 3.2 * cm, 3.2 * cm, 1.8 * cm]))
    total = next(r for r in ctx if r["part"] == "TOTAL")
    story.append(
        Paragraph(
            f"TOTAL={total['tokens']} tokens; fits_window={total.get('fits_window')}. "
            f"Grounding: cite chunk IDs; fallback exactly: “{total.get('fallback')}”.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>3(f) Twist B</b>: retrieval filters expired 2025 policies; stale codes WAIT-48→WAIT-24 and "
            "RFD-7D→RFD-14D rewritten before search. Probes P-T1 (14-day 2026 refund, not 7-day 2025) and "
            "P-T2 (WAIT-24 current) both pass under hybrid_mem (correct=1 in probe_results.csv).",
            st["body"],
        )
    )

    # Task 4
    story.append(Paragraph("Task 4 — Evaluation and error analysis", st["h2"]))
    story.append(
        Paragraph(
            "<b>4(a)</b> Ablation (Sessions A+B separate processes; numbers from "
            "<font face='Courier'>results/ablation_summary.json</font> + logs):",
            st["body"],
        )
    )
    abl_rows = [["config", "acc", "R", "U", "F", "E", "K", "N", "S", "T", "mean in", "tot tok"]]
    for row in ablation["table"]:
        cats = row["accuracy_by_category"]
        abl_rows.append(
            [
                row["config"],
                f"{row['accuracy_overall']:.3f}" if row["accuracy_overall"] is not None else "-",
                f"{cats.get('R', 0):.1f}" if cats else "-",
                f"{cats.get('U', 0):.1f}" if cats else "-",
                f"{cats.get('F', 0):.1f}" if cats else "-",
                f"{cats.get('E', 0):.1f}" if cats else "-",
                f"{cats.get('K', 0):.1f}" if cats else "-",
                f"{cats.get('N', 0):.1f}" if cats else "-",
                f"{cats.get('S', 0):.1f}" if cats else "-",
                f"{cats.get('T', 0):.1f}" if cats else "-",
                f"{row['mean_input_tokens_per_chat_turn']:.0f}"
                if row["mean_input_tokens_per_chat_turn"] is not None
                else "-",
                str(row["total_tokens_logged"]),
            ]
        )
    story.append(table(abl_rows, col_widths=[1.8 * cm] + [1.05 * cm] * 11, font_size=6.5))
    story.append(
        Paragraph(
            "Contribution: no_rag keeps much of N/S/F via state+fallback; hybrid adds grounded K/T; "
            "hybrid_sem restores R/U; hybrid_mem adds E via episodes+reflection. "
            "Under Qwen NLG, hybrid_mem probe accuracy is ~0.81 (13/16): P-U2 wording drift, P-E2 miss, "
            "and P-K1 auto-judge false negative on a correct 14-day refund cite. "
            "CS1 rubric (manual on Session B samples, 1–5): coherence≈4, relevance≈4, "
            "groundedness≈5 when KB cited, safety≈5 (fallback used; no clinical invention). "
            "judged_by=manual on probe_results.csv.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>4(b) Error analysis (three failure modes; hybrid path)</b><br/>"
            "(1) <i>NLG / judge mismatch (P-U2, P-K1)</i> — Qwen paraphrases “DR-GP-22” / refund answers; "
            "evidence in probe_results.csv. Fix at NLG/judge: constrain preferred-doctor template and "
            "accept “14-day” / RFD-14D spans in the scorer.<br/>"
            "(2) <i>Episodic/retrieval miss (P-E2)</i> — LOC-HYD primary-centre probe fell through to fallback. "
            "Fix at memory retrieval: boost decision episodes and/or FAQ-HOURS when query mentions centre.<br/>"
            "(3) <i>Twist stale-chunk</i> — WAIT-48 / 2025 refund could win without time filter. "
            "Fix: validity filter + code rewrite; P-T1/P-T2 pass under MiniLM+hybrid_mem.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>4(c) Surprise probes</b> (LMS 24/11/2026; Session C on hybrid_mem; "
            "<font face='Courier'>python -m src.run_surprise</font>). "
            "Adapted clinic wording in <font face='Courier'>data/surprise_probes.json</font>. "
            "<b>Before</b> (r_surprise, no post-probe fixes): S1 fail (NLU/prompt — listed KB FAQ instead of profile), "
            "S2 fail (state — name not parsed from “for Anita Rao …”, asked for missing slot), "
            "S3 pass (POL-REFUND-2026 / 14 days), S4 pass (bare P-204?), "
            "S5 fail (retrieval — LAB chunk cited instead of fallback). Acc=0.40. "
            "<b>After</b> (r_surprise_after): S1–S5 all pass (acc=1.00). Fixes: "
            "recall_profile intent + active-fact listing (NLU/NLG); name entity “for First Last” (state); "
            "skip KB + exact fallback for “last time you told me / blood type” (retrieval/prompt). "
            "Evidence: <font face='Courier'>results/surprise_summary_before.json</font>, "
            "<font face='Courier'>surprise_summary_after.json</font>, "
            "<font face='Courier'>surprise_probe_results.csv</font>.",
            st["body"],
        )
    )

    # Task 5
    story.append(Paragraph("Task 5 — Cost and scale", st["h2"]))
    trim_no, trim_c = monthly(trim_stats) if trim_stats else (None, None)
    hm_no, hm_c = monthly(hm_stats) if hm_stats else (None, None)
    story.append(
        Paragraph(
            f"<b>5(a)</b> Price row: <b>GPT-4o</b> (CS3 May-2025 indicative: in $2.50 / out $10 / cached in $1.25 per 1M). "
            f"Prefix (system+skills) = {prefix} tokens ≥ 1024 min cache length. "
            f"Measured chat tokens from run_ids r_trim_A and r_hm_A+r_hm_B "
            f"(Qwen chat logs; billed input floored at prefix when mean_in &lt; prefix). "
            f"trim: turns={trim_stats['turns'] if trim_stats else '-'}, "
            f"mean_in={trim_stats['mean_input']:.1f} → monthly no-cache ${trim_no}, with-cache ${trim_c}. "
            f"hybrid_mem: turns={hm_stats['turns'] if hm_stats else '-'}, "
            f"mean_in={hm_stats['mean_input']:.1f} → monthly no-cache ${hm_no}, with-cache ${hm_c} "
            f"(5,000 users × 30 days × turns/convo).",
            st["body"],
        )
    )
    lat = cost["latency"]
    yv = cost["year_vectors"]
    story.append(
        Paragraph(
            f"<b>5(b)</b> Year-1 vectors ≈ {yv['total']:,} "
            f"(KB {yv['kb_chunks']} + semantic {yv['semantic']:,} + episodic {yv['episodic']:,}). "
            f"Flat float32 ≈ {yv['flat_gb']} GB; HNSW M=16 ≈ {yv['hnsw_m16_gb']} GB. "
            f"Measured on padded N={lat['n']:,}, dim={lat['dim']}: "
            f"flat latency {lat['flat_latency_ms']:.3f} ms; HNSW {lat['hnsw_latency_ms']:.3f} ms; "
            f"HNSW recall@1={lat['hnsw_recall_at_1']:.2f} (M={lat['m']}, ef_search={lat['ef_search']}). "
            f"Recommendation: {lat['recommend']}",
            st["body"],
        )
    )

    # Limitations
    story.append(Paragraph("4. Limitations and one more week", st["h1"]))
    story.append(
        Paragraph(
            "This report’s tables use the local MiniLM + Qwen run in logs/calls.jsonl. "
            "Qwen increases mean input tokens vs template NLG; Task-5 costs use measured chat tokens floored at the system prefix. "
            "Surprise probes are complete with before/after evidence. "
            "Remaining for LMS: ≤5 min demo video + video_link.txt, then zip packaging. "
            "Optional: expand LLM-judge agreement checks on Session B replies.",
            st["body"],
        )
    )

    # Appendix A
    story.append(PageBreak())
    story.append(Paragraph("Appendix A — AI-use declaration (Task 6b)", st["h1"]))
    story.append(
        Paragraph(
            "<b>Tools used:</b> Cursor IDE agent (Composer) for scaffolding src/, scripts, Prayogshala/Windows "
            "bootstrap, notebook cells, and drafting this report; ChatGPT/Claude-class assistants earlier for "
            "KB wording ideas. All BM25, RRF, episodic scoring, chunker, state tracker, dialogue manager, and "
            "memory CRUD were implemented and tested in this repository; logs/results are produced by "
            "<font face='Courier'>python -m src.*</font> runs (not hand-typed).",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>One wrong AI suggestion (specific):</b> An assistant initially suggested relying on dense "
            "hash embeddings alone for hybrid RRF fusion on clinic <i>code</i> queries (P-204, E-4021, WAIT-24). "
            "After measuring hit_rate.csv, dense@1 on code questions was far below BM25 (~0.35 vs ~0.92). "
            "I found the failure by inspecting ranked lists for Q02/Q04-style IDs where hash-dense neighbours "
            "were semantically related but wrong codes. <b>Change:</b> keep own BM25 + RRF with BM25-first "
            "behaviour for exact codes, add Twist-B validity filtering, and use MiniLM "
            "(sentence-transformers/all-MiniLM-L6-v2) for the evidence tables in this report.",
            st["body"],
        )
    )

    # Appendix B
    story.append(Paragraph("Appendix B — Prompts", st["h1"]))
    sys_prompt = (SKILLS / "system_prompt_v1.md").read_text(encoding="utf-8")
    steps = (SKILLS / "book_appointment_steps_v1.md").read_text(encoding="utf-8")
    story.append(Paragraph("<b>System + procedural (skills/system_prompt_v1.md)</b>", st["h2"]))
    # Truncate slightly if huge but keep substance
    story.append(Preformatted(sys_prompt[:4500], st["mono"]))
    story.append(Paragraph("<b>Booking steps (skills/book_appointment_steps_v1.md)</b>", st["h2"]))
    story.append(Preformatted(steps, st["mono"]))
    story.append(Paragraph("<b>RAG / NLG assembly (src/nlg.py)</b>", st["h2"]))
    story.append(
        Preformatted(
            "History:\\n{history}\\n\\nContext:\\n{kb_chunks + FACT key=value + EPISODE text}\\n\\n"
            "User: {user_text}\\nIntent: {intent}\\n"
            "If answer unknown, reply exactly: "
            "I do not have that information in the clinic knowledge base or your saved profile.",
            st["mono"],
        )
    )
    story.append(Paragraph("<b>Summary (src/stm.py)</b>", st["h2"]))
    story.append(
        Preformatted(
            "Earlier conversation summary: {role}:{text[:60]} ; ... (last 10 older turns)\n"
            "+ last 2 turns verbatim. Logged as call_type=summary, model=rule-summary.",
            st["mono"],
        )
    )
    story.append(Paragraph("<b>Extraction / importance / reflection / judge</b>", st["h2"]))
    story.append(
        Preformatted(
            "Extraction: rule extract_from_turn -> keyed semantic records (no LLM filler).\n"
            "Importance: rule-importance 1-10 (book/complaint/decision=8; chitchat=2).\n"
            "Reflection: end of Session A concatenates high-importance episodes into stream.\n"
            "Judge: manual probe marking (judged_by=manual); no automated LLM judge for final table.",
            st["mono"],
        )
    )
    story.append(
        Paragraph(
            "Repo: https://github.com/bits-pgaiml-cgai/pcam-zg517-a1-recallbot · "
            "Reproduce via README.md / scripts/prayogshala_bootstrap.sh",
            st["caption"],
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="RecallBot V31 Mini Project 1 Report",
        author="Venkata Srinivasa Rao Tunuguntla",
    )
    doc.build(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
