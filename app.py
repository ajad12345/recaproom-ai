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

st.set_page_config(page_title="RecapRoom AI", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded",
                   menu_items={"About": "RecapRoom AI: Lecture and Meeting Summarizer (GMRIT student project)"})
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
        bar = st.progress(0.0, text="Starting…")

        def on_progress(done: int, total: int, msg: str):
            bar.progress(min(done / total, 1.0), text=msg)

        with st.spinner("Summarising…"):
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
st.subheader("Lecture and Meeting Summarizer")
st.write("Turn a long transcript into an overview, key points, decisions, action items and open questions. "
         "Every item is labelled **Stated** (backed by a quote and line number) or **Inferred** (the model's interpretation). "
         "Owners and deadlines are never invented.")
with st.expander("How to use", expanded="summary" not in st.session_state):
    st.markdown("1. **Add a transcript**: paste it, upload a `.txt` file, or load a sample.\n"
                "2. **Pick settings** in the sidebar (length, format, Meeting or Lecture).\n"
                "3. **Click Summarise**, then check the evidence tab and export your notes.")
st.info("🔒 **Privacy:** do not upload confidential or personal data. In Live Mode the transcript text is sent to the "
        "selected AI provider. Demo Mode never leaves your machine.")

modes = ["Paste text", "Upload .txt file"] + (["Audio (optional)"] if audio_available() else [])
mode = st.radio("Input method", modes, horizontal=True, key="input_mode")
rc = st.session_state["reset_counter"]
text = ""

if mode == "Paste text":
    st.selectbox("Load a sample transcript", ["—"] + list_samples(), key="sample_choice", on_change=_on_sample)
    text = st.text_area("Transcript", key="transcript_text", height=280,
                        placeholder="Paste your lecture or meeting transcript here…")
elif mode == "Upload .txt file":
    up = st.file_uploader("Upload a .txt transcript (max 2 MB)", type=["txt"], key=f"upload_{rc}")
    if up is not None:
        try:
            text, file_warnings = validate_upload(up.name, up.getvalue())
            for w in file_warnings:
                st.warning(w)
            with st.expander("Preview"):
                st.text(text[:1500] + ("…" if len(text) > 1500 else ""))
        except ValueError as err:
            st.warning(str(err))
else:
    st.caption("Audio is transcribed with Groq Whisper. **Review and edit the transcript before summarising.** "
               "Transcription can contain errors, and speaker labels are usually missing.")
    audio = st.file_uploader("Upload audio (mp3, wav, m4a; max 24 MB)", type=["mp3", "wav", "m4a"], key=f"audio_{rc}")
    if audio is not None and st.button("Transcribe audio"):
        try:
            with st.spinner("Transcribing…"):
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
    st.caption(f"{words:,} words · {len(text):,} characters · ~{estimate_chunks(words)} processing section(s)")

c1, c2, _ = st.columns([1, 1, 4])
go = c1.button("✨ Summarise", type="primary", use_container_width=True)
c2.button("Reset", on_click=_reset, use_container_width=True)
if go:
    _run(text, settings)

if "summary" in st.session_state:
    st.divider()
    render_summary(st.session_state["summary"])
