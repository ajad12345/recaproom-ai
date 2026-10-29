"""Clean a transcript, number its lines (L001, L002 ...) and detect speaker labels."""
import re
from collections import OrderedDict
from dataclasses import dataclass, field

_SPEAKER_RE = re.compile(
    r"^\s*(?:\[(?P<br>[^\]\n]{1,30})\]|(?P<plain>[A-Za-z][A-Za-z0-9.'\- ]{0,29}?))"
    r"\s*(?:\((?:\d{1,2}:)?\d{1,2}:\d{2}\))?\s*:\s*(?P<body>\S.*)$"
)
_NOT_NAMES = {"note", "notes", "action", "summary", "agenda", "topic", "decision", "question",
              "answer", "example", "remember", "important", "homework", "todo", "warning", "tip"}


@dataclass
class Line:
    number: int
    text: str


@dataclass
class Preprocessed:
    lines: list[Line]
    speakers: list[str] = field(default_factory=list)
    word_count: int = 0

    @property
    def clean_text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    def numbered_text(self) -> str:
        return "\n".join(f"L{line.number:03d}: {line.text}" for line in self.lines)


def _valid_name(name: str) -> bool:
    words = name.split()
    if not 1 <= len(words) <= 4 or name.lower() in _NOT_NAMES:
        return False
    return all(w[0].isupper() or w[0].isdigit() for w in words)


def split_speaker(text: str) -> tuple[str | None, str]:
    """Return (speaker or None, body)."""
    m = _SPEAKER_RE.match(text)
    if not m:
        return None, text.strip()
    name = (m.group("br") or m.group("plain") or "").strip()
    if not _valid_name(name):
        return None, text.strip()
    return name, m.group("body").strip()


def detect_speakers(texts: list[str], min_count: int = 2) -> list[str]:
    counts: "OrderedDict[str, int]" = OrderedDict()
    for t in texts:
        name, _ = split_speaker(t)
        if name:
            counts[name] = counts.get(name, 0) + 1
    if sum(counts.values()) < 3:
        return []
    return [n for n, c in counts.items() if c >= min_count]


def preprocess(text: str) -> Preprocessed:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    lines: list[Line] = []
    for raw in text.split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", raw).strip()
        if cleaned:
            lines.append(Line(number=len(lines) + 1, text=cleaned))
    words = sum(len(l.text.split()) for l in lines)
    return Preprocessed(lines=lines, speakers=detect_speakers([l.text for l in lines]), word_count=words)
