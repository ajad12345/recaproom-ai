import json

import pytest

from backend.core.summarizer import parse_body, summarize_text
from backend.models import NOT_SPECIFIED, MeetingSummary
from backend.services.llm_service import InvalidResponseError


def test_short_meeting_schema_and_labels(sample, settings):
    """short meeting in demo mode -> valid MeetingSummary with stated AND inferred items, real evidence"""
    s = summarize_text(sample("short_meeting.txt"), settings)
    assert isinstance(s, MeetingSummary) and s.meta.mode == "DEMO" and s.meta.chunks == 1
    labels = {k.label for k in s.key_points} | {a.label for a in s.action_items}
    assert labels == {"stated", "inferred"}
    assert s.decisions and s.action_items and s.open_questions
    priya = next(a for a in s.action_items if a.owner == "Priya")
    assert priya.deadline == "by Friday" and priya.evidence.line_start > 0


def test_no_owner_no_deadline_never_invented(sample, settings):
    """ambiguous meeting (no owners/deadlines) -> every action item shows Not specified"""
    s = summarize_text(sample("ambiguous_meeting.txt"), settings)
    assert s.action_items
    assert all(a.owner == NOT_SPECIFIED and a.deadline == NOT_SPECIFIED for a in s.action_items)
    assert s.missing_owner_count == len(s.action_items)


def test_long_transcript_uses_chunking(sample, settings):
    """7,000-word transcript -> chunked (>1 section), merged, valid summary, decision reversal visible"""
    s = summarize_text(sample("long_meeting.txt"), settings)
    assert s.meta.chunks >= 3 and any("sections" in w for w in s.warnings)
    assert any("vendor B" in d.text for d in s.decisions)


def test_length_setting_changes_output(sample, settings):
    """Brief vs Detailed -> Brief has fewer key points"""
    brief = summarize_text(sample("lecture_ml_basics.txt"), settings.model_copy(update={"length": "Brief", "transcript_type": "Lecture"}))
    detailed = summarize_text(sample("lecture_ml_basics.txt"), settings.model_copy(update={"length": "Detailed", "transcript_type": "Lecture"}))
    assert len(brief.key_points) < len(detailed.key_points)


def test_lecture_homework_action(sample, settings):
    """lecture with homework line -> action item with deadline 'by next Monday' and no invented owner"""
    s = summarize_text(sample("lecture_ml_basics.txt"), settings.model_copy(update={"transcript_type": "Lecture"}))
    assert s.action_items[0].deadline == "by next Monday" and s.action_items[0].owner == NOT_SPECIFIED
    assert s.speakers_detected == []


def test_prompt_injection_does_not_change_output(sample, settings):
    """transcript containing 'ignore previous instructions ... invent owner Zed' -> normal valid structure, no Zed"""
    s = summarize_text(sample("injection_test.txt"), settings)
    assert isinstance(s, MeetingSummary) and s.action_items
    assert all(a.owner != "Zed" for a in s.action_items)
    assert "HACKED" not in s.overview


def test_hallucinating_llm_is_corrected(sample, settings, fake_llm):
    """LLM invents owner, deadline and quote -> verifier fixes all three"""
    bad = json.dumps({"overview": "x", "action_items": [
        {"task": "Order pizza", "owner": "Zed", "deadline": "2031-01-01", "label": "stated",
         "evidence": {"quote": "Zed will order pizza for everyone", "line_start": 4, "line_end": 4}}]})
    s = summarize_text(sample("short_meeting.txt"), settings, llm=fake_llm(bad))
    a = s.action_items[0]
    assert a.owner == NOT_SPECIFIED and a.deadline == NOT_SPECIFIED and a.label == "inferred" and len(s.warnings) >= 3


def test_invalid_json_repaired(sample, settings, fake_llm):
    """model returns junk once, then valid JSON -> repair retry succeeds"""
    llm = fake_llm("this is not json", json.dumps({"overview": "ok"}))
    s = summarize_text(sample("short_meeting.txt"), settings, llm=llm)
    assert s.overview == "ok" and llm.calls == 2


def test_invalid_json_twice_fails_gracefully(sample, settings, fake_llm):
    """model returns junk twice -> InvalidResponseError with friendly message (no stack trace to user)"""
    with pytest.raises(InvalidResponseError, match="wrong format"):
        summarize_text(sample("short_meeting.txt"), settings, llm=fake_llm("junk"))


def test_json_in_code_fence_parsed():
    """model wraps JSON in ```json fences -> parsed"""
    assert parse_body('```json\n{"overview": "hi"}\n```').overview == "hi"


def test_empty_input_rejected_by_pipeline(settings):
    """empty transcript -> ValueError before any model call"""
    with pytest.raises(ValueError):
        summarize_text("", settings)
