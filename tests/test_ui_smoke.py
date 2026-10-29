"""UI smoke tests using Streamlit's AppTest (headless)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _app(page="app.py"):
    return AppTest.from_file(str(ROOT / page), default_timeout=60)


def test_home_page_loads_in_demo_mode():
    """open app.py with no API key -> no exception, Demo Mode toggle on, title shown"""
    at = _app().run()
    assert not at.exception
    assert at.toggle(key="demo_mode").value is True
    assert any("RecapRoom" in t.value for t in at.title)


def test_empty_input_shows_warning():
    """click Summarise with empty text -> warning, no summary"""
    at = _app().run()
    next(b for b in at.button if "Summarise" in b.label).click().run()
    assert not at.exception and any("paste or upload" in w.value for w in at.warning)
    assert "summary" not in at.session_state


def test_sample_to_summary_flow():
    """load short_meeting sample then Summarise -> summary stored in session, results rendered"""
    at = _app().run()
    at.selectbox(key="sample_choice").select("short_meeting.txt").run()
    next(b for b in at.button if "Summarise" in b.label).click().run()
    assert not at.exception
    s = at.session_state["summary"]
    assert s.meta.mode == "DEMO" and s.action_items
    assert len(at.tabs) >= 6


def test_live_mode_without_key_shows_readable_error():
    """Demo Mode off and no key -> readable error mentioning Demo Mode, no crash"""
    at = _app().run()
    at.selectbox(key="sample_choice").select("short_meeting.txt").run()
    at.toggle(key="demo_mode").set_value(False).run()
    next(b for b in at.button if "Summarise" in b.label).click().run()
    assert not at.exception and any("API key" in e.value for e in at.error)


def test_reset_clears_state():
    """Reset after a summary -> summary and text removed"""
    at = _app().run()
    at.selectbox(key="sample_choice").select("short_meeting.txt").run()
    next(b for b in at.button if "Summarise" in b.label).click().run()
    next(b for b in at.button if b.label == "Reset").click().run()
    assert "summary" not in at.session_state


def test_compare_page_runs():
    """compare page with preloaded sample pair -> results rendered without error"""
    at = _app("pages/1_Compare_Meetings.py").run()
    next(b for b in at.button if "Compare" in b.label).click().run()
    assert not at.exception and "cmp_result" in at.session_state


def test_about_page_loads():
    """about page -> loads without error"""
    assert not _app("pages/2_About_and_Limits.py").run().exception
