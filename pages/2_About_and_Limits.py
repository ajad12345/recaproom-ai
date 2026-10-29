"""Privacy, limitations and how to read RecapRoom's output."""
import streamlit as st

from components.sidebar import render_sidebar
from components.ui_theme import inject_custom_theme

st.set_page_config(page_title="About & Limits · RecapRoom AI", page_icon="ℹ️", layout="wide")
inject_custom_theme()
render_sidebar()

st.title("ℹ️ About, Privacy and Limits")
st.header("How to read the output")
st.markdown(
    "- 🟢 **STATED**: backed by a short quote from the transcript and a line number. The verifier checked that the quote exists.\n"
    "- 🟠 **INFERRED**: the model's interpretation or a summary across lines. Treat it as a suggestion and verify it.\n"
    "- **Not specified**: the transcript does not say it. RecapRoom never guesses owners or deadlines.\n"
    "- The **overview** is always inferred.")
st.header("Privacy")
st.markdown(
    "- **Do not upload confidential or personal data.**\n"
    "- **Demo Mode** runs fully on this machine: nothing is sent anywhere.\n"
    "- **Live Mode** sends the transcript text to the selected provider (Groq or Gemini). Check their privacy policies first.\n"
    "- Transcripts and results live only in your browser session. On Streamlit Community Cloud nothing is saved between sessions, "
    "so download your export before leaving.\n"
    "- API keys are read from `.env` or Streamlit secrets by the backend only and are never shown or logged.")
st.header("Known limitations")
st.markdown(
    "1. **Model errors:** a language model can still mislabel an item. The verifier catches invented quotes, owners and deadlines, "
    "but not every wrong interpretation.\n"
    "2. **Speech-to-text transcripts:** recognition mistakes carry into the notes. Review the transcript first.\n"
    "3. **Speaker attribution:** detection is pattern-based and fails when labels are missing or inconsistent.\n"
    "4. **Rate limits:** free provider tiers limit tokens per minute; very long transcripts may hit them.\n"
    "5. **Language:** English only for now.\n"
    "6. **Demo Mode:** uses simple rules, so its notes are basic. It exists to demonstrate the workflow without a key.\n"
    "7. **Comparison:** matching actions between meetings uses text similarity; paraphrased tasks can be missed or flagged as uncertain.")
st.header("Responsible use")
st.write("RecapRoom is an educational note-taking assistant. Do not rely on it alone for decisions with legal, "
         "financial, health or career consequences. Always check important items against the original transcript.")

st.divider()
st.header("👥 Project Team")
st.markdown("""
**GMR Institute of Technology (GMRIT) — Department of Computer Science & Engineering**
- **Jammu Dinesh** (`23341A05A3`) — Preprocessing, Line Indexing, Chunker & Map-Reduce Pipeline
- **Manish Sharma** (`23341A05F7`) — LLM Integrations (Groq & Gemini), Prompts & Offline Engine
- **Mohammed Ajad** (`23341A05G3`) — Streamlit UI, Deterministic Verifier, Meeting Diff & Cloud Deployment
""")
