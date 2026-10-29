"""Deterministic anti-hallucination checks. No LLM call is made here.

Checks (all against the original transcript):
  * every evidence quote really appears (otherwise the item is downgraded to 'inferred')
  * line numbers are corrected when the quote is found on another line
  * owners / decided_by names must appear in the transcript (otherwise 'Not specified')
  * deadline strings must appear in the transcript (otherwise 'Not specified')
  * duplicates are removed
"""
import re

from backend.utils.fuzzy import fuzz

from backend.core.preprocess import Preprocessed
from backend.models import NOT_SPECIFIED, SummaryBody


def norm(text: str) -> str:
    text = (text or "").lower().replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def dedupe_items(items: list, key, threshold: int = 90) -> tuple[list, int]:
    kept: list = []
    kept_keys: list[str] = []
    removed = 0
    for item in items:
        k = norm(key(item))
        if not k:
            removed += 1
            continue
        if any(fuzz.ratio(k, other) >= threshold for other in kept_keys):
            removed += 1
            continue
        kept.append(item)
        kept_keys.append(k)
    return kept, removed


def _locate(quote_norm: str, line_norms: list[tuple[int, str]]):
    for number, ln in line_norms:
        if quote_norm in ln:
            return number, number
    for (n1, l1), (n2, l2) in zip(line_norms, line_norms[1:]):
        if quote_norm in f"{l1} {l2}":
            return n1, n2
    return None


def _short(text: str, n: int = 60) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def verify(body: SummaryBody, pre: Preprocessed) -> tuple[SummaryBody, list[str]]:
    body = body.model_copy(deep=True)
    warnings: list[str] = []
    line_norms = [(l.number, norm(l.text)) for l in pre.lines]
    full_norm = " ".join(ln for _, ln in line_norms)
    vocab = set(full_norm.split())

    def check_evidence(item, label_text: str):
        ev = item.evidence
        if ev is None:
            if item.label == "stated":
                item.label = "inferred"
                warnings.append(f"“{_short(label_text)}” was marked stated but had no evidence; shown as inferred.")
            return
        q = norm(ev.quote)
        found = bool(q) and (q in full_norm or (len(q) >= 12 and fuzz.partial_ratio(q, full_norm) >= 92))
        if not found:
            item.evidence = None
            item.label = "inferred"
            warnings.append(f"Evidence quote for “{_short(label_text)}” was not found in the transcript; shown as inferred.")
            return
        loc = _locate(q, line_norms)
        if loc:
            ev.line_start, ev.line_end = loc

    def check_name(value: str, label_text: str, field: str) -> str:
        if value == NOT_SPECIFIED:
            return value
        tokens = [t for t in re.findall(r"\w+", value.lower()) if len(t) >= 2]
        if tokens and any(t in vocab for t in tokens):
            return value
        warnings.append(f"{field} “{value}” for “{_short(label_text)}” does not appear in the transcript; set to Not specified.")
        return NOT_SPECIFIED

    def check_deadline(value: str, label_text: str) -> str:
        if value == NOT_SPECIFIED:
            return value
        v = norm(value)
        stripped = re.sub(r"^(by|before|until|due on|due|on)\s+", "", v)
        if v and (v in full_norm or stripped in full_norm):
            return value
        warnings.append(f"Deadline “{value}” for “{_short(label_text)}” does not appear in the transcript; set to Not specified.")
        return NOT_SPECIFIED

    for kp in body.key_points:
        check_evidence(kp, kp.text)
    for d in body.decisions:
        check_evidence(d, d.text)
        d.decided_by = check_name(d.decided_by, d.text, "Decision maker")
    for a in body.action_items:
        check_evidence(a, a.task)
        a.owner = check_name(a.owner, a.task, "Owner")
        a.deadline = check_deadline(a.deadline, a.task)
    for q in body.open_questions:
        check_evidence(q, q.text)
    body.overview_label = "inferred"

    for name, key in (("key point", lambda x: x.text), ("decision", lambda x: x.text),
                      ("action item", lambda x: x.task), ("open question", lambda x: x.text)):
        attr = {"key point": "key_points", "decision": "decisions", "action item": "action_items",
                "open question": "open_questions"}[name]
        kept, removed = dedupe_items(getattr(body, attr), key)
        setattr(body, attr, kept)
        if removed:
            warnings.append(f"Removed {removed} duplicate or empty {name}(s).")
    return body, warnings
