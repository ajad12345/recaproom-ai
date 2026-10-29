"""Compare two meetings: which actions from Meeting A are completed, still open, unresolved or new in B.

Matching is deterministic and explainable (fuzzy token similarity). Weak matches are flagged as
'uncertain' instead of being forced.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

from backend.utils.fuzzy import fuzz

from backend.core.preprocess import preprocess, split_speaker
from backend.core.summarizer import Progress, summarize_text
from backend.core.verifier import norm
from backend.models import ActionItem, MeetingSummary, SummarySettings

MATCH = 80
UNCERTAIN = 60
DONE_SCORE = 75
_DONE_RE = re.compile(r"\b(done|completed?|finished|shipped|merged|deployed|resolved|published|wrapped up|is ready|are ready)\b", re.I)
_FUTURE_RE = re.compile(r"\b(will|going to|need to|needs to|should|to be|not done|not finished|still)\b", re.I)
_STOP = set("""a an the to of and or in on at for with by from is are was were be been i we you it this that will
shall should can could please would my our their its as so up out about into""".split())
_DATEISH = re.compile(r"\b(?:by|before|until|due)\b|\b(?:next|this)\s+\w+day\b|\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b|tomorrow|next week|next month", re.I)


def _key(text: str) -> str:
    text = _DATEISH.sub(" ", text or "")
    return " ".join(sorted(t for t in norm(text).split() if t not in _STOP))


def _score(a: str, b: str) -> float:
    ka, kb = _key(a), _key(b)
    return float(fuzz.token_set_ratio(ka, kb)) if ka and kb else 0.0


@dataclass
class ActionMatch:
    action: ActionItem
    status: str  # completed | still_open | uncertain | unresolved
    score: float
    matched_text: Optional[str]
    reason: str


@dataclass
class ComparisonResult:
    actions: list[ActionMatch] = field(default_factory=list)
    new_actions: list[ActionItem] = field(default_factory=list)
    carried_questions: list[tuple[str, str, float]] = field(default_factory=list)
    changed_decisions: list[tuple[str, str, float]] = field(default_factory=list)

    def by_status(self, status: str) -> list[ActionMatch]:
        return [m for m in self.actions if m.status == status]


def compare_summaries(a: MeetingSummary, b: MeetingSummary, transcript_b: str) -> ComparisonResult:
    pre_b = preprocess(transcript_b)
    result = ComparisonResult()
    done_lines = [(l.number, l.text) for l in pre_b.lines
                  if _DONE_RE.search(l.text) and not _FUTURE_RE.search(split_speaker(l.text)[1])]

    for act in a.action_items:
        best_b = max(((_score(act.task, x.task), x) for x in b.action_items), key=lambda t: t[0], default=(0.0, None))
        done = max(((_score(act.task, t), n, t) for n, t in done_lines), key=lambda t: t[0], default=(0.0, 0, ""))
        if done[0] >= DONE_SCORE:
            result.actions.append(ActionMatch(act, "completed", done[0], f"L{done[1]}: {done[2]}",
                                              f"Meeting B mentions it as done (similarity {done[0]:.0f})."))
        elif best_b[0] >= MATCH:
            result.actions.append(ActionMatch(act, "still_open", best_b[0], best_b[1].task,
                                              f"Appears again as an action item in Meeting B (similarity {best_b[0]:.0f})."))
        elif best_b[0] >= UNCERTAIN:
            result.actions.append(ActionMatch(act, "uncertain", best_b[0], best_b[1].task,
                                              f"Weak match ({best_b[0]:.0f}); verify manually."))
        else:
            result.actions.append(ActionMatch(act, "unresolved", best_b[0], None,
                                              "Not mentioned as done and not repeated as an action in Meeting B."))

    for x in b.action_items:
        best = max((_score(x.task, act.task) for act in a.action_items), default=0.0)
        if best < UNCERTAIN:
            result.new_actions.append(x)

    for qa in a.open_questions:
        best = max(((_score(qa.text, qb.text), qb) for qb in b.open_questions), key=lambda t: t[0], default=(0.0, None))
        if best[0] >= MATCH:
            result.carried_questions.append((qa.text, best[1].text, best[0]))

    for da in a.decisions:
        best = max(((_score(da.text, db.text), db) for db in b.decisions), key=lambda t: t[0], default=(0.0, None))
        if best[1] is not None and 55 <= best[0] < 95:
            result.changed_decisions.append((da.text, best[1].text, best[0]))
    return result


def compare_transcripts(text_a: str, text_b: str, settings: SummarySettings, progress: Progress = None):
    """Summarise both transcripts and compare them. Returns (summary_a, summary_b, result)."""
    sa = summarize_text(text_a, settings, progress=progress)
    sb = summarize_text(text_b, settings, progress=progress)
    return sa, sb, compare_summaries(sa, sb, text_b)
