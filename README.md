# 🎙️ RecapRoom AI — Lecture and Meeting Summarizer

> **AI-generated notes can be wrong. Always verify important items against the original transcript.**

RecapRoom AI turns long lecture and meeting transcripts into concise, trustworthy structured notes — with every output item clearly labelled as **Stated** (directly supported by the transcript) or **Inferred** (the model's interpretation).

---

## 1. Problem Statement

Students and project teams routinely sit through hours of lectures and meetings, then spend equal time re-reading full transcripts to extract action items, key decisions, and open questions. Existing AI summarisers hallucinate owners, deadlines, and decisions — users have no way to tell what the model invented versus what was actually said.

RecapRoom AI solves this by making honesty a first-class feature: every item carries a provenance label, stated items include a verbatim evidence quote with a line number, and a deterministic verifier (no additional LLM call) checks that those quotes, owner names, and deadline strings actually appear in the transcript before they reach the user.

---

## 2. Objectives

1. Generate structured summaries (overview, key points, decisions, action items, open questions) from any plain-text transcript.
2. Label every item as **Stated** or **Inferred** and provide evidence for stated items.
3. Never invent action owners or deadlines — output `"Not specified"` when not explicit.
4. Support both short (single-pass) and long (map-reduce) transcripts up to 60,000 words.
5. Run in **Demo Mode** with no API key and in **Live Mode** with Groq or Gemini.
6. Deploy on Streamlit Community Cloud with no local server dependency.

---

## 3. Features

### MVP
- ✅ Paste or upload `.txt` transcript (UTF-8, with latin-1 fallback)
- ✅ Settings: output length (Brief / Standard / Detailed), format (Bullets / Narrative / Table), transcript type (Lecture / Meeting)
- ✅ Output sections: Overview, Key Points, Decisions, Action Items, Open Questions
- ✅ **Stated / Inferred** labels with evidence quotes and line numbers
- ✅ Action items with owner, deadline, status — defaulting to `"Not specified"` when absent
- ✅ Warnings panel: missing owners, missing deadlines, unverified quotes
- ✅ Demo Mode (offline, no key required)
- ✅ Loading spinners, progress bar, Reset button

### Advanced Extensions
- ✅ Speaker label detection (with an attribution-uncertainty warning)
- ✅ Export to Markdown and plain text with full provenance
- ✅ Compare Two Meetings page (completed vs. still open vs. unresolved vs. new actions, with similarity scores and uncertain-match flags)
- ✅ Optional audio upload → transcript → editable review → summarise (needs a Groq key; shown only when a key is configured)

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit 1.40 |
| Data models | Pydantic v2 |
| LLM providers | Groq API, Gemini API (switchable) |
| Anti-hallucination | Deterministic verifier (rapidfuzz, no LLM) |
| Environment config | python-dotenv + st.secrets |
| Testing | pytest + pytest-mock + Streamlit AppTest |
| Language | Python 3.11 / 3.12 |
| Deployment | Streamlit Community Cloud |

---

## 5. Architecture

```mermaid
flowchart TD
    A[User Input\npaste / upload .txt] --> B[Validation\nvalidators.py]
    B --> C[Preprocess\nclean · line numbers · speaker detect]
    C --> D{Transcript size}
    D -- short ≤4000w --> E[Single-pass LLM call]
    D -- long > 4000w --> F[Chunker\n3000w chunks + 200w overlap]
    F --> G[MAP\nextract per chunk]
    G --> H[REDUCE\nmerge · deduplicate · resolve conflicts]
    E --> I[Verifier\ndeterministic checks\nno LLM call]
    H --> I
    I --> J[MeetingSummary\nPydantic schema]
    J --> K[Streamlit UI\ntabs · badges · warnings]
    J --> L[Export\n.md / .txt]
    K --> M[Compare Page\ncompleted · unresolved · new]
```

---

## 6. Project Structure

```
recaproom-ai/
├── app.py                      # Streamlit entry (main file on deploy): input, buttons, results. No prompts/logic
├── pages/
│   ├── 1_Compare_Meetings.py   # compare two meetings
│   └── 2_About_and_Limits.py   # privacy, limitations, how to read the output
├── components/
│   ├── sidebar.py              # settings, provider, Demo Mode toggle, status badge
│   └── result_views.py         # tabs, Stated/Inferred badges, evidence, tables, export buttons
├── backend/
│   ├── config.py               # get_setting(): st.secrets → env → .env; provider_status()
│   ├── models.py               # Pydantic v2 schemas
│   ├── services/
│   │   ├── llm_service.py      # Groq / Gemini calls, timeouts, retries, error mapping
│   │   ├── mock_llm.py         # Demo Mode (rule-based, offline)
│   │   └── transcribe_service.py  # optional audio → text
│   ├── core/
│   │   ├── preprocess.py       # clean text, line numbers, speaker detection
│   │   ├── chunker.py          # overlapping chunks for long transcripts
│   │   ├── prompts.py          # all prompt templates
│   │   ├── summarizer.py       # MAP → merge → REDUCE pipeline
│   │   ├── verifier.py         # deterministic anti-hallucination checks (no LLM)
│   │   ├── comparer.py         # compare two meetings
│   │   └── exporter.py         # Markdown / TXT export
│   └── utils/
│       ├── validators.py       # input and file validation
│       ├── logging_utils.py    # safe logging (keys redacted, no transcripts)
│       └── samples.py          # loads bundled sample transcripts
├── data/sample/                # 7 synthetic transcripts
├── tests/                      # 55 pytest tests (LLM fully mocked) incl. headless UI smoke tests
├── docs/                       # test report, project report, prompt design, viva cheat-sheet, slides outline, deployment checklist
├── assets/                     # put your screenshots here
├── .streamlit/config.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 7. Prerequisites

- Python 3.11 or 3.12
- pip (comes with Python)
- A Groq API key (free at [console.groq.com](https://console.groq.com)) **or** a Gemini API key (free at [aistudio.google.com](https://aistudio.google.com)) — **optional; Demo Mode works without any key**

---

## 8. Installation (Windows PowerShell)

```powershell
# Clone the repo
git clone https://github.com/ajad12345/recaproom-ai.git
cd recaproom-ai

# Create and activate a virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Open .env and set LLM_PROVIDER and your API key
```

**macOS / Linux:**
```bash
git clone https://github.com/ajad12345/recaproom-ai.git
cd recaproom-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
```

---

## 9. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 10. How to Use

### Demo Mode (no API key needed)
1. Run `streamlit run app.py`
2. Leave `LLM_PROVIDER=demo` in `.env` (the default)
3. Select a sample transcript from the dropdown or paste your own
4. Click **Summarise** — you will see realistic canned output labelled **DEMO MODE**

### Live Mode (with API key)
1. Set `LLM_PROVIDER=groq` and `GROQ_API_KEY=your-key` in `.env`
2. Run the app and paste/upload your transcript
3. Adjust settings in the sidebar (length, format, transcript type)
4. Click **Summarise** — results appear in tabs with Stated/Inferred badges

### Sample Expected Output (data/sample/short_meeting.txt, Demo Mode)
```
Action Items
STATED   | Task: I will set up the feature flag configuration by Friday.
         | Owner: Priya | Deadline: by Friday
         | Evidence: "Priya: I will set up the feature flag configuration by Friday." (L5)

STATED   | Task: Someone needs to prepare the A/B test report template.
         | Owner: Not specified | Deadline: Not specified   <- not in the transcript, never guessed
```
Demo Mode uses simple rules, so its wording is basic; Live Mode gives richer notes. Both go through the same verifier.

---

## 11. Configuration

Set these in `.env` (local) or Streamlit Secrets (cloud):

| Variable | Description | Example |
|---|---|---|
| `LLM_PROVIDER` | `groq`, `gemini`, or `demo` | `groq` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `GEMINI_API_KEY` | Gemini API key | `AIza...` |
| `MODEL_NAME` | Model override (optional) | `llama3-8b-8192` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` | `INFO` |

---

## 12. Testing

```bash
pytest -q                      # 55 tests, fully offline (LLM mocked), ~2 seconds
RECAP_REPORT=1 pytest -q       # also regenerates docs/test_report.md
```

Latest result: **55 passed**. Covered: input/file validation, preprocessing and speaker detection, chunking with overlap,
the verifier (fake owners/deadlines/quotes are removed), the pipeline in Demo Mode (short, long, ambiguous, lecture and
prompt-injection transcripts), invalid-JSON repair, provider outage/rate-limit/missing-key handling, exports, meeting
comparison, and headless UI flows. See [docs/test_report.md](docs/test_report.md).

---

## 13. Screenshots & Visual Walkthrough

| Screenshot | Description |
|---|---|
| ![Home Input Screen](assets/01_home_input.png) | **1. Home / Input View:** Sample transcript loader, input tabs (paste text, upload `.txt`, audio), settings, and live word counter. |
| ![Summary Results View](assets/02_summary_results.png) | **2. Summary Results View:** Overview card with provenance label, tabbed navigation, and Action Items with verbatim quotes and line numbers. |
| ![Edge Case & Verification Warnings](assets/03_edge_case_warnings.png) | **3. Edge Case & Verification Warnings:** Deterministic verifier catching hallucinated owners/deadlines, unverified quotes, and friendly missing key alerts. |
| ![Compare Two Meetings](assets/04_compare_meetings.png) | **4. Cross-Meeting Comparative Diff:** Tracks actions across recurring syncs (completed, unresolved, new actions, carried-over questions). |

### Deliverables & Artifacts
- **GitHub Repository:** [https://github.com/ajad12345/recaproom-ai](https://github.com/ajad12345/recaproom-ai)
- **Live Streamlit App:** `https://recaproom-ai.streamlit.app` *(or your custom app URL on Streamlit Cloud)*
- **Executive Presentation:** [RecapRoom_AI_Presentation.pptx](RecapRoom_AI_Presentation.pptx) (16:9 widescreen, industry-standard slides)
- **Technical Documentation:** [docs/technical_documentation.md](docs/technical_documentation.md)
- **Empirical Test Report (55/55 passed):** [docs/test_report.md](docs/test_report.md)
- **Viva Defense Cheatsheet:** [docs/viva_cheatsheet.md](docs/viva_cheatsheet.md)

---

## 14. Known Limitations

1. **Model errors** — LLMs can still misclassify an item as stated vs. inferred. Always verify.
2. **ASR transcripts** — Automatic speech recognition errors propagate into summaries. Review the transcript for accuracy first.
3. **Speaker attribution** — Speaker detection is pattern-based. Inconsistent or missing labels will degrade attribution quality.
4. **Rate limits** — Free Groq and Gemini tiers have token-per-minute limits. Very long transcripts may hit these limits.
5. **Language** — English only in the current version.
6. **Temporary storage** — Results are not persisted between sessions on Streamlit Community Cloud. Download your export before leaving the page.

---

## 15. Privacy and Responsible Use

- **Do not upload confidential or personal data.**
- In Demo Mode, no data leaves your machine.
- In Live Mode, transcript text is sent to the configured LLM provider. Review [Groq's privacy policy](https://groq.com/privacy-policy/) or [Google's privacy policy](https://policies.google.com/privacy) before using real transcripts.
- All sample transcripts in this repo are fully synthetic and contain no real persons or organisations.

---

## 16. Future Enhancements

- Audio upload → transcription → editable review → summarise (Groq Whisper)
- Multi-language support
- Persistent storage (user accounts, summary history)
- Team workspace: shared summaries and action tracking
- Integration with calendar apps for automatic action-item reminders
- Fine-tuned model for domain-specific transcripts (medical, legal)

---

## 17. Credits and License

**RecapRoom AI** was built as a student project for the GMRIT Grand AI & NLP Projects Handbook.

**Team Members (GMR Institute of Technology - Department of CSE):**
- **Jammu Dinesh (23341A05A3)** — Core Pipeline: Preprocessing, line-number indexing, overlapping chunker & Map-Reduce summarization.
- **Manish Sharma (23341A05F7)** — LLM Services: Provider integrations (Groq & Gemini), prompt templates, offline mock engine & config.
- **Mohammed Ajad (23341A05G3)** — Frontend & Verification: Streamlit UI, deterministic anti-hallucination verifier, meeting comparison diff, test suite & cloud deployment.

**Libraries:** Streamlit, Pydantic, Groq, Google GenerativeAI, rapidfuzz, python-dotenv, pytest.

Released under the **MIT License** — see [LICENSE](LICENSE).

---

## Contributing

We use a **branch-per-feature** workflow. Suggested branches and commit messages:

```
feat/validators          "Add transcript validators"
feat/mock-llm            "Add demo mode mock LLM responses"
feat/preprocess          "Add line numbering and speaker detection"
feat/chunker             "Add overlap chunker for long transcripts"
feat/prompts             "Add map-reduce prompt templates"
feat/llm-service         "Add Groq/Gemini provider with error handling"
feat/summarizer          "Add single-pass summarisation pipeline"
feat/map-reduce          "Add chunking + map-reduce pipeline"
feat/verifier            "Add evidence verifier and anti-hallucination checks"
feat/exporter            "Add Markdown and TXT export"
feat/compare-page        "Add Compare Two Meetings page"
feat/tests               "Add full pytest suite with mocked LLM"
feat/docs                "Add README, viva cheatsheet, presentation outline"
```

**Before every push:** run `git status` and `pytest -q`. **Never commit `.env` or API keys.**

### Team Work Split (3 Members)

| Team Member | Roll Number | Key Responsibilities & Modules |
|---|---|---|
| **Jammu Dinesh** | `23341A05A3` | `backend/core/preprocess.py`, `backend/core/chunker.py`, `backend/core/summarizer.py`, Map-Reduce pipeline, long-transcript testing |
| **Manish Sharma** | `23341A05F7` | `backend/services/llm_service.py`, `backend/services/mock_llm.py`, `backend/core/prompts.py`, `backend/config.py`, prompt injection defense |
| **Mohammed Ajad** | `23341A05G3` | `app.py`, `components/`, `pages/`, `backend/core/verifier.py`, `backend/core/comparer.py`, `backend/core/exporter.py`, `tests/`, deployment |
