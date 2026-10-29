# Project Report: RecapRoom AI

## 1. Problem statement
Students and project teams spend hours re-reading transcripts to find decisions, action items and open questions. AI summarisers help,
but they can invent owners, deadlines and decisions, and users cannot tell what was really said. Target users: students, project teams,
meeting coordinators.

## 2. Objectives
Structured notes (overview, key points, decisions, actions, open questions); a Stated/Inferred label on every item with evidence;
never invent owners/deadlines; handle short and long transcripts; work offline in Demo Mode and online with Groq/Gemini;
export, compare meetings, test thoroughly, deploy on Streamlit Community Cloud.

## 3. Related work / resources
Meeting-summary and note-taking assistants; map-reduce summarisation of long documents; LLM hallucination research and
grounding/attribution techniques; Streamlit, Pydantic, rapidfuzz, Groq and Gemini API docs.

## 4. Architecture
Streamlit frontend (`app.py`, `pages/`, `components/`) → Python backend package (`backend/`): validators → preprocess → chunker →
summarizer (MAP/REDUCE with `llm_service`) → verifier → models → exporter/comparer. Config via `st.secrets`/`.env`. See README flowchart.

## 5. Modules
| Module | Responsibility |
|---|---|
| validators | empty/short/long/binary/oversize/gibberish checks, encoding fallback |
| preprocess | clean text, `L###` line numbers, speaker detection |
| chunker | ~3,000-word chunks, 200-word overlap, original line numbers kept |
| prompts | system, MAP, REDUCE and REPAIR templates |
| llm_service / mock_llm | provider calls with retry & error mapping / offline demo |
| summarizer | pipeline, JSON parsing and repair, merge and dedupe |
| verifier | quote, line, owner, deadline checks; duplicate removal |
| comparer | action matching between meetings, completion detection |
| exporter | Markdown/TXT with labels, evidence, settings, disclaimer |

## 6. Implementation notes
Pydantic v2 validates every model output. Retries use exponential backoff; auth errors are not retried. Logging redacts API keys and
never logs transcripts. Demo Mode shares the same prompts/pipeline so behaviour matches live mode structurally.

## 7. Testing
55 automated tests, LLM mocked (see `docs/test_report.md`): validation, preprocessing, chunking, verifier, pipeline (short/long/
ambiguous/lecture/injection), repair, provider failures, export, comparison, UI flows. Manual checks: screenshots and live URL.

## 8. Results
Add your own measurements here: demo timings, a live-mode example, and a table of 3–5 transcripts with items found and verifier
warnings. (Do not claim accuracy numbers you did not measure.)

## 9. Limitations
Model errors, ASR quality, speaker detection by pattern, rate limits, English only, temporary storage on Community Cloud.

## 10. Future scope
Multilingual support, saved history, team workspace, calendar integration, domain fine-tuning, a labelled evaluation set for measuring accuracy.
