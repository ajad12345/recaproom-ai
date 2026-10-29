# Viva Cheat-Sheet: RecapRoom AI

## 30-second pitch
RecapRoom turns lecture/meeting transcripts into notes where every item is labelled **Stated** (with a quote and line number) or
**Inferred**, and where owners and deadlines are never invented.

## Data flow
paste/upload → `validators.py` → `preprocess.py` (clean, number lines, detect speakers) → `chunker.py` (only if >4,000 words)
→ MAP per chunk (`summarizer.py` + `prompts.py` + `llm_service.py`) → merge/dedupe → REDUCE → `verifier.py` → `MeetingSummary`
→ `result_views.py` (tabs) / `exporter.py`.

## Main files
| File | Role |
|---|---|
| `app.py` | UI only: input, buttons, error display |
| `backend/core/summarizer.py` | pipeline orchestration, JSON parse + repair |
| `backend/core/verifier.py` | deterministic hallucination checks |
| `backend/services/llm_service.py` | Groq/Gemini, retries, error mapping |
| `backend/services/mock_llm.py` | Demo Mode |
| `backend/core/comparer.py` | compare two meetings |
| `backend/models.py` | Pydantic schemas |

## Likely questions
- **Why map-reduce?** Long transcripts exceed what a model handles reliably in one call. We summarise overlapping chunks, merge, then reduce.
- **Why overlap?** So an item spanning a chunk boundary is not lost; duplicates are removed afterwards.
- **How do you stop invented owners/deadlines?** Prompt rule + verifier: names and date phrases must appear in the transcript, else "Not specified".
- **Why a deterministic verifier and not another LLM?** An LLM checking an LLM can make the same mistake. String matching is predictable and testable.
- **What is Demo Mode for?** Works with no key/internet, demonstrates the full flow, makes tests free and repeatable. It is labelled DEMO everywhere.
- **What if the model returns bad JSON?** One repair retry, then a friendly error (no stack trace).
- **What about prompt injection?** Transcript is treated as data; output is validated against a schema; a test uses an injection transcript.
- **How is comparison explained?** Token-set similarity between action texts; ≥80 match, 60–80 flagged uncertain; done-lines in Meeting B detected separately.

## Three honest limitations
1. The model can still mislabel an interpretation as stated; the verifier only checks that quotes/names/dates exist.
2. Demo Mode is rule-based and basic.
3. Speaker detection and action matching are pattern/similarity-based and can be wrong; English only.

## Demo script (3–5 min)
1. Home page, privacy note. 2. Load `short_meeting.txt` → Summarise (Demo Mode). 3. Show Stated vs Inferred, "Not specified" warning.
4. Evidence tab. 5. Edge case: empty input / Demo Mode off without key → readable error. 6. Compare page. 7. Export Markdown.
