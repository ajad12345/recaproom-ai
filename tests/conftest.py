"""Shared fixtures + optional auto-generated test report (RECAP_REPORT=1 pytest)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.models import SummarySettings  # noqa: E402
from backend.utils.samples import read_sample  # noqa: E402

_RESULTS: list[tuple[str, str, str, str]] = []


@pytest.fixture
def settings():
    return SummarySettings(demo_mode=True, provider="groq")


@pytest.fixture
def sample():
    return read_sample


class FakeLLM:
    """Scripted LLM: returns the given raw strings in order (the last one repeats)."""
    mode, provider, model = "LIVE", "fake", "fake-1"

    def __init__(self, *responses: str):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, system, user):
        r = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return r


@pytest.fixture
def fake_llm():
    return FakeLLM


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.skipped):
        doc = (item.function.__doc__ or item.name).strip().replace("\n", " ")
        inp, _, exp = doc.partition("->")
        msg = "Matched expected result" if rep.passed else (str(rep.longrepr).strip().splitlines()[-1][:160] if rep.failed else "skipped")
        _RESULTS.append((item.name, inp.strip(), exp.strip() or "see test", f"{msg}|{'PASS' if rep.passed else 'FAIL' if rep.failed else 'SKIP'}"))


def pytest_sessionfinish(session, exitstatus):
    if not os.environ.get("RECAP_REPORT"):
        return
    lines = ["# Test Report", "", "Generated automatically by `RECAP_REPORT=1 pytest -q`. "
             "All LLM calls are mocked, so the suite runs offline.", "",
             f"**Total: {len(_RESULTS)} tests, {sum(r[3].endswith('PASS') for r in _RESULTS)} passed.**", "",
             "| ID | Input | Expected result | Actual result | Pass/Fail |", "|---|---|---|---|---|"]
    for i, (name, inp, exp, act) in enumerate(_RESULTS, 1):
        actual, status = act.split("|")
        esc = lambda s: s.replace("|", "/")
        lines.append(f"| T{i:02d} | {esc(inp)} | {esc(exp)} | {esc(actual)} | {status} |")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "test_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
