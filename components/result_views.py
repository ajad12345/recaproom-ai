"""Reusable result renderers: tabs, Stated/Inferred badges, evidence quotes, tables, exports."""
import html
import re

import pandas as pd
import streamlit as st

from backend.core.exporter import DISCLAIMER, to_markdown, to_text
from backend.models import NOT_SPECIFIED, MeetingSummary

_STATED = '<span style="background:#1b7f3b;color:#fff;padding:1px 8px;border-radius:10px;font-size:0.72rem;font-weight:600">STATED</span>'
_INFERRED = '<span style="background:#b36b00;color:#fff;padding:1px 8px;border-radius:10px;font-size:0.72rem;font-weight:600">INFERRED</span>'


def badge(label: str) -> str:
    return _STATED if label == "stated" else _INFERRED


def _loc(ev) -> str:
    if ev.line_start == 0:
        return "line unknown"
    return f"L{ev.line_start}" if ev.line_start == ev.line_end else f"L{ev.line_start}–{ev.line_end}"


def _evidence_line(item) -> str:
    if not item.evidence:
        return ""
    return f'<div style="margin:2px 0 10px 12px;padding-left:10px;border-left:3px solid #8884;opacity:.8;font-size:.88rem">“{html.escape(item.evidence.quote)}” <i>({_loc(item.evidence)})</i></div>'


def _item_html(text: str, item, extra: str = "") -> str:
    return (f'<div style="margin:8px 0 2px 0">{badge(item.label)} &nbsp;{html.escape(text)}{extra}</div>'
            + _evidence_line(item))


def _empty(msg: str):
    st.caption(msg)


def _visible(items, only_stated: bool):
    return [i for i in items if i.label == "stated"] if only_stated else list(items)


def _style_not_specified(df: pd.DataFrame):
    fn = lambda v: "background-color:#7a5200;color:#fff" if v == NOT_SPECIFIED else ""
    styler = df.style
    return styler.map(fn) if hasattr(styler, "map") else styler.applymap(fn)


def _ev_text(item) -> str:
    return f"“{item.evidence.quote}” ({_loc(item.evidence)})" if item.evidence else ""


def _overview(s: MeetingSummary):
    st.markdown(f"{_INFERRED} &nbsp;**Overview**", unsafe_allow_html=True)
    if s.meta.format == "Bullet notes":
        for sent in [x for x in re.split(r"(?<=[.!?])\s+", s.overview) if x]:
            st.markdown(f"- {sent}")
    else:
        st.write(s.overview)


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
        with st.expander("Show evidence for each point"):
            for i in items:
                st.markdown(_item_html(i.text, i), unsafe_allow_html=True)
    else:
        for i in items:
            st.markdown(_item_html(i.text, i), unsafe_allow_html=True)


def _actions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.action_items, only_stated)
    if s.action_items and (s.missing_owner_count or s.missing_deadline_count):
        st.warning(f"{s.missing_owner_count} of {len(s.action_items)} action items have no owner and "
                   f"{s.missing_deadline_count} have no deadline in the transcript. RecapRoom never guesses these.")
    if not items:
        return _empty("No action items to show.")
    df = pd.DataFrame([{"Label": a.label.title(), "Task": a.task, "Owner": a.owner, "Deadline": a.deadline,
                        "Status": a.status, "Evidence": _ev_text(a)} for a in items])
    st.dataframe(_style_not_specified(df), use_container_width=True, hide_index=True)


def _decisions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.decisions, only_stated)
    if not items:
        return _empty("No explicit decisions found. RecapRoom only lists a decision when the transcript shows agreement.")
    for d in items:
        st.markdown(_item_html(d.text, d, f' <span style="opacity:.7">(decided by: {html.escape(d.decided_by)})</span>'),
                    unsafe_allow_html=True)


def _questions(s: MeetingSummary, only_stated: bool):
    items = _visible(s.open_questions, only_stated)
    if not items:
        return _empty("No open questions found.")
    for q in items:
        st.markdown(_item_html(q.text, q), unsafe_allow_html=True)


def _evidence_tab(s: MeetingSummary):
    allitems = list(s.key_points) + list(s.decisions) + list(s.action_items) + list(s.open_questions)
    stated = sum(i.label == "stated" for i in allitems)
    c1, c2, c3 = st.columns(3)
    c1.metric("Stated items", stated)
    c2.metric("Inferred items", len(allitems) - stated)
    c3.metric("Verifier warnings", len(s.warnings))
    if s.warnings:
        st.subheader("Warnings")
        for w in s.warnings:
            st.warning(w)
    else:
        st.success("The verifier found no problems: all quotes, owners and deadlines match the transcript.")
    if s.speakers_detected:
        st.subheader("Speakers detected")
        st.write(", ".join(s.speakers_detected))
        st.caption("⚠️ Speaker detection is pattern-based. Missing or inconsistent labels (especially in "
                   "speech-to-text transcripts) can make attribution wrong.")
    st.subheader("Run details")
    m = s.meta
    st.table(pd.DataFrame({"Setting": ["Mode", "Provider / model", "Length", "Format", "Transcript type",
                                       "Words", "Sections", "Generated (UTC)"],
                           "Value": [m.mode, f"{m.provider} / {m.model}", m.length, m.format, m.transcript_type,
                                     f"{m.transcript_words:,}", str(m.chunks), m.generated_at]}))


def _export_tab(s: MeetingSummary):
    st.write("Exports include Stated/Inferred labels, evidence quotes, your settings, the mode and a disclaimer.")
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Download Markdown (.md)", to_markdown(s), "recaproom_notes.md", "text/markdown", use_container_width=True)
    c2.download_button("⬇️ Download Text (.txt)", to_text(s), "recaproom_notes.txt", "text/plain", use_container_width=True)
    with st.expander("Preview Markdown"):
        st.code(to_markdown(s), language="markdown")


def render_summary(s: MeetingSummary) -> None:
    if s.meta.mode == "DEMO":
        st.info("🟠 **DEMO MODE**: this output was produced by simple rules, not by a language model.")
    else:
        st.success(f"🟢 **LIVE** ({s.meta.provider} / {s.meta.model})")
    st.markdown(f"Legend: {_STATED} directly supported by a quote from the transcript &nbsp;·&nbsp; "
                f"{_INFERRED} the model's interpretation (verify it)", unsafe_allow_html=True)
    st.caption(DISCLAIMER)
    only_stated = st.checkbox("Show only stated items", key="only_stated")
    tabs = st.tabs(["Summary", "Action Items", "Decisions", "Open Questions", "Evidence & Warnings", "Export"])
    with tabs[0]:
        _overview(s)
        st.markdown("#### Key points")
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
