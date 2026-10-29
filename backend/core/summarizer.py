"""Summarisation pipeline: preprocess -> (chunk -> MAP) -> merge -> REDUCE -> verify -> MeetingSummary."""
import json
import math
import re
from typing import Callable, Optional

from backend.core import prompts
from backend.core.chunker import chunk_lines
from backend.core.preprocess import preprocess
from backend.core.verifier import dedupe_items, verify
from backend.models import MeetingMeta, MeetingSummary, SummaryBody, SummarySettings
from backend.services.llm_service import InvalidResponseError, get_llm_service
from backend.utils.logging_utils import get_logger
from backend.utils.validators import validate_text_input

log = get_logger(__name__)
SINGLE_PASS_WORDS = 4000
CHUNK_WORDS = 3000
OVERLAP_WORDS = 200
Progress = Optional[Callable[[int, int, str], None]]


def estimate_chunks(words: int) -> int:
    return 1 if words <= SINGLE_PASS_WORDS else math.ceil(words / (CHUNK_WORDS - OVERLAP_WORDS))


def parse_body(raw: str) -> SummaryBody:
    """Parse model output into SummaryBody. Raises ValueError on bad JSON/schema."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the model output.")
    return SummaryBody.model_validate(json.loads(text[start:end + 1]))


def _call_and_parse(llm, system: str, user: str) -> SummaryBody:
    raw = llm.generate(system, user)
    problem = ""
    try:
        return parse_body(raw)
    except ValueError as first:
        problem = str(first)
        log.info("Model output invalid (%s); asking for a repair.", problem[:120])
    raw2 = llm.generate(*prompts.build_repair_prompt(raw, problem))
    try:
        return parse_body(raw2)
    except ValueError as second:
        raise InvalidResponseError(
            "The AI returned an answer in the wrong format twice. Please try again, or switch to Demo Mode."
        ) from second


def merge_bodies(bodies: list[SummaryBody]) -> SummaryBody:
    merged = SummaryBody(overview=" ".join(b.overview for b in bodies if b.overview))
    for b in bodies:
        merged.key_points += b.key_points
        merged.decisions += b.decisions
        merged.action_items += b.action_items
        merged.open_questions += b.open_questions
    merged.key_points, _ = dedupe_items(merged.key_points, lambda x: x.text)
    merged.decisions, _ = dedupe_items(merged.decisions, lambda x: x.text)
    merged.action_items, _ = dedupe_items(merged.action_items, lambda x: x.task)
    merged.open_questions, _ = dedupe_items(merged.open_questions, lambda x: x.text)
    return merged


def summarize_text(text: str, settings: SummarySettings, llm=None, progress: Progress = None) -> MeetingSummary:
    clean, input_warnings = validate_text_input(text)
    pre = preprocess(clean)
    llm = llm or get_llm_service(settings.provider, settings.demo_mode)
    chunks = chunk_lines(pre.lines, CHUNK_WORDS, OVERLAP_WORDS) if pre.word_count > SINGLE_PASS_WORDS \
        else chunk_lines(pre.lines, chunk_words=10 ** 9)
    steps = len(chunks) + (1 if len(chunks) > 1 else 0) + 1

    def tick(i: int, msg: str):
        if progress:
            progress(i, steps, msg)

    extra: list[str] = list(input_warnings)
    bodies = []
    for i, ch in enumerate(chunks):
        tick(i, f"Reading section {i + 1} of {len(chunks)}…")
        system, user = prompts.build_map_prompt(ch.text, settings.transcript_type, settings.length,
                                                settings.fmt, i + 1, len(chunks))
        bodies.append(_call_and_parse(llm, system, user))

    if len(bodies) == 1:
        body = bodies[0]
    else:
        tick(len(chunks), "Merging sections…")
        merged = merge_bodies(bodies)
        system, user = prompts.build_reduce_prompt(merged.model_dump_json(), settings.transcript_type,
                                                   settings.length, settings.fmt)
        try:
            body = _call_and_parse(llm, system, user)
        except InvalidResponseError:
            body = merged
            extra.append("The final merge step failed, so the combined notes of all sections are shown.")
        extra.append(f"Long transcript: processed in {len(chunks)} overlapping sections.")

    tick(steps - 1, "Checking evidence against the transcript…")
    body, verifier_warnings = verify(body, pre)
    tick(steps, "Done")
    meta = MeetingMeta(mode=llm.mode, provider=llm.provider, model=llm.model, length=settings.length,
                       format=settings.fmt, transcript_type=settings.transcript_type,
                       transcript_words=pre.word_count, chunks=len(chunks))
    return MeetingSummary(**body.model_dump(), speakers_detected=pre.speakers,
                          warnings=extra + verifier_warnings, meta=meta)
