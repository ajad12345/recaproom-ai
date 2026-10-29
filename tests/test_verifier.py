from backend.core.preprocess import preprocess
from backend.core.verifier import verify
from backend.models import SummaryBody

TRANSCRIPT = """Maya: We agreed to ship the beta on March 3rd.
Priya: I will write the release notes by Friday.
Sam: Someone should check the logs after the deployment is finished."""


def _body(**kw):
    return SummaryBody.model_validate(kw)


def test_fabricated_owner_and_deadline_removed():
    """LLM invents owner 'Zed' and deadline 'next March' -> both become Not specified"""
    pre = preprocess(TRANSCRIPT)
    body = _body(action_items=[{"task": "check the logs", "owner": "Zed", "deadline": "next March", "label": "stated",
                                "evidence": {"quote": "Someone should check the logs", "line_start": 3, "line_end": 3}}])
    out, warns = verify(body, pre)
    a = out.action_items[0]
    assert a.owner == "Not specified" and a.deadline == "Not specified"
    assert len(warns) == 2


def test_real_owner_and_deadline_kept():
    """owner Priya + deadline 'by Friday' that appear in transcript -> kept"""
    pre = preprocess(TRANSCRIPT)
    body = _body(action_items=[{"task": "write the release notes", "owner": "Priya", "deadline": "by Friday",
                                "label": "stated", "evidence": {"quote": "I will write the release notes by Friday.", "line_start": 2, "line_end": 2}}])
    out, warns = verify(body, pre)
    assert out.action_items[0].owner == "Priya" and out.action_items[0].deadline == "by Friday" and not warns


def test_fake_quote_downgraded():
    """stated item with a quote that is not in the transcript -> downgraded to inferred, evidence dropped"""
    pre = preprocess(TRANSCRIPT)
    body = _body(key_points=[{"text": "Budget approved", "label": "stated",
                              "evidence": {"quote": "The budget of two million was approved", "line_start": 1, "line_end": 1}}])
    out, warns = verify(body, pre)
    assert out.key_points[0].label == "inferred" and out.key_points[0].evidence is None and warns


def test_stated_without_evidence_downgraded():
    """stated item with no evidence -> shown as inferred"""
    out, warns = verify(_body(key_points=[{"text": "Something", "label": "stated"}]), preprocess(TRANSCRIPT))
    assert out.key_points[0].label == "inferred" and warns


def test_wrong_line_number_corrected():
    """real quote with wrong line number -> line number fixed"""
    body = _body(decisions=[{"text": "Ship beta", "label": "stated",
                             "evidence": {"quote": "We agreed to ship the beta on March 3rd", "line_start": 9, "line_end": 9}}])
    out, _ = verify(body, preprocess(TRANSCRIPT))
    assert out.decisions[0].evidence.line_start == 1 and out.decisions[0].label == "stated"


def test_duplicates_merged():
    """two near-identical action items -> one remains"""
    item = {"task": "Write the release notes by Friday", "label": "inferred"}
    out, warns = verify(_body(action_items=[item, {**item, "task": "Write the release notes by Friday."}]), preprocess(TRANSCRIPT))
    assert len(out.action_items) == 1 and any("duplicate" in w for w in warns)


def test_overview_always_inferred():
    """LLM labels overview 'stated' -> forced to inferred"""
    out, _ = verify(_body(overview="x", overview_label="stated"), preprocess(TRANSCRIPT))
    assert out.overview_label == "inferred"
