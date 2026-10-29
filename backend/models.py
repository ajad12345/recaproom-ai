"""Pydantic v2 schemas shared by the backend, the UI and the tests."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

NOT_SPECIFIED = "Not specified"
Label = Literal["stated", "inferred"]
_EMPTY = {"", "none", "null", "n/a", "na", "unknown", "unspecified", "not specified", "tbd", "-"}


def _clean_field(value) -> str:
    if value is None:
        return NOT_SPECIFIED
    text = str(value).strip()
    return NOT_SPECIFIED if text.lower() in _EMPTY else text


class Evidence(BaseModel):
    quote: str
    line_start: int = Field(default=0, ge=0)  # 0 = unknown (verifier will try to locate it)
    line_end: int = Field(default=0, ge=0)

    @field_validator("quote")
    @classmethod
    def _trim_quote(cls, v):
        return " ".join(str(v).split()[:25])

    @model_validator(mode="after")
    def _order(self):
        if self.line_end < self.line_start:
            self.line_end = self.line_start
        return self


class _Item(BaseModel):
    label: Label = "inferred"
    evidence: Optional[Evidence] = None

    @field_validator("label", mode="before")
    @classmethod
    def _lower(cls, v):
        return "inferred" if v is None else str(v).strip().lower()

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce_evidence(cls, v):
        if isinstance(v, dict) and not str(v.get("quote", "")).strip():
            return None
        if isinstance(v, str):
            return {"quote": v} if v.strip() else None
        return v


class KeyPoint(_Item):
    text: str


class Decision(_Item):
    text: str
    decided_by: str = NOT_SPECIFIED

    @field_validator("decided_by", mode="before")
    @classmethod
    def _by(cls, v):
        return _clean_field(v)


class ActionItem(_Item):
    task: str
    owner: str = NOT_SPECIFIED
    deadline: str = NOT_SPECIFIED
    status: str = "Open"

    @field_validator("owner", "deadline", mode="before")
    @classmethod
    def _not_specified(cls, v):
        return _clean_field(v)


class OpenQuestion(_Item):
    text: str


class SummaryBody(BaseModel):
    """What the LLM is asked to return."""
    overview: str = ""
    overview_label: Label = "inferred"
    key_points: list[KeyPoint] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)


class MeetingMeta(BaseModel):
    mode: Literal["LIVE", "DEMO"] = "DEMO"
    provider: str = "demo"
    model: str = ""
    length: str = "Standard"
    format: str = "Bullet notes"
    transcript_type: str = "Meeting"
    transcript_words: int = 0
    chunks: int = 1
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


class MeetingSummary(SummaryBody):
    speakers_detected: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: MeetingMeta = Field(default_factory=MeetingMeta)

    @property
    def missing_owner_count(self) -> int:
        return sum(1 for a in self.action_items if a.owner == NOT_SPECIFIED)

    @property
    def missing_deadline_count(self) -> int:
        return sum(1 for a in self.action_items if a.deadline == NOT_SPECIFIED)


class SummarySettings(BaseModel):
    length: Literal["Brief", "Standard", "Detailed"] = "Standard"
    fmt: Literal["Bullet notes", "Narrative paragraphs", "Structured table"] = "Bullet notes"
    transcript_type: Literal["Meeting", "Lecture"] = "Meeting"
    provider: str = "groq"
    demo_mode: bool = True
