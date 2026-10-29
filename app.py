"""
app.py — RecapRoom AI (Streamlit entry point)
This file has NO prompts, NO model calls and NO business logic. It collects input, calls backend
functions and displays results or readable errors.
"""
import streamlit as st

from backend.core.summarizer import estimate_chunks, summarize_text
from backend.services.llm_service import LLMError, MissingKeyError
from backend.services.transcribe_service import audio_available, transcribe_audio
from backend.utils.logging_utils import get_logger
from backend.utils.samples import list_samples, read_sample
from backend.utils.validators import count_words, validate_text_input, validate_upload
from components.result_views import render_summary
from components.sidebar import render_sidebar
from components.ui_theme import inject_custom_theme, render_hero_header

st.set_page_config(page_title="RecapRoom AI — Lecture and Meeting Summarizer", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded",
                   menu_items={"About": "RecapRoom AI by Jammu Dinesh (23341A05A3), Manish Sharma (23341A05F7), Mohammed Ajad (23341A05G3) — GMRIT CSE"})
inject_custom_theme()
log = get_logger("app")
st.session_state.setdefault("reset_counter", 0)


def _on_sample():
    choice = st.session_state.get("sample_choice")
    if choice and choice != "—":
        st.session_state["transcript_text"] = read_sample(choice)
        st.session_state.pop("summary", None)


def _reset():
    for key in ("summary", "transcript_text", "audio_text", "sample_choice"):
        st.session_state.pop(key, None)
    st.session_state["reset_counter"] += 1


def _run(text: str, settings):
    try:
        clean, warns = validate_text_input(text)
        for w in warns:
            st.warning(w)
        bar = st.progress(0.0, text="Initializing verifier pipeline…")

        def on_progress(done: int, total: int, msg: str):
            bar.progress(min(done / total, 1.0), text=msg)

        with st.spinner("Extracting & verifying grounded claims…"):
            st.session_state["summary"] = summarize_text(clean, settings, progress=on_progress)
        bar.empty()
    except ValueError as err:
        st.warning(str(err))
    except MissingKeyError as err:
        st.error(str(err))
        st.info("Tip: turn on **Demo Mode** in the sidebar to try the app without a key.")
    except LLMError as err:
        st.error(str(err))
        st.info("Tip: you can switch to **Demo Mode** in the sidebar and try again.")
    except Exception:  # noqa: BLE001 - never show a stack trace to the user
        log.exception("Unexpected error while summarising")
        st.error("Something went wrong. Please try again.")


settings = render_sidebar()

st.title("🎙️ RecapRoom AI")
render_hero_header()

with st.expander("📖 How to use RecapRoom AI", expanded="summary" not in st.session_state):
    st.markdown("""
    1. **Provide a transcript**: choose a quick sample below, paste raw text, upload a `.txt` file, or upload audio.
    2. **Configure settings** in the sidebar: output length (*Brief / Standard / Detailed*), format (*Bullet notes / Narrative / Table*), and AI Provider.
    3. **Click Summarise**: results display with **`STATED`** (backed by verbatim quotes and line numbers) or **`INFERRED`** labels.
    4. **Export notes**: download verified notes as Markdown or plain text with full provenance preserved.
    """)

st.info("🔒 **Privacy & Safety Notice:** Do not upload confidential or personal PII data. In Live Mode the transcript text is processed by the selected AI provider. In Demo Mode all execution is 100% offline and stays on your machine.")

modes = ["Paste text", "Upload .txt file"] + (["Audio (optional)"] if audio_available() else [])
mode = st.radio("Input method", modes, horizontal=True, key="input_mode")
rc = st.session_state["reset_counter"]
text = ""

if mode == "Paste text":
    st.markdown("**Quick Load Sample Transcripts:**")
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("💼 Engineering Sync", use_container_width=True):
        st.session_state["sample_choice"] = "short_meeting.txt"
        st.session_state["transcript_text"] = read_sample("short_meeting.txt")
        st.session_state.pop("summary", None)
        st.rerun()
    if q2.button("🎓 ML Lecture", use_container_width=True):
        st.session_state["sample_choice"] = "lecture_ml_basics.txt"
        st.session_state["transcript_text"] = read_sample("lecture_ml_basics.txt")
        st.session_state.pop("summary", None)
        st.rerun()
    if q3.button("⚠️ Ambiguous Meeting", use_container_width=True):
        st.session_state["sample_choice"] = "ambiguous_meeting.txt"
        st.session_state["transcript_text"] = read_sample("ambiguous_meeting.txt")
        st.session_state.pop("summary", None)
        st.rerun()
    if q4.button("🛡️ Prompt Injection", use_container_width=True):
        st.session_state["sample_choice"] = "injection_test.txt"
        st.session_state["transcript_text"] = read_sample("injection_test.txt")
        st.session_state.pop("summary", None)
        st.rerun()

    st.selectbox("Or select from all samples", ["—"] + list_samples(), key="sample_choice", on_change=_on_sample)
    text = st.text_area("Transcript content", key="transcript_text", height=280,
                        placeholder="Paste your lecture or meeting transcript here…")
elif mode == "Upload .txt file":
    up = st.file_uploader("Upload a .txt transcript (max 2 MB)", type=["txt"], key=f"upload_{rc}")
    if up is not None:
        try:
            text, file_warnings = validate_upload(up.name, up.getvalue())
            for w in file_warnings:
                st.warning(w)
            with st.expander("📄 Document Preview", expanded=True):
                st.text(text[:1500] + ("…" if len(text) > 1500 else ""))
        except ValueError as err:
            st.warning(str(err))
else:
    st.caption("Audio is transcribed with Groq Whisper. **Review and edit the transcript before summarising.** "
               "Transcription can contain acoustic errors, and speaker labels are usually missing.")
    audio = st.file_uploader("Upload audio (mp3, wav, m4a; max 24 MB)", type=["mp3", "wav", "m4a"], key=f"audio_{rc}")
    if audio is not None and st.button("Transcribe audio", type="secondary"):
        try:
            with st.spinner("Transcribing with Whisper…"):
                st.session_state["audio_text"] = transcribe_audio(audio.name, audio.getvalue())
        except (ValueError, LLMError) as err:
            st.warning(str(err))
        except Exception:  # noqa: BLE001
            log.exception("Transcription failed")
            st.error("Transcription failed. Please try again.")
    if "audio_text" in st.session_state:
        text = st.text_area("Transcript (review and edit before summarising)", key="audio_text", height=280)

if text.strip():
    words = count_words(text)
    chunks = estimate_chunks(words)
    pipeline_type = "Single-Pass Fast Pipeline" if words <= 4000 else f"Map-Reduce Pipeline (~{chunks} chunks)"
    st.markdown(f'<div style="background:rgba(128,128,128,0.06);padding:8px 14px;border-radius:8px;'
                f'margin:8px 0 16px 0;font-size:0.88rem;display:flex;justify-content:space-between;align-items:center">'
                f'<span>📊 <b>Metrics:</b> {words:,} words &nbsp;·&nbsp; {len(text):,} chars</span>'
                f'<span style="background:rgba(37,99,235,0.1);color:#2563eb;padding:2px 8px;border-radius:6px;font-weight:600">⚡ {pipeline_type}</span>'
                f'</div>', unsafe_allow_html=True)

c1, c2, _ = st.columns([1.2, 1, 4])
go = c1.button("✨ Summarise", type="primary", use_container_width=True)
c2.button("Reset", on_click=_reset, use_container_width=True)
if go:
    _run(text, settings)

if "summary" in st.session_state:
    st.divider()
    render_summary(st.session_state["summary"])
