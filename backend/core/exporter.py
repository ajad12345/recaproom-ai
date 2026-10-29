"""Export a MeetingSummary as Markdown or plain text, keeping provenance labels and evidence."""
from backend.models import MeetingSummary

DISCLAIMER = "AI-generated notes can be wrong. Verify important items against the original transcript."


def _ev(item) -> str:
    if not item.evidence:
        return ""
    e = item.evidence
    loc = f"L{e.line_start}" if e.line_start == e.line_end else f"L{e.line_start}-{e.line_end}"
    return f"“{e.quote}” ({loc})"


def _header(s: MeetingSummary) -> list[str]:
    m = s.meta
    return [f"Mode: {m.mode} ({m.provider}/{m.model}) | Length: {m.length} | Format: {m.format} | "
            f"Type: {m.transcript_type} | Words: {m.transcript_words:,} | Generated: {m.generated_at}"]


def to_markdown(s: MeetingSummary) -> str:
    out = ["# RecapRoom AI — Notes", "", f"> {DISCLAIMER}", "", *_header(s), "",
           "## Overview", f"*[Inferred]* {s.overview}", "", "## Key Points"]
    out += [f"- **[{k.label.title()}]** {k.text}" + (f"\n  - Evidence: {_ev(k)}" if k.evidence else "") for k in s.key_points] or ["_None_"]
    out += ["", "## Decisions"]
    out += [f"- **[{d.label.title()}]** {d.text} (decided by: {d.decided_by})" + (f"\n  - Evidence: {_ev(d)}" if d.evidence else "") for d in s.decisions] or ["_None_"]
    out += ["", "## Action Items"]
    if s.action_items:
        out += ["| Label | Task | Owner | Deadline | Status | Evidence |", "|---|---|---|---|---|---|"]
        out += [f"| {a.label.title()} | {a.task.replace('|', '/')} | {a.owner} | {a.deadline} | {a.status} | {_ev(a).replace('|', '/')} |"
                for a in s.action_items]
    else:
        out.append("_None_")
    out += ["", "## Open Questions"]
    out += [f"- **[{q.label.title()}]** {q.text}" + (f"\n  - Evidence: {_ev(q)}" if q.evidence else "") for q in s.open_questions] or ["_None_"]
    if s.speakers_detected:
        out += ["", "## Speakers detected", ", ".join(s.speakers_detected) + " (speaker detection is pattern-based and can be wrong)"]
    if s.warnings:
        out += ["", "## Warnings", *[f"- {w}" for w in s.warnings]]
    return "\n".join(out) + "\n"


def to_text(s: MeetingSummary) -> str:
    out = ["RECAPROOM AI - NOTES", DISCLAIMER, "", *_header(s), "", "OVERVIEW (Inferred)", s.overview, "", "KEY POINTS"]
    out += [f"- [{k.label.upper()}] {k.text}" + (f"\n    Evidence: {_ev(k)}" if k.evidence else "") for k in s.key_points] or ["(none)"]
    out += ["", "DECISIONS"]
    out += [f"- [{d.label.upper()}] {d.text} (decided by: {d.decided_by})" + (f"\n    Evidence: {_ev(d)}" if d.evidence else "") for d in s.decisions] or ["(none)"]
    out += ["", "ACTION ITEMS"]
    out += [f"- [{a.label.upper()}] {a.task} | Owner: {a.owner} | Deadline: {a.deadline} | Status: {a.status}"
            + (f"\n    Evidence: {_ev(a)}" if a.evidence else "") for a in s.action_items] or ["(none)"]
    out += ["", "OPEN QUESTIONS"]
    out += [f"- [{q.label.upper()}] {q.text}" + (f"\n    Evidence: {_ev(q)}" if q.evidence else "") for q in s.open_questions] or ["(none)"]
    if s.warnings:
        out += ["", "WARNINGS", *[f"- {w}" for w in s.warnings]]
    return "\n".join(out) + "\n"
