from backend.core.exporter import DISCLAIMER, to_markdown, to_text
from backend.core.summarizer import summarize_text


def test_markdown_export_has_labels_evidence_disclaimer(sample, settings):
    """summary -> Markdown containing Stated/Inferred labels, evidence quote, settings and disclaimer"""
    s = summarize_text(sample("short_meeting.txt"), settings)
    md = to_markdown(s)
    assert "[Stated]" in md and "[Inferred]" in md and "Evidence:" in md
    assert DISCLAIMER in md and "Mode: DEMO" in md and "Length: Standard" in md and "Not specified" in md


def test_text_export(sample, settings):
    """summary -> plain-text export with labels and disclaimer"""
    t = to_text(summarize_text(sample("short_meeting.txt"), settings))
    assert "[STATED]" in t and "ACTION ITEMS" in t and DISCLAIMER in t
