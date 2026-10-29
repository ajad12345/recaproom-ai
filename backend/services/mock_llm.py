"""Demo mode: a deterministic, rule-based stand-in for the LLM.

It reads the numbered transcript out of the prompt and extracts items with simple patterns, so the
quotes and line numbers are real and the whole pipeline (parsing, verifier, UI) behaves exactly as in
live mode. No network, no API key. Output quality is intentionally basic: it is a demo, not a model.
"""
import json
import re
from collections import Counter

from backend.core.preprocess import detect_speakers, split_speaker
from backend.core.prompts import LIMITS

_DAY = r"(?:mon|tues|wednes|thurs|fri|satur|sun)day"
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_DEADLINE_RE = re.compile(
    rf"\b((?:by|before|until|due(?: on)?|on)\s+)?((?:next|this|coming)\s+{_DAY}|{_DAY}|tomorrow|tonight|"
    rf"end of (?:the )?(?:day|week|month|sprint|quarter)|next week|next month|"
    rf"{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?|\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{_MONTH})\b",
    re.I,
)
_ACTION_RE = re.compile(
    r"\b(i will|i'll|i'm going to|we will|we'll|will (?:set|send|prepare|draft|review|create|update|write|check|"
    r"share|fix|build|test|schedule|follow|handle|own|look|reach|book|finali[sz]e|submit|complete|run|"
    r"investigate|integrate|collect|migrate|deploy|document|plan|design)|"
    r"needs? to \w+|should \w+|must \w+|has to \w+|action item|going to \w+|responsible for|"
    r"(?:can|could) you (?:please )?\w+)\b", re.I)
_REQUEST_RE = re.compile(r"\b([A-Z][a-z]{2,}),?\s+(?:can|could) you\b")
_LECTURE_ACTION_RE = re.compile(r"\b(homework|assignment|exercise for|please submit|submit (?:it|your)|due)\b", re.I)
_DECISION_RE = re.compile(
    r"\b(we(?:'ve| have)? (?:agreed|decided|settled)|(?:agreed|decided) (?:to|on|that)|let'?s go with|"
    r"we'?ll go with|the decision is|decision:|approved|final call|going with)\b", re.I)
_SELF_RE = re.compile(r"\b(i will|i'll|i'm going to|let me)\b", re.I)
_NAME_RE = re.compile(r"\b([A-Z][a-z]{2,})\s+(?:will|should|needs? to|is going to|has to|must)\b")
_ACK_RE = re.compile(r"^(sure|okay|ok|yes|yeah|will do|of course|i'll|i will|i can|got it)\b", re.I)
_NOT_OWNERS = {"someone", "somebody", "anyone", "anybody", "everyone", "everybody", "nobody", "team", "this",
               "that", "there", "then", "they", "also", "and", "but", "who", "what", "when", "which", "one",
               "the", "maybe", "please", "these", "those", "students", "people"}
_MEETING_KW = re.compile(r"\b(roadmap|launch|release|budget|risk|blocker|priority|deadline|milestone|status|"
                         r"plan|issue|metric|customer|feature|ready|testing|bug|delay|cost|timeline)\b", re.I)
_LECTURE_KW = re.compile(r"\b(defined as|is called|means|refers to|for example|for instance|important|key idea|"
                         r"remember|in other words|because|therefore|is a|is the)\b", re.I)
_STOP = set("""that this with from have will your about there their which would could should these those
because where when what then than them they were been being into also just more most some such only over
very much many other like make made does done each both while after before again here going think really""".split())


def _words(text: str, n: int = 30) -> str:
    parts = text.split()
    return " ".join(parts[:n]) + ("…" if len(parts) > n else "")


def _evidence(raw: str, n: int) -> dict:
    return {"quote": " ".join(raw.split()[:25]), "line_start": n, "line_end": n}


def _param(user: str, name: str, default: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", user, re.M)
    return m.group(1).strip() if m else default


def _action_sentence(body: str) -> str:
    """Pick the sentence that actually contains the action (falls back to the whole body)."""
    for sent in re.split(r"(?<=[.!?])\s+", body):
        if _ACTION_RE.search(sent) or _REQUEST_RE.search(sent):
            return sent
    return body


def _owner_for(speaker, body: str) -> str:
    if speaker and _SELF_RE.search(body):
        return speaker
    m = _REQUEST_RE.search(body)
    if m:
        return m.group(1)
    for m in _NAME_RE.finditer(body):
        if m.group(1).lower() not in _NOT_OWNERS:
            return m.group(1)
    return "Not specified"


def _deadline_for(body: str) -> str:
    m = _DEADLINE_RE.search(body)
    return ((m.group(1) or "") + m.group(2)).strip() if m else "Not specified"


class MockLLMService:
    mode = "DEMO"
    provider = "demo"
    model = "demo-heuristic"

    def generate(self, system: str, user: str) -> str:
        m = re.search(r"^TASK:\s*(\w+)", user, re.M)
        task = m.group(1).upper() if m else "MAP"
        if task == "REDUCE":
            return json.dumps(self._reduce(user))
        if task == "REPAIR":
            return json.dumps({"overview": "", "key_points": [], "decisions": [], "action_items": [], "open_questions": []})
        return json.dumps(self._map(user))

    # ------------------------------------------------------------------ MAP
    def _map(self, user: str) -> dict:
        ttype = _param(user, "TRANSCRIPT_TYPE", "Meeting")
        length = _param(user, "LENGTH", "Standard")
        kp_cap, q_cap, sent_cap = LIMITS.get(length, LIMITS["Standard"])
        body_m = re.search(r"<<<TRANSCRIPT\n(.*?)\nTRANSCRIPT>>>", user, re.S)
        lines = []
        for ln in (body_m.group(1) if body_m else "").split("\n"):
            lm = re.match(r"L(\d+):\s?(.*)$", ln)
            if lm:
                lines.append((int(lm.group(1)), lm.group(2)))

        speakers = detect_speakers([t for _, t in lines])
        decisions, actions, questions, used = [], [], [], set()
        last_request = None  # (line_no, owner, action dict)
        for idx, (n, raw) in enumerate(lines):
            speaker, body = split_speaker(raw)
            if len(body.split()) < 4:
                continue
            is_q = body.rstrip().endswith("?")
            if _DECISION_RE.search(body):
                dm = re.search(r"\b([A-Z][a-z]{2,})\s+(?:approved|decided|agreed)\b", body)
                decisions.append({"text": _words(body), "label": "stated", "evidence": _evidence(raw, n),
                                  "decided_by": dm.group(1) if dm and dm.group(1).lower() not in _NOT_OWNERS else "Not specified"})
                used.add(n)
                continue
            if ttype == "Lecture":
                if _LECTURE_ACTION_RE.search(body):
                    actions.append({"task": _words(body), "owner": "Not specified", "deadline": _deadline_for(body),
                                    "status": "Open", "label": "stated", "evidence": _evidence(raw, n)})
                    used.add(n)
                    continue
            else:
                if is_q and _REQUEST_RE.search(body):
                    owner = _owner_for(speaker, body)
                    act = {"task": _words(_action_sentence(body)), "owner": owner, "deadline": _deadline_for(body), "status": "Open",
                           "label": "stated", "evidence": _evidence(raw, n)}
                    actions.append(act)
                    last_request = (n, owner, act)
                    used.add(n)
                    continue
                if not is_q and _ACTION_RE.search(body):
                    if last_request and last_request[0] == n - 1 and speaker == last_request[1] and _ACK_RE.match(body):
                        if last_request[2]["deadline"] == "Not specified":
                            last_request[2]["deadline"] = _deadline_for(body)
                        used.add(n)
                        continue
                    sent = _action_sentence(body)
                    actions.append({"task": _words(sent), "owner": _owner_for(speaker, sent),
                                    "deadline": _deadline_for(sent), "status": "Open", "label": "stated",
                                    "evidence": _evidence(raw, n)})
                    used.add(n)
                    continue
            if is_q and len(body.split()) >= 6:
                questions.append({"text": _words(body), "label": "stated", "evidence": _evidence(raw, n)})
                used.add(n)

        # key points: score the remaining lines
        kw = _LECTURE_KW if ttype == "Lecture" else _MEETING_KW
        scored = []
        for n, raw in lines:
            if n in used:
                continue
            _, body = split_speaker(raw)
            wc = len(body.split())
            if wc < 6:
                continue
            score = len(kw.findall(body)) + (1 if 8 <= wc <= 40 else 0)
            scored.append((score, n, raw, body))
        top = sorted(scored, key=lambda s: (-s[0], s[1]))[:kp_cap]
        key_points = [{"text": _words(b), "label": "stated", "evidence": _evidence(r, n)}
                      for _, n, r, b in sorted(top, key=lambda s: s[1])]

        # a few clearly-labelled inferred items so the demo shows both badges
        counts = Counter(w for _, t in lines for w in re.findall(r"[a-z]{5,}", t.lower()) if w not in _STOP)
        topics = [w for w, _ in counts.most_common(5)]
        if topics and length != "Brief":
            key_points.append({"text": "Most frequently mentioned terms: " + ", ".join(topics) + ".",
                               "label": "inferred", "evidence": None})
        if ttype == "Meeting" and length != "Brief":
            for a in [a for a in actions if a["owner"] == "Not specified"][:2]:
                questions.append({"text": f"Who will take ownership of: {_words(a['task'], 12)}?",
                                  "label": "inferred", "evidence": None})

        words = sum(len(t.split()) for _, t in lines)
        parts = [f"This {'lecture' if ttype == 'Lecture' else 'meeting'} transcript section has about {words:,} words"
                 + (f" and {len(speakers)} identified speakers ({', '.join(speakers[:5])})." if speakers else ".")]
        if topics:
            parts.append("Frequently mentioned terms: " + ", ".join(topics) + ".")
        parts.append(f"The notes list {len(actions)} action item(s), {len(decisions)} decision(s) and "
                     f"{len(questions)} open question(s) found in the text.")
        parts.append("This overview was generated in demo mode by simple rules, not by a language model.")
        return {"overview": " ".join(parts[:sent_cap]), "overview_label": "inferred", "key_points": key_points,
                "decisions": decisions, "action_items": actions, "open_questions": questions[:q_cap + 2]}

    # --------------------------------------------------------------- REDUCE
    def _reduce(self, user: str) -> dict:
        length = _param(user, "LENGTH", "Standard")
        kp_cap, q_cap, _ = LIMITS.get(length, LIMITS["Standard"])
        m = re.search(r"<<<DATA\n(.*?)\nDATA>>>", user, re.S)
        data = json.loads(m.group(1)) if m else {}
        stated = [k for k in data.get("key_points", []) if k.get("label") == "stated"]
        inferred = [k for k in data.get("key_points", []) if k.get("label") != "stated"]
        data["key_points"] = sorted(stated, key=lambda k: (k.get("evidence") or {}).get("line_start", 0))[:kp_cap] + inferred[:1]
        data["open_questions"] = data.get("open_questions", [])[: q_cap + 2]
        overview = data.get("overview", "")
        data["overview"] = overview[:700] + ("…" if len(overview) > 700 else "")
        return data
