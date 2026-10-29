"""Reusable result renderers: tabs, Stated/Inferred badges, evidence quotes, tables, exports."""
import html
import re

import pandas as pd
import streamlit as st

from backend.core.exporter import DISCLAIMER, to_markdown, to_text
from backend.models import NOT_SPECIFIED, MeetingSummary

_STATED = '<span class="badge-stated" style="background:#059669;color:#fff;padding:2px 8px;border-radius:6px;font-size:0.74rem;font-weight:700">✓ STATED</span>'
_INFERRED = '<span class="badge-inferred" style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:6px;font-size:0.74rem;font-weight:700">💡 INFERRED</span>'


def badge(label: str) -> str:
    return _STATED if label == "stated" else _INFERRED


def _loc(ev) -> str:
    if ev.line_start == 0:
        return "line unknown"
    return f"L{ev.line_start}" if ev.line_start == ev.line_end else f"L{ev.line_start}–{ev.line_end}"


def _evidence_line(item) -> str:
    if not item.evidence:
        return ""
    q = html.escape(item.evidence.quote)
    loc = _loc(item.evidence)
    return (f'<div style="margin:6px 0 12px 14px;padding:6px 12px;border-left:3px solid #059669;'
            f'background:rgba(5, 150, 105, 0.05);border-radius:0 6px 6px 0;font-size:0.86rem">'
            f'“{q}” <span style="background:rgba(0,0,0,0.06);padding:1px 6px;border-radius:4px;'
            f'font-weight:600;font-size:0.75rem;margin-left:6px">📍 {loc}</span></div>')


def _item_html(text: str, item, extra: str = "") -> str:
    return (f'<div style="margin:10px 0 3px 0;line-height:1.45">{badge(item.label)} &nbsp;<b>{html.escape(text)}</b>{extra}</div>'
            + _evidence_line(item))


def _empty(msg: str):
    st.info(f"ℹ️ {msg}")


def _visible(items, only_stated: bool):
    return [i for i in items if i.label == "stated"] if only_stated else list(items)


def _style_not_specified(df: pd.DataFrame):
    fn = lambda v: "background-color:rgba(217, 119, 6, 0.2);color:#d97706;font-weight:bold" if v == NOT_SPECIFIED else ""
    styler = df.style
    return styler.map(fn) if hasattr(styler, "map") else styler.applymap(fn)


def _ev_text(item) -> str:
    return f"“{item.evidence.quote}” ({_loc(item.evidence)})" if item.evidence else "—"


def _overview(s: MeetingSummary):
    st.markdown(f'<div class="result-card" style="border-left:4px solid #2563eb;padding:1rem 1.25rem;'
                f'background:rgba(37,99,235,0.03);border-radius:8px;margin-bottom:1rem">'
                f'<div style="margin-bottom:6px">{_INFERRED} &nbsp;<b>Executive Overview</b></div>'
                f'<div style="font-size:1.02rem;line-height:1.55;opacity:0.95">{html.escape(s.overview)}</div>'
                f'</div>', unsafe_allow_html=True)
    if s.meta.format == "Bullet notes":
        st.markdown("**Core Summary Takeaways:**")
        for sent in [x for x in re.split(r"(?<=[.!?])\s+", s.overview) if x]:
            st.markdown(f"- {sent}")


def _key_points(s: MeetingSummary, only_stated: bool):
    items = _visible(s.key_points, only_stated)
    if not items:
        return _empty("No key points to show.")
    fmt = s.meta.format
    if fmt == "Structured table":
        st.dataframe(pd.DataFrame([{"Label": i.label.title(), "Key point": i.text, "Evidence": _ev_text(i)} for i in items]),
                     use_container_width=True, hide_index=True)
    elif fmt == "Narrative paragraphs":
        st.write(" ".join(i.text.rstrip(".") + "." for i in items))
        with st.expander("🔍 Show evidence and line numbers for each point"):
            for i in items:
                st.markdown(_item_html(i.text, i), unsafe_allow_html=True)
    else:
        for i in items:
            st.markdown(_item_html(i.text, i), unsafe_allow_html=True)


def _actions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.action_items, only_stated)
    if s.action_items and (s.missing_owner_count or s.missing_deadline_count):
        st.warning(f"🛡️ **Grounding Notice:** {s.missing_owner_count} of {len(s.action_items)} action items have no owner and "
                   f"{s.missing_deadline_count} have no deadline in the transcript. RecapRoom strictly tags them 'Not specified' without guessing.")
    if not items:
        return _empty("No action items to show.")
    
    # Render interactive table
    df = pd.DataFrame([{"Label": a.label.title(), "Task": a.task, "Owner": a.owner, "Deadline": a.deadline,
                        "Status": a.status, "Evidence": _ev_text(a)} for a in items])
    st.dataframe(_style_not_specified(df), use_container_width=True, hide_index=True)

    # Detailed card view toggle
    with st.expander("📋 View Action Items as Cards with Direct Provenance", expanded=False):
        for a in items:
            own_color = "#d97706" if a.owner == NOT_SPECIFIED else "#059669"
            dead_color = "#d97706" if a.deadline == NOT_SPECIFIED else "#2563eb"
            extra = (f'<div style="margin:6px 0 4px 0;font-size:0.88rem">'
                     f'👤 <b>Owner:</b> <span style="color:{own_color};font-weight:600">{html.escape(a.owner)}</span> &nbsp;·&nbsp; '
                     f'📅 <b>Deadline:</b> <span style="color:{dead_color};font-weight:600">{html.escape(a.deadline)}</span> &nbsp;·&nbsp; '
                     f'⚡ <b>Status:</b> <code>{a.status}</code></div>')
            st.markdown(_item_html(a.task, a, extra), unsafe_allow_html=True)


def _decisions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.decisions, only_stated)
    if not items:
        return _empty("No explicit decisions found. RecapRoom only lists a decision when the transcript shows explicit consensus.")
    for d in items:
        dec_by = html.escape(d.decided_by)
        extra = f' &nbsp; <span style="font-size:0.85rem;background:rgba(0,0,0,0.05);padding:2px 8px;border-radius:4px">👥 <b>Decided by:</b> {dec_by}</span>'
        st.markdown(_item_html(d.text, d, extra), unsafe_allow_html=True)


def _questions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.open_questions, only_stated)
    if not items:
        return _empty("No open questions found.")
    for q in items:
        st.markdown(_item_html(q.text, q), unsafe_allow_html=True)


def _evidence_tab(s: MeetingSummary):
    allitems = list(s.key_points) + list(s.decisions) + list(s.action_items) + list(s.open_questions)
    stated = sum(i.label == "stated" for i in allitems)
    
    st.markdown("### 📊 Evidence & Grounding Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stated Items", stated, help="Explicitly supported by line quotes")
    c2.metric("Inferred Items", len(allitems) - stated, help="Synthesized deductions")
    c3.metric("Verifier Warnings", len(s.warnings), help="Items automatically corrected or downgraded")
    c4.metric("Action Items", len(s.action_items))

    if s.warnings:
        st.subheader("⚠️ Verifier Adjustments")
        for w in s.warnings:
            st.warning(w)
    else:
        st.success("✅ **Deterministic Verification Passed:** All quotes, line numbers, owners, and deadlines match the transcript vocabulary.")
    
    if s.speakers_detected:
        st.subheader("🗣️ Speakers Detected")
        st.write(" · ".join(f"**{spk}**" for spk in s.speakers_detected))
        st.caption("ℹ️ Speaker detection is pattern-based. Transcripts missing speaker tags show attribution warnings.")

    st.subheader("⚙️ Session Metadata")
    m = s.meta
    st.table(pd.DataFrame({"Parameter": ["Execution Mode", "AI Provider / Model", "Output Length", "Format Setting",
                                        "Transcript Type", "Word Count", "Sections Processed", "Timestamp (UTC)"],
                           "Configuration": [m.mode, f"{m.provider} / {m.model}", m.length, m.format, m.transcript_type,
                                             f"{m.transcript_words:,}", str(m.chunks), m.generated_at]}))


def _export_tab(s: MeetingSummary):
    st.markdown("### 📥 Export Verified Notes")
    st.write("Downloaded files preserve full provenance tags, evidence quotes, line numbers, and anti-hallucination disclaimers.")
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Download Markdown (.md)", to_markdown(s), "recaproom_notes.md", "text/markdown", use_container_width=True)
    c2.download_button("⬇️ Download Text (.txt)", to_text(s), "recaproom_notes.txt", "text/plain", use_container_width=True)
    
    with st.expander("👀 Live Markdown Preview", expanded=False):
        st.code(to_markdown(s), language="markdown")


def render_summary(s: MeetingSummary) -> None:
    # Mode Banner
    if s.meta.mode == "DEMO":
        st.info("🟠 **DEMO MODE**: output was generated by deterministic local rules (offline mode).")
    else:
        st.success(f"🟢 **LIVE PIPELINE**: {s.meta.provider.upper()} ({s.meta.model})")

    # Legend & Filters Bar
    l_col1, l_col2 = st.columns([3, 1])
    with l_col1:
        st.markdown(f"<b>Legend:</b> {_STATED} verified transcript quote &nbsp;·&nbsp; "
                    f"{_INFERRED} model synthesis (verify against transcript)", unsafe_allow_html=True)
    with l_col2:
        only_stated = st.checkbox("Show stated only", key="only_stated")

    st.caption(f"🔒 {DISCLAIMER}")

    # Tabs
    tabs = st.tabs(["📌 Summary", "✅ Action Items", "🎯 Decisions", "❓ Open Questions", "🔍 Evidence & Warnings", "📥 Export"])
    with tabs[0]:
        _overview(s)
        st.markdown("#### Key Points")
        _key_points(s, only_stated)
    with tabs[1]:
        _actions(s, only_stated)
    with tabs[2]:
        _decisions(s, only_stated)
    with tabs[3]:
        _questions(s, only_stated)
    with tabs[4]:
        _evidence_tab(s)
    with tabs[5]:
        _export_tab(s)
