# Presentation Outline (6–8 slides)

**1. Title:** RecapRoom AI: Lecture & Meeting Summarizer (team, GMRIT). *Notes:* one-line pitch.
**2. Problem & users:** long transcripts; AI summaries invent owners/deadlines; students, project teams, coordinators.
**3. Solution:** Stated vs Inferred labels, evidence quotes + line numbers, "Not specified" instead of guessing. Screenshot of results.
**4. Architecture:** flowchart (input → validate → preprocess → chunk → MAP → REDUCE → verifier → UI/export). Streamlit + Python backend + Groq/Gemini + Demo Mode.
**5. Live demo:** sample transcript → summary → evidence tab → export → one edge case (empty input / missing key).
**6. Testing & results:** 55 automated tests (offline); cases: fake owner removed, long transcript chunking, injection, provider outage; compare-meetings result.
**7. Limitations & responsible use:** model errors, ASR quality, speaker detection, rate limits, English only; privacy (don't upload confidential data).
**8. Future scope:** multilingual, saved history, team workspace, calendar reminders, fine-tuned domain models. *Closing:* thanks + repo/live URL.
